"""
Módulo para manejar los permisos de la aplicación.

Este módulo contiene funciones para verificar los permisos de los usuarios
y lanzar excepciones cuando no tienen los permisos necesarios.
"""
from typing import Optional
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserRole
from app.services.user_store import UserStoreService

class StorePermissions:
    """Clase para manejar los permisos relacionados con tiendas."""
    
    @staticmethod
    async def check_store_owner_or_admin(
        db: AsyncSession, 
        store_id: UUID, 
        user_id: UUID
    ) -> None:
        """
        Verifica si el usuario es propietario o administrador de la tienda.
        
        Args:
            db: Sesión de base de datos
            store_id: ID de la tienda
            user_id: ID del usuario a verificar
            
        Raises:
            HTTPException: Si el usuario no tiene permisos
        """
        user_store_service = UserStoreService(db)
        user_role = await user_store_service.get_user_role_in_store(store_id, user_id)
        
        # Si el usuario no tiene rol en la tienda o no es ni admin ni owner, denegar acceso
        if user_role not in [UserRole.ADMIN, UserRole.OWNER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para realizar esta acción en esta tienda"
            )
    
    @staticmethod
    async def check_store_owner(
        db: AsyncSession, 
        store_id: UUID, 
        user_id: UUID
    ) -> None:
        """
        Verifica si el usuario es propietario de la tienda.
        
        Args:
            db: Sesión de base de datos
            store_id: ID de la tienda
            user_id: ID del usuario a verificar
            
        Raises:
            HTTPException: Si el usuario no es propietario
        """
        user_store_service = UserStoreService(db)
        user_role = await user_store_service.get_user_role_in_store(store_id, user_id)
        
        if user_role != UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el propietario de la tienda puede realizar esta acción"
            )
    
    @staticmethod
    def check_admin_or_superuser(user_role: int) -> None:
        """
        Verifica si el usuario es administrador o superusuario.
        
        Args:
            user_role: Rol del usuario
            
        Raises:
            HTTPException: Si el usuario no es admin ni superusuario
        """
        if user_role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Se requieren permisos de administrador"
            )

# Alias para facilitar el acceso
store_permissions = StorePermissions()
