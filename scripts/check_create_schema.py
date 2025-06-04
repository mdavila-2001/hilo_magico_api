import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def check_and_create_schema():
    """Verifica si el esquema development existe, si no, lo crea"""
    engine = None
    try:
        # Crear motor de conexión
        engine = create_async_engine(settings.DATABASE_URL, echo=True)
        
        async with engine.connect() as conn:
            logger.info("✅ Conectado a la base de datos")
            
            # Verificar si el esquema development existe
            result = await conn.execute(
                text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'development'")
            )
            schema_exists = result.scalar_one_or_none() is not None
            
            if not schema_exists:
                logger.warning("⚠️  El esquema 'development' no existe. Creando...")
                await conn.execute(text("CREATE SCHEMA development"))
                await conn.commit()
                logger.info("✅ Esquema 'development' creado exitosamente")
            else:
                logger.info("✅ El esquema 'development' ya existe")
            
            # Verificar tablas en el esquema development
            result = await conn.execute(
                text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'development'
                """)
            )
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                logger.info(f"📊 Tablas en el esquema 'development': {', '.join(tables)}")
            else:
                logger.warning("⚠️  No hay tablas en el esquema 'development'")
            
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        raise
    finally:
        if engine:
            await engine.dispose()
            logger.info("🔌 Conexión cerrada")

if __name__ == "__main__":
    logger.info("🚀 Iniciando verificación del esquema...")
    asyncio.run(check_and_create_schema())
