from datetime import datetime
from typing import Optional, List, TypeVar, Generic
from pydantic import BaseModel, Field, EmailStr, UUID4
from app.schemas.response import APIResponse

# Definir tipo genérico para respuestas
T = TypeVar('T')

# Esquemas para Tienda (Store)

class StoreBase(BaseModel):
    """Esquema base para Tienda"""
    name: str = Field(..., min_length=3, max_length=100, description="Nombre de la tienda")
    description: Optional[str] = Field(None, max_length=500, description="Descripción de la tienda")
    address: str = Field(..., max_length=255, description="Dirección física de la tienda")
    phone: str = Field(..., max_length=20, description="Teléfono de contacto de la tienda")
    email: Optional[EmailStr] = Field(None, description="Correo electrónico de contacto")
    is_active: bool = Field(default=True, description="Indica si la tienda está activa")

class StoreCreate(StoreBase):
    """Esquema para crear una nueva tienda"""
    pass

class StoreUpdate(BaseModel):
    """Esquema para actualizar una tienda existente"""
    name: Optional[str] = Field(None, min_length=3, max_length=100, description="Nombre de la tienda")
    description: Optional[str] = Field(None, max_length=500, description="Descripción de la tienda")
    address: Optional[str] = Field(None, max_length=255, description="Dirección física de la tienda")
    phone: Optional[str] = Field(None, max_length=20, description="Teléfono de contacto de la tienda")
    email: Optional[EmailStr] = Field(None, description="Correo electrónico de contacto")
    is_active: Optional[bool] = Field(None, description="Indica si la tienda está activa")

class StoreInDB(StoreBase):
    """Esquema para representar una tienda en la base de datos"""
    id: UUID4 = Field(..., description="Identificador único de la tienda")
    created_at: datetime = Field(..., description="Fecha de creación del registro")
    updated_at: datetime = Field(..., description="Fecha de última actualización")
    deleted_at: Optional[datetime] = Field(None, description="Fecha de eliminación lógica")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Esquemas para la relación Usuario-Tienda (UserStore)

class UserStoreBase(BaseModel):
    """Esquema base para la relación Usuario-Tienda"""
    user_id: UUID4 = Field(..., description="ID del usuario")
    store_id: UUID4 = Field(..., description="ID de la tienda")
    role: str = Field(..., description="Rol del usuario en la tienda (ej. 'owner', 'admin', 'staff')")
    is_active: bool = Field(default=True, description="Indica si el usuario está activo en la tienda")

class UserStoreCreate(UserStoreBase):
    """Esquema para crear una nueva relación Usuario-Tienda"""
    pass

class UserStoreUpdate(BaseModel):
    """Esquema para actualizar una relación Usuario-Tienda existente"""
    role: Optional[str] = Field(None, description="Nuevo rol del usuario en la tienda")
    is_active: Optional[bool] = Field(None, description="Nuevo estado de activación")

class UserStoreInDB(UserStoreBase):
    """Esquema para representar una relación Usuario-Tienda en la base de datos"""
    id: UUID4 = Field(..., description="Identificador único de la relación")
    created_at: datetime = Field(..., description="Fecha de creación del registro")
    updated_at: datetime = Field(..., description="Fecha de última actualización")
    deleted_at: Optional[datetime] = Field(None, description="Fecha de eliminación lógica")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Esquemas para respuestas de la API
class StoreResponse(APIResponse[StoreInDB]):
    """Esquema de respuesta para operaciones con tiendas"""
    pass

class StoreListResponse(APIResponse[List[StoreInDB]]):
    """Esquema de respuesta para listados de tiendas"""
    pass

class UserStoreResponse(APIResponse[UserStoreInDB]):
    """Esquema de respuesta para operaciones con relaciones Usuario-Tienda"""
    pass

class UserStoreListResponse(APIResponse[List[UserStoreInDB]]):
    """Esquema de respuesta para listados de relaciones Usuario-Tienda"""
    pass