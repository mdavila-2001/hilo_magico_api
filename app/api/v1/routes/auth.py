from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.auth_controller import AuthController
from app.core.config import settings
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.schemas.response import APIResponse
from app.schemas.token import Token, TokenData
from app.schemas.user import UserBase, UserCreate, UserOut

class LoginRequest(BaseModel):
    """Esquema para la solicitud de inicio de sesión"""
    email: EmailStr = Field(..., description="Correo electrónico del usuario")
    password: str = Field(..., min_length=6, description="Contraseña del usuario")

router = APIRouter(tags=["Autenticación"])

@router.post(
    "/login",
    response_model=APIResponse[Token],
    summary="Iniciar sesión",
    description="Autentica un usuario y devuelve tokens de acceso y actualización.",
)
async def login_for_access_token(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[Token]:
    """
    Inicia sesión de un usuario y devuelve tokens de acceso y actualización.
    
    - **email**: Correo electrónico del usuario
    - **password**: Contraseña del usuario
    """
    auth_controller = AuthController(db)
    return await auth_controller.login(login_data.email, login_data.password)

@router.post(
    "/refresh-token",
    response_model=APIResponse[Token],
    summary="Refrescar token",
    description="Obtiene un nuevo token de acceso usando un token de actualización.",
)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[Token]:
    """
    Refresca el token de acceso usando un token de actualización.
    
    - **refresh_token**: Token de actualización
    """
    # La lógica de validación del refresh token se manejará en el servicio de autenticación
    user = await get_current_active_user(refresh_token, db)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return APIResponse[Token](
        data=Token(
            access_token=new_access_token,
            token_type="bearer",
            refresh_token=refresh_token,
        ),
        message="Token actualizado exitosamente",
    )


@router.post(
    "/register",
    response_model=APIResponse[UserOut],
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
    description="Crea un nuevo usuario en el sistema.",
)
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[UserOut]:
    """
    Registra un nuevo usuario en el sistema.
    
    - **email**: Correo electrónico del usuario (debe ser único)
    - **password**: Contraseña (mínimo 6 caracteres)
    - **full_name**: Nombre completo del usuario (opcional)
    """
    auth_controller = AuthController(db)
    return await auth_controller.register(user_in)


@router.get(
    "/me",
    response_model=APIResponse[UserOut],
    summary="Obtener usuario actual",
    description="Obtiene la información del usuario autenticado.",
)
async def read_users_me(
    current_user: UserOut = Depends(get_current_active_user),
) -> APIResponse[UserOut]:
    """
    Obtiene la información del usuario autenticado.
    
    Devuelve los datos del usuario actualmente autenticado.
    """
    return APIResponse[UserOut](
        data=current_user,
        message="Información del usuario obtenida exitosamente",
    )


@router.post(
    "/change-password",
    response_model=APIResponse[Dict[str, Any]],
    summary="Cambiar contraseña",
    description="Permite a un usuario cambiar su contraseña.",
)
async def change_password(
    current_password: str,
    new_password: str,
    current_user: UserOut = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[Dict[str, Any]]:
    """
    Cambia la contraseña del usuario autenticado.
    
    - **current_password**: Contraseña actual
    - **new_password**: Nueva contraseña
    """
    user_service = UserService(db)
    
    # Verificar la contraseña actual
    if not await user_service.verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta",
        )
    
    # Actualizar la contraseña
    hashed_password = get_password_hash(new_password)
    await user_service.update_user(
        str(current_user.id),
        {"hashed_password": hashed_password},
    )
    
    return APIResponse[Dict[str, Any]](
        data={"message": "Contraseña actualizada exitosamente"},
        message="Contraseña actualizada exitosamente",
    )
