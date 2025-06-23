from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from app.db.session import get_db
from app.schemas.store import (
    StoreCreate, StoreUpdate, StoreInDB, StoreResponse, StoreListResponse,
    UserStoreCreate, UserStoreUpdate, UserStoreInDB, UserStoreResponse, UserStoreListResponse
)
from app.services.store import StoreService
from app.services.user_store import UserStoreService
from app.core.security import get_current_user, get_current_admin_user, get_current_superuser
from app.core.permissions import store_permissions
from app.core.exceptions import (
    DatabaseError, NotFoundException, ForbiddenException, 
    BadRequestException, ConflictException
)
from app.models.user import User, UserRole

router = APIRouter()
logger = logging.getLogger(__name__)

# Dependencia para verificar si el usuario es propietario de la tienda
async def get_store_owner(store_id: UUID, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Dependencia que verifica si el usuario actual es propietario de la tienda.
    
    Args:
        store_id: ID de la tienda
        db: Sesión de base de datos
        current_user: Usuario actual autenticado
        
    Returns:
        dict: Datos del usuario si es propietario
        
    Raises:
        HTTPException: Si el usuario no es propietario de la tienda
    """
    user_store_service = UserStoreService(db)
    user_role = await user_store_service.get_user_role_in_store(store_id, current_user["id"])
    
    if user_role != UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el propietario de la tienda puede realizar esta acción"
        )
    
    return current_user

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
    description="""Obtiene una lista de todas las tiendas disponibles en el sistema con paginación. 
    Requiere rol de administrador o superusuario.""",
    tags=["Tiendas"],
    responses={
        200: {"description": "Lista de tiendas obtenida exitosamente"},
        401: {"description": "No autorizado - Se requiere autenticación"},
        403: {"description": "No tiene permisos para realizar esta acción"},
        500: {"description": "Error interno del servidor"}
    }
)
async def list_stores(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, le=100, description="Número máximo de registros a devolver"),
    name: Optional[str] = Query(None, description="Filtrar por nombre de tienda"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Obtiene una lista paginada de todas las tiendas.
    
    Solo disponible para administradores y superusuarios.
    
    - **skip**: Número de registros a omitir (paginación)
    - **limit**: Número máximo de registros a devolver (máx. 100)
    - **name**: Filtrar por nombre de tienda (opcional)
    - **is_active**: Filtrar por estado activo/inactivo (opcional)
    """
    try:
        store_service = StoreService(db)
        
        # Construir filtros
        filters = []
        if name:
            from sqlalchemy import or_
            filters.append(Store.name.ilike(f"%{name}%"))
        if is_active is not None:
            filters.append(Store.is_active == is_active)
            
        # Obtener tiendas con los filtros aplicados
        result = await store_service.get_stores(
            skip=skip, 
            limit=limit,
            filters=filters if filters else None,
            order_by="-created_at"  # Ordenar por fecha de creación por defecto
        )
        
        return {
            "data": result["data"], 
            "success": True, 
            "message": "Tiendas obtenidas exitosamente",
            "total": result["total"],
            "skip": result["skip"],
            "limit": result["limit"],
            "has_more": result["has_more"]
        }
        
    except Exception as e:
        logger.error(f"Error al listar tiendas: {str(e)}", exc_info=True)
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener la lista de tiendas"
        )

