"""Módulo para manejar eventos de dominio."""
from __future__ import annotations
from typing import Any, Dict, Generic, List, Protocol, Type, TypeVar
from uuid import UUID

from . import DomainEventProtocol  # Importamos el protocolo desde __init__.py

# Usamos TypeVar con el protocolo
T = TypeVar('T', bound=DomainEventProtocol)

class EventHandler(Protocol, Generic[T]):
    """Interfaz base para los manejadores de eventos."""
    
    async def handle(self, event: T) -> None:
        """Procesa un evento.
        
        Args:
            event: Evento a procesar
        """
        ...

class EventBus:
    """Bus de eventos para publicar y suscribirse a eventos de dominio."""
    
    def __init__(self):
        """Inicializa el bus de eventos."""
        self._handlers: Dict[Type[Any], List[EventHandler[Any]]] = {}
    
    def subscribe(self, event_type: Type[T], handler: EventHandler[T]) -> None:
        """Suscribe un manejador a un tipo de evento.
        
        Args:
            event_type: Tipo de evento al que suscribirse
            handler: Manejador que procesará el evento
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    async def publish(self, event: DomainEventProtocol) -> None:
        """Publica un evento para que sea procesado por sus manejadores.
        
        Args:
            event: Evento a publicar
        """
        event_type = type(event)
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                # Verificar que el manejador puede manejar este tipo de evento
                if isinstance(handler, EventHandler) and hasattr(handler, 'handle'):
                    await handler.handle(event)
    
    def unsubscribe(self, event_type: Type[T], handler: EventHandler[T]) -> None:
        """Elimina la suscripción de un manejador a un tipo de evento.
        
        Args:
            event_type: Tipo de evento del que desuscribirse
            handler: Manejador a eliminar
        """
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

# Instancia global del bus de eventos
event_bus = EventBus()
