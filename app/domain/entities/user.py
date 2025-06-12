from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
from typing import List, Optional, TypeVar

from ..events import DomainEvent, event_bus
from ..value_objects import Email, Password, FullName

T = TypeVar('T', bound=DomainEvent)

@dataclass
class User:
    """
    Agregado raíz que representa a un usuario en el sistema.
    
    Atributos:
        id: Identificador único del usuario
        email: Dirección de correo electrónico del usuario
        password: Contraseña hasheada del usuario
        full_name: Nombre completo del usuario (opcional)
        is_active: Indica si la cuenta está activa
        created_at: Fecha de creación del usuario
        updated_at: Fecha de última actualización
    """
    email: Email
    _password: Password
    id: UUID = field(default_factory=uuid4)
    full_name: Optional[FullName] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    _domain_events: List[DomainEvent] = field(default_factory=list, init=False)

    def __post_init__(self):
        """Valida los datos después de la inicialización."""
        # Validaciones adicionales si son necesarias
        pass
        
    def add_domain_event(self, event: DomainEvent) -> None:
        """Agrega un evento de dominio a la lista de eventos pendientes."""
        self._domain_events.append(event)
    
    def clear_domain_events(self) -> None:
        """Limpia la lista de eventos de dominio pendientes."""
        self._domain_events.clear()
    
    async def publish_events(self) -> None:
        """Publica todos los eventos de dominio pendientes."""
        for event in self._domain_events:
            await event_bus.publish(event)
        self.clear_domain_events()
    
    def get_domain_events(self) -> List[DomainEvent]:
        """Obtiene una copia de los eventos de dominio pendientes."""
        return list(self._domain_events)

    @classmethod
    def create(
        cls,
        email: str,
        plain_password: str,
        first_name: str = None,
        last_name: str = None
    ) -> 'User':
        """
        Factory method para crear un nuevo usuario.
        
        Args:
            email: Email del usuario
            plain_password: Contraseña en texto plano
            first_name: Nombre del usuario
            last_name: Apellido del usuario
            
        Returns:
            User: Nueva instancia de Usuario
            
        Raises:
            ValueError: Si el email o la contraseña no son válidos
        """
        # Crear value objects
        email_vo = Email(email)
        password_vo = Password.from_plain_text(plain_password)
        full_name = FullName(first_name, last_name) if first_name and last_name else None
        
        # Crear la instancia de usuario
        user = cls(
            email=email_vo,
            _password=password_vo,
            full_name=full_name
        )
        
        # Agregar evento de dominio
        from ..events.user_events import UserRegisteredEvent
        user.add_domain_event(
            UserRegisteredEvent.from_user(user)
        )
        
        return user

    @property
    def password(self) -> str:
        """Obtiene la contraseña hasheada."""
        return self._password.hashed_password

    def activate(self) -> None:
        """Activa la cuenta del usuario."""
        if not self.is_active:
            self.is_active = True
            self.updated_at = datetime.utcnow()
            # Podríamos agregar un evento de dominio aquí si es necesario
            # self.add_domain_event(UserActivatedEvent(user_id=self.id))

    def deactivate(self) -> None:
        """Desactiva la cuenta del usuario."""
        if self.is_active:
            self.is_active = False
            self.updated_at = datetime.utcnow()
            # Podríamos agregar un evento de dominio aquí si es necesario
            # self.add_domain_event(UserDeactivatedEvent(user_id=self.id))

    def change_password(self, current_password: str, new_plain_password: str) -> None:
        """
        Cambia la contraseña del usuario.
        
        Args:
            current_password: Contraseña actual en texto plano
            new_plain_password: Nueva contraseña en texto plano
            
        Raises:
            ValueError: Si la contraseña actual es incorrecta
        """
        if not self._password.verify(current_password):
            raise ValueError("La contraseña actual es incorrecta")
            
        self._password = Password.from_plain_text(new_plain_password)
        self.updated_at = datetime.utcnow()

    def update_profile(self, first_name: str = None, last_name: str = None) -> None:
        """
        Actualiza la información del perfil del usuario.
        
        Args:
            first_name: Nuevo nombre
            last_name: Nuevo apellido
        """
        if first_name is not None or last_name is not None:
            current_first = self.full_name.first_name if self.full_name else ""
            current_last = self.full_name.last_name if self.full_name else ""
            
            new_first = first_name if first_name is not None else current_first
            new_last = last_name if last_name is not None else current_last
            
            self.full_name = FullName(new_first, new_last)
            self.updated_at = datetime.utcnow()
    
    def verify_password(self, plain_password: str) -> bool:
        """
        Verifica si la contraseña proporcionada coincide con la del usuario.
        
        Args:
            plain_password: Contraseña en texto plano a verificar
            
        Returns:
            bool: True si la contraseña es correcta, False en caso contrario
        """
        return self._password.verify(plain_password)