@router.get(
    "/{store_id}",
    response_model=StoreResponse,
    summary="Obtener detalles de una tienda",
    description="""Obtiene los detalles de una tienda específica por su ID.
    
    - Los administradores pueden ver cualquier tienda.
    - Los propietarios solo pueden ver sus propias tiendas.
    - Los vendedores solo pueden ver las tiendas donde trabajan.
    """,
    tags=["Tiendas"],
    responses={
        200: {"description": "Detalles de la tienda obtenidos exitosamente"},
        401: {"description": "No autorizado - Se requiere autenticación"},
        403: {"description": "No tiene permisos para ver esta tienda"},
        404: {"description": "Tienda no encontrada"},
        500: {"description": "Error interno del servidor"}
    }
)
async def get_store(
    store_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene los detalles de una tienda específica.
    
    - **store_id**: ID de la tienda a consultar (UUID)
    
    Nota: 
    - Los administradores pueden ver cualquier tienda.
    - Los propietarios solo pueden ver sus propias tiendas.
    - Los vendedores solo pueden ver las tiendas donde trabajan.
    """
    try:
        store_service = StoreService(db)
        store = await store_service.get_store(store_id)
        
        if not store:
            raise NotFoundException("Tienda no encontrada")
            
        # Verificar permisos
        user_role = current_user.get("role")
        
        # Si no es admin, verificar si tiene acceso a la tienda
        if user_role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
            user_store_service = UserStoreService(db)
            user_store = await user_store_service.get_user_store(store_id, current_user["id"])
            
            if not user_store:
                raise ForbiddenException("No tiene permisos para ver esta tienda")
        
        return {
            "data": store, 
            "success": True, 
            "message": "Tienda obtenida exitosamente"
        }
        
    except (NotFoundException, ForbiddenException) as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error al obtener tienda {store_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener los detalles de la tienda"
        )

@router.put(
    "/{store_id}",
    response_model=StoreResponse,
    summary="Actualizar una tienda",
    description="""Actualiza la información de una tienda existente.
    
    - Solo el propietario de la tienda puede actualizar toda la información.
    - Los administradores pueden actualizar cualquier tienda.
    - Los vendedores solo pueden actualizar ciertos campos.
    """,
    tags=["Tiendas"],
    responses={
        200: {"description": "Tienda actualizada exitosamente"},
        400: {"description": "Datos de entrada no válidos"},
        401: {"description": "No autorizado - Se requiere autenticación"},
        403: {"description": "No tiene permisos para actualizar esta tienda"},
        404: {"description": "Tienda no encontrada"},
        500: {"description": "Error interno del servidor"}
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
    
    Nota:
    - Solo el propietario puede actualizar toda la información.
    - Los administradores pueden actualizar cualquier tienda.
    - Los vendedores solo pueden actualizar ciertos campos.
    """
    try:
        store_service = StoreService(db)
        user_store_service = UserStoreService(db)
        
        # Verificar que la tienda existe
        store = await store_service.get_store(store_id)
        if not store:
            raise NotFoundException("Tienda no encontrada")
        
        # Verificar permisos
        user_role = current_user.get("role")
        user_store_role = await user_store_service.get_user_role_in_store(store_id, current_user["id"])
        
        # Si no es admin, verificar permisos específicos
        if user_role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
            if not user_store_role:
                raise ForbiddenException("No tiene permisos para actualizar esta tienda")
            
            # Si es vendedor, solo puede actualizar ciertos campos
            if user_store_role == UserRole.SELLER:
                update_data = store_in.dict(exclude_unset=True)
                allowed_fields = ["description", "phone", "email"]
                if any(field not in allowed_fields for field in update_data.keys()):
                    raise ForbiddenException("Solo puede actualizar la descripción, teléfono y correo")
        
        # Actualizar la tienda
        updated_store = await store_service.update_store(store_id, store_in)
        
        return {
            "data": updated_store, 
            "success": True, 
            "message": "Tienda actualizada exitosamente"
        }
        
    except (NotFoundException, ForbiddenException) as e:
        raise HTTPException(
            status_code=e.status_code if hasattr(e, 'status_code') else status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error al actualizar tienda {store_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar la tienda"
        )

@router.delete(
    "/{store_id}",
    status_code=status.HTTP_200_OK,
    summary="Eliminar una tienda",
    description="""Elimina lógicamente una tienda del sistema.
    
    - Solo el propietario de la tienda puede eliminarla.
    - Los administradores también pueden eliminar cualquier tienda.
    """,
    tags=["Tiendas"],
    responses={
        200: {"description": "Tienda eliminada exitosamente"},
        401: {"description": "No autorizado - Se requiere autenticación"},
        403: {"description": "No tiene permisos para eliminar esta tienda"},
        404: {"description": "Tienda no encontrada"},
        500: {"description": "Error interno del servidor"}
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
    
    Nota: Solo el propietario de la tienda o un administrador pueden eliminarla.
    """
    try:
        store_service = StoreService(db)
        
        # Verificar que la tienda existe
        store = await store_service.get_store(store_id)
        if not store:
            raise NotFoundException("Tienda no encontrada")
        
        # Verificar permisos
        user_role = current_user.get("role")
        
        # Solo el propietario o un administrador pueden eliminar la tienda
        if user_role not in [UserRole.ADMIN, UserRole.SUPERUSER]:
            user_store_service = UserStoreService(db)
            user_store_role = await user_store_service.get_user_role_in_store(store_id, current_user["id"])
            
            if user_store_role != UserRole.OWNER:
                raise ForbiddenException("Solo el propietario puede eliminar esta tienda")
        
        # Eliminar la tienda
        success = await store_service.delete_store(store_id)
        
        if not success:
            raise NotFoundException("No se pudo eliminar la tienda")
        
        return {
            "success": True,
            "message": "Tienda eliminada exitosamente"
        }
        
    except (NotFoundException, ForbiddenException) as e:
        raise HTTPException(
            status_code=e.status_code if hasattr(e, 'status_code') else status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error al eliminar tienda {store_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar la tienda"
        )

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
