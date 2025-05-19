from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from passlib.context import CryptContext
from typing import List, Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)

async def create_user(db: AsyncSession, user: UserCreate):
    hashed_pw = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        first_name=user.first_name,
        middle_name=user.middle_name,
        last_name=user.last_name,
        mother_last_name=user.mother_last_name,
        store=user.store,
        hashed_password=hashed_pw,
        role=user.role
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_user(db: AsyncSession, user_id: UUID, include_inactive: bool = False) -> Optional[User]:
    query = select(User).filter(User.id == user_id)
    if not include_inactive:
        query = query.filter(User.is_active is True)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str, include_inactive: bool = False) -> Optional[User]:
    query = select(User).filter(User.email == email)
    if not include_inactive:
        query = query.filter(User.is_active is True)
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> List[User]:
    query = select(User)
    if not include_inactive:
        query = query.filter(User.is_active is True)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

async def update_user(db: AsyncSession, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
    user = await get_user(db, user_id)
    if not user:
        return None

    update_data = user_data.dict(exclude_unset=True)
    if not update_data:
        return user

    if user_data.password:
        update_data["hashed_password"] = get_password_hash(user_data.password)
        del update_data["password"]

    query = update(User).where(User.id == user_id).values(update_data)
    await db.execute(query)
    await db.commit()
    
    return await get_user(db, user_id)

async def delete_user(db: AsyncSession, user_id: UUID):
    user = await get_user(db, user_id)
    if not user:
        return None
    
    # Implementar borrado lógico actualizando is_active a False y estableciendo deleted_at
    from datetime import datetime
    query = update(User).where(User.id == user_id).values({
        "is_active": False,
        "deleted_at": datetime.utcnow()
    })
    await db.execute(query)
    await db.commit()
    return await get_user(db, user_id)
