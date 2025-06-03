from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.schemas.response import APIResponse
from app.services.user_service import (
    create_user, get_user_by_id, update_user, delete_user, get_all_users
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
@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        result = await create_user(db, user)
        return APIResponse(
            data=UserOut.from_orm(result),
            message="Usuario registrado con éxito"
        )
    except HTTPException as e:
        return APIResponse(
            success=False,
            message=str(e.detail),
            status_code=e.status_code
        )

# 📄 Obtener todos los usuarios
@router.get("/", response_model=APIResponse)
async def get_users(db: AsyncSession = Depends(get_db)):
    try:
        users = await get_all_users(db)
        return APIResponse(
            data=[UserOut.from_orm(user) for user in users],
            message="Usuarios obtenidos exitosamente"
        )
    except HTTPException as e:
        return APIResponse(
            success=False,
            message=str(e.detail),
            status_code=e.status_code
        )

# 🔍 Obtener usuario por ID
@router.get("/{user_id}", response_model=APIResponse)
async def read_user(user_id: str, db: AsyncSession = Depends(get_db)):
    try:
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        return APIResponse(
            data=UserOut.from_orm(user),
            message="Usuario encontrado exitosamente"
        )
    except HTTPException as e:
        return APIResponse(
            success=False,
            message=str(e.detail),
            status_code=e.status_code
        )

# 📝 Actualizar usuario
@router.put("/{user_id}", response_model=APIResponse)
async def update(user_id: str, data: UserUpdate, db: AsyncSession = Depends(get_db)):
    try:
        result = await update_user(db, user_id, data)
        return APIResponse(
            data=UserOut.from_orm(result),
            message="Usuario actualizado con éxito"
        )
    except HTTPException as e:
        return APIResponse(
            success=False,
            message=str(e.detail),
            status_code=e.status_code
        )

# ❌ Eliminar lógicamente
@router.delete("/{user_id}", response_model=APIResponse)
async def delete(user_id: str, db: AsyncSession = Depends(get_db)):
    try:
        result = await delete_user(db, user_id)
        return APIResponse(
            data=result,
            message="Usuario desvinculado con éxito"
        )
    except HTTPException as e:
        return APIResponse(
            success=False,
            message=str(e.detail),
            status_code=e.status_code
        )