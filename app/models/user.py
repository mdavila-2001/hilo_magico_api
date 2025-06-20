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
    __table_args__ = {"schema": "development"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String(50), nullable=False)
    middle_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=False)
    mother_last_name = Column(String(50), nullable=True)
    hashed_password = Column(String, nullable=False)
    
    # Campos de autenticación y autorización
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    role = Column(Integer, default=0, nullable=False)  # 0=USER, 1=ADMIN, 2=OWNER, 3=SELLER, 4=CUSTOMER
    
    # Timestamps - Using timezone-naive datetimes for compatibility
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)
    
    # Relaciones comentadas temporalmente para simplificar
    # store_associations = relationship('UserStoreAssociation', back_populates='user')
    # stores = relationship(
    #     'Store',
    #     secondary='development.user_store_association',
    #     back_populates='users',
    #     viewonly=True
    # )

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
            'first_name': self.first_name,
            'middle_name': self.middle_name,
            'last_name': self.last_name,
            'mother_last_name': self.mother_last_name,
            'full_name': f"{self.first_name} {self.middle_name or ''} {self.last_name} {self.mother_last_name or ''}".replace('  ', ' ').strip(),
            'is_active': self.is_active,
            'is_superuser': self.is_superuser,
            'role': self.role.value if self.role else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }
        
        # La inclusión de tiendas ha sido temporalmente deshabilitada
        # if include_stores:
        #     result['stores'] = [{
        #         'id': str(store.id),
        #         'name': store.name,
        #         'role': next(
        #             (assoc.role.value for assoc in self.store_associations 
        #              if assoc.store_id == store.id and assoc.is_active),
        #             None
        #         )
        #     } for store in self.stores]
            
        return result
        
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
