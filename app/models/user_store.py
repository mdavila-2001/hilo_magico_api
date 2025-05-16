from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base

user_store = Table(
    'user_store',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('public.users.id'), primary_key=True),
    Column('store_id', Integer, ForeignKey('public.stores.id'), primary_key=True),
    schema='public'
)