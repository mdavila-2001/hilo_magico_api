import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_connection():
    """Test database connection and basic operations"""
    logger.info("🚀 Probando conexión a la base de datos...")
    logger.info(f"URL de conexión: {settings.DATABASE_URL}")
    
    # Crear motor con más opciones de depuración
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True,
        pool_pre_ping=True,
        pool_recycle=300
    )
    
    try:
        # Probar conexión
        async with engine.connect() as conn:
            logger.info("✅ Conexión exitosa a la base de datos")
            
            # Obtener versión de PostgreSQL
            result = await conn.execute(text("SELECT version()"))
            db_version = result.scalar_one()
            logger.info(f"📊 Versión de la base de datos: {db_version}")
            
            # Verificar esquema development
            result = await conn.execute(
                text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'development'")
            )
            schema_exists = result.scalar_one_or_none() is not None
            
            if not schema_exists:
                logger.warning("⚠️  El esquema 'development' no existe. Creando...")
                await conn.execute(text("CREATE SCHEMA IF NOT EXISTS development"))
                await conn.commit()
                logger.info("✅ Esquema 'development' creado exitosamente")
            else:
                logger.info("✅ El esquema 'development' ya existe")
            
            # Verificar si la tabla users existe
            result = await conn.execute(
                text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'development' 
                    AND table_name = 'users'
                )
                """)
            )
            table_exists = result.scalar_one()
            
            if table_exists:
                logger.info("✅ La tabla 'users' existe en el esquema 'development'")
                
                # Contar usuarios
                result = await conn.execute(
                    text("SELECT COUNT(*) FROM development.users")
                )
                count = result.scalar_one()
                logger.info(f"👥 Número de usuarios en la base de datos: {count}")
                
                # Mostrar estructura de la tabla
                result = await conn.execute(
                    text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_schema = 'development' 
                    AND table_name = 'users'
                    ORDER BY ordinal_position
                    """)
                )
                
                logger.info("\n📋 Estructura de la tabla 'users':")
                logger.info("-" * 80)
                logger.info(f"{'Columna':<25} | {'Tipo':<20} | ¿Nulo?")
                logger.info("-" * 80)
                
                for row in result.fetchall():
                    logger.info(f"{row[0]:<25} | {row[1]:<20} | {'Sí' if row[2] == 'YES' else 'No'}")
                
            else:
                logger.warning("⚠️  La tabla 'users' NO existe en el esquema 'development'")
                
    except Exception as e:
        logger.error(f"❌ Error de conexión: {str(e)}", exc_info=True)
        raise
    finally:
        if engine:
            await engine.dispose()
            logger.info("🔌 Conexión cerrada")

if __name__ == "__main__":
    asyncio.run(test_connection())
