"""Manejadores de eventos para usuarios."""
import logging
from typing import Optional

from app.domain.events import EventHandler, event_bus
from app.domain.events.user_events import UserRegisteredEvent

logger = logging.getLogger(__name__)

class SendWelcomeEmailHandler(EventHandler[UserRegisteredEvent]):
    """Manejador que envía un correo de bienvenida al usuario registrado."""
    
    async def handle(self, event: UserRegisteredEvent) -> None:
        """Envía un correo de bienvenida al usuario."""
        # En una implementación real, aquí se integraría con un servicio de correo
        logger.info(
            "Enviando correo de bienvenida a %s (ID: %s)",
            event.email,
            event.user_id
        )
        
        # Ejemplo de implementación con un servicio de correo:
        # await email_service.send_welcome_email(
        #     to_email=event.email,
        #     user_name=event.full_name or "Usuario",
        # )


def register_user_event_handlers() -> None:
    """Registra los manejadores de eventos de usuario."""
    welcome_handler = SendWelcomeEmailHandler()
    event_bus.subscribe(UserRegisteredEvent, welcome_handler)
    
    logger.info("Manejadores de eventos de usuario registrados")
