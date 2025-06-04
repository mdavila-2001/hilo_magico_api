from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate
from passlib.context import CryptContext
from fastapi import HTTPException, status
from datetime import datetime
from uuid import UUID as UUID4

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🔐 Encripta la contraseña
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# 🔍 Verifica si el email ya existe
async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()

# 🔍 Verifica si el usuario existe por ID
async def get_user_by_id(db: AsyncSession, user_id: UUID4 | str):
    if isinstance(user_id, str):
        try:
            user_id = UUID4(user_id)
        except ValueError:
            return None
    result = await db.execute(select(User).filter(User.id == user_id, User.is_active == True))
    return result.scalar_one_or_none()

# ✅ Crear usuario nuevo
async def create_user(db: AsyncSession, user_data: UserCreate):
    # Validación de duplicados
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con este correo electrónico"
        )

    hashed_password = get_password_hash(user_data.password)
    
    # Usar el rol proporcionado o USER por defecto
    role = user_data.role if hasattr(user_data, 'role') else UserRole.USER

    new_user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        middle_name=user_data.middle_name if hasattr(user_data, 'middle_name') else None,
        last_name=user_data.last_name,
        mother_last_name=user_data.mother_last_name if hasattr(user_data, 'mother_last_name') else None,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=role == UserRole.ADMIN,
        role=role
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

# 📄 Obtener todos los usuarios (activos)
async def get_all_users(db: AsyncSession):
    query = select(User).where(
        User.is_active == True
    ).order_by(User.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

# 📄 Obtener usuario por ID (solo activos)
async def get_user_by_id(db: AsyncSession, user_id: UUID4 | str):
    if isinstance(user_id, str):
        try:
            user_id = UUID4(user_id)
        except ValueError:
            return None
    result = await db.execute(
        select(User).filter(
            User.id == user_id,
            User.is_active == True
        )
    )
    return result.scalar_one_or_none()

# 🔄 Actualizar usuario (solo campos permitidos)
async def update_user(db: AsyncSession, user_id: UUID4 | str, update_data: UserUpdate):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    update_dict = update_data.dict(exclude_unset=True)
    
    # Actualizar solo los campos permitidos
    allowed_fields = [
        'first_name', 'middle_name', 'last_name', 'mother_last_name',
        'is_active', 'role'
    ]
    
    for field in allowed_fields:
        if field in update_dict:
            setattr(user, field, update_dict[field])
    
    # Si se actualiza el rol, actualizar también is_superuser
    if 'role' in update_dict:
        user.is_superuser = (update_dict['role'] == UserRole.ADMIN)
    
    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    return user

# ❌ Eliminación lógica
async def delete_user(db: AsyncSession, user_id: UUID4 | str):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    user.is_active = False
    user.deleted_at = datetime.utcnow()
    await db.commit()
    return {"message": "Usuario desactivado exitosamente"}