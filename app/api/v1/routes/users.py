from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserCreate, UserOut, UserUpdate, UserInDB
from app.schemas.response import APIResponse
from app.db.session import get_db
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])

# 🟢 Crear usuario
@router.post(
    "/",
    response_model=APIResponse[UserOut],
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo usuario",
    description="Crea un nuevo usuario en el sistema con los datos proporcionados."
)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Crea un nuevo usuario en el sistema.
    
    - **email**: Email del usuario (debe ser único)
    - **password**: Contraseña (mínimo 6 caracteres)
    - **full_name**: Nombre completo del usuario (opcional)
    """
    try:
        user_service = UserService(db)
        db_user = await user_service.create_user(user)
        return APIResponse[UserOut](
            data=UserOut.from_orm(db_user),
            message="Usuario registrado con éxito"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear el usuario"
        )

# 📄 Obtener todos los usuarios
@router.get(
    "/",
    response_model=APIResponse[List[UserOut]],
    summary="Listar usuarios",
    description="Obtiene una lista de todos los usuarios registrados en el sistema."
)
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene una lista paginada de usuarios.
    
    - **skip**: Número de registros a saltar (para paginación)
    - **limit**: Número máximo de registros a devolver (máx. 100)
    """
    try:
        user_service = UserService(db)
        users = await user_service.get_users(skip=skip, limit=limit)
        return APIResponse[List[UserOut]](
            data=[UserOut.from_orm(user) for user in users],
            message="Usuarios obtenidos exitosamente"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener los usuarios"
        )

# 🔍 Obtener usuario por ID
@router.get(
    "/{user_id}",
    response_model=APIResponse[UserOut],
    summary="Obtener usuario por ID",
    description="Obtiene la información detallada de un usuario específico."
)
async def read_user(user_id: str, db: AsyncSession = Depends(get_db)):
    try:
        user_service = UserService(db)
        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        return APIResponse[UserOut](
            data=UserOut.from_orm(user),
            message="Usuario encontrado exitosamente"
        )
    except HTTPException as e:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener el usuario"
        )

# 📝 Actualizar usuario
@router.put(
    "/{user_id}",
    response_model=APIResponse[UserOut],
    summary="Actualizar usuario",
    description="Actualiza la información de un usuario existente."
)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza un usuario existente.
    
    - **user_id**: ID del usuario a actualizar
    - **user_update**: Datos a actualizar (todos los campos son opcionales)
    """
    try:
        user_service = UserService(db)
        updated_user = await user_service.update_user(user_id, user_update)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
            
        return APIResponse[UserOut](
            data=UserOut.from_orm(updated_user),
            message="Usuario actualizado exitosamente"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar el usuario"
        )

# ❌ Eliminar usuario (lógicamente)
@router.delete(
    "/{user_id}",
    response_model=APIResponse[Dict[str, Any]],
    summary="Eliminar usuario",
    description="Elimina un usuario del sistema (eliminación lógica)."
)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Elimina un usuario (eliminación lógica).
    
    - **user_id**: ID del usuario a eliminar
    """
    try:
        user_service = UserService(db)
        success = await user_service.delete_user(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
            
        return APIResponse[Dict[str, Any]](
            data={"id": user_id},
            message="Usuario eliminado exitosamente"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar el usuario"
        )