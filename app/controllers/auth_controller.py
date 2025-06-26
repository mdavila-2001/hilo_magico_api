from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash
)
from app.schemas.response import APIResponse
from app.schemas.token import Token, TokenData
from app.schemas.user import UserCreate, UserOut
from app.services.user import UserService
from app.models.user import User

class AuthController:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)

    async def login(self, email: str, password: str) -> APIResponse[Token]:
        """
        Autentica un usuario y devuelve los tokens de acceso y actualización.
        
        Args:
            email (str): Correo electrónico del usuario
            password (str): Contraseña del usuario
            
        Returns:
            APIResponse[Token]: Respuesta con los tokens de autenticación
            
        Raises:
            HTTPException: Si las credenciales son inválidas o el usuario está inactivo
        """
        user = await self.user_service.authenticate(email, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo electrónico o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario inactivo",
            )

        # Crear tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        expires_at = datetime.utcnow() + access_token_expires
        
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        # Obtener el nombre del rol
        from app.models.user import UserRole  # Asegúrate de importar UserRole
        
        # Si el rol es un entero, convertirlo a su representación de cadena
        if isinstance(user.role, int):
            try:
                role_name = UserRole(user.role).name.lower()
            except ValueError:
                role_name = str(user.role)
        elif hasattr(user.role, 'value'):
            # Si es un enum, obtener su valor
            role_name = user.role.value
        else:
            # Si ya es un string, usarlo directamente
            role_name = str(user.role)
            
        # Crear objeto de información del usuario
        user_info = {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "middle_name": user.middle_name,
            "last_name": user.last_name,
            "mother_last_name": user.mother_last_name,
            "role": role_name,
            "is_active": user.is_active
        }

        return APIResponse[Token].create_success(
            data=Token(
                access_token=access_token,
                token_type="bearer",
                refresh_token=refresh_token,
                expires_at=expires_at,
                user=user_info
            ),
            message=f"Inicio de sesión exitoso"
        )

    async def refresh_token(self, refresh_token: str) -> APIResponse[Token]:
        """
        Refresca un token de acceso usando un token de actualización.
        
        Args:
            refresh_token (str): Token de actualización
            
        Returns:
            APIResponse[Token]: Nueva respuesta con tokens actualizados
        """
        # Implementar lógica de refresco de token
        pass

    async def register(self, user_data: UserCreate) -> APIResponse[UserOut]:
        """
        Registra un nuevo usuario en el sistema.
        
        Args:
            user_data (UserCreate): Datos del nuevo usuario
            
        Returns:
            APIResponse[UserOut]: Usuario creado
        """
        # Verificar si el usuario ya existe
        existing_user = await self.user_service.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está registrado"
            )
        
        # Crear el usuario
        user = await self.user_service.create_user(user_data)
        return APIResponse[UserOut].create_success(
            data=UserOut.from_orm(user),
            status_code=status.HTTP_201_CREATED,
            message="Usuario registrado exitosamente"
        )
