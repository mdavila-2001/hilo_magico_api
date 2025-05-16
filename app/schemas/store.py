from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class StoreBase(BaseModel):
    name: str
    city: str
    address: str
    phone: str
    is_active: Optional[bool] = True

class StoreCreate(StoreBase):
    pass

class StoreUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None

class Store(StoreBase):
    id: UUID

    class Config:
        from_attributes = True