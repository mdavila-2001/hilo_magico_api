from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.user_store import user_store

class Store(Base):
    __tablename__ = "stores"
    __table_args__ = {"schema": "public"}
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    address = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relación many-to-many con User
    users = relationship("User", secondary=user_store, back_populates="stores")