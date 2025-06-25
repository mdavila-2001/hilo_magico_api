import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order import OrderCreate, OrderUpdate, OrderStatus as OrderStatusEnum
from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ForbiddenException
)

logger = logging.getLogger(__name__)

class OrderService:
    """
    Servicio para gestionar las operaciones relacionadas con las órdenes.
    """
    
    @classmethod
    async def generate_order_number(cls, db: AsyncSession) -> str:
        """
        Genera un número de orden único basado en la fecha y un contador.
        Formato: ORD-YYYYMMDD-XXXXX
        """
        today = datetime.utcnow().strftime("%Y%m%d")
        
        # Obtener el último número de orden del día
        result = await db.execute(
            select(Order.order_number)
            .where(Order.order_number.like(f"ORD-{today}-%"))
            .order_by(Order.order_number.desc())
            .limit(1)
        )
        last_order = result.scalar_one_or_none()
        
        if last_order:
            # Extraer el contador y sumar 1
            counter = int(last_order.split('-')[-1]) + 1
        else:
            # Primera orden del día
            counter = 1
            
        return f"ORD-{today}-{counter:05d}"
    
    @classmethod
    async def create_order(
        cls, 
        db: AsyncSession, 
        order_data: OrderCreate,
        user_id: Optional[UUID] = None
    ) -> Order:
        """
        Crea una nueva orden en el sistema.
        
        Args:
            db: Sesión de base de datos asíncrona
            order_data: Datos de la orden a crear
            user_id: ID del usuario que realiza la orden (opcional)
            
        Returns:
            Order: La orden creada
            
        Raises:
            BadRequestException: Si hay un error en los datos de la orden
            Exception: Si hay un error al crear la orden
        """
        from app.services.product_service import ProductService
        
        async with db.begin():
            try:
                # Verificar que todos los productos existan y tengan stock suficiente
                product_ids = [str(item.product_id) for item in order_data.items]
                products = await ProductService.get_products_by_ids(db, product_ids)
                
                if len(products) != len(order_data.items):
                    raise BadRequestException("Uno o más productos no existen")
                
                # Verificar stock y calcular totales
                subtotal = 0.0
                order_items = []
                
                for item in order_data.items:
                    product = next((p for p in products if str(p.id) == str(item.product_id)), None)
                    if not product:
                        raise BadRequestException(f"Producto con ID {item.product_id} no encontrado")
                        
                    if product.stock < item.quantity:
                        raise BadRequestException(
                            f"Stock insuficiente para el producto {product.name}. "
                            f"Disponible: {product.stock}, Solicitado: {item.quantity}"
                        )
                    
                    # Calcular subtotal del ítem
                    item_subtotal = product.price * item.quantity
                    
                    order_items.append({
                        'product_id': product.id,
                        'quantity': item.quantity,
                        'unit_price': product.price,
                        'subtotal': item_subtotal
                    })
                    
                    subtotal += item_subtotal
                
                # Calcular totales (aquí se podrían agregar impuestos, descuentos, etc.)
                tax_rate = 0.18  # 18% de IGV (ejemplo)
                tax = subtotal * tax_rate
                shipping_cost = 0.0  # Aquí se podría implementar lógica de envío
                total = subtotal + tax + shipping_cost
                
                # Generar número de orden
                order_number = await cls.generate_order_number(db)
                
                # Crear la orden
                db_order = Order(
                    order_number=order_number,
                    customer_name=order_data.customer_name,
                    customer_email=order_data.customer_email,
                    customer_phone=order_data.customer_phone,
                    shipping_address=order_data.shipping_address,
                    subtotal=subtotal,
                    tax=tax,
                    shipping_cost=shipping_cost,
                    total=total,
                    status=OrderStatus.PENDING,
                    notes=order_data.notes,
                    is_paid=False,
                    store_id=order_data.store_id,
                    user_id=user_id,
                    is_active=True
                )
                
                db.add(db_order)
                await db.flush()  # Para obtener el ID de la orden
                
                # Crear los ítems de la orden
                for item in order_items:
                    db_item = OrderItem(
                        order_id=db_order.id,
                        product_id=item['product_id'],
                        quantity=item['quantity'],
                        unit_price=item['unit_price'],
                        subtotal=item['subtotal']
                    )
                    db.add(db_item)
                    
                    # Actualizar el stock del producto
                    await ProductService.update_stock(
                        db=db,
                        product_id=item['product_id'],
                        quantity=-item['quantity'],  # Restar del stock
                        commit_changes=False
                    )
                
                await db.commit()
                await db.refresh(db_order)
                return db_order
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error al crear orden: {str(e)}")
                raise
    
    @classmethod
    async def get_order_by_id(
        cls, 
        db: AsyncSession, 
        order_id: UUID,
        include_items: bool = True
    ) -> Optional[Order]:
        """
        Obtiene una orden por su ID.
        
        Args:
            db: Sesión de base de datos asíncrona
            order_id: ID de la orden a buscar
            include_items: Si es True, incluye los ítems de la orden
            
        Returns:
            Optional[Order]: La orden encontrada o None si no existe
        """
        try:
            query = select(Order).where(Order.id == order_id)
            
            if include_items:
                query = query.options(selectinload(Order.items))
            
            result = await db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error al obtener orden {order_id}: {str(e)}")
            raise
    
    @classmethod
    async def update_order_status(
        cls,
        db: AsyncSession,
        order_id: UUID,
        new_status: OrderStatus,
        user_id: Optional[UUID] = None
    ) -> Optional[Order]:
        """
        Actualiza el estado de una orden.
        
        Args:
            db: Sesión de base de datos asíncrona
            order_id: ID de la orden a actualizar
            new_status: Nuevo estado de la orden
            user_id: ID del usuario que realiza la actualización
            
        Returns:
            Optional[Order]: La orden actualizada o None si no se encontró
        """
        from app.services.product_service import ProductService
        
        async with db.begin():
            try:
                # Obtener la orden con sus ítems
                order = await cls.get_order_by_id(db, order_id, include_items=True)
                if not order:
                    raise NotFoundException(f"Orden con ID {order_id} no encontrada")
                
                # Validar transición de estado
                valid_transitions = {
                    OrderStatus.PENDING: [OrderStatus.PROCESSING, OrderStatus.CANCELLED],
                    OrderStatus.PROCESSING: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
                    OrderStatus.SHIPPED: [OrderStatus.DELIVERED],
                    OrderStatus.DELIVERED: [OrderStatus.REFUNDED],
                    OrderStatus.CANCELLED: [],
                    OrderStatus.REFUNDED: []
                }
                
                if new_status not in valid_transitions.get(order.status, []):
                    raise BadRequestException(
                        f"No se puede cambiar el estado de {order.status} a {new_status}"
                    )
                
                # Actualizar el estado
                order.status = new_status
                order.updated_at = datetime.utcnow()
                
                # Si se cancela una orden pendiente o en proceso, devolver el stock
                if new_status == OrderStatus.CANCELLED and order.status in [OrderStatus.PENDING, OrderStatus.PROCESSING]:
                    # Devolver el stock de cada producto
                    for item in order.items:
                        await ProductService.update_stock(
                            db=db,
                            product_id=item.product_id,
                            quantity=item.quantity,  # Sumar al stock
                            commit_changes=False
                        )
                
                await db.commit()
                await db.refresh(order)
                return order
                
            except Exception as e:
                await db.rollback()
                logger.error(f"Error al actualizar estado de orden: {str(e)}")
                raise
    
    @classmethod
    async def list_orders(
        cls,
        db: AsyncSession,
        user_id: Optional[UUID] = None,
        store_id: Optional[UUID] = None,
        status: Optional[OrderStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Order]:
        """
        Lista órdenes con filtros opcionales.
        
        Args:
            db: Sesión de base de datos asíncrona
            user_id: Filtrar por ID de usuario (opcional)
            store_id: Filtrar por ID de tienda (opcional)
            status: Filtrar por estado (opcional)
            skip: Número de registros a omitir (para paginación)
            limit: Número máximo de registros a devolver
            
        Returns:
            List[Order]: Lista de órdenes que coinciden con los filtros
        """
        try:
            query = select(Order)
            
            # Aplicar filtros
            conditions = []
            if user_id:
                conditions.append(Order.user_id == user_id)
            if store_id:
                conditions.append(Order.store_id == store_id)
            if status:
                conditions.append(Order.status == status)
                
            if conditions:
                query = query.where(and_(*conditions))
            
            # Ordenar por fecha de creación (más reciente primero)
            query = query.order_by(Order.created_at.desc())
            
            # Aplicar paginación
            query = query.offset(skip).limit(limit)
            
            # Cargar relaciones necesarias
            query = query.options(selectinload(Order.items))
            
            # Ejecutar consulta
            result = await db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error al listar órdenes: {str(e)}")
            raise