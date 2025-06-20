import enum
from datetime import datetime
from sqlalchemy import Column, ForeignKey, Enum as SQLEnum, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.session import Base
from app.schemas.user import UserRole

# Usamos el UserRole de app.schemas.user que ya está importado
# Este enum incluye: ADMIN, USER, SELLER, OWNER, CUSTOMER

class UserStoreAssociation(Base):
    """Modelo para la relación muchos a muchos entre User y Store"""
    __tablename__ = 'user_store_association'
    __table_args__ = {'schema': 'development'}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('development.users.id'), index=True, nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey('development.stores.id'), index=True, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.USER)  # Cambiado de STAFF a USER
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    # Relaciones comentadas temporalmente para simplificar
    # user = relationship('User', back_populates='store_associations')
    # store = relationship('Store', back_populates='user_associations')

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
