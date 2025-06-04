from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict, model_validator

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
    last_name: str = Field(..., min_length=1, max_length=50, description="Apellido paterno del usuario")
    
    # Configuración de Pydantic
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class UserCreate(BaseModel):
    """Esquema para la creación de un nuevo usuario."""
    email: EmailStr = Field(..., description="Correo electrónico del usuario")
    first_name: str = Field(..., min_length=1, max_length=50, description="Primer nombre del usuario")
    middle_name: Optional[str] = Field(None, max_length=50, description="Segundo nombre del usuario (opcional)")
    last_name: str = Field(..., min_length=1, max_length=50, description="Apellido paterno del usuario")
    mother_last_name: Optional[str] = Field(None, max_length=50, description="Apellido materno del usuario (opcional)")
    password: str = Field(..., min_length=6, description="Contraseña del usuario (mínimo 6 caracteres)")
    role: UserRole = Field(default=UserRole.USER, description="Rol del usuario")
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        # Puedes agregar más validaciones de contraseña aquí si es necesario
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "usuario@ejemplo.com",
                "first_name": "Juan",
                "middle_name": "Carlos",
                "last_name": "Pérez",
                "mother_last_name": "González",
                "password": "micontraseñasegura",
                "role": "user"
            }
        }


class UserUpdate(BaseModel):
    """Esquema para actualizar un usuario existente."""
    email: Optional[EmailStr] = Field(None, description="Nuevo correo electrónico")
    first_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Nuevo primer nombre")
    middle_name: Optional[str] = Field(None, max_length=50, description="Nuevo segundo nombre (opcional)")
    last_name: Optional[str] = Field(None, min_length=1, max_length=50, description="Nuevo apellido paterno")
    mother_last_name: Optional[str] = Field(None, max_length=50, description="Nuevo apellido materno (opcional)")
    password: Optional[str] = Field(None, description="Nueva contraseña (opcional)")
    is_active: Optional[bool] = Field(None, description="Estado de activación")
    role: Optional[UserRole] = Field(None, description="Nuevo rol del usuario")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "nuevo@email.com",
                "first_name": "Nuevo",
                "last_name": "Usuario",
                "is_active": True,
                "role": "user"
            }
        }


class UserInDB(UserBase):
    """Esquema para representar un usuario en la base de datos."""
    id: UUID = Field(..., description="Identificador único del usuario")
    hashed_password: str = Field(..., description="Hash de la contraseña")
    is_active: bool = Field(True, description="Indica si el usuario está activo")
    is_superuser: bool = Field(False, description="Indica si el usuario es superusuario")
    role: UserRole = Field(UserRole.USER, description="Rol del usuario")
    created_at: datetime = Field(..., description="Fecha de creación del usuario")
    updated_at: Optional[datetime] = Field(None, description="Fecha de última actualización")
    deleted_at: Optional[datetime] = Field(None, description="Fecha de eliminación (si aplica)")
    
    class Config:
        from_attributes = True
        use_enum_values = True


class UserOut(BaseModel):
    """Esquema para mostrar información de usuario (sin datos sensibles)."""
    id: UUID = Field(..., description="Identificador único del usuario")
    email: EmailStr = Field(..., description="Correo electrónico del usuario")
    first_name: str = Field(..., description="Primer nombre del usuario")
    middle_name: Optional[str] = Field(None, description="Segundo nombre del usuario (opcional)")
    last_name: str = Field(..., description="Apellido paterno del usuario")
    mother_last_name: Optional[str] = Field(None, description="Apellido materno del usuario (opcional)")
    full_name: str = Field(..., description="Nombre completo del usuario")
    is_active: bool = Field(..., description="Indica si el usuario está activo")
    role: str = Field(..., description="Rol del usuario")
    created_at: str = Field(..., description="Fecha de creación del usuario (ISO format)")
    updated_at: Optional[str] = Field(None, description="Fecha de última actualización (ISO format)")
    
    @model_validator(mode='before')
    @classmethod
    def build_full_name(cls, values):
        if isinstance(values, dict):
            parts = [values.get('first_name', '')]
            if values.get('middle_name'):
                parts.append(values['middle_name'])
            parts.append(values.get('last_name', ''))
            if values.get('mother_last_name'):
                parts.append(values['mother_last_name'])
            values['full_name'] = ' '.join(part for part in parts if part)
        return values
    
    @classmethod
    def from_orm(cls, obj):
        # Construir el nombre completo
        full_name_parts = [obj.first_name]
        if obj.middle_name:
            full_name_parts.append(obj.middle_name)
        full_name_parts.append(obj.last_name)
        if obj.mother_last_name:
            full_name_parts.append(obj.mother_last_name)
            
        full_name = " ".join(full_name_parts)
        
        # Asegurarse de que las fechas sean serializables
        created_at = obj.created_at.isoformat() if obj.created_at else None
        updated_at = obj.updated_at.isoformat() if obj.updated_at else None
        
        return cls(
            id=obj.id,
            email=obj.email,
            first_name=obj.first_name,
            middle_name=obj.middle_name,
            last_name=obj.last_name,
            mother_last_name=obj.mother_last_name,
            full_name=full_name,
            is_active=obj.is_active,
            role=obj.role.value if hasattr(obj.role, 'value') else str(obj.role),
            created_at=created_at,
            updated_at=updated_at
        )
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: str
        }
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