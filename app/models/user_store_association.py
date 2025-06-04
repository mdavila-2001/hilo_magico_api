import enum
from datetime import datetime
from sqlalchemy import Column, ForeignKey, Enum as SQLEnum, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.session import Base

class UserRole(str, enum.Enum):
    """Enumeración de roles de usuario en la tienda"""
    OWNER = 'owner'     # Dueño de la tienda (máximos privilegios)
    ADMIN = 'admin'     # Administrador de la tienda
    MANAGER = 'manager' # Gerente/encargado
    STAFF = 'staff'     # Personal de la tienda
    VIEWER = 'viewer'   # Solo lectura

class UserStoreAssociation(Base):
    """Modelo para la relación muchos a muchos entre User y Store"""
    __tablename__ = 'user_store_association'
    __table_args__ = {'schema': 'public'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('public.users.id'), index=True, nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey('public.stores.id'), index=True, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.STAFF)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Relaciones
    user = relationship('User', back_populates='store_associations')
    store = relationship('Store', back_populates='user_associations')

    def __repr__(self):
        return f"<UserStoreAssociation(user_id={self.user_id}, store_id={self.store_id}, role='{self.role}')>"

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'store_id': str(self.store_id),
            'role': self.role.value,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }
