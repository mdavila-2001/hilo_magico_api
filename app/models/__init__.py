"""
Módulo de modelos de la aplicación.

Este módulo importa y expone todos los modelos de la base de datos
para que estén disponibles en toda la aplicación.
"""

# Importar el modelo base primero
from app.models.base import Base, TimestampMixin

# Importar todos los modelos existentes
from app.models.user import User
from app.models.store import Store
from app.models.product import Product
from app.models.order import Order
from app.models.user_store_association import UserStoreAssociation, UserRole

# Hacer que los modelos estén disponibles para SQLAlchemy
__all__ = [
    # Base y mixins
    'Base',
    'TimestampMixin',
    
    # Modelos principales
    'User',
    'Store',
    'Product',
    'Order',
    
    # Relaciones y asociaciones
    'UserStoreAssociation',
    'UserRole'
]