from pydantic import BaseModel, EmailStr, constr
from typing import Optional, List
from uuid import UUID
from app.schemas.store import Store

class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    mother_last_name: Optional[str] = None

class UserCreate(UserBase):
    password: constr(min_length=8)
    role: Optional[int] = 3  # 1: admin, 2: emprendedor, 3: cliente

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    mother_last_name: Optional[str] = None
    password: Optional[str] = None  # se encripta si cambia
    role: Optional[int] = None  # 1: admin, 2: emprendedor, 3: cliente
    is_active: Optional[bool] = None

class UserOut(UserBase):
    id: UUID
    role: int  # 1: admin, 2: emprendedor, 3: cliente
    is_active: bool
    stores: List[Store] = []

    class Config:
        from_attributes = True