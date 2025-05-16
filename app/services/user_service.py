from sqlalchemy.orm import Session
from uuid import UUID
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)

def create_user(db: Session, user: UserCreate):
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
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: UUID):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()

def update_user(db: Session, user_id: UUID, user_data: UserUpdate):
    user = get_user(db, user_id)
    if not user:
        return None

    if user_data.email:
        user.email = user_data.email
    if user_data.first_name:
        user.first_name = user_data.first_name
    if user_data.middle_name is not None:
        user.middle_name = user_data.middle_name
    if user_data.last_name:
        user.last_name = user_data.last_name
    if user_data.mother_last_name is not None:
        user.mother_last_name = user_data.mother_last_name
    if user_data.store is not None:
        user.store = user_data.store
    if user_data.password:
        user.hashed_password = get_password_hash(user_data.password)
    if user_data.role is not None:
        user.role = user_data.role if user_data.role else 3
    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: UUID):
    user = get_user(db, user_id)
    if not user:
        return None
    db.delete(user)
    db.commit()
    return user
