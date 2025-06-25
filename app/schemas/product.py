from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from uuid import UUID as PyUUID

class ProductBase(BaseModel):
    """Esquema base para productos"""
    name: str = Field(..., max_length=100, description="Nombre del producto")
    description: Optional[str] = Field(None, description="Descripción detallada del producto")
    sku: Optional[str] = Field(None, max_length=50, description="Código único de referencia del producto")
    price: float = Field(..., gt=0, description="Precio del producto (debe ser mayor a 0)")
    stock: int = Field(0, ge=0, description="Cantidad disponible en inventario")
    is_active: bool = Field(True, description="Indica si el producto está activo")
    store_id: PyUUID = Field(..., description="ID de la tienda a la que pertenece el producto")

    @validator('price')
    def price_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('El precio debe ser mayor a 0')
        return v

    @validator('stock')
    def stock_must_be_non_negative(cls, v):
        if v < 0:
            raise ValueError('El stock no puede ser negativo')
        return v

class ProductCreate(ProductBase):
    """Esquema para la creación de productos"""
    pass

class ProductUpdate(BaseModel):
    """Esquema para la actualización de productos"""
    name: Optional[str] = Field(None, max_length=100, description="Nuevo nombre del producto")
    description: Optional[str] = Field(None, description="Nueva descripción del producto")
    sku: Optional[str] = Field(None, max_length=50, description="Nuevo código SKU")
    price: Optional[float] = Field(None, gt=0, description="Nuevo precio (debe ser mayor a 0)")
    stock: Optional[int] = Field(None, ge=0, description="Nuevo stock disponible")
    is_active: Optional[bool] = Field(None, description="Estado de activación del producto")

    @validator('price')
    def price_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('El precio debe ser mayor a 0')
        return v

    @validator('stock')
    def stock_must_be_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError('El stock no puede ser negativo')
        return v

class ProductInDBBase(ProductBase):
    """Esquema base para productos en la base de datos"""
    id: PyUUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            PyUUID: str
        }

class Product(ProductInDBBase):
    """Esquema para devolver productos a través de la API"""
    pass

class ProductInDB(ProductInDBBase):
    """Esquema para productos en la base de datos"""
    pass