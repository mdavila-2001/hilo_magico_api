import asyncio
import os
import sys
import logging
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Añadir el directorio raíz al path para poder importar la configuración
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.core.config import settings
except ImportError as e:
    logger.error("❌ No se pudo importar la configuración. Asegúrate de que el módulo app existe.")
    logger.error(f"Error: {e}")
    sys.exit(1)

def get_db_url():
    """Obtiene y formatea correctamente la URL de la base de datos."""
    db_url = settings.DATABASE_URL
    logger.info(f"URL de la base de datos original: {db_url}")
    
    # Asegurarse de que la URL use el driver asyncpg
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        logger.info(f"URL modificada para asyncpg: {db_url}")
    
    return db_url

async def test_connection():
    logger.info("🔍 Iniciando prueba de conexión a la base de datos...")
    
    try:
        db_url = get_db_url()
        logger.info(f"📡 Intentando conectar a: {db_url}")
        
        # Crear motor asíncrono con configuración mínima
        engine = create_async_engine(
            db_url,
            echo=True,  # Muestra las consultas SQL
            pool_pre_ping=True  # Verifica la conexión antes de usarla
        )
        
        logger.info("✅ Motor de base de datos creado correctamente")
        
        async with engine.connect() as conn:
            print("\n✅ Conexión exitosa con la base de datos")
            
            # Obtener información de la base de datos
            result = await conn.execute(text("SELECT version()"))
            db_version = result.scalar()
            print(f"\n📊 Versión de PostgreSQL: {db_version}")
            
            # Obtener listado de tablas
            print("\n📋 Tablas en la base de datos:")
            result = await conn.execute(text("""
                SELECT table_schema, table_name 
                FROM information_schema.tables 
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                ORDER BY table_schema, table_name
            """))
            
            tables = result.fetchall()
            if tables:
                for schema, table in tables:
                    print(f"   - {schema}.{table}")
            else:
                print("   No se encontraron tablas en la base de datos.")
            
            # Verificar si hay usuarios en la tabla de usuarios (si existe)
            try:
                result = await conn.execute(text("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users')"))
                users_table_exists = result.scalar()
                
                if users_table_exists:
                    result = await conn.execute(text("SELECT COUNT(*) FROM users"))
                    user_count = result.scalar()
                    print(f"\n👥 Usuarios en la base de datos: {user_count}")
                else:
                    print("\nℹ️ La tabla 'users' no existe en la base de datos.")
                    
            except Exception as e:
                print(f"\n⚠️ No se pudo verificar la tabla de usuarios: {e}")
    
    except ImportError as e:
        logger.error(f"❌ Error de importación: {e}")
        logger.error("Asegúrate de que todos los paquetes estén instalados correctamente.")
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}", exc_info=True)
        logger.error("\n🔧 Posibles soluciones:")
        logger.error("1. Verifica que la URL de conexión en .env sea correcta")
        logger.error("2. Asegúrate de que la base de datos esté en línea y accesible")
        logger.error("3. Verifica que el usuario y contraseña sean correctos")
        logger.error("4. Comprueba que tu conexión a internet sea estable")
        logger.error("5. Si usas una VPN, asegúrate de que permite conexiones a la base de datos")
        logger.error(f"\n🔍 Error detallado: {str(e)}")
    finally:
        if 'engine' in locals():
            try:
                await engine.dispose()
                logger.info("🔌 Conexión cerrada correctamente")
            except Exception as e:
                logger.error(f"⚠️ Error al cerrar la conexión: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando prueba de conexión a la base de datos...")
    asyncio.run(test_connection())