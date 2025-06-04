from typing import AsyncGenerator, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import NullPool
from sqlalchemy.sql import text
from app.core.config import settings

# Configuración de la conexión a la base de datos
connect_args: Dict[str, Any] = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args["check_same_thread"] = False

# Crear el motor asíncrono
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
    poolclass=NullPool if "sqlite" in settings.DATABASE_URL else None,
    **connect_args
)

# Configuración de la sesión asíncrona
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base para los modelos SQLAlchemy
Base = declarative_base()

# Configurar el esquema por defecto basado en el entorno
schema_name = settings.ENVIRONMENT.lower()
Base.metadata.schema = schema_name

# Configurar el schema para las tablas existentes
for table in Base.metadata.tables.values():
    if not table.schema:
        table.schema = schema_name

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
            # Establecer el esquema de búsqueda para esta sesión
            await session.execute(text(f'SET search_path TO {schema_name}, public'))
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

# Función para obtener una sesión síncrona (útil para scripts)
def get_sync_db() -> Session:
    """Obtiene una sesión síncrona para scripts."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    sync_engine = create_engine(
        settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql"),
        pool_pre_ping=True
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
    return SessionLocal()