"""Manejadores de eventos para usuarios."""
import logging
from typing import Any, Awaitable, Callable, Type, TypeVar

from app.domain.events import EventHandler, event_bus, DomainEventProtocol
from app.domain.events.user_events import UserRegisteredEvent

logger = logging.getLogger(__name__)

# Tipo para funciones manejadoras de eventos
EventHandlerFunc = Callable[[Any], Awaitable[None]]

class SendWelcomeEmailHandler:
    """Manejador que envía un correo de bienvenida al usuario registrado."""
    
    async def handle(self, event: UserRegisteredEvent) -> None:
        """Envía un correo de bienvenida al usuario."""
        # En una implementación real, aquí se integraría con un servicio de correo
        logger.info(
            "Enviando correo de bienvenida a %s (ID: %s)",
            getattr(event, 'email', 'sin-email'),
            getattr(event, 'user_id', 'sin-id')
        )
        
        # Ejemplo de implementación con un servicio de correo:
        # try:
        #     await email_service.send_welcome_email(
        #         to_email=event.email,
        #         user_name=getattr(event, 'full_name', 'Usuario'),
        #     )
        # except Exception as e:
        #     logger.error("Error al enviar correo de bienvenida: %s", str(e))
        #     raise

# Creamos una instancia del manejador
welcome_handler = SendWelcomeEmailHandler()

def register_user_event_handlers() -> None:
    """Registra los manejadores de eventos de usuario."""
    # Registrar el manejador directamente
    event_bus.subscribe(UserRegisteredEvent, welcome_handler)
    
    logger.info("✅ Manejadores de eventos de usuario registrados")
