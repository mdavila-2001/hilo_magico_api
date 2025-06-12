"""Eventos relacionados con los usuarios."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from . import DomainEvent

class UserRegisteredEvent(DomainEvent):
    """Evento que se dispara cuando un usuario se registra."""
    
    def __init__(
        self,
        user_id: UUID,
        email: str,
        full_name: Optional[str] = None,
        event_id: Optional[UUID] = None,
        occurred_on: Optional[datetime] = None
    ):
        """Inicializa el evento de usuario registrado.
        
        Args:
            user_id: ID del usuario registrado
            email: Email del usuario
            full_name: Nombre completo del usuario (opcional)
            event_id: ID único del evento (se genera uno si no se proporciona)
            occurred_on: Fecha y hora del evento (ahora si no se proporciona)
        """
        super().__init__()
        self.user_id = user_id
        self.email = email
        self.full_name = full_name
        
        # Sobrescribir valores por defecto si se proporcionan
        if event_id:
            self.event_id = event_id
        if occurred_on:
            self.occurred_on = occurred_on
    
    @classmethod
    def from_user(cls, user: 'User') -> 'UserRegisteredEvent':
        """Crea un evento a partir de una entidad User."""
        from ...domain.entities.user import User  # Importación local para evitar circularidad
        
        full_name = None
        if user.full_name:
            first = getattr(user.full_name, 'first_name', '')
            last = getattr(user.full_name, 'last_name', '')
            full_name = f"{first} {last}".strip()
            
        return cls(
            user_id=user.id,
            email=str(user.email) if hasattr(user, 'email') else '',
            full_name=full_name
        )
    
    def __str__(self) -> str:
        """Representación en cadena del evento."""
        return f"{self.__class__.__name__}(user_id={self.user_id}, email={self.email})"
