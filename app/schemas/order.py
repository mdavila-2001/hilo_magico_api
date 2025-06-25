from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator, HttpUrl
from uuid import UUID

from app.schemas.response import APIResponse

class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

# Esquemas para OrderItem
class OrderItemBase(BaseModel):
    """Esquema base para ítems de orden"""
    product_id: UUID = Field(..., description="ID del producto")
    quantity: int = Field(..., gt=0, description="Cantidad del producto")
    unit_price: float = Field(..., gt=0, description="Precio unitario al momento de la compra")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('La cantidad debe ser mayor a 0')
        return v

class OrderItemCreate(OrderItemBase):
    """Esquema para crear un ítem de orden"""
    pass

class OrderItemUpdate(BaseModel):
    """Esquema para actualizar un ítem de orden"""
    quantity: Optional[int] = Field(None, gt=0, description="Nueva cantidad")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v is not None and v <= 0:
            raise ValueError('La cantidad debe ser mayor a 0')
        return v

class OrderItemInDB(OrderItemBase):
    """Esquema para ítems de orden en la base de datos"""
    id: UUID
    subtotal: float = Field(..., description="Precio total del ítem (cantidad * precio unitario)")
    created_at: datetime
    
    class Config:
        from_attributes = True

# Esquemas para Order
class OrderBase(BaseModel):
    """Esquema base para órdenes"""
    customer_name: str = Field(..., max_length=100, description="Nombre del cliente")
    customer_email: str = Field(..., max_length=100, description="Email del cliente")
    customer_phone: Optional[str] = Field(None, max_length=20, description="Teléfono del cliente")
    shipping_address: Dict[str, Any] = Field(..., description="Dirección de envío")
    notes: Optional[str] = Field(None, max_length=500, description="Notas adicionales")
    store_id: UUID = Field(..., description="ID de la tienda")

class OrderCreate(OrderBase):
    """Esquema para crear una orden"""
    items: List[OrderItemCreate] = Field(..., min_items=1, description="Ítems de la orden")
    
    @validator('shipping_address')
    def validate_shipping_address(cls, v):
        required_fields = ['street', 'city', 'state', 'postal_code', 'country']
        for field in required_fields:
            if field not in v or not v[field]:
                raise ValueError(f'El campo {field} es requerido en la dirección de envío')
        return v

class OrderUpdate(BaseModel):
    """Esquema para actualizar una orden"""
    status: Optional[OrderStatus] = Field(None, description="Nuevo estado de la orden")
    notes: Optional[str] = Field(None, max_length=500, description="Notas adicionales")
    is_paid: Optional[bool] = Field(None, description="Indica si la orden ha sido pagada")

class OrderInDBBase(OrderBase):
    """Esquema base para órdenes en la base de datos"""
    id: UUID
    order_number: str = Field(..., description="Número de orden único")
    subtotal: float = Field(..., description="Subtotal de la orden (sin impuestos ni envío)")
    tax: float = Field(..., description="Impuestos aplicados")
    shipping_cost: float = Field(..., description="Costo de envío")
    total: float = Field(..., description="Total de la orden (subtotal + impuestos + envío)")
    status: OrderStatus = Field(..., description="Estado actual de la orden")
    is_paid: bool = Field(False, description="Indica si la orden ha sido pagada")
    paid_at: Optional[datetime] = Field(None, description="Fecha de pago")
    is_active: bool = Field(True, description="Indica si la orden está activa")
    user_id: Optional[UUID] = Field(None, description="ID del usuario que realizó la orden")
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            UUID: str
        }

class OrderWithItems(OrderInDBBase):
    """Esquema para orden con sus ítems"""
    items: List[OrderItemInDB] = Field(..., description="Ítems de la orden")

# Esquemas para respuestas de la API
class OrderResponse(APIResponse):
    """Respuesta estándar para una orden"""
    data: OrderWithItems

class OrderListResponse(APIResponse):
    """Respuesta estándar para una lista de órdenes"""
    data: List[OrderInDBBase]

class OrderItemResponse(APIResponse):
    """Respuesta estándar para un ítem de orden"""
    data: OrderItemInDB