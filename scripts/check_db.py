import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def check_database():
    logger.info("🔍 Checking database structure...")
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    
    try:
        # Create an async engine
        engine = create_async_engine(settings.DATABASE_URL, echo=True)
        
        async with engine.connect() as conn:
            logger.info("✅ Connected to database")
            
            # List all schemas
            result = await conn.execute(text("SELECT schema_name FROM information_schema.schemata"))
            schemas = [row[0] for row in result.fetchall()]
            logger.info(f"📂 Database schemas: {', '.join(schemas)}")
            
            # List all tables in the development schema
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
            
            # Check if users table exists
            if 'users' in tables:
                logger.info("🔎 Checking 'users' table structure...")
                result = await conn.execute(text(
                    """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_schema = 'development' AND table_name = 'users'
                    ORDER BY ordinal_position
                    """
                ))
                
                logger.info("\n📋 'users' table structure:")
                logger.info("-" * 70)
                logger.info(f"{'Column':<25} | {'Type':<20} | {'Nullable':<10} | {'Default'}")
                logger.info("-" * 70)
                
                for col in result.fetchall():
                    col_name, data_type, is_nullable, col_default = col
                    logger.info(f"{col_name:<25} | {data_type:<20} | {is_nullable:<10} | {col_default or 'NULL'}")
                
                # Check for required columns
                required_columns = {'email', 'hashed_password', 'first_name', 'last_name'}
                result = await conn.execute(text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema = 'development' AND table_name = 'users'"
                ))
                existing_columns = {row[0] for row in result.fetchall()}
                missing_columns = required_columns - existing_columns
                
                if missing_columns:
                    logger.warning(f"⚠️  Missing required columns in 'users' table: {', '.join(missing_columns)}")
                else:
                    logger.info("✅ All required columns are present in 'users' table")
            
            # Check for sample data
            try:
                result = await conn.execute(text("SELECT COUNT(*) FROM development.users"))
                count = result.scalar_one()
                logger.info(f"📊 Total users in database: {count}")
            except Exception as e:
                logger.warning(f"⚠️  Could not count users: {str(e)}")
                
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}", exc_info=True)
        return False
    finally:
        if 'engine' in locals():
            await engine.dispose()
            logger.info("🔌 Database connection closed")
    
    return True

if __name__ == "__main__":
    logger.info("🚀 Starting database check...")
    success = asyncio.run(check_database())
    if success:
        logger.info("✅ Database check completed successfully")
    else:
        logger.error("❌ Database check failed")
