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
    async with engine.begin() as conn:
        # Crear esquema development si no existe
        schema_name = settings.ENVIRONMENT.lower()
        await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
        await conn.commit()

async def drop_all_tables():
    """Elimina todas las tablas de todos los esquemas."""
    async with engine.begin() as conn:
        # Obtener todas las tablas
        result = await conn.execute(text(
            """
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_schema IN ('public', 'development')
            AND table_type = 'BASE TABLE'
            """
        ))
        tables = result.fetchall()
        
        # Eliminar cada tabla
        for schema, table in tables:
            await conn.execute(text(f'DROP TABLE IF EXISTS \"{schema}\".\"{table}\" CASCADE'))
        await conn.commit()

async def create_tables():
    """Crea todas las tablas definidas en los modelos."""
    print("🔧 Configurando base de datos...")
    
    # 1. Crear esquema de desarrollo si no existe
    print("📂 Creando/Verificando esquema de desarrollo...")
    await create_schema()
    
    # 2. Eliminar tablas existentes
    print("🗑️  Eliminando tablas existentes...")
    await drop_all_tables()
    
    # 3. Crear todas las tablas en el esquema de desarrollo
    print("🛠️  Creando tablas en el esquema de desarrollo...")
    schema_name = settings.ENVIRONMENT.lower()
    
    # Configurar el esquema para todos los modelos
    for table in Base.metadata.tables.values():
        table.schema = schema_name
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print(f"✅ ¡Tablas creadas exitosamente en el esquema '{schema_name}'!")
    
    # 4. Verificar tablas creadas
    async with AsyncSessionLocal() as session:
        result = await session.execute(text(
            f"""
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_schema = '{schema_name}'
            ORDER BY table_name
            """
        ))
        tables = result.fetchall()
        
        if tables:
            print("\n📋 Tablas creadas:")
            for schema, table in tables:
                print(f"   - {schema}.{table}")
        else:
            print("\n⚠️ No se encontraron tablas en el esquema.")

if __name__ == "__main__":
    print("🚀 Iniciando configuración de la base de datos...")
    print(f"🔌 Conectando a: {settings.DATABASE_URL}")
    print(f"🏗️  Entorno: {settings.ENVIRONMENT}")
    
    try:
        asyncio.run(create_tables())
        print("\n✨ Proceso completado exitosamente!")
        print("💡 Recuerda ejecutar 'python -m scripts.seed_database' para poblar la base de datos con datos de prueba.")
    except Exception as e:
        print(f"\n❌ Error durante la creación de tablas: {str(e)}")
        import traceback
        traceback.print_exc()
