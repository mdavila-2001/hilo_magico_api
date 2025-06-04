from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from app.models.user_store_association import UserStoreAssociation, UserRole
from app.models.store import Store
from app.models.user import User
from app.schemas.store import UserStoreCreate, UserStoreUpdate, UserStoreInDB
from datetime import datetime
from app.core.exceptions import NotFoundException, ConflictException, ForbiddenException, BadRequestException

class UserStoreService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def _get_store(self, store_id: UUID) -> Store:
        """Obtiene una tienda por su ID o lanza una excepción si no se encuentra."""
        result = await self.db.execute(select(Store).where(Store.id == store_id))
        store = result.scalars().first()
        if not store:
            raise NotFoundException("Tienda no encontrada")
        return store
    
    async def _get_user(self, user_id: UUID) -> User:
        """Obtiene un usuario por su ID o lanza una excepción si no se encuentra."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise NotFoundException("Usuario no encontrado")
        return user
    
    async def _get_user_store_association(
        self, 
        user_id: UUID, 
        store_id: UUID
    ) -> Optional[UserStoreAssociation]:
        """Obtiene la asociación usuario-tienda si existe."""
        result = await self.db.execute(
            select(UserStoreAssociation)
            .where(
                UserStoreAssociation.user_id == user_id,
                UserStoreAssociation.store_id == store_id,
                UserStoreAssociation.deleted_at.is_(None)
            )
        )
        return result.scalars().first()
    
    async def add_user_to_store(
        self,
        store_id: UUID,
        user_store_in: UserStoreCreate,
        current_user_id: UUID
    ) -> UserStoreInDB:
        """Agrega un usuario a una tienda con un rol específico."""
        # Verificar que la tienda existe
        store = await self._get_store(store_id)
        
        # Verificar que el usuario existe
        user = await self._get_user(user_store_in.user_id)
        
        # Verificar que el usuario actual tiene permisos (por ejemplo, es propietario o administrador)
        current_user_association = await self._get_user_store_association(current_user_id, store_id)
        if not current_user_association or current_user_association.role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise ForbiddenException("No tienes permisos para agregar usuarios a esta tienda")
        
        # Verificar que el usuario no esté ya asociado a la tienda
        existing_association = await self._get_user_store_association(user_store_in.user_id, store_id)
        if existing_association:
            if existing_association.deleted_at is None:
                raise ConflictException("El usuario ya está asociado a esta tienda")
            # Si existe pero está marcado como eliminado, reactivarlo
            existing_association.role = user_store_in.role
            existing_association.is_active = True
            existing_association.deleted_at = None
            existing_association.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(existing_association)
            return UserStoreInDB.from_orm(existing_association)
        
        # Crear nueva asociación
        new_association = UserStoreAssociation(
            user_id=user_store_in.user_id,
            store_id=store_id,
            role=user_store_in.role,
            is_active=True
        )
        
        self.db.add(new_association)
        await self.db.commit()
        await self.db.refresh(new_association)
        
        return UserStoreInDB.from_orm(new_association)
    
    async def get_user_role_in_store(self, store_id: UUID, user_id: UUID) -> Optional[UserRole]:
        """Obtiene el rol de un usuario en una tienda específica"""
        association = await self._get_user_store_association(user_id, store_id)
        return association.role if association and association.is_active else None
    
    async def get_store_users(self, store_id: UUID, skip: int = 0, limit: int = 100) -> List[UserStoreInDB]:
        """Obtiene todos los usuarios de una tienda con paginación"""
        result = await self.db.execute(
            select(UserStoreAssociation)
            .where(and_(
                UserStoreAssociation.store_id == store_id,
                UserStoreAssociation.deleted_at.is_(None)
            ))
            .order_by(UserStoreAssociation.created_at)
            .offset(skip)
            .limit(limit)
        )
        user_stores = result.scalars().all()
        return [UserStoreInDB.from_orm(us) for us in user_stores]
        
    async def get_user_store(self, store_id: UUID, user_id: UUID) -> Optional[UserStoreInDB]:
        """Obtiene la relación de un usuario específico en una tienda"""
        association = await self._get_user_store_association(user_id, store_id)
        return UserStoreInDB.from_orm(association) if association else None
        
    async def update_user_store(
        self,
        store_id: UUID,
        user_id: UUID,
        user_store_in: UserStoreUpdate,
        current_user_id: UUID
    ) -> Optional[UserStoreInDB]:
        """Actualiza la relación usuario-tienda"""
        # Obtener la relación existente
        db_user_store = await self._get_user_store_association(user_id, store_id)
        
        if not db_user_store:
            return None
            
        # Verificar permisos (solo admin/owner puede actualizar)
        current_user_role = await self.get_user_role_in_store(store_id, current_user_id)
        if not current_user_role or current_user_role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise ForbiddenException("No tienes permisos para actualizar esta relación")
        if current_user_role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise PermissionError("No tiene permisos para actualizar usuarios en esta tienda")
            
        # Actualizar campos
        update_data = user_store_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == 'role' and value is not None:
                setattr(db_user_store, field, UserRole(value))
            elif field in update_data:
                setattr(db_user_store, field, value)
                
        db_user_store.updated_at = datetime.utcnow()
        
        self.db.add(db_user_store)
        await self.db.commit()
        await self.db.refresh(db_user_store)
        
        return UserStoreInDB.from_orm(db_user_store)
        
    async def remove_user_from_store(
        self,
        store_id: UUID,
        user_id: UUID,
        current_user_id: UUID
    ) -> bool:
        """Elimina lógicamente la relación usuario-tienda"""
        # Obtener la relación existente
        db_user_store = await self._get_user_store_association(user_id, store_id)
        
        if not db_user_store:
            return False
            
        # Verificar permisos (solo admin/owner puede eliminar)
        current_user_role = await self.get_user_role_in_store(store_id, current_user_id)
        if not current_user_role or current_user_role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise ForbiddenException("No tienes permisos para eliminar usuarios de esta tienda")
            
        # No permitir que un usuario se elimine a sí mismo (debe ser eliminado por otro admin/owner)
        if user_id == current_user_id:
            raise ForbiddenException("No puedes eliminarte a ti mismo de la tienda")
            
        # Marcar como eliminado (soft delete)
        db_user_store.is_active = False
        db_user_store.deleted_at = datetime.utcnow()
        db_user_store.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(db_user_store)
        
        return True
    
    async def update_user_role_in_store(
        self,
        store_id: UUID,
        user_id: UUID,
        user_store_in: UserStoreUpdate,
        current_user_id: UUID
    ) -> Optional[UserStoreInDB]:
        """Actualiza el rol de un usuario en una tienda"""
        # Obtener la relación existente
        db_user_store = await self._get_user_store_association(user_id, store_id)
        
        if not db_user_store:
            return None
            
        # Verificar permisos (solo el dueño puede cambiar roles)
        current_user_role = await self.get_user_role_in_store(store_id, current_user_id)
        if current_user_role != UserRole.OWNER:
            raise ForbiddenException("Solo el dueño de la tienda puede cambiar roles")
            
        # Verificar que no se esté cambiando el rol del dueño actual
        if db_user_store.role == UserRole.OWNER and user_id != current_user_id:
            raise ForbiddenException("No puedes cambiar el rol del dueño actual")
            
        # Actualizar el rol
        db_user_store.role = user_store_in.role
        db_user_store.updated_at = datetime.utcnow()
        
        self.db.add(db_user_store)
        await self.db.commit()
        await self.db.refresh(db_user_store)
        
        return UserStoreInDB.from_orm(db_user_store)
    
    async def remove_user_from_store(
        self,
        store_id: UUID,
        user_id: UUID,
        current_user_id: UUID
    ) -> bool:
        """Elimina a un usuario de una tienda"""
        # Verificar permisos (solo el dueño o el propio usuario pueden eliminarlo)
        if user_id != current_user_id:
            current_user_role = await self.get_user_role_in_store(store_id, current_user_id)
            if current_user_role != UserRole.OWNER:
                raise PermissionError("No tiene permisos para eliminar a este usuario de la tienda")
        
        # Obtener la relación usuario-tienda
        result = await self.db.execute(
            select(UserStore).where(and_(
                UserStore.user_id == user_id,
                UserStore.store_id == store_id,
                UserStore.deleted_at.is_(None)
            ))
        )
        db_user_store = result.scalars().first()
        
        if not db_user_store:
            return False
        
        # Eliminación lógica
        db_user_store.deleted_at = datetime.utcnow()
        self.db.add(db_user_store)
        await self.db.commit()
        
        return True
