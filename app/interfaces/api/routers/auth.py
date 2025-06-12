from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.persistence.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.interfaces.api.controllers.auth_controller import AuthController
from app.schemas.response import APIResponse
from app.schemas.token import Token
from app.db.session import get_db

router = APIRouter(tags=["Autenticación"])

class LoginRequest(BaseModel):
    """Esquema para la solicitud de inicio de sesión"""
    email: EmailStr = Field(..., description="Correo electrónico del usuario")
    password: str = Field(..., min_length=6, description="Contraseña del usuario")

@router.post(
    "/login",
    response_model=APIResponse[Token],
    summary="Iniciar sesión",
    description="Autentica un usuario y devuelve un token de acceso.",
)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[Token]:
    """
    Inicia sesión de un usuario y devuelve un token de acceso.
    
    - **email**: Correo electrónico del usuario
    - **password**: Contraseña del usuario
    """
    # Inicializar repositorio y controlador
    user_repository = SQLAlchemyUserRepository(db)
    auth_controller = AuthController(user_repository)
    
    # Llamar al controlador
    return await auth_controller.login(login_data.email, login_data.password)

# Aquí puedes agregar más rutas relacionadas con autenticación, como:
# - /register
# - /refresh-token
# - /forgot-password
# - /reset-password
