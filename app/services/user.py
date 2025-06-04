from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from passlib.context import CryptContext

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Obtiene un usuario por su ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalars().first()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Obtiene un usuario por su email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalars().first()
    
    async def create_user(self, user_in: UserCreate) -> User:
        """Crea un nuevo usuario"""
        # Verificar si el usuario ya existe
        existing_user = await self.get_user_by_email(user_in.email)
        if existing_user:
            raise ValueError("El correo electrónico ya está registrado")
        
        # Crear el usuario
        db_user = User(
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name,
            is_active=user_in.is_active if user_in.is_active is not None else True,
            is_superuser=user_in.is_superuser if user_in.is_superuser is not None else False,
        )
        
        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        
        return db_user
    
    async def update_user(
        self, 
        user_id: str, 
        user_in: UserUpdate,
        current_user: User
    ) -> Optional[User]:
        """Actualiza un usuario existente"""
        # Solo el propio usuario o un superusuario puede actualizar
        if str(current_user.id) != user_id and not current_user.is_superuser:
            raise PermissionError("No tiene permisos para actualizar este usuario")
        
        db_user = await self.get_user_by_id(user_id)
        if not db_user:
            return None
        
        update_data = user_in.dict(exclude_unset=True)
        
        # Si se está actualizando la contraseña, hashearla
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        
        # Actualizar campos
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        await self.db.commit()
        await self.db.refresh(db_user)
        
        return db_user
    
    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """Autentica un usuario con email y contraseña"""
        user = await self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    async def get_users(
        self, 
        skip: int = 0, 
        limit: int = 100,
        current_user: Optional[User] = None
    ) -> List[User]:
        """Obtiene una lista de usuarios"""
        # Solo los superusuarios pueden ver todos los usuarios
        if current_user and not current_user.is_superuser:
            raise PermissionError("No tiene permisos para ver la lista de usuarios")
        
        result = await self.db.execute(
            select(User)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def delete_user(
        self, 
        user_id: str, 
        current_user: User
    ) -> bool:
        """Elimina un usuario (eliminación lógica)"""
        # Solo el propio usuario o un superusuario puede eliminarse
        if str(current_user.id) != user_id and not current_user.is_superuser:
            raise PermissionError("No tiene permisos para eliminar este usuario")
        
        db_user = await self.get_user_by_id(user_id)
        if not db_user:
            return False
        
        # Eliminación lógica
        db_user.is_active = False
        await self.db.commit()
        
        return True
