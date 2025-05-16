from sqlalchemy import Column, Integer, String, Boolean
from app.db.session import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    last_name = Column(String, nullable=False)
    mother_last_name = Column(String, nullable=True)
    store = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(Integer, default=3)  # 1: admin, 2: emprendedor, 3: cliente