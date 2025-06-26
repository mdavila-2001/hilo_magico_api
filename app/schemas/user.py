from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict, model_validator

from app.schemas.response import APIResponse


class UserRole(int, Enum):
    """Roles de usuario disponibles en el sistema.
    
    Valores:
        USER = 0 (default)
        ADMIN = 1
        OWNER = 2
        SELLER = 3
        CUSTOMER = 4
    """
    USER = 0
    ADMIN = 1
    OWNER = 2
    SELLER = 3
    CUSTOMER = 4


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
    role: Union[str, int] = Field(..., description="Rol del usuario (puede ser string o int)")
    created_at: Union[str, datetime] = Field(..., description="Fecha de creación del usuario")
    updated_at: Optional[Union[str, datetime]] = Field(None, description="Fecha de última actualización")
    
    @model_validator(mode='before')
    @classmethod
    def build_full_name(cls, values):
        if isinstance(values, dict):
            # Construir full_name (siempre debe tener al menos nombre y apellido)
            first_name = values.get('first_name', '')
            last_name = values.get('last_name', '')
            
            if not first_name or not last_name:
                raise ValueError("Se requieren al menos el nombre y apellido")
                
            parts = [first_name]
            if values.get('middle_name'):
                parts.append(values['middle_name'])
            parts.append(last_name)
            if values.get('mother_last_name'):
                parts.append(values['mother_last_name'])
                
            full_name = ' '.join(part for part in parts if part)
            if not full_name:
                raise ValueError("No se pudo generar un nombre completo válido")
                
            values['full_name'] = full_name
            
            # Asegurar que el rol sea string
            if 'role' in values:
                role = values['role']
                # Si es un enum, obtener su valor
                if hasattr(role, 'value'):
                    role = role.value
                # Si es un entero, obtener el nombre del enum correspondiente
                if isinstance(role, int):
                    try:
                        role = UserRole(role).name.lower()
                    except ValueError:
                        role = str(role)
                # Asegurar que sea string
                values['role'] = str(role)
                
            # Asegurar que las fechas sean strings
            if 'created_at' in values and isinstance(values['created_at'], datetime):
                values['created_at'] = values['created_at'].isoformat()
            if 'updated_at' in values and values['updated_at'] and isinstance(values['updated_at'], datetime):
                values['updated_at'] = values['updated_at'].isoformat()
                
        return values
    
    @classmethod
    def from_orm(cls, obj):
        # Convertir el objeto a diccionario
        data = {
            'id': obj.id,
            'email': obj.email,
            'first_name': obj.first_name,
            'middle_name': obj.middle_name,
            'last_name': obj.last_name,
            'mother_last_name': obj.mother_last_name,
            'is_active': obj.is_active,
            'role': obj.role,
            'created_at': obj.created_at,
            'updated_at': obj.updated_at
        }
        return cls(**data)
    
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
                "role": "1",
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