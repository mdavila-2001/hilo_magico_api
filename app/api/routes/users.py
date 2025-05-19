from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api import deps
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services import user_service

router = APIRouter()

@router.post("/", response_model=UserOut)
async def create_user(user: UserCreate, db: AsyncSession = Depends(deps.get_db)):
    existing = await user_service.get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email ya registrado.")
    return await user_service.create_user(db, user)

@router.get("/", response_model=List[UserOut])
async def list_users(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(deps.get_db)):
    return await user_service.get_all_users(db, skip, limit)

@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: AsyncSession = Depends(deps.get_db)):
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return user

@router.put("/{user_id}", response_model=UserOut)
async def update_user(user_id: int, user_data: UserUpdate, db: AsyncSession = Depends(deps.get_db)):
    updated = await user_service.update_user(db, user_id, user_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return updated

@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(deps.get_db)):
    deleted = await user_service.delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return {"message": "Usuario eliminado correctamente."}
