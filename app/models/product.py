from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, func, ForeignKey, Integer, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.session import Base

class Product(Base):
    """Modelo SQLAlchemy para la entidad Producto"""
    __tablename__ = 'products'
    __table_args__ = {'schema': 'public'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sku = Column(String(50), unique=True, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Clave foránea
    store_id = Column(UUID(as_uuid=True), ForeignKey('public.stores.id'), nullable=False, index=True)

    # Relaciones
    store = relationship('Store', back_populates='products')
    order_items = relationship('OrderItem', back_populates='product')

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price})>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'sku': self.sku,
            'price': self.price,
            'stock': self.stock,
            'is_active': self.is_active,
            'store_id': str(self.store_id),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }