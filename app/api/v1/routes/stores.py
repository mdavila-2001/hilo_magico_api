from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_db
from app.schemas.store import (
    StoreCreate, StoreUpdate, StoreInDB, StoreResponse, StoreListResponse,
    UserStoreCreate, UserStoreUpdate, UserStoreInDB, UserStoreResponse, UserStoreListResponse
)
from app.services.store import StoreService
from app.services.user_store import UserStoreService
from app.core.security import get_current_user

router = APIRouter()

# Endpoints para Tiendas (Stores)

@router.post(
    "/",
    response_model=StoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva tienda",
    description="Crea una nueva tienda con la información proporcionada.",
    tags=["Tiendas"]
)
async def create_store(
    store_in: StoreCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Crea una nueva tienda en el sistema.
    
    - **name**: Nombre de la tienda (requerido)
    - **description**: Descripción opcional
    - **address**: Dirección física de la tienda (requerido)
    - **phone**: Teléfono de contacto (requerido)
    - **email**: Correo electrónico de contacto (opcional)
    - **is_active**: Estado de activación (por defecto: True)
    """
    store_service = StoreService(db)
    store = await store_service.create_store(store_in, current_user["id"])
    return {"data": store}

@router.get(
    "/",
    response_model=StoreListResponse,
    summary="Listar todas las tiendas",
    description="Obtiene una lista de todas las tiendas disponibles en el sistema.",
    tags=["Tiendas"]
)
async def list_stores(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene una lista paginada de todas las tiendas.
    
    - **skip**: Número de registros a omitir (paginación)
    - **limit**: Número máximo de registros a devolver (paginación)
    """
    store_service = StoreService(db)
    stores = await store_service.get_stores(skip=skip, limit=limit)
    return {"data": stores}

@router.get(
    "/{store_id}",
    response_model=StoreResponse,
    summary="Obtener una tienda por ID",
    description="Obtiene los detalles de una tienda específica por su ID.",
    tags=["Tiendas"]
)
async def get_store(
    store_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene los detalles de una tienda específica.
    
    - **store_id**: ID de la tienda a consultar
    """
    store_service = StoreService(db)
    store = await store_service.get_store(store_id)
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tienda no encontrada"
        )
    return {"data": store}

# Endpoints para la relación Usuario-Tienda (UserStore)

@router.post(
    "/{store_id}/users/",
    response_model=UserStoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar usuario a una tienda",
    description="Agrega un usuario a una tienda con un rol específico.",
    tags=["Usuarios en Tiendas"]
)
async def add_user_to_store(
    store_id: UUID,
    user_store_in: UserStoreCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Agrega un usuario a una tienda con un rol específico.
    
    - **user_id**: ID del usuario a agregar (requerido)
    - **role**: Rol del usuario en la tienda (requerido)
    - **is_active**: Estado de activación (por defecto: True)
    """
    user_store_service = UserStoreService(db)
    try:
        user_store = await user_store_service.add_user_to_store(
            store_id=store_id,
            user_store_in=user_store_in,
            current_user_id=current_user["id"]
        )
        return {"data": user_store}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.get(
    "/{store_id}/users/",
    response_model=UserStoreListResponse,
    summary="Listar usuarios de una tienda",
    description="Obtiene la lista de usuarios asociados a una tienda específica.",
    tags=["Usuarios en Tiendas"]
)
async def list_store_users(
    store_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene la lista de usuarios asociados a una tienda específica.
    
    - **store_id**: ID de la tienda
    """
    user_store_service = UserStoreService(db)
    try:
        users = await user_store_service.get_store_users(store_id)
        return {"data": users}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
