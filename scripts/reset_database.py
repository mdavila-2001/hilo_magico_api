"""
Script para reiniciar completamente la base de datos.

Este script:
1. Elimina todas las tablas existentes
2. Elimina tipos personalizados (enums, etc.)
3. Crea el esquema de desarrollo
4. Crea todas las tablas
5. Pobla la base de datos con datos iniciales
"""
import asyncio
import sys
import os
from pathlib import Path
from typing import List, Tuple

# Añadir el directorio raíz al path para que Python pueda encontrar los módulos
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import settings
from app.db.session import Base, AsyncSessionLocal, engine as db_engine
from app.models import *  # Importa todos los modelos

# Configuración de logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def drop_all_constraints(conn, schema: str = 'development') -> None:
    """Elimina todas las restricciones de clave foránea."""
    logger.info(f"Buscando restricciones en el esquema {schema}...")
    
    # Obtener todas las restricciones de clave foránea
    query = """
    SELECT conname, conrelid::regclass, confrelid::regclass
    FROM pg_constraint
    WHERE contype = 'f' 
    AND conrelid IN (
        SELECT oid FROM pg_class 
        WHERE relnamespace = (
            SELECT oid FROM pg_namespace WHERE nspname = :schema
        )
    )
    """
    
    result = await conn.execute(text(query), {"schema": schema})
    constraints = result.fetchall()
    
    # Eliminar cada restricción
    for conname, conrelid, confrelid in constraints:
        try:
            logger.info(f"Eliminando restricción {conname} de {conrelid}")
            await conn.execute(
                text(f'ALTER TABLE {conrelid} DROP CONSTRAINT IF EXISTS \"{conname}\" CASCADE')
            )
        except Exception as e:
            logger.error(f"Error eliminando restricción {conname}: {e}")
    
    await conn.commit()

async def drop_all_tables(engine: AsyncEngine) -> None:
    """Elimina todas las tablas de los esquemas public y development."""
    logger.info("🗑️  Eliminando tablas existentes...")
    
    async with engine.begin() as conn:
        # Obtener todas las tablas
        query = """
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_schema IN ('public', 'development')
        AND table_type = 'BASE TABLE'
        """
        result = await conn.execute(text(query))
        tables = result.fetchall()
        
        if not tables:
            logger.info("No se encontraron tablas para eliminar.")
            return
            
        # Eliminar restricciones primero
        for schema, _ in tables:
            await drop_all_constraints(conn, schema)
        
        # Deshabilitar triggers temporalmente
        await conn.execute(text('SET session_replication_role = "replica";'))
        
        # Eliminar cada tabla
        for schema, table in tables:
            try:
                logger.info(f"  - Eliminando {schema}.{table}")
                await conn.execute(
                    text(f'DROP TABLE IF EXISTS \"{schema}\".\"{table}\" CASCADE')
                )
            except Exception as e:
                logger.error(f"Error eliminando {schema}.{table}: {e}")
        
        # Volver a habilitar triggers
        await conn.execute(text('SET session_replication_role = "origin";'))
        await conn.commit()

async def drop_all_types(engine: AsyncEngine) -> None:
    """Elimina todos los tipos personalizados (enums, etc.)."""
    logger.info("🗑️  Eliminando tipos personalizados...")
    
    async with engine.begin() as conn:
        # Obtener todos los tipos personalizados
        query = """
        SELECT n.nspname as schema, t.typname as type_name
        FROM pg_type t 
        LEFT JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace 
        WHERE (t.typrelid = 0 OR (SELECT c.relkind = 'c' FROM pg_catalog.pg_class c WHERE c.oid = t.typrelid))
        AND NOT EXISTS(SELECT 1 FROM pg_catalog.pg_type el WHERE el.oid = t.typelem AND el.typarray = t.oid)
        AND n.nspname IN ('public', 'development')
        AND t.typtype = 'e'  # Solo tipos enum
        """
        result = await conn.execute(text(query))
        types = result.fetchall()
        
        if not types:
            logger.info("No se encontraron tipos personalizados para eliminar.")
            return
        
        # Eliminar cada tipo
        for schema, type_name in types:
            try:
                logger.info(f"  - Eliminando tipo {schema}.{type_name}")
                await conn.execute(
                    text(f'DROP TYPE IF EXISTS \"{schema}\".\"{type_name}\" CASCADE')
                )
            except Exception as e:
                logger.error(f"Error eliminando tipo {schema}.{type_name}: {e}")
        
        await conn.commit()

