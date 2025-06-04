from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

from app.models.store import Store
from app.schemas.store import StoreCreate, StoreUpdate, StoreInDB
from app.core.security import get_password_hash
from datetime import datetime

class StoreService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_store(self, store_in: StoreCreate, owner_id: UUID) -> StoreInDB:
        """Crea una nueva tienda y asigna al usuario como propietario"""
        # Crear la tienda
        db_store = Store(
            **store_in.dict(exclude_unset=True)
        )
        self.db.add(db_store)
        await self.db.commit()
        await self.db.refresh(db_store)
        
        # Convertir a Pydantic para validar
        store = StoreInDB.from_orm(db_store)
        
        return store
    
    async def get_store(self, store_id: UUID) -> Optional[StoreInDB]:
        """Obtiene una tienda por su ID"""
        result = await self.db.execute(
            select(Store).where(and_(
                Store.id == store_id,
                Store.deleted_at.is_(None)
            ))
        )
        db_store = result.scalars().first()
        
        if db_store is None:
            return None
            
        return StoreInDB.from_orm(db_store)
    
    async def get_stores(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[StoreInDB]:
        """Obtiene una lista de tiendas con paginación"""
        result = await self.db.execute(
            select(Store)
            .where(Store.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )
        stores = result.scalars().all()
        return [StoreInDB.from_orm(store) for store in stores]
    
    async def update_store(
        self,
        store_id: UUID,
        store_in: StoreUpdate
    ) -> Optional[StoreInDB]:
        """Actualiza una tienda existente"""
        result = await self.db.execute(
            select(Store).where(and_(
                Store.id == store_id,
                Store.deleted_at.is_(None)
            ))
        )
        db_store = result.scalars().first()
        
        if db_store is None:
            return None
            
        # Actualizar campos
        update_data = store_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_store, field, value)
            
        db_store.updated_at = datetime.utcnow()
        
        self.db.add(db_store)
        await self.db.commit()
        await self.db.refresh(db_store)
        
        return StoreInDB.from_orm(db_store)
    
    async def delete_store(self, store_id: UUID) -> bool:
        """Elimina lógicamente una tienda"""
        result = await self.db.execute(
            select(Store).where(and_(
                Store.id == store_id,
                Store.deleted_at.is_(None)
            ))
        )
        db_store = result.scalars().first()
        
        if db_store is None:
            return False
            
        db_store.deleted_at = datetime.utcnow()
        self.db.add(db_store)
        await self.db.commit()
        
        return True
