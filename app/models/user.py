from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.session import Base
from app.models.user_store import user_store

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    last_name = Column(String, nullable=False)
    mother_last_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(Integer, default=3)  # 1: admin, 2: emprendedor, 3: cliente
    
    # Relación many-to-many con Store
    stores = relationship("Store", secondary=user_store, back_populates="users")