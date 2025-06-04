import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def describe_table(schema: str, table_name: str):
    logger.info(f"Connecting to database: {settings.DATABASE_URL}")
    try:
        # Create an async engine
        engine = create_async_engine(settings.DATABASE_URL, echo=True)
        
        async with engine.begin() as conn:
            logger.info(f"Connected to database. Describing table: {schema}.{table_name}")
            # Get table columns
            result = await conn.execute(text(
                """
                SELECT 
                    column_name, 
                    data_type,
                    is_nullable,
                    column_default
                FROM 
                    information_schema.columns 
                WHERE 
                    table_schema = :schema
                    AND table_name = :table_name
                ORDER BY 
                    ordinal_position
                """
            ), {"schema": schema, "table_name": table_name})
        
            columns = result.fetchall()
            
            if not columns:
                logger.warning(f"No columns found for table {schema}.{table_name}")
                return
                
            print(f"\nTable: {schema}.{table_name}")
            print("-" * 70)
            print(f"{'Column':<25} | {'Type':<20} | {'Nullable':<10} | {'Default'}")
            print("-" * 70)
            for col in columns:
                col_name, data_type, is_nullable, col_default = col
                print(f"{col_name:<25} | {data_type:<20} | {is_nullable:<10} | {col_default or 'NULL'}")
            print("-" * 70)
            
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise
    finally:
        if 'engine' in locals():
            await engine.dispose()
            logger.info("Database connection closed")

if __name__ == "__main__":
    print("🔍 Describing database table...")
    asyncio.run(describe_table("development", "users"))
