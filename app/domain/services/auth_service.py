"""
Servicio de dominio para operaciones de autenticación.
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID

from jose import JWTError, jwt

from ....core.config import settings
from ....core.logging_config import get_logger
from ..entities.user import User
from ..value_objects import Email
from ..repositories.user_repository import UserRepository

# Configurar logger
logger = get_logger(__name__)


class AuthService:
    """
    Servicio de dominio que maneja la lógica de autenticación.
    """

    def __init__(self, user_repository: UserRepository):
        """
        Inicializa el servicio de autenticación.

        Args:
            user_repository: Repositorio para acceder a los datos de usuarios
        """
        self.user_repository = user_repository
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    async def authenticate_user(self, email: Email, password: str) -> Optional[User]:
        """
        Autentica a un usuario con su email y contraseña.

        Args:
            email: Email del usuario
            password: Contraseña en texto plano

        Returns:
            Optional[User]: El usuario autenticado o None si la autenticación falla
        """
        user = await self.user_repository.get_by_email(email)
        if not user:
            return None
        if not user.verify_password(password):
            return None
        return user

    def create_access_token(self, user_id: UUID) -> str:
        """
        Crea un token de acceso JWT para el usuario.

        Args:
            user_id: ID del usuario

        Returns:
            str: Token JWT codificado
        """
        expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "type": "access"
        }
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[UUID]:
        """
        Verifica un token JWT y devuelve el ID de usuario si es válido.

        Args:
            token: Token JWT a verificar

        Returns:
            Optional[UUID]: ID del usuario si el token es válido, None en caso contrario
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != "access":
                return None
                
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
                
            return UUID(user_id)
            
        except (JWTError, ValueError):
            return None

    async def get_current_user(self, token: str) -> Optional[User]:
        """
        Obtiene el usuario actual a partir de un token JWT.

        Args:
            token: Token JWT

        Returns:
            Optional[User]: El usuario si el token es válido, None en caso contrario
        """
        user_id = self.verify_token(token)
        if user_id is None:
            return None
            
        return await self.user_repository.get_by_id(user_id)

    async def register_user(
        self,
        email: str,
        password: str,
        first_name: str = None,
        last_name: str = None
    ) -> User:
        """
        Registra un nuevo usuario en el sistema.

        Este método crea un nuevo usuario, lo guarda en el repositorio y dispara
        un evento de dominio UserRegisteredEvent.

        Args:
            email: Email del nuevo usuario
            password: Contraseña en texto plano
            first_name: Nombre del usuario (opcional)
            last_name: Apellido del usuario (opcional)

        Returns:
            User: El usuario recién creado

        Raises:
            ValueError: Si hay un error de validación o el email ya está en uso
        """
        logger.info(f"Iniciando registro de usuario: {email}")
        
        # Validar el formato del email
        email_vo = Email(email)
        
        # Verificar si el email ya está en uso
        if await self.user_repository.email_exists(email_vo):
            error_msg = f"El correo electrónico {email} ya está en uso"
            logger.warning(error_msg)
            raise ValueError(error_msg)
        
        try:
            # Crear el nuevo usuario (esto ya dispara el evento UserRegisteredEvent internamente)
            user = User.create(
                email=email,
                plain_password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Guardar el usuario en el repositorio
            await self.user_repository.add(user)
            logger.info(f"Usuario {email} creado exitosamente")
            
            # Nota: Los eventos de dominio se publicarán cuando se llame a user.publish_events()
            # desde la capa de aplicación (controlador)
            
            return user
            
        except Exception as e:
            logger.error(f"Error al registrar usuario {email}: {str(e)}")
            # Relanzar la excepción para que la capa de aplicación la maneje
            raise
