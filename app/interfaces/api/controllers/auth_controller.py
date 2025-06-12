from typing import Optional

from fastapi import HTTPException, status, Depends
from pydantic import EmailStr

from ....domain.entities.user import User
from ....domain.events import event_bus
from ....domain.repositories.user_repository import UserRepository
from ....domain.services.auth_service import AuthService
from ....infrastructure.persistence.sqlalchemy_unit_of_work import SQLAlchemyUnitOfWork
from .....core.logging_config import get_logger
from .....schemas.response import APIResponse
from .....schemas.token import Token
from .....schemas.user import UserCreate, UserResponse
from .....core.dependencies import get_unit_of_work

# Configurar logger
logger = get_logger(__name__)


class AuthController:
    """
    Controlador para manejar las operaciones de autenticación.
    """

    def __init__(self, auth_service: AuthService):
        """
        Inicializa el controlador con el servicio de autenticación.

        Args:
            auth_service: Servicio de autenticación
        """
        self.auth_service = auth_service

    @classmethod
    def create(cls, uow: SQLAlchemyUnitOfWork = Depends(get_unit_of_work)):
        """
        Factory method para crear una instancia del controlador con sus dependencias.
        
        Args:
            uow: Unidad de trabajo para manejar transacciones
            
        Returns:
            AuthController: Instancia del controlador
        """
        with uow.repository(UserRepository) as user_repo:
            auth_service = AuthService(user_repo)
            return cls(auth_service)

    async def login(self, email: str, password: str) -> APIResponse[Token]:
        """
        Maneja la solicitud de inicio de sesión.

        Args:
            email: Email del usuario
            password: Contraseña sin encriptar

        Returns:
            APIResponse[Token]: Respuesta con el token de acceso

        Raises:
            HTTPException: Si las credenciales son inválidas o el usuario está inactivo
        """
        try:
            # Validar el formato del email
            email_vo = Email(email)
            
            # Autenticar al usuario
            user = await self.auth_service.authenticate_user(email_vo, password)
            
            if not user:
                logger.warning(f"Intento de inicio de sesión fallido para el email: {email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales inválidas",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            if not user.is_active:
                logger.warning(f"Intento de inicio de sesión para usuario inactivo: {email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Usuario inactivo. Por favor, contacte al administrador.",
                )
            
            # Generar token de acceso
            access_token = self.auth_service.create_access_token(user.id)
            
            # Registrar inicio de sesión exitoso
            logger.info(f"Inicio de sesión exitoso para el usuario: {email}")
            
            return APIResponse[Token].create_success(
                data=Token(
                    access_token=access_token,
                    token_type="bearer"
                ),
                message="Inicio de sesión exitoso"
            )
            
        except ValueError as e:
            logger.error(f"Error de validación en inicio de sesión: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.exception(f"Error inesperado durante el inicio de sesión: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ocurrió un error inesperado durante el inicio de sesión"
            )
    
    async def register(self, user_data: UserCreate) -> APIResponse[UserResponse]:
        """
        Maneja el registro de un nuevo usuario.
        
        Este método crea un nuevo usuario, publica un evento de dominio para notificar
        el registro y devuelve los datos del usuario creado.
        
        Args:
            user_data: Datos del nuevo usuario
            
        Returns:
            APIResponse[UserResponse]: Respuesta con los datos del usuario registrado
            
        Raises:
            HTTPException: Si hay un error durante el registro o validación
        """
        try:
            logger.info(f"Iniciando registro de nuevo usuario: {user_data.email}")
            
            # Registrar al nuevo usuario
            user = await self.auth_service.register_user(
                email=user_data.email,
                password=user_data.password,
                first_name=user_data.first_name,
                last_name=user_data.last_name
            )
            
            # Publicar eventos de dominio pendientes
            await user.publish_events()
            
            logger.info(f"Usuario registrado exitosamente: {user.email}")
            
            # Convertir la entidad a esquema de respuesta
            user_response = UserResponse.from_entity(user)
            
            return APIResponse[UserResponse].create_success(
                data=user_response,
                message="Usuario registrado exitosamente",
                status_code=status.HTTP_201_CREATED
            )
            
        except ValueError as e:
            logger.error(f"Error de validación en registro: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException as he:
            # Re-lanzar excepciones HTTP existentes
            raise he
        except Exception as e:
            logger.exception(f"Error inesperado durante el registro: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ocurrió un error inesperado durante el registro"
            )
