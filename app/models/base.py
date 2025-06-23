from datetime import datetime
from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.sql import expression

class TimestampMixin:
    """Mixin que agrega campos de timestamp a los modelos."""
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime, nullable=True)

class BaseModel:
    """Clase base para todos los modelos con funcionalidad común."""
    
    @declared_attr
    def __tablename__(cls):
        """
        Genera automáticamente el nombre de la tabla en minúsculas.
        Ej: User -> users, ProductCategory -> product_categories
        """
        name = cls.__name__.lower()
        if name.endswith('y'):
            return f"{name[:-1]}ies"
        return f"{name}s"

    def to_dict(self):
        """Convierte el modelo a un diccionario."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

# Crear la base declarativa
Base = declarative_base(cls=BaseModel)
