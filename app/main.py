import logging
from fastapi import FastAPI, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# Importar configuración
from app.core.config import settings
from app.core.logging_config import setup_logging

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

# Importar routers
from app.api.v1.routes import users, stores, auth, products

def create_application() -> FastAPI:
    # Crear aplicación FastAPI
    app = FastAPI(
        title="Hilo Mágico API",
        description="API para la plataforma de comercio electrónico Hilo Mágico",
        version="1.0.0",
        docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
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
        
        # Convertir el cuerpo a string si es bytes
        body = exc.body
        if isinstance(body, bytes):
            try:
                body = body.decode('utf-8')
            except UnicodeDecodeError:
                body = str(body)
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(), "body": body},
        )

    # Ruta raíz
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "message": "✨ Bienvenido a Hilo Mágico API ✂️",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "docs": "/api/docs" if settings.ENVIRONMENT != "production" else None,
        }

    # Importar dependencias de autenticación
    from app.core.security import get_current_active_user, check_user_permissions
    from app.models.user import UserRole

    # Incluir routers
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticación"])
    
    # Rutas protegidas que requieren autenticación
    app.include_router(
        users.router,
        prefix="/api/v1/users",
        tags=["Usuarios"],
        dependencies=[Depends(get_current_active_user)]
    )
    
    app.include_router(
        stores.router,
        prefix="/api/v1/stores",
        tags=["Tiendas"],
        dependencies=[Depends(get_current_active_user)]
    )
    
    app.include_router(
        products.router,
        prefix="/api/v1/products",
        tags=["Productos"],
        dependencies=[Depends(get_current_active_user)]
    )
    
    # Middleware para logging de peticiones
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info(f"Inicio de petición: {request.method} {request.url}")
        try:
            response = await call_next(request)
            logger.info(f"Fin de petición: {request.method} {request.url} - {response.status_code}")
            return response
        except Exception as e:
            logger.exception(f"Error en petición: {request.method} {request.url}")
            raise

    return app

# Crear la aplicación
app = create_application()

# Eventos de inicio/cierre
@app.on_event("startup")
async def startup_event():
    logger.info("Iniciando Hilo Mágico API...")
    logger.info(f"Entorno: {settings.ENVIRONMENT}")
    logger.info(f"Debug: {settings.DEBUG}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Deteniendo Hilo Mágico API...")
