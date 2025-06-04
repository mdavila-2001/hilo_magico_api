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
    description="Obtiene una lista de todas las tiendas disponibles en el sistema con paginación.",
    tags=["Tiendas"],
    responses={
        200: {"description": "Lista de tiendas obtenida exitosamente"},
        401: {"description": "No autorizado"},
        403: {"description": "No tiene permisos para realizar esta acción"}
    }
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
    summary="Obtener detalles de una tienda",
    description="Obtiene los detalles de una tienda específica por su ID.",
    tags=["Tiendas"],
    responses={
        200: {"description": "Detalles de la tienda obtenidos exitosamente"},
        401: {"description": "No autorizado"},
        403: {"description": "No tiene permisos para ver esta tienda"},
        404: {"description": "Tienda no encontrada"}
    }
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
    
    # Verificar permisos (solo administradores o usuarios con acceso a la tienda)
    user_store_service = UserStoreService(db)
    user_role = await user_store_service.get_user_role_in_store(store_id, current_user["id"])
    
    if not user_role and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver esta tienda"
        )
    
    return {"data": store}

@router.put(
    "/{store_id}",
    response_model=StoreResponse,
    summary="Actualizar una tienda",
    description="Actualiza la información de una tienda existente.",
    tags=["Tiendas"],
    responses={
        200: {"description": "Tienda actualizada exitosamente"},
        400: {"description": "Datos de entrada no válidos"},
        401: {"description": "No autorizado"},
        403: {"description": "No tiene permisos para actualizar esta tienda"},
        404: {"description": "Tienda no encontrada"}
    }
)
async def update_store(
    store_id: UUID,
    store_in: StoreUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Actualiza la información de una tienda existente.
    
    - **store_id**: ID de la tienda a actualizar
    - **store_in**: Datos a actualizar (todos los campos son opcionales)
    """
    store_service = StoreService(db)
    user_store_service = UserStoreService(db)
    
    try:
        # Verificar permisos (solo administradores o dueños/admin de la tienda pueden actualizar)
        user_role = await user_store_service.get_user_role_in_store(store_id, current_user["id"])
        
        if not user_role and current_user["role"] != "admin":
            raise ForbiddenException("No tiene permisos para actualizar esta tienda")
        
        # Si es staff, solo puede actualizar ciertos campos
        if user_role and user_role not in [UserRole.OWNER, UserRole.ADMIN] and current_user["role"] != "admin":
            # Solo permitir actualizar ciertos campos para managers/staff
            update_data = store_in.dict(exclude_unset=True)
            allowed_fields = ["description", "phone", "email"]
            if any(field not in allowed_fields for field in update_data.keys()):
                raise ForbiddenException("No tiene permisos para actualizar estos campos")
        
        updated_store = await store_service.update_store(store_id, store_in)
        if not updated_store:
            raise NotFoundException("Tienda no encontrada")
        
        return {"data": updated_store}
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar la tienda"
        )

@router.delete(
    "/{store_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una tienda",
    description="Elimina lógicamente una tienda del sistema.",
    tags=["Tiendas"],
    responses={
        204: {"description": "Tienda eliminada exitosamente"},
        401: {"description": "No autorizado"},
        403: {"description": "No tiene permisos para eliminar esta tienda"},
        404: {"description": "Tienda no encontrada"}
    }
)
async def delete_store(
    store_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Elimina lógicamente una tienda del sistema.
    
    - **store_id**: ID de la tienda a eliminar
    """
    store_service = StoreService(db)
    user_store_service = UserStoreService(db)
    
    # Verificar permisos (solo administradores o dueños pueden eliminar)
    user_role = await user_store_service.get_user_role_in_store(store_id, current_user["id"])
    if user_role != UserRole.OWNER and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el dueño o un administrador pueden eliminar esta tienda"
        )
    
    success = await store_service.delete_store(store_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tienda no encontrada"
        )
    
    return {"message": "Tienda eliminada exitosamente"}

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
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except BadRequestException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

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
        # Verificar que el usuario tiene acceso a la tienda
        current_user_role = await user_store_service.get_user_role_in_store(store_id, current_user["id"])
        if not current_user_role:
            raise ForbiddenException("No tienes acceso a esta tienda")
            
        users = await user_store_service.get_store_users(store_id)
        return {"data": users}
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
