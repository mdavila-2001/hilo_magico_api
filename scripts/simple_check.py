import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def check_db():
    """Simple database connection and schema check"""
    logger.info("🚀 Starting database check...")
    
    engine = None
    try:
        # Create engine with connection pooling
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=True,
            pool_pre_ping=True,
            pool_recycle=300
        )
        
        # Test connection
        async with engine.connect() as conn:
            logger.info("✅ Successfully connected to database")
            
            # Get database version
            result = await conn.execute(text("SELECT version()"))
            db_version = result.scalar_one()
            logger.info(f"📊 Database version: {db_version}")
            
            # List schemas
            result = await conn.execute(text(
                "SELECT schema_name FROM information_schema.schemata ORDER BY schema_name"
            ))
            schemas = [row[0] for row in result.fetchall()]
            logger.info(f"📂 Available schemas: {', '.join(schemas)}")
            
            # List tables in development schema
            if 'development' in schemas:
                result = await conn.execute(text(
                    """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'development'
                    ORDER BY table_name
                    """
                ))
                tables = [row[0] for row in result.fetchall()]
                logger.info(f"📊 Tables in 'development' schema: {', '.join(tables) if tables else 'None'}")
                
                if 'users' in tables:
                    # Get columns for users table
                    result = await conn.execute(text(
                        """
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns 
                        WHERE table_schema = 'development' 
                        AND table_name = 'users'
                        ORDER BY ordinal_position
                        """
                    ))
                    logger.info("\n📋 'users' table columns:")
                    for col in result.fetchall():
                        logger.info(f"- {col[0]} ({col[1]}, {'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            
            # Try a simple query
            try:
                result = await conn.execute(text("SELECT 1"))
                value = result.scalar_one()
                logger.info(f"✅ Simple query test: SELECT 1 = {value}")
            except Exception as e:
                logger.error(f"❌ Simple query failed: {str(e)}")
                
    except Exception as e:
        logger.error(f"❌ Database check failed: {str(e)}")
        return False
    finally:
        if engine:
            await engine.dispose()
            logger.info("🔌 Database connection closed")
    
    return True

if __name__ == "__main__":
    asyncio.run(check_db())
