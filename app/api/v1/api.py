from fastapi import APIRouter
from app.api.v1.endpoints import stores

api_router = APIRouter()

# Incluir los routers de los diferentes endpoints
api_router.include_router(stores.router, prefix="/stores", tags=["stores"])