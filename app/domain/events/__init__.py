"""
Módulo que contiene las definiciones de eventos de dominio.

Los eventos de dominio representan sucesos significativos en el dominio que
pueden desencadenar acciones en otras partes del sistema.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from uuid import UUID

# Importar el bus de eventos desde el manejador de eventos
from .event_handler import EventHandler, EventBus, event_bus

# Tipo genérico para eventos
event_type = TypeVar('event_type', bound='DomainEvent')

@dataclass
class DomainEvent:
    """Clase base para todos los eventos de dominio."""
    event_id: UUID
    occurred_on: datetime
    event_type: str = ""
    
    def __init_subclass__(cls, **kwargs):
        """Registra el tipo de evento al crear una subclase."""
        super().__init_subclass__(**kwargs)
        cls.event_type = f"{cls.__module__}.{cls.__name__}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el evento a un diccionario."""
        result = {
            'event_id': str(self.event_id),
            'occurred_on': self.occurred_on.isoformat(),
            'event_type': self.event_type or type(self).__name__,
        }
        # Agregar atributos específicos de la subclase
        result.update({
            k: str(v) if hasattr(v, '__str__') else v 
            for k, v in self.__dict__.items() 
            if not k.startswith('_')
        })
        return result

# Importar eventos específicos después de definir DomainEvent
from .user_events import UserRegisteredEvent  # noqa: E402

__all__ = [
    'DomainEvent',
    'EventHandler',
    'EventBus',
    'event_bus',
    'UserRegisteredEvent',
]
