import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base
from app.schemas.user import UserRole

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    
    # Campos de autenticación y autorización
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    
    # Auditoría
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
    
    # Relaciones
    store_associations = relationship('UserStore', back_populates='user')
    stores = relationship(
        'Store',
        secondary='public.user_store',
        back_populates='users',
        viewonly=True
    )

    def to_dict(self, include_stores: bool = False) -> dict:
        """
        Convierte el modelo User a un diccionario.
        
        Args:
            include_stores: Si es True, incluye la información de las tiendas del usuario
            
        Returns:
            dict: Diccionario con los datos del usuario
        """
        result = {
            'id': str(self.id),
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_superuser': self.is_superuser,
            'role': self.role.value if self.role else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }
        
        if include_stores:
            result['stores'] = [{
                'id': str(store.id),
                'name': store.name,
                'role': next(
                    (assoc.role.value for assoc in self.store_associations 
                     if assoc.store_id == store.id and assoc.is_active),
                    None
                )
            } for store in self.stores]
            
        return result
        
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
