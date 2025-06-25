import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from app.core.config import settings

# Create a module-level logger instance
logger: logging.Logger = logging.getLogger(__name__)

def setup_logging() -> None:
    """Configura el sistema de logging para la aplicación.
    
    Configura el logging basado en el entorno (desarrollo/producción)
    y en la configuración de settings.
    """
    global logger
    
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    log_format = (
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        if settings.ENVIRONMENT == "development"
        else '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Clear any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Configuración básica
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Configuración específica para SQLAlchemy
    logging.getLogger('sqlalchemy.engine').setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )
    
    # Configuración para uvicorn
    logging.getLogger("uvicorn").handlers.clear()
    logging.getLogger("uvicorn").propagate = True
    logging.getLogger("uvicorn.access").handlers.clear()
    
    # Reconfigure the module logger
    logger = logging.getLogger(__name__)
    logger.info("Logging configurado correctamente")

# Inicializar logging al importar el módulo
setup_logging()
