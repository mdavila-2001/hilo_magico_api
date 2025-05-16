import sys
sys.path.append('.')

import asyncio
from app.db.session import engine
from app.models import user
from app.models import store
from app.db.session import Base

async def create_tables():
    print("🔧 Creando tablas en la base de datos...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tablas creadas correctamente.")

if __name__ == "__main__":
    asyncio.run(create_tables())