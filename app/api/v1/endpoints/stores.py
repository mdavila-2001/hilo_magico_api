from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.schemas.store import Store, StoreCreate, StoreUpdate
from app.services.store import StoreService

router = APIRouter()

@router.post("/", response_model=Store, status_code=status.HTTP_201_CREATED)
async def create_store(
    store_data: StoreCreate,
    db: AsyncSession = Depends(deps.get_db)
) -> Store:
    """Crear una nueva tienda."""
    store_service = StoreService(db)
    return await store_service.create_store(store_data)

@router.get("/{store_id}", response_model=Store)
async def get_store(
    store_id: int,
    db: AsyncSession = Depends(deps.get_db)
) -> Store:
    """Obtener una tienda por su ID."""
    store_service = StoreService(db)
    store = await store_service.get_store(store_id)
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tienda no encontrada"
        )
    return store

@router.get("/", response_model=List[Store])
async def get_stores(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(deps.get_db)
) -> List[Store]:
    """Obtener lista de tiendas."""
    store_service = StoreService(db)
    return await store_service.get_stores(skip=skip, limit=limit)

@router.put("/{store_id}", response_model=Store)
async def update_store(
    store_id: int,
    store_data: StoreUpdate,
    db: AsyncSession = Depends(deps.get_db)
) -> Store:
    """Actualizar una tienda."""
    store_service = StoreService(db)
    store = await store_service.update_store(store_id, store_data)
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tienda no encontrada"
        )
    return store

@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_store(
    store_id: int,
    db: AsyncSession = Depends(deps.get_db)
) -> None:
    """Eliminar una tienda."""
    store_service = StoreService(db)
    deleted = await store_service.delete_store(store_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tienda no encontrada"
        )

@router.get("/active/list", response_model=List[Store])
async def get_active_stores(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(deps.get_db)
) -> List[Store]:
    """Obtener lista de tiendas activas."""
    store_service = StoreService(db)
    return await store_service.get_active_stores(skip=skip, limit=limit)