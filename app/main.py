import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Importar configuración
from app.core.config import settings
from app.core.logging_config import setup_logging

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

# Importar manejadores de eventos
from app.infrastructure.event_handlers.user_handlers import register_user_event_handlers

# Importar routers
from app.interfaces.api.routers import auth as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Maneja el ciclo de vida de la aplicación."""
    # Inicio de la aplicación
    logger.info("🚀 Iniciando Hilo Mágico API...")
    logger.info(f"🏷️  Entorno: {settings.ENVIRONMENT}")
    logger.info(f"🐞 Modo debug: {'Activado' if settings.DEBUG else 'Desactivado'}")
    
    # Registrar manejadores de eventos
    register_user_event_handlers()
    logger.info("✅ Manejadores de eventos registrados")
    
    yield  # La aplicación está en ejecución
    
    # Cierre de la aplicación
    logger.info("🛑 Deteniendo Hilo Mágico API...")

def create_application() -> FastAPI:
    """Crea y configura la aplicación FastAPI."""
    # Crear aplicación FastAPI con lifespan personalizado
    app = FastAPI(
        title="Hilo Mágico API",
        description="API para la plataforma de comercio electrónico Hilo Mágico",
        version="1.0.0",
        docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/api/openapi.json" if settings.ENVIRONMENT != "production" else None,
        lifespan=lifespan,
    )

    # Configurar CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Manejar excepciones de validación
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(f"Error de validación: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(), "body": exc.body},
        )

    # Ruta raíz
    @app.get(
        "/",
        tags=["Root"],
        summary="Endpoint raíz",
        description="Proporciona información básica sobre la API y su estado",
        responses={
            200: {
                "description": "Información de la API",
                "content": {
                    "application/json": {
                        "example": {
                            "message": "✨ Bienvenido a Hilo Mágico API ✂️",
                            "version": "1.0.0",
                            "environment": "development",
                            "docs": "/api/docs"
                        }
                    }
                }
            }
        }
    )
    async def root():
        """Endpoint raíz que proporciona información sobre la API."""
        return {
            "message": "✨ Bienvenido a Hilo Mágico API ✂️",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "docs": "/api/docs" if settings.ENVIRONMENT != "production" else None,
        }

    # Incluir routers
    app.include_router(auth_router.router, prefix="/api/v1/auth")
    # Nota: Los routers de users y stores se incluirán cuando se implementen siguiendo la nueva arquitectura
    
    # Middleware para logging de peticiones
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Middleware para registrar información detallada de las peticiones HTTP."""
        # No registrar peticiones a la documentación en producción
        if settings.ENVIRONMENT == "production" and any(
            path in str(request.url) for path in ["/api/docs", "/api/redoc", "/api/openapi.json"]
        ):
            return await call_next(request)
            
        logger.info(f"🌐 Inicio de petición: {request.method} {request.url}")
        
        try:
            response = await call_next(request)
            logger.info(
                f"✅ {request.method} {request.url} - {response.status_code}"
            )
            return response
            
        except Exception as e:
            logger.exception(
                f"❌ Error en petición: {request.method} {request.url} - {str(e)}"
            )
            raise

    return app

# Crear la aplicación
app = create_application()
