from typing import Optional, List, Any, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, func

from ....domain.entities.user import User
from ....domain.repositories.user_repository import UserRepository
from .....models.user import User as UserModel
from ....domain.value_objects import Email, FullName


class SQLAlchemyUserRepository(UserRepository):
    """
    Implementación concreta del repositorio de usuarios usando SQLAlchemy.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el repositorio con una sesión de SQLAlchemy.

        Args:
            session: Sesión asíncrona de SQLAlchemy
        """
        self.session = session

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Obtiene un usuario por su ID.

        Args:
            user_id: ID del usuario a buscar

        Returns:
            Optional[User]: El usuario si se encuentra, None en caso contrario
        """
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == str(user_id))
        )
        user_model = result.scalar_one_or_none()
        if not user_model:
            return None
        return await self._to_entity(user_model)

    async def get_by_email(self, email: Email) -> Optional[User]:
        """
        Obtiene un usuario por su email.

        Args:
            email: Email del usuario a buscar (objeto Email value object)

        Returns:
            Optional[User]: El usuario si se encuentra, None en caso contrario
        """
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == str(email))
        )
        user_model = result.scalar_one_or_none()
        if not user_model:
            return None
        return await self._to_entity(user_model)

    async def add(self, user: User) -> None:
        """
        Agrega un nuevo usuario al repositorio.

        Args:
            user: Usuario a agregar
        """
        user_dict = self._to_dict(user)
        user_model = UserModel(**user_dict)
        self.session.add(user_model)
        await self.session.flush()
        
        # Actualizar el usuario con cualquier valor generado por la base de datos
        await self.session.refresh(user_model)

    async def update(self, user: User) -> None:
        """
        Actualiza un usuario existente.

        Args:
            user: Usuario con los datos actualizados
        """
        user_dict = self._to_dict(user)
        
        stmt = (
            update(UserModel)
            .where(UserModel.id == str(user.id))
            .values(**user_dict)
        )
        
        await self.session.execute(stmt)
        await self.session.flush()

    async def delete(self, user_id: UUID) -> bool:
        """
        Elimina un usuario por su ID.

        Args:
            user_id: ID del usuario a eliminar

        Returns:
            bool: True si se eliminó correctamente, False en caso contrario
        """
        stmt = delete(UserModel).where(UserModel.id == str(user_id))
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
        
    async def email_exists(self, email: Email) -> bool:
        """
        Verifica si ya existe un usuario con el email proporcionado.
        
        Args:
            email: Email a verificar
            
        Returns:
            bool: True si el email ya está en uso, False en caso contrario
        """
        result = await self.session.execute(
            select(func.count()).where(UserModel.email == str(email))
        )
        return result.scalar() > 0

    async def _to_entity(self, model: UserModel) -> User:
        """
        Convierte un modelo de SQLAlchemy a una entidad de dominio.

        Args:
            model: Modelo de SQLAlchemy

        Returns:
            User: Entidad de dominio User
        """
        # Convertir el email a un objeto Email value object
        email = Email(model.email)
        
        # Convertir el nombre completo a un objeto FullName si existe
        full_name = None
        if model.full_name:
            # Asumimos que full_name se almacena como "Nombre Apellido"
            name_parts = model.full_name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            full_name = FullName(first_name, last_name)
        
        # Crear el usuario con los value objects
        user = User.create(
            email=str(email),
            plain_password=model.hashed_password,  # En un caso real, no deberíamos tener la contraseña en texto plano
            first_name=full_name.first_name if full_name else None,
            last_name=full_name.last_name if full_name else None
        )
        
        # Establecer atributos que no se manejan en el factory method
        user.id = UUID(model.id)
        user.is_active = model.is_active
        user.created_at = model.created_at
        user.updated_at = model.updated_at
        
        return user
        
    def _to_dict(self, user: User) -> Dict[str, Any]:
        """
        Convierte una entidad de dominio a un diccionario para su almacenamiento.
        
        Args:
            user: Entidad de dominio User
            
        Returns:
            Dict: Diccionario con los datos del usuario
        """
        return {
            "id": str(user.id),
            "email": str(user.email),
            "hashed_password": user.password,  # Usar la propiedad que devuelve el hash
            "full_name": str(user.full_name) if user.full_name else None,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
