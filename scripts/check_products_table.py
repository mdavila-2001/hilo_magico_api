import asyncio
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Cargar variables de entorno
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def check_products_table():
    # Crear motor asíncrono
    engine = create_async_engine(DATABASE_URL)
    
    try:
        async with engine.connect() as conn:
            # Verificar si la tabla products existe
            result = await conn.execute(
                text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'development' AND table_name = 'products';
                """)
            )
            
            columns = result.fetchall()
            
            if not columns:
                print("La tabla 'products' no existe en el esquema 'development'.")
                return
                
            print("\nEstructura de la tabla 'products':")
            print("-" * 80)
            print(f"{'Columna':<30} {'Tipo':<20} {'Nulo?':<10} {'Valor por defecto'}")
            print("-" * 80)
            
            for col in columns:
                print(f"{col[0]:<30} {col[1]:<20} {col[2]:<10} {col[3] or 'None'}")
            
            # Verificar si hay algún producto en la tabla
            result = await conn.execute(
                text("SELECT COUNT(*) FROM development.products")
            )
            count = result.scalar()
            print(f"\nTotal de productos en la tabla: {count}")
            
    except Exception as e:
        print(f"Error al verificar la tabla 'products': {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_products_table())
