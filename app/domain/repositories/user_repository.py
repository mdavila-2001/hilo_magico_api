from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from ..entities.user import User


class UserRepository(ABC):
    """
    Interfaz del repositorio de usuarios que define las operaciones
    que deben ser implementadas por cualquier repositorio concreto.
    """

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Obtiene un usuario por su ID.

        Args:
            user_id: ID del usuario a buscar

        Returns:
            Optional[User]: El usuario si se encuentra, None en caso contrario
        """
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario por su email.

        Args:
            email: Email del usuario a buscar

        Returns:
            Optional[User]: El usuario si se encuentra, None en caso contrario
        """
        pass

    @abstractmethod
    async def add(self, user: User) -> None:
        """
        Agrega un nuevo usuario al repositorio.

        Args:
            user: Usuario a agregar
        """
        pass

    @abstractmethod
    async def update(self, user: User) -> None:
        """
        Actualiza un usuario existente.

        Args:
            user: Usuario con los datos actualizados
        """
        pass

    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        """
        Elimina un usuario por su ID.

        Args:
            user_id: ID del usuario a eliminar

        Returns:
            bool: True si se eliminó correctamente, False en caso contrario
        """
        pass
