from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict

from app.schemas.response import APIResponse


class UserRole(str, Enum):
    """Roles de usuario disponibles en el sistema."""
    ADMIN = "admin"
    USER = "user"
    SELLER = "seller"
    OWNER = "owner"


class UserBase(BaseModel):
    """Esquema base para usuarios."""
    email: EmailStr = Field(..., description="Correo electrónico del usuario")
    first_name: str = Field(..., min_length=1, max_length=50, description="Primer nombre del usuario")
    middle_name: Optional[str] = Field(None, max_length=50, description="Segundo nombre del usuario (opcional)")
    last_name: str = Field(..., min_length=1, max_length=50, description="Apellido paterno del usuario")
    mother_last_name: Optional[str] = Field(None, max_length=50, description="Apellido materno del usuario (opcional)")
    is_active: bool = Field(True, description="Indica si el usuario está activo")
    is_superuser: bool = Field(False, description="Indica si el usuario es superusuario")
    role: UserRole = Field(UserRole.USER, description="Rol del usuario")


class UserCreate(UserBase):
    """Esquema para la creación de un nuevo usuario."""
    password: str = Field(..., min_length=6, description="Contraseña del usuario (mínimo 6 caracteres)")
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        return v


class UserUpdate(BaseModel):
    """Esquema para actualizar un usuario existente."""
    email: Optional[EmailStr] = Field(None, description="Nuevo correo electrónico")
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Nuevo primer nombre")
    middle_name: Optional[str] = Field(None, max_length=50, description="Nuevo segundo nombre (opcional)")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Nuevo apellido paterno")
    mother_last_name: Optional[str] = Field(None, max_length=50, description="Nuevo apellido materno (opcional)")
    password: Optional[str] = Field(None, description="Nueva contraseña (opcional)")
    is_active: Optional[bool] = Field(None, description="Estado de activación")
    is_superuser: Optional[bool] = Field(None, description="Si es superusuario")
    role: Optional[UserRole] = Field(None, description="Nuevo rol del usuario")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "nuevo@email.com",
                "full_name": "Nuevo Nombre",
                "is_active": True,
                "role": "user"
            }
        }


class UserInDB(UserBase):
    """Esquema para representar un usuario en la base de datos."""
    id: UUID = Field(..., description="Identificador único del usuario")
    hashed_password: str = Field(..., description="Hash de la contraseña")
    created_at: datetime = Field(..., description="Fecha de creación del usuario")
    updated_at: datetime = Field(..., description="Fecha de última actualización")
    deleted_at: Optional[datetime] = Field(None, description="Fecha de eliminación (si aplica)")
    
    class Config:
        from_attributes = True


class UserOut(UserBase):
    """Esquema para mostrar información de usuario (sin datos sensibles)."""
    id: UUID = Field(..., description="Identificador único del usuario")
    full_name: str = Field(..., description="Nombre completo del usuario")
    created_at: datetime = Field(..., description="Fecha de creación del usuario")
    updated_at: datetime = Field(..., description="Fecha de última actualización")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "usuario@ejemplo.com",
                "first_name": "Juan",
                "middle_name": "Carlos",
                "last_name": "Pérez",
                "mother_last_name": "González",
                "full_name": "Juan Carlos Pérez González",
                "is_active": True,
                "is_superuser": False,
                "role": "user",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        }


class UserListResponse(APIResponse[List[UserOut]]):
    """Respuesta para listados de usuarios."""
    pass


class UserResponse(APIResponse[UserOut]):
    """Respuesta para operaciones con un solo usuario."""
    pass


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
    scopes: List[str] = []