async def create_schema(engine: AsyncEngine) -> None:
    """Crea el esquema de desarrollo si no existe."""
    schema_name = settings.ENVIRONMENT.lower()
    logger.info(f"📂 Creando/Verificando esquema '{schema_name}'...")
    
    async with engine.begin() as conn:
        try:
            # Verificar si el esquema ya existe
            result = await conn.execute(
                text("SELECT 1 FROM pg_namespace WHERE nspname = :schema"),
                {"schema": schema_name}
            )
            schema_exists = result.scalar() is not None
            
            if not schema_exists:
                await conn.execute(text(f"CREATE SCHEMA \"{schema_name}\""))
                logger.info(f"  - Esquema '{schema_name}' creado exitosamente")
            else:
                logger.info(f"  - El esquema '{schema_name}' ya existe")
                
            await conn.commit()
        except Exception as e:
            logger.error(f"Error al crear el esquema: {e}")
            raise

async def create_tables(engine: AsyncEngine) -> None:
    """Crea todas las tablas definidas en los modelos."""
    schema_name = settings.ENVIRONMENT.lower()
    logger.info(f"🛠️  Creando tablas en el esquema '{schema_name}'...")
    
    # Configurar el esquema para todos los modelos
    for table in Base.metadata.tables.values():
        table.schema = schema_name
    
    try:
        async with engine.begin() as conn:
            # Crear las tablas
            logger.info("  - Creando tablas...")
            await conn.run_sync(Base.metadata.create_all)
            
            # Verificar las tablas creadas
            result = await conn.execute(text(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = :schema
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
                """
            ), {"schema": schema_name})
            
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"✅ Se crearon {len(tables)} tablas en el esquema '{schema_name}':")
            for table in tables:
                logger.info(f"   - {schema_name}.{table}")
                
    except Exception as e:
        logger.error(f"Error al crear las tablas: {e}")
        raise

async def seed_initial_data() -> None:
    """Poblar la base de datos con datos iniciales."""
    logger.info("🌱 Poblando base de datos con datos iniciales...")
    
    try:
        # Importar aquí para evitar dependencias circulares
        from scripts.seed_users import seed_users
        
        # Ejecutar seeders
        logger.info("  - Ejecutando seeder de usuarios...")
        user_count = await asyncio.to_thread(seed_users)
        logger.info(f"  - Se crearon {user_count} usuarios de prueba")
        
        # Aquí puedes agregar más seeders si son necesarios
        # from scripts.seed_otra_tabla import seed_otra_tabla
        # await seed_otra_tabla()
        
        logger.info("✅ Datos iniciales creados exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error al poblar datos iniciales: {e}")
        raise

async def analyze_database(engine: AsyncEngine) -> None:
    """Analiza la base de datos y muestra información útil."""
    logger.info("🔍 Analizando base de datos...")
    
    async with engine.connect() as conn:
        # Obtener esquemas
        result = await conn.execute(text(
            "SELECT schema_name FROM information_schema.schemata ORDER BY schema_name"
        ))
        schemas = [row[0] for row in result.fetchall()]
        logger.info(f"\n📂 Esquemas encontrados: {', '.join(schemas)}")
        
        # Para cada esquema, mostrar tablas y tamaños
        for schema in schemas:
            if schema in ['pg_toast', 'pg_catalog', 'information_schema']:
                continue
                
            logger.info(f"\n📊 Esquema: {schema}")
            
            # Obtener tablas y sus tamaños
            result = await conn.execute(text("""
                SELECT 
                    table_name,
                    pg_size_pretty(pg_total_relation_size(quote_ident(table_schema) || '.' || quote_ident(table_name))) as size
                FROM information_schema.tables
                WHERE table_schema = :schema
                AND table_type = 'BASE TABLE'
                ORDER BY pg_total_relation_size(quote_ident(table_schema) || '.' || quote_ident(table_name)) DESC
            """), {"schema": schema})
            
            tables = result.fetchall()
            if tables:
                logger.info("  Tablas:")
                for table, size in tables:
                    logger.info(f"    - {table} ({size})")
            else:
                logger.info("  No hay tablas en este esquema")

def find_duplicate_files(directory: str) -> List[Tuple[str, List[str]]]:
    """Encuentra archivos duplicados en un directorio."""
    import hashlib
    from collections import defaultdict
    
    # Diccionario para almacenar hashes de archivos
    hashes = defaultdict(list)
    
    # Recorrer el directorio
    for root, _, files in os.walk(directory):
        # Ignorar directorios comunes que no necesitamos
        if any(ignore in root for ignore in ['__pycache__', '.git', '.venv', 'venv', 'node_modules']):
            continue
            
        for filename in files:
            # Ignorar archivos comunes que no necesitamos
            if any(filename.endswith(ext) for ext in ['.pyc', '.pyo', '.pyd', '.so', '.o']):
                continue
                
            filepath = os.path.join(root, filename)
            try:
                # Calcular hash del archivo
                hasher = hashlib.md5()
                with open(filepath, 'rb') as f:
                    buf = f.read()
                    hasher.update(buf)
                file_hash = hasher.hexdigest()
                
                # Agregar a nuestro diccionario
                hashes[file_hash].append(filepath)
            except (IOError, OSError) as e:
                logger.warning(f"No se pudo leer el archivo {filepath}: {e}")
    
    # Retornar solo los duplicados (listas con más de un elemento)
    return {k: v for k, v in hashes.items() if len(v) > 1}

async def cleanup_pycache(directory: str) -> None:
    """
    Elimina archivos __pycache__ y .pyc de manera segura.
    Ignora errores de permisos o archivos bloqueados.
    """
    logger.info(f"🧹 Limpiando archivos __pycache__ y .pyc en {directory}...")
    
    deleted = []
    errors = 0
    
    def safe_remove(path):
        nonlocal errors
        try:
            if os.path.isfile(path):
                os.remove(path)
                return True
            elif os.path.isdir(path):
                # Solo eliminar directorios vacíos
                if not os.listdir(path):
                    os.rmdir(path)
                    return True
        except (OSError, PermissionError) as e:
            errors += 1
            # No mostramos el error completo para no saturar la salida
            if errors < 5:  # Mostrar solo los primeros 5 errores
                logger.warning(f"  - No se pudo eliminar {path}: {str(e).split(':')[0]}")
            return False
        return False
    
    for root, dirs, files in os.walk(directory, topdown=False):
        # No recorrer directorios de entorno virtual
        if 'venv' in root or '.venv' in root or 'env' in root:
            continue
            
        # Eliminar archivos .pyc, .pyo, .pyd
        for f in files:
            if f.endswith(('.pyc', '.pyo', '.pyd')):
                path = os.path.join(root, f)
                if safe_remove(path):
                    deleted.append(path)
        
        # Eliminar directorios __pycache__ vacíos
        if os.path.basename(root) == '__pycache__':
            if safe_remove(root):
                deleted.append(root)
    
    if deleted:
        logger.info(f"  - Se eliminaron {len(deleted)} archivos/directorios")
    else:
        logger.info("  - No se encontraron archivos para limpiar")
        
    if errors > 5:
        logger.warning(f"  - Se omitieron {errors} archivos/directorios debido a errores")

async def main():
    """Función principal que orquesta el reinicio de la base de datos."""
    logger.info("🚀 Iniciando reinicio completo de la base de datos...")
    logger.info(f"🔌 Conectando a: {settings.DATABASE_URL}")
    logger.info(f"🏗️  Entorno: {settings.ENVIRONMENT}")
    
    # Usar el motor existente
    engine = db_engine
    
    try:
        # 0. Limpiar archivos temporales de Python
        await cleanup_pycache(os.path.dirname(os.path.dirname(__file__)))
        
        # 1. Analizar base de datos actual
        await analyze_database(engine)
        
        # 2. Eliminar tablas existentes
        await drop_all_tables(engine)
        
        # 3. Eliminar tipos personalizados
        await drop_all_types(engine)
        
        # 4. Crear esquema
        await create_schema(engine)
        
        # 5. Crear tablas
        await create_tables(engine)
        
        # 6. Poblar con datos iniciales
        await seed_initial_data()
        
        # 7. Analizar base de datos después de los cambios
        await analyze_database(engine)
        
        # 8. Buscar archivos duplicados
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        duplicates = find_duplicate_files(project_root)
        
        if duplicates:
            logger.warning("\n⚠️  Se encontraron archivos duplicados:")
            for file_hash, file_paths in duplicates.items():
                logger.warning(f"\nHash: {file_hash}")
                for path in file_paths:
                    logger.warning(f"  - {path}")
        else:
            logger.info("\n✅ No se encontraron archivos duplicados")
        
        logger.info("\n✨ ¡Base de datos reiniciada exitosamente!")
        
    except Exception as e:
        logger.error(f"\n❌ Error durante el reinicio de la base de datos: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        await engine.dispose()
        logger.info("🔌 Conexión a la base de datos cerrada")

if __name__ == "__main__":
    asyncio.run(main())
