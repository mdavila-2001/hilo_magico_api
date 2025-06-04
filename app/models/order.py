from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, func, ForeignKey, Integer, Float, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from enum import Enum as PyEnum

from app.db.session import Base

class OrderStatus(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class Order(Base):
    """Modelo SQLAlchemy para la entidad Orden"""
    __tablename__ = 'orders'
    __table_args__ = {'schema': 'public'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    order_number = Column(String(20), unique=True, nullable=False, index=True)
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(100), nullable=False)
    customer_phone = Column(String(20), nullable=True)
    shipping_address = Column(JSONB, nullable=False)  # Almacena la dirección de envío completa
    subtotal = Column(Float, nullable=False)
    tax = Column(Float, default=0.0, nullable=False)
    shipping_cost = Column(Float, default=0.0, nullable=False)
    total = Column(Float, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    notes = Column(String(500), nullable=True)
    is_paid = Column(Boolean, default=False, nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Claves foráneas
    store_id = Column(UUID(as_uuid=True), ForeignKey('public.stores.id'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('public.users.id'), nullable=True, index=True)

    # Relaciones
    store = relationship('Store', back_populates='orders')
    user = relationship('User')
    items = relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Order(id={self.id}, order_number='{self.order_number}', status='{self.status}')>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'order_number': self.order_number,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'customer_phone': self.customer_phone,
            'shipping_address': self.shipping_address,
            'subtotal': self.subtotal,
            'tax': self.tax,
            'shipping_cost': self.shipping_cost,
            'total': self.total,
            'status': self.status.value,
            'notes': self.notes,
            'is_paid': self.is_paid,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'is_active': self.is_active,
            'store_id': str(self.store_id),
            'user_id': str(self.user_id) if self.user_id else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'items': [item.to_dict() for item in self.items] if self.items else []
        }

class OrderItem(Base):
    """Modelo SQLAlchemy para los ítems de una orden"""
    __tablename__ = 'order_items'
    __table_args__ = {'schema': 'public'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Claves foráneas
    order_id = Column(UUID(as_uuid=True), ForeignKey('public.orders.id'), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey('public.products.id'), nullable=False, index=True)

    # Relaciones
    order = relationship('Order', back_populates='items')
    product = relationship('Product', back_populates='order_items')

    def __repr__(self):
        return f"<OrderItem(id={self.id}, product_id='{self.product_id}', quantity={self.quantity})>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'subtotal': self.subtotal,
            'order_id': str(self.order_id),
            'product_id': str(self.product_id),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'product': self.product.to_dict() if hasattr(self, 'product') and self.product else None
        }