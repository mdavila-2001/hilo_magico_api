from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True
)

# Configuración de la sesión asíncrona
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

# Dependencia para obtener la sesión de la base de datos
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Proveedor de dependencia que obtiene una sesión de base de datos.
    
    Uso:
    ```python
    async def some_endpoint(db: AsyncSession = Depends(get_db)):
        # Usar la sesión db aquí
        pass
    ```
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()