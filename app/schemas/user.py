from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum

# Roles de usuario
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    SELLER = "seller"

# 🔸 Base común (sin password)
class UserBase(BaseModel):
    email: EmailStr = Field(..., description="Correo electrónico del usuario")
    full_name: Optional[str] = Field(None, description="Nombre completo del usuario")
    is_active: bool = Field(True, description="Indica si el usuario está activo")
    is_superuser: bool = Field(False, description="Indica si el usuario es superusuario")
    role: UserRole = Field(UserRole.USER, description="Rol del usuario")

# 🔸 Esquema para creación de usuario (entrada)
class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Contraseña del usuario")

# 🔸 Esquema para actualizar usuario (entrada parcial)
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    role: Optional[UserRole] = None

# 🔸 Esquema para mostrar información de usuario (salida)
class UserOut(UserBase):
    id: UUID = Field(..., description="Identificador único del usuario")
    created_at: datetime = Field(..., description="Fecha de creación del usuario")
    updated_at: datetime = Field(..., description="Fecha de última actualización")
    deleted_at: Optional[datetime] = Field(None, description="Fecha de eliminación (si aplica)")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "usuario@ejemplo.com",
                "full_name": "Juan Pérez",
                "is_active": True,
                "is_superuser": False,
                "role": "user",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }

# 🔸 Esquema para autenticación
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None
    scopes: List[str] = []

class UserInDB(UserOut):
    hashed_password: str