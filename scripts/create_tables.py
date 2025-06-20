import asyncio
import sys
from pathlib import Path
from sqlalchemy import text

# Añadir el directorio raíz al path para que Python pueda encontrar los módulos
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.db.session import engine, Base, AsyncSessionLocal
from app.models import *  # Importa todos los modelos para que SQLAlchemy los registre

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
        for table_name, table in Base.metadata.tables.items():
            table.schema = schema_name
            print(f"    - Tabla: {table_name}")
        
        print("  🏗️  Creando tablas...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print(f"\n✅ ¡Tablas creadas exitosamente en el esquema '{schema_name}'!")
        
        # 4. Verificar las tablas creadas
        print("\n🔍 Verificando tablas creadas...")
        async with engine.connect() as conn:
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
                print("\n📋 Tablas creadas:")
                for i, table in enumerate(tables, 1):
                    print(f"   {i}. {table}")
            else:
                print("\n⚠️  No se encontraron tablas en el esquema")
                
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
