# Importar el modelo base primero
from app.models.base import Base, TimestampMixin

# Luego importar todos los demás modelos
from app.models.user import User
from app.models.store import Store
from app.models.product import Product
from app.models.order import Order
from app.models.user_store_association import UserStoreAssociation, UserRole

# Hacer que los modelos estén disponibles para SQLAlchemy
__all__ = [
    'Base',
    'TimestampMixin',
    'User',
    'Store',
    'Product',
    'Order',
    'UserStoreAssociation',
    'UserRole'
]