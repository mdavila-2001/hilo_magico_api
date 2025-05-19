from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

# 🔸 Base común (sin password)
class UserBase(BaseModel):
    email: EmailStr
    ci: str = Field(..., min_length=5, max_length=20)
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    mother_last_name: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[int] = 3  # valor por defecto para "cliente"
    # 1: Admin 2: Emprendedor 3: Cliente

# 🔸 Esquema para creación de usuario (entrada)
class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

# 🔸 Esquema para actualizar usuario (entrada parcial)
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    mother_last_name: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[int] = None

# 🔸 Esquema para mostrar información de usuario (salida)
class UserOut(UserBase):
    id: UUID
    status: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        orm_mode = True