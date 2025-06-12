"""
Módulo que contiene las definiciones de eventos de dominio.

Los eventos de dominio representan sucesos significativos en el dominio que
pueden desencadenar acciones en otras partes del sistema.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, Type, TypeVar, runtime_checkable
from uuid import UUID, uuid4

# Definir el protocolo para eventos de dominio
@runtime_checkable
class DomainEventProtocol(Protocol):
    """Protocolo que define la interfaz mínima de un evento de dominio."""
    event_id: UUID
    occurred_on: datetime
    event_type: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el evento a un diccionario."""
        ...

# Primero definimos DomainEvent sin dependencias circulares
@dataclass
class DomainEvent(DomainEventProtocol):
    """Clase base para todos los eventos de dominio."""
    event_id: UUID = field(default_factory=uuid4)
    occurred_on: datetime = field(default_factory=datetime.utcnow)
    event_type: str = ""
    
    def __post_init__(self):
        """Inicialización posterior a la creación."""
        if not self.event_type:
            self.event_type = f"{self.__class__.__module__}.{self.__class__.__name__}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el evento a un diccionario."""
        result = {
            'event_id': str(self.event_id),
            'occurred_on': self.occurred_on.isoformat() if self.occurred_on else None,
            'event_type': self.event_type or type(self).__name__,
        }
        # Agregar atributos específicos de la subclase
        result.update({
            k: str(v) if hasattr(v, '__str__') else v 
            for k, v in self.__dict__.items() 
            if not k.startswith('_') and k not in ('event_id', 'occurred_on', 'event_type')
        })
        return result

    def __str__(self) -> str:
        """Representación en cadena del evento."""
        return f"{self.__class__.__name__}({self.event_id})"

# Ahora importamos el manejador de eventos que ya no depende de DomainEvent
from .event_handler import EventHandler, EventBus, event_bus  # noqa: E402

# Tipo genérico para eventos
event_type = TypeVar('event_type', bound=DomainEvent)

# Importar eventos específicos después de definir DomainEvent
from .user_events import UserRegisteredEvent  # noqa: E402

__all__ = [
    'DomainEvent',
    'DomainEventProtocol',  # Asegurarse de exportar el protocolo
    'EventHandler',
    'EventBus',
    'event_bus',
    'UserRegisteredEvent',
    'event_type',
]
