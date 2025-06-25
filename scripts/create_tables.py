import asyncio
import sys
import logging
from pathlib import Path
from sqlalchemy import text, inspect

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Añadir el directorio raíz al path para que Python pueda encontrar los módulos
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.db.session import engine, Base, AsyncSessionLocal

# Importar explícitamente todos los modelos
from app.models.user import User
from app.models.store import Store
from app.models.product import Product
from app.models.order import Order
from app.models.user_store_association import UserStoreAssociation

logger.info("Importación de modelos completada")

async def create_schema():
    """Crea el esquema de desarrollo si no existe."""
    schema_name = settings.ENVIRONMENT.lower()
    print(f"  🔍 Verificando esquema '{schema_name}'...")
    
    try:
        async with engine.begin() as conn:
            # Verificar si el esquema ya existe
            result = await conn.execute(
                text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema"),
                {"schema": schema_name}
            )
            schema_exists = result.scalar() is not None
            
            if not schema_exists:
                print(f"  🆕 Creando esquema '{schema_name}'...")
                await conn.execute(text(f"CREATE SCHEMA {schema_name}"))
                await conn.commit()
                print(f"  ✅ Esquema '{schema_name}' creado exitosamente")
            else:
                print(f"  ✅ El esquema '{schema_name}' ya existe")
                
    except Exception as e:
        print(f"❌ Error al crear/verificar esquema: {str(e)}")
        raise

async def drop_all_tables():
    """Elimina todas las tablas de todos los esquemas."""
    try:
        async with engine.begin() as conn:
            # Obtener todas las tablas
            print("  🔍 Buscando tablas existentes...")
            result = await conn.execute(text(
                """
                SELECT table_schema, table_name 
                FROM information_schema.tables 
                WHERE table_schema IN ('public', 'development')
                AND table_type = 'BASE TABLE'
                """
            ))
            tables = result.fetchall()
            
            if not tables:
                print("  ℹ️  No se encontraron tablas para eliminar")
                return
                
            print(f"  🗑️  Eliminando {len(tables)} tablas...")
            
            # Eliminar cada tabla
            for i, (schema, table) in enumerate(tables, 1):
                try:
                    print(f"    {i}. Eliminando tabla: {schema}.{table}")
                    await conn.execute(text(f'DROP TABLE IF EXISTS \"{schema}\".\"{table}\" CASCADE'))
                except Exception as e:
                    print(f"    ❌ Error al eliminar {schema}.{table}: {str(e)}")
            
            await conn.commit()
            print("  ✅ Todas las tablas eliminadas exitosamente")
            
    except Exception as e:
        print(f"❌ Error al eliminar tablas: {str(e)}")
        raise

async def create_tables():
    """Crea todas las tablas definidas en los modelos."""
    print("🔧 Configurando base de datos...")
    
    try:
        # 1. Crear esquema de desarrollo si no existe
        print("\n📂 Creando/Verificando esquema de desarrollo...")
        await create_schema()
        
        # 2. Eliminar tablas existentes
        print("\n🗑️  Eliminando tablas existentes...")
        await drop_all_tables()
        
        # 3. Crear todas las tablas en el esquema de desarrollo
        print("\n🛠️  Creando tablas en el esquema de desarrollo...")
        schema_name = settings.ENVIRONMENT.lower()
        
        # Configurar el esquema para todos los modelos
        print(f"  🔄 Configurando esquema '{schema_name}' para los modelos...")
        
        # Verificar que hay tablas en los metadatos
        if not Base.metadata.tables:
            print("  ⚠️  No se encontraron tablas en los metadatos de SQLAlchemy")
            print("  🔍 Tablas registradas en Base.metadata.tables:", list(Base.metadata.tables.keys()))
            print("  ℹ️  Asegúrate de que los modelos estén correctamente importados")
            return False
            
        # Configurar esquema para cada tabla
        for table_name, table in Base.metadata.tables.items():
            table.schema = schema_name
            print(f"    - Tabla: {schema_name}.{table_name}")
        
        print("  🏗️  Creando tablas...")
        try:
            async with engine.begin() as conn:
                # Crear el esquema si no existe
                await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
                # Establecer el search_path para esta conexión
                await conn.execute(text(f'SET search_path TO "{schema_name}"'))
                # Crear todas las tablas
                await conn.run_sync(Base.metadata.create_all)
                await conn.commit()
                print("  ✅ Tablas creadas exitosamente")
        except Exception as e:
            print(f"  ❌ Error al crear tablas: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        print(f"\n✅ ¡Tablas creadas exitosamente en el esquema '{schema_name}'!")
        
        # 4. Verificar las tablas creadas
        print("\n🔍 Verificando tablas creadas...")
        try:
            async with engine.connect() as conn:
                # Verificar tablas en el esquema
                result = await conn.execute(
                    text("""\
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = :schema
                    ORDER BY table_name
                    """),
                    {"schema": schema_name}
                )
                tables = result.scalars().all()
                
                if tables:
                    print("\n📋 Tablas creadas en el esquema:")
                    for i, table in enumerate(tables, 1):
                        print(f"   {i}. {schema_name}.{table}")
                        
                    # Verificar columnas de una tabla de ejemplo (users)
                    try:
                        columns_result = await conn.execute(
                            text("""
                            SELECT column_name, data_type, is_nullable
                            FROM information_schema.columns 
                            WHERE table_schema = :schema AND table_name = 'users'
                            ORDER BY ordinal_position
                            """),
                            {"schema": schema_name}
                        )
                        columns = columns_result.fetchall()
                        if columns:
                            print("\n🔍 Columnas de la tabla 'users':")
                            for col in columns:
                                print(f"   - {col.column_name}: {col.data_type} (NULL: {col.is_nullable})")
                    except Exception as e:
                        print(f"  ⚠️  No se pudieron obtener las columnas de la tabla 'users': {str(e)}")
                else:
                    print("\n⚠️  No se encontraron tablas en el esquema")
                    
                    # Verificar esquemas existentes
                    schemas_result = await conn.execute(
                        text("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name")
                    )
                    schemas = schemas_result.scalars().all()
                    print("\n🔍 Esquemas existentes en la base de datos:")
                    for i, schema in enumerate(schemas, 1):
                        print(f"   {i}. {schema}")
                        
        except Exception as e:
            print(f"  ❌ Error al verificar tablas: {str(e)}")
            return False
                
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante la creación de tablas: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()

if __name__ == "__main__":
    print("🚀 Iniciando configuración de la base de datos...")
    print(f"🔌 Conectando a: {settings.DATABASE_URL}")
    print(f"🏗️  Entorno: {settings.ENVIRONMENT}")
    
    try:
        success = asyncio.run(create_tables())
        if not success:
            print("\n❌ La creación de tablas falló. Por favor revisa los errores anteriores.")
            sys.exit(1)
            
        print("\n✨ Proceso completado exitosamente!")
        print("💡 Recuerda ejecutar 'python -m scripts.seed_database' para poblar la base de datos con datos de prueba.")
        
    except KeyboardInterrupt:
        print("\n❌ Proceso cancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Asegurarse de que la conexión se cierre correctamente
        if 'engine' in locals():
            # No podemos usar await aquí, ya que estamos fuera de una función asíncrona
            # La conexión se cierra automáticamente al final del script
            pass
