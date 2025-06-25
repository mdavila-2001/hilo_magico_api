from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.order import Order, OrderStatus
from app.schemas.order import (
    OrderCreate, OrderUpdate, OrderResponse, 
    OrderListResponse, OrderStatus as OrderStatusEnum
)
from app.schemas.response import APIResponse
from app.services.order_service import OrderService
from app.core.security import get_current_active_user
from app.models.user import User

router = APIRouter()

@router.post(
    "/", 
    status_code=status.HTTP_201_CREATED,
    response_model=OrderResponse,
    summary="Crear una nueva orden",
    description="Crea una nueva orden en el sistema con los productos especificados."
)
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Crea una nueva orden en el sistema.
    
    - **customer_name**: Nombre del cliente
    - **customer_email**: Email del cliente
    - **customer_phone**: Teléfono del cliente (opcional)
    - **shipping_address**: Dirección de envío (debe incluir calle, ciudad, estado, código postal y país)
    - **notes**: Notas adicionales (opcional)
    - **store_id**: ID de la tienda
    - **items**: Lista de ítems de la orden (producto y cantidad)
    """
    try:
        order = await OrderService.create_order(
            db=db,
            order_data=order_data,
            user_id=current_user.id
        )
        
        # Obtener la orden con sus ítems para la respuesta
        order_with_items = await OrderService.get_order_by_id(db, order.id)
        return APIResponse(data=order_with_items)
        
    except Exception as e:
        if hasattr(e, 'status_code'):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la orden: {str(e)}"
        )

@router.get(
    "/{order_id}", 
    response_model=OrderResponse,
    summary="Obtener una orden por ID",
    description="Obtiene los detalles de una orden específica por su ID."
)
async def get_order(
    order_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene los detalles de una orden específica por su ID.
    """
    try:
        order = await OrderService.get_order_by_id(db, order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Orden con ID {order_id} no encontrada"
            )
            
        # Verificar que el usuario tenga permiso para ver esta orden
        if not current_user.is_superuser and order.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para ver esta orden"
            )
            
        return APIResponse(data=order)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la orden: {str(e)}"
        )

@router.get(
    "/", 
    response_model=OrderListResponse,
    summary="Listar órdenes",
    description="Lista las órdenes con filtros opcionales."
)
async def list_orders(
    status: Optional[OrderStatusEnum] = Query(None, description="Filtrar por estado"),
    store_id: Optional[UUID] = Query(None, description="Filtrar por ID de tienda"),
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros a devolver"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lista las órdenes con filtros opcionales.
    
    - **status**: Filtrar por estado (opcional)
    - **store_id**: Filtrar por ID de tienda (opcional, solo para administradores)
    - **skip**: Número de registros a omitir (para paginación)
    - **limit**: Número máximo de registros a devolver (máx. 100)
    """
    try:
        # Si no es administrador, solo puede ver sus propias órdenes
        user_id = current_user.id if not current_user.is_superuser else None
        
        # Solo los administradores pueden filtrar por tienda
        if store_id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los administradores pueden filtrar por tienda"
            )
            
        orders = await OrderService.list_orders(
            db=db,
            user_id=user_id,
            store_id=store_id,
            status=status,
            skip=skip,
            limit=limit
        )
        
        return APIResponse(data=orders)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar las órdenes: {str(e)}"
        )

@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Actualizar estado de una orden",
    description="Actualiza el estado de una orden existente."
)
async def update_order_status(
    order_id: UUID,
    status_update: OrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Actualiza el estado de una orden existente.
    
    - **status**: Nuevo estado de la orden
    - **notes**: Notas adicionales (opcional)
    - **is_paid**: Indica si la orden ha sido pagada (opcional)
    """
    try:
        # Verificar permisos (solo administradores o dueños de la orden)
        order = await OrderService.get_order_by_id(db, order_id, include_items=False)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Orden con ID {order_id} no encontrada"
            )
            
        if not current_user.is_superuser and order.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para actualizar esta orden"
            )
        
        # Actualizar el estado de la orden
        if status_update.status:
            order = await OrderService.update_order_status(
                db=db,
                order_id=order_id,
                new_status=status_update.status,
                user_id=current_user.id
            )
        
        # Actualizar otros campos si es necesario
        if status_update.notes is not None:
            order.notes = status_update.notes
        
        if status_update.is_paid is not None:
            order.is_paid = status_update.is_paid
            if status_update.is_paid and not order.paid_at:
                from datetime import datetime
                order.paid_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(order)
        
        # Obtener la orden actualizada con sus ítems
        updated_order = await OrderService.get_order_by_id(db, order_id)
        return APIResponse(data=updated_order)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar el estado de la orden: {str(e)}"
        )