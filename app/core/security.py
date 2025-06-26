"""Security utilities for the application."""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.exceptions import ForbiddenException, InvalidTokenException, UnauthorizedException
from app.models.user import User

# Configure logger
logger = logging.getLogger(__name__)

# Security configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify if the provided password matches the hashed password.
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password from the database
        
    Returns:
        bool: True if the password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        # Log the error but don't expose it to the user
        logger = logging.getLogger(__name__)
        logger.error(f"Error verifying password: {str(e)}")
        return False


def get_password_hash(password: str) -> str:
    """
    Generate a hashed version of the password.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        str: The hashed password
        
    Raises:
        ValueError: If password hashing fails
    """
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error hashing password: {str(e)}")
        raise ValueError("Failed to hash password") from e

def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a new JWT access token.
    
    Args:
        data: The data to encode in the token (usually a user ID or similar)
        expires_delta: Optional timedelta for token expiration
        
    Returns:
        str: Encoded JWT token
        
    Raises:
        ValueError: If token creation fails
    """
    try:
        to_encode = data.copy()
        expire = (
            datetime.utcnow() + expires_delta 
            if expires_delta 
            else datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        return jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating access token: {str(e)}")
        raise ValueError("Failed to create access token") from e


def create_refresh_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a new JWT refresh token.
    
    Args:
        data: The data to encode in the token (usually a user ID or similar)
        expires_delta: Optional timedelta for token expiration
        
    Returns:
        str: Encoded JWT refresh token
        
    Raises:
        ValueError: If token creation fails
    """
    try:
        to_encode = data.copy()
        
        # Set expiration time (default to 30 days)
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            
        # Add token claims
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        # Encode the token
        return jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating refresh token: {str(e)}")
        raise ValueError("Failed to create refresh token") from e

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current user from the JWT token.
    
    Args:
        token: JWT token from the Authorization header
        db: Database session
        
    Returns:
        User: The user model instance
        
    Raises:
        UnauthorizedException: If the token is invalid or user not found
    """
    if not token:
        raise UnauthorizedException(detail="No se encuentra con la sesión activa")
    
    try:
        # Decode the token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={"verify_aud": False}  # Skip audience verification if not used
        )
        
        # Get user ID from token
        user_id: str = payload.get("sub")
        if not user_id:
            raise InvalidTokenException(detail="Invalid token payload: missing 'sub' claim")
            
        # Get user from database
        from uuid import UUID
        try:
            user = await db.get(User, UUID(user_id))
            if not user:
                raise UnauthorizedException(detail="User not found")
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid user ID format: {str(e)}")
            raise UnauthorizedException(detail="Invalid user ID format")
            
        # Check if user is active
        if not user.is_active:
            raise ForbiddenException(detail="Inactive user")
            
        return user
        
    except JWTError as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"JWT validation error: {str(e)}")
        raise InvalidTokenException(detail="Invalid or expired token") from e
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in get_current_user: {str(e)}")
        raise UnauthorizedException(detail="Could not validate credentials") from e

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verify that the current user is active.
    
    Args:
        current_user: The current user from get_current_user
        
    Returns:
        User: The active user
        
    Raises:
        ForbiddenException: If the user is inactive
    """
    if not current_user.is_active:
        logger.warning(f"Intento de acceso de usuario inactivo: {current_user.email}")
        raise ForbiddenException("Usuario inactivo")
    return current_user


def check_user_permissions(
    required_roles: list[str] = None,
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Verifica si el usuario actual tiene los permisos necesarios.
    
    Args:
        required_roles: Lista de roles requeridos. Si es None, cualquier usuario autenticado tiene acceso.
        current_user: Usuario actual obtenido del token JWT.
        
    Returns:
        User: El usuario actual si tiene los permisos necesarios.
        
    Raises:
        ForbiddenException: Si el usuario no tiene los permisos necesarios.
    """
    if required_roles is None:
        required_roles = ["user"]  # Por defecto, cualquier usuario autenticado
        
    from app.schemas.user import UserRole
    
    # Si el usuario es superadmin, tiene acceso a todo
    if current_user.role == UserRole.ADMIN:  # Asumiendo que ADMIN=1 es el superadmin
        return current_user
        
    # Convertir los roles requeridos a enteros si son strings
    required_roles_int = []
    for role in required_roles:
        if isinstance(role, str):
            # Si es string, obtener el valor del enum
            try:
                role_enum = getattr(UserRole, role.upper())
                required_roles_int.append(role_enum)
            except AttributeError:
                # Si no existe el rol, lo ignoramos
                continue
        else:
            # Si ya es un entero, usarlo directamente
            required_roles_int.append(role)
    
    # Verificar si el rol del usuario está en los roles requeridos
    if current_user.role not in required_roles_int:
        logger.warning(
            f"Intento de acceso no autorizado. "
            f"Usuario: {current_user.email}, Rol: {current_user.role}, "
            f"Roles requeridos: {required_roles}"
        )
        raise ForbiddenException(
            "No tiene permisos suficientes para acceder a este recurso"
        )
        
    return current_user


def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Verifica que el usuario actual sea un administrador.
    
    Args:
        current_user: Usuario actual obtenido del token JWT.
        
    Returns:
        User: El usuario actual si es administrador.
        
    Raises:
        ForbiddenException: Si el usuario no es administrador.
    """
    from app.schemas.user import UserRole
    # ADMIN = 1, OWNER = 2 pueden tener acceso a funciones de administrador
    return check_user_permissions(required_roles=[UserRole.ADMIN, UserRole.OWNER], current_user=current_user)


def get_current_seller_user(
    current_user: User = Depends(get_current_active_user)
):
    """
    Verifica que el usuario actual sea un vendedor.
    
    Args:
        current_user: Usuario actual obtenido del token JWT.
        
    Returns:
        User: El usuario actual si es vendedor.
        
    Raises:
        ForbiddenException: Si el usuario no tiene rol de vendedor.
    """
    if current_user.role != "seller" and not current_user.is_superuser:
        raise ForbiddenException("El usuario no tiene permisos de vendedor")
    return current_user


def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
):
    """
    Verifica que el usuario actual sea un superusuario.
    
    Args:
        current_user: Usuario actual obtenido del token JWT.
        
    Returns:
        User: El usuario actual si es superusuario.
        
    Raises:
        ForbiddenException: Si el usuario no es superusuario.
    """
    if not current_user.is_superuser:
        raise ForbiddenException("El usuario no tiene permisos de superusuario")
    return current_user