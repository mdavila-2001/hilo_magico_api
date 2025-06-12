"""Eventos relacionados con los usuarios."""
from datetime import datetime
from uuid import UUID, uuid4

from . import DomainEvent
from ...domain.entities.user import User

class UserRegisteredEvent(DomainEvent):
    """Evento que se dispara cuando un usuario se registra."""
    
    def __init__(
        self,
        user_id: UUID,
        email: str,
        full_name: str = None,
        event_id: UUID = None,
        occurred_on: datetime = None
    ):
        """Inicializa el evento de usuario registrado.
        
        Args:
            user_id: ID del usuario registrado
            email: Email del usuario
            full_name: Nombre completo del usuario (opcional)
            event_id: ID único del evento (se genera uno si no se proporciona)
            occurred_on: Fecha y hora del evento (ahora si no se proporciona)
        """
        super().__init__(
            event_id=event_id or uuid4(),
            occurred_on=occurred_on or datetime.utcnow(),
            event_type=self.__class__.__name__
        )
        self.user_id = user_id
        self.email = email
        self.full_name = full_name
    
    @classmethod
    def from_user(cls, user: User) -> 'UserRegisteredEvent':
        """Crea un evento a partir de una entidad User."""
        full_name = f"{user.full_name.first_name} {user.full_name.last_name}" if user.full_name else None
        return cls(
            user_id=user.id,
            email=str(user.email),
            full_name=full_name
        )
