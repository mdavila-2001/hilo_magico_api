from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, func, ForeignKey, Integer, Float, Text, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Session
import uuid
import re

from app.db.session import Base

class Product(Base):
    """Modelo SQLAlchemy para la entidad Producto"""
    __tablename__ = 'products'
    __table_args__ = {'schema': 'development'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sku = Column(String(50), unique=True, nullable=True, index=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
    
    # Clave foránea
    store_id = Column(UUID(as_uuid=True), ForeignKey('development.stores.id'), nullable=False, index=True)

    # Relaciones comentadas temporalmente para simplificar
    # store = relationship('Store', back_populates='products')
    # order_items = relationship('OrderItem', back_populates='product')

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

    @staticmethod
    def generate_sku(name: str, db_session: Session, product_id: UUID = None) -> str:
        """Genera un SKU único basado en el nombre del producto."""
        # Mapeo de palabras clave a prefijos de categoría
        category_map = {
            'hilo': 'HIL',
            'aguja': 'AGU',
            'tela': 'TEL',
            'tejido': 'TEJ',
            'lana': 'LAN',
            'gancho': 'GAN',
            'agujas': 'AGU',
            'accesorio': 'ACC',
            'boton': 'BOT',
            'cierre': 'CIE'
        }
        
        # Determinar la categoría basada en el nombre
        category = 'OTR'  # Categoría por defecto
        name_lower = name.lower()
        
        for keyword, cat in category_map.items():
            if keyword in name_lower:
                category = cat
                break
        
        # Buscar el último SKU de esta categoría
        from app.models.product import Product as ProductModel
        
        query = db_session.query(ProductModel.sku).filter(
            ProductModel.sku.like(f"{category}-%")
        )
        
        if product_id:
            query = query.filter(ProductModel.id != product_id)
            
        last_sku = query.order_by(ProductModel.sku.desc()).first()
        
        if last_sku:
            # Extraer el número del último SKU y sumar 1
            match = re.search(rf"{category}-(\d+)", last_sku[0])
            if match:
                next_num = int(match.group(1)) + 1
            else:
                next_num = 1
        else:
            next_num = 1
            
        return f"{category}-{next_num:04d}"


@event.listens_for(Session, 'before_flush')
def before_flush(session, context, instances):
    """Evento que se dispara antes de hacer flush a la sesión."""
    for instance in session.new:
        if isinstance(instance, Product) and not instance.sku:
            # Generar SKU solo si no se proporcionó uno
            instance.sku = Product.generate_sku(instance.name, session, instance.id)