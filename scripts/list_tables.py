import sys
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings

async def list_tables():
    # Create an async engine
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.begin() as conn:
        # Get all tables in the public and development schemas
        result = await conn.execute(text(
            """
            SELECT table_schema, table_name 
            FROM information_schema.tables 
            WHERE table_schema IN ('public', 'development')
            ORDER BY table_schema, table_name
            """
        ))
        tables = result.fetchall()
        
        if not tables:
            print("No tables found in the database.")
            return
            
        print("\nDatabase Tables:")
        print("-" * 50)
        print(f"{'Schema':<15} | {'Table Name'}")
        print("-" * 50)
        for schema, table in tables:
            print(f"{schema:<15} | {table}")
        print("-" * 50)

if __name__ == "__main__":
    print("🔍 Listing database tables...")
    asyncio.run(list_tables())
