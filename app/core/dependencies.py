"""
Módulo para definir las dependencias inyectables de la aplicación.
"""
from typing import Generator, AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.config import settings
from ....domain.entities.user import User
from ....infrastructure.persistence.database import AsyncSessionLocal
from ....infrastructure.persistence.sqlalchemy_unit_of_work import SQLAlchemyUnitOfWork
from ....domain.services.auth_service import AuthService
from ....domain.repositories.user_repository import UserRepository

# Esquema de autenticación OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Proveedor de dependencia para obtener una sesión de base de datos.
    
    Yields:
        AsyncSession: Sesión de base de datos asíncrona
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()


def get_unit_of_work() -> Generator[SQLAlchemyUnitOfWork, None, None]:
    """
    Proveedor de dependencia para obtener una unidad de trabajo.
    
    Yields:
        SQLAlchemyUnitOfWork: Unidad de trabajo configurada
    """
    with AsyncSessionLocal() as session:
        uow = SQLAlchemyUnitOfWork(session)
        try:
            yield uow
        finally:
            pass  # La sesión se cierra automáticamente al salir del contexto


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    uow: SQLAlchemyUnitOfWork = Depends(get_unit_of_work)
) -> User:
    """
    Obtiene el usuario actual a partir del token de autenticación.
    
    Args:
        token: Token JWT
        uow: Unidad de trabajo para acceder al repositorio de usuarios
        
    Returns:
        User: Usuario autenticado
        
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        with uow.repository(UserRepository) as user_repo:
            auth_service = AuthService(user_repo)
            user = await auth_service.get_current_user(token)
            
            if user is None:
                raise credentials_exception
                
            return user
            
    except JWTError:
        raise credentials_exception


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Verifica que el usuario actual esté activo.
    
    Args:
        current_user: Usuario obtenido del token
        
    Returns:
        User: Usuario activo
        
    Raises:
        HTTPException: Si el usuario está inactivo
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user
