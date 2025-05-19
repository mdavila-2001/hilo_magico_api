from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services.user_service import (
    create_user, get_user_by_id, update_user, delete_user
)
from app.db.session import SessionLocal

router = APIRouter()

# Dependency para la DB
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# 🟢 Crear usuario
@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create(user: UserCreate, db: AsyncSession = Depends(get_db)):
    return await create_user(db, user)

# 🔍 Obtener usuario por ID
@router.get("/{user_id}", response_model=UserOut)
async def read_user(user_id: str, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

# 📝 Actualizar usuario
@router.put("/{user_id}", response_model=UserOut)
async def update(user_id: str, data: UserUpdate, db: AsyncSession = Depends(get_db)):
    return await update_user(db, user_id, data)

# ❌ Eliminar lógicamente
@router.delete("/{user_id}")
async def delete(user_id: str, db: AsyncSession = Depends(get_db)):
    return await delete_user(db, user_id)