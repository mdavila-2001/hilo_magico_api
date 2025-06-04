from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from app.models.user_store import UserStore, UserRole
from app.models.store import Store
from app.models.user import User
from app.schemas.store import UserStoreCreate, UserStoreUpdate, UserStoreInDB
from datetime import datetime

class UserStoreService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def add_user_to_store(
        self,
        store_id: UUID,
        user_store_in: UserStoreCreate,
        current_user_id: UUID
    ) -> UserStoreInDB:
        """Agrega un usuario a una tienda con un rol específico"""
        # Verificar que la tienda existe y está activa
        store_result = await self.db.execute(
            select(Store).where(and_(
                Store.id == store_id,
                Store.deleted_at.is_(None)
            ))
        )
        store = store_result.scalars().first()
        if not store:
            raise ValueError("Tienda no encontrada o inactiva")
        
        # Verificar que el usuario a agregar existe
        user_result = await self.db.execute(
            select(User).where(and_(
                User.id == user_store_in.user_id,
                User.deleted_at.is_(None)
            ))
        )
        user = user_result.scalars().first()
        if not user:
            raise ValueError("Usuario no encontrado o inactivo")
        
        # Verificar permisos del usuario actual (solo el dueño o admin puede agregar usuarios)
        current_user_role = await self.get_user_role_in_store(store_id, current_user_id)
        if current_user_role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise PermissionError("No tiene permisos para agregar usuarios a esta tienda")
        
        # Verificar que el rol a asignar es válido
        if user_store_in.role not in [role.value for role in UserRole]:
            raise ValueError(f"Rol no válido. Roles permitidos: {[role.value for role in UserRole]}")
        
        # Verificar que el usuario no esté ya en la tienda
        existing = await self.db.execute(
            select(UserStore).where(and_(
                UserStore.user_id == user_store_in.user_id,
                UserStore.store_id == store_id,
                UserStore.deleted_at.is_(None)
            ))
        )
        if existing.scalars().first():
            raise ValueError("El usuario ya está asociado a esta tienda")
        
        # Crear la relación usuario-tienda
        db_user_store = UserStore(
            user_id=user_store_in.user_id,
            store_id=store_id,
            role=UserRole(user_store_in.role),
            is_active=user_store_in.is_active
        )
        
        self.db.add(db_user_store)
        await self.db.commit()
        await self.db.refresh(db_user_store)
        
        return UserStoreInDB.from_orm(db_user_store)
    
    async def get_user_role_in_store(self, store_id: UUID, user_id: UUID) -> Optional[UserRole]:
        """Obtiene el rol de un usuario en una tienda específica"""
        result = await self.db.execute(
            select(UserStore).where(and_(
                UserStore.user_id == user_id,
                UserStore.store_id == store_id,
                UserStore.is_active == True,
                UserStore.deleted_at.is_(None)
            ))
        )
        user_store = result.scalars().first()
        return user_store.role if user_store else None
    
    async def get_store_users(self, store_id: UUID) -> List[UserStoreInDB]:
        """Obtiene todos los usuarios de una tienda"""
        result = await self.db.execute(
            select(UserStore).where(and_(
                UserStore.store_id == store_id,
                UserStore.deleted_at.is_(None)
            )).order_by(UserStore.created_at)
        )
        user_stores = result.scalars().all()
        return [UserStoreInDB.from_orm(us) for us in user_stores]
    
    async def update_user_role_in_store(
        self,
        store_id: UUID,
        user_id: UUID,
        user_store_in: UserStoreUpdate,
        current_user_id: UUID
    ) -> Optional[UserStoreInDB]:
        """Actualiza el rol de un usuario en una tienda"""
        # Verificar permisos (solo el dueño puede cambiar roles)
        current_user_role = await self.get_user_role_in_store(store_id, current_user_id)
        if current_user_role != UserRole.OWNER:
            raise PermissionError("Solo el dueño de la tienda puede cambiar roles")
        
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
            return None
        
        # Actualizar campos
        update_data = user_store_in.dict(exclude_unset=True)
        for field, value in update_data.items():
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
