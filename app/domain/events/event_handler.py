"""Módulo para manejar eventos de dominio."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Type, TypeVar, Generic, Protocol
from uuid import UUID

# Usamos un Protocol para evitar la importación circular
class DomainEventProtocol(Protocol):
    """Protocolo que define la interfaz mínima de un evento de dominio."""
    event_id: UUID
    occurred_on: Any
    event_type: str

# Usamos TypeVar con el protocolo
T = TypeVar('T', bound=DomainEventProtocol)

class EventHandler(Protocol):
    """Interfaz base para los manejadores de eventos."""
    
    async def handle(self, event: Any) -> None:
        """Procesa un evento.
        
        Args:
            event: Evento a procesar
        """
        ...

class EventBus:
    """Bus de eventos para publicar y suscribirse a eventos de dominio."""
    
    def __init__(self):
        """Inicializa el bus de eventos."""
        self._handlers: Dict[Type[Any], List[EventHandler]] = {}
    
    def subscribe(self, event_type: Type[T], handler: EventHandler) -> None:
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
                await handler.handle(event)
    
    def unsubscribe(self, event_type: Type[T], handler: EventHandler) -> None:
        """Elimina la suscripción de un manejador a un tipo de evento.
        
        Args:
            event_type: Tipo de evento del que desuscribirse
            handler: Manejador a eliminar
        """
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

# Instancia global del bus de eventos
event_bus = EventBus()
