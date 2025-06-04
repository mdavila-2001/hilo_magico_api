import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.exceptions import (
    BadRequestException,
    NotFoundException,
    UnauthorizedException,
    ForbiddenException,
    ConflictException
)
from app.models.user import User
from app.schemas.user import (
    UserRole,
    UserCreate,
    UserUpdate,
    UserInDB,
    UserOut
)
from app.schemas.response import APIResponse

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user with email and password.
        
        Args:
            email: User's email
            password: Plain text password
            
        Returns:
            User: The authenticated user if successful, None otherwise
        """
        try:
            user = await self.get_by_email(email=email)
            
            if not user:
                self.logger.warning(f"Login attempt failed: User with email {email} not found")
                return None
                
            if not verify_password(password, user.hashed_password):
                self.logger.warning(f"Login attempt failed: Invalid password for user {email}")
                return None
                
            if not user.is_active:
                self.logger.warning(f"Login attempt failed: User {email} is inactive")
                return None
                
            return user
            
        except Exception as e:
            self.logger.error(f"Error authenticating user {email}: {str(e)}")
            return None

    async def get_user_by_id(self, user_id: Union[UUID, str]) -> Optional[User]:
        """
        Retrieve a user by their ID.
        
        Args:
            user_id: The UUID of the user to retrieve (as string or UUID object)
            
        Returns:
            Optional[User]: The user if found, None otherwise
        """
        try:
            user_uuid = UUID(str(user_id)) if isinstance(user_id, str) else user_id
            result = await self.db.execute(
                select(User).where(User.id == user_uuid, User.deleted_at.is_(None))
            )
            return result.scalars().first()
        except ValueError:
            raise BadRequestException("Invalid user ID format")
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by their email address.
        
        Args:
            email: The email address to search for
            
        Returns:
            Optional[User]: The user if found, None otherwise
        """
        if not email:
            raise BadRequestException("Email is required")
            
        result = await self.db.execute(
            select(User).where(
                User.email == email.lower(),
                User.deleted_at.is_(None)
            )
        )
        return result.scalars().first()
    
    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user in the system.
        
        Args:
            user_data: The user data for the new user
            
        Returns:
            User: The newly created user
            
        Raises:
            ConflictException: If a user with the email already exists
        """
        try:
            self.logger.info(f"Iniciando creación de usuario: {user_data.email}")
            
            # Check if user with this email already exists
            self.logger.info("Verificando si el correo ya existe...")
            existing_user = await self.get_user_by_email(user_data.email)
            if existing_user:
                self.logger.warning(f"Intento de crear usuario con correo existente: {user_data.email}")
                raise ConflictException("A user with this email already exists")
            
            # Create new user
            self.logger.info("Creando objeto de usuario...")
            now = datetime.now(timezone.utc)
            hashed_pwd = get_password_hash(user_data.password)
            
            self.logger.info("Hasheando contraseña...")
            
            db_user = User(
                email=user_data.email.lower(),
                hashed_password=hashed_pwd,
                first_name=user_data.first_name,
                middle_name=user_data.middle_name,
                last_name=user_data.last_name,
                mother_last_name=user_data.mother_last_name,
                is_active=user_data.is_active if hasattr(user_data, 'is_active') else True,
                is_superuser=user_data.is_superuser if hasattr(user_data, 'is_superuser') else False,
                role=user_data.role if hasattr(user_data, 'role') else UserRole.CUSTOMER,
                created_at=now,
                updated_at=now
            )
            
            self.logger.info("Agregando usuario a la sesión...")
            self.db.add(db_user)
            
            self.logger.info("Realizando commit...")
            await self.db.commit()
            
            self.logger.info("Actualizando objeto de usuario...")
            await self.db.refresh(db_user)
            
            self.logger.info(f"Usuario creado exitosamente con ID: {db_user.id}")
            return db_user
            
        except Exception as e:
            self.logger.error(f"Error al crear usuario: {str(e)}", exc_info=True)
            # Rollback en caso de error
            await self.db.rollback()
            raise
    
    async def update_user(
        self, 
        user_id: Union[UUID, str],
        user_data: UserUpdate,
        current_user: User
    ) -> User:
        """
        Update an existing user.
        
        Args:
            user_id: The ID of the user to update
            user_data: The updated user data
            current_user: The currently authenticated user
            
        Returns:
            User: The updated user
            
        Raises:
            NotFoundException: If the user is not found
            ForbiddenException: If the current user doesn't have permission
        """
        # Only the user themselves or an admin can update
        db_user = await self.get_user_by_id(user_id)
        if not db_user:
            raise NotFoundException("User not found")
            
        if str(current_user.id) != str(user_id) and not current_user.is_superuser:
            raise ForbiddenException("You don't have permission to update this user")
        
        # Only admins can update certain fields
        if not current_user.is_superuser:
            if user_data.role is not None and user_data.role != db_user.role:
                raise ForbiddenException("You can't change user roles")
            if user_data.is_superuser is not None and user_data.is_superuser != db_user.is_superuser:
                raise ForbiddenException("You can't change superuser status")
        
        update_data = user_data.dict(exclude_unset=True)
        
        # Handle password update
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        # Update fields
        for field, value in update_data.items():
            # Skip fields that shouldn't be updated directly
            if field in ['password', 'email']:
                continue
                
            # Special handling for name fields
            if field == 'first_name':
                db_user.first_name = value
            elif field == 'middle_name':
                db_user.middle_name = value
            elif field == 'last_name':
                db_user.last_name = value
            elif field == 'mother_last_name':
                db_user.mother_last_name = value
            # Handle other fields normally
            elif hasattr(db_user, field):
                setattr(db_user, field, value)
        
        db_user.updated_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        await self.db.refresh(db_user)
        
        return db_user
    
    async def authenticate(self, email: str, password: str) -> User:
        """
        Authenticate a user with email and password.
        
        Args:
            email: The user's email
            password: The user's password
            
        Returns:
            User: The authenticated user
            
        Raises:
            UnauthorizedException: If authentication fails
        """
        user = await self.get_user_by_email(email)
        if not user or not user.hashed_password:
            raise UnauthorizedException("Incorrect email or password")
            
        if not user.is_active:
            raise UnauthorizedException("This account is inactive")
            
        if not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Incorrect email or password")
            
        return user
    
    async def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        current_user: Optional[User] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[User]:
        """
        Get a list of users with optional filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            current_user: The currently authenticated user
            filters: Optional filters to apply
            
        Returns:
            List[User]: List of users
            
        Raises:
            ForbiddenException: If the user doesn't have permission
        """
        # Only admins can list all users
        if current_user and not current_user.is_superuser:
            raise ForbiddenException("You don't have permission to list users")
        
        query = select(User).where(User.deleted_at.is_(None))
        
        # Apply filters if provided
        if filters:
            filter_conditions = []
            for field, value in filters.items():
                if hasattr(User, field):
                    filter_conditions.append(getattr(User, field) == value)
            if filter_conditions:
                query = query.where(and_(*filter_conditions))
        
        # Apply pagination
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def delete_user(
        self,
        user_id: Union[UUID, str],
        current_user: User,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete a user (soft delete by default).
        
        Args:
            user_id: The ID of the user to delete
            current_user: The currently authenticated user
            hard_delete: If True, permanently delete the user
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            ForbiddenException: If the user doesn't have permission
            NotFoundException: If the user is not found
        """
        db_user = await self.get_user_by_id(user_id)
        if not db_user:
            raise NotFoundException("User not found")
            
        # Only the user themselves or an admin can delete
        if str(current_user.id) != str(user_id) and not current_user.is_superuser:
            raise ForbiddenException("You don't have permission to delete this user")
            
        # Prevent admins from being deleted by non-superusers
        if db_user.is_superuser and not current_user.is_superuser:
            raise ForbiddenException("Cannot delete admin users")
            
        if hard_delete and current_user.is_superuser:
            # Hard delete (permanent removal)
            await self.db.delete(db_user)
        else:
            # Soft delete (mark as deleted)
            db_user.is_active = False
            db_user.deleted_at = datetime.now(timezone.utc)
            
        await self.db.commit()
        return True
    
    async def count_users(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count the number of users matching optional filters.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            int: The count of matching users
        """
        query = select(User).where(User.deleted_at.is_(None))
        
        if filters:
            filter_conditions = []
            for field, value in filters.items():
                if hasattr(User, field):
                    filter_conditions.append(getattr(User, field) == value)
            if filter_conditions:
                query = query.where(and_(*filter_conditions))
                
        result = await self.db.execute(select([func.count()]).select_from(query.subquery()))
        return result.scalar_one()
