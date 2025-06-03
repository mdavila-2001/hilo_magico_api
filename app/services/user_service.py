from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from passlib.context import CryptContext
from fastapi import HTTPException, status
from datetime import datetime

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🔐 Encripta la contraseña
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# 🔍 Verifica si el email ya existe
async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()

# 🔍 Verifica si el CI ya existe
async def get_user_by_ci(db: AsyncSession, ci: str):
    result = await db.execute(select(User).filter(User.ci == ci))
    return result.scalar_one_or_none()

# ✅ Crear usuario nuevo
async def create_user(db: AsyncSession, user_data: UserCreate):
    # Validación duplicados
    if await get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Correo ya registrado")
    
    if await get_user_by_ci(db, user_data.ci):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CI ya registrado")

    hashed_password = get_password_hash(user_data.password)

    new_user = User(
        email=user_data.email,
        ci=user_data.ci,
        first_name=user_data.first_name,
        middle_name=user_data.middle_name,
        last_name=user_data.last_name,
        mother_last_name=user_data.mother_last_name,
        phone=user_data.phone,
        role_id=user_data.role_id or 3,
        hashed_password=hashed_password,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

# 📄 Obtener todos los usuarios
async def get_all_users(db: AsyncSession):
    query = select(User).where(and_(User.deleted_at.is_(None), User.status is True)).order_by(User.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

# 📄 Obtener usuario por ID
async def get_user_by_id(db: AsyncSession, user_id):
    result = await db.execute(select(User).filter(User.id == user_id, User.status is True))
    return result.scalar_one_or_none()

# 🔄 Actualizar usuario (solo campos permitidos)
async def update_user(db: AsyncSession, user_id, update_data: UserUpdate):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(user, field, value)

    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    return user

# ❌ Eliminación lógica
async def delete_user(db: AsyncSession, user_id):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    user.status = False
    user.deleted_at = datetime.utcnow()
    await db.commit()
    return {"message": "Usuario eliminado (lógicamente)"}