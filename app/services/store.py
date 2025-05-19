from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.models.store import Store
from app.schemas.store import StoreCreate, StoreUpdate

class StoreService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_store(self, store_data: StoreCreate) -> Store:
        store = Store(**store_data.dict())
        self.db.add(store)
        await self.db.commit()
        await self.db.refresh(store)
        return store

    async def get_store(self, store_id: int) -> Optional[Store]:
        result = await self.db.execute(select(Store).filter(Store.id == store_id))
        return result.scalar_one_or_none()

    async def get_stores(self, skip: int = 0, limit: int = 100) -> List[Store]:
        result = await self.db.execute(select(Store).offset(skip).limit(limit))
        return result.scalars().all()

    async def update_store(self, store_id: int, store_data: StoreUpdate) -> Optional[Store]:
        update_data = store_data.dict(exclude_unset=True)
        if not update_data:
            return None
        
        query = update(Store).where(Store.id == store_id).values(update_data)
        await self.db.execute(query)
        await self.db.commit()
        
        return await self.get_store(store_id)

    async def delete_store(self, store_id: int) -> bool:
        query = delete(Store).where(Store.id == store_id)
        result = await self.db.execute(query)
        await self.db.commit()
        return result.rowcount > 0

    async def get_active_stores(self, skip: int = 0, limit: int = 100) -> List[Store]:
        result = await self.db.execute(
            select(Store)
            .filter(Store.is_active is True)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()