from typing import Optional, Tuple
from datetime import timedelta
from uuid import UUID

from ....domain.entities.user import User
from ....domain.repositories.user_repository import UserRepository
from .....core.security import verify_password, create_access_token, create_refresh_token
from .....core.config import settings


class LoginUseCase:
    """
    Caso de uso para el inicio de sesión de un usuario.
    """

    def __init__(self, user_repository: UserRepository):
        """
        Inicializa el caso de uso con el repositorio de usuarios.

        Args:
            user_repository: Repositorio para acceder a los datos de usuarios
        """
        self.user_repository = user_repository

    async def execute(self, email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Ejecuta el caso de uso de inicio de sesión.

        Args:
            email: Email del usuario
            password: Contraseña sin encriptar

        Returns:
            Tuple[Optional[User], Optional[str]]: Tupla con el usuario y el token de acceso
        """
        # 1. Buscar usuario por email
        user = await self.user_repository.get_by_email(email)
        if not user:
            return None, None

        # 2. Verificar contraseña
        if not verify_password(password, user.hashed_password):
            return None, None

        # 3. Verificar si el usuario está activo
        if not user.is_active:
            return user, None

        # 4. Generar token de acceso
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )

        return user, access_token
