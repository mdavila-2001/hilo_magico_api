from typing import List, Optional, Dict, Any, Union
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from fastapi import UploadFile, HTTPException

from app.models.product import Product as ProductModel
from app.schemas.product import ProductCreate, ProductUpdate, ProductInDB
from app.services.file_service import file_service
from app.core.logging_config import logger

class ProductService:
    """Servicio para manejar operaciones relacionadas con productos"""
    
    @classmethod
    async def get_products(
        cls, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        store_id: Optional[UUID] = None,
        active_only: bool = True
    ) -> List[ProductInDB]:
        """
        Obtiene una lista de productos con paginación.
        
        Args:
            db: Sesión de base de datos asíncrona
            skip: Número de registros a omitir (para paginación)
            limit: Número máximo de registros a devolver
            store_id: Filtrar por ID de tienda (opcional)
            active_only: Si es True, solo devuelve productos activos
            
        Returns:
            Lista de productos
        """
        try:
            query = select(ProductModel)
            
            # Aplicar filtros
            if store_id:
                query = query.where(ProductModel.store_id == store_id)
                
            if active_only:
                query = query.where(ProductModel.is_active == True)
                
            # Aplicar paginación
            query = query.offset(skip).limit(limit)
            
            result = await db.execute(query)
            products = result.scalars().all()
            
            return [ProductInDB.from_orm(product) for product in products]
            
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener productos: {str(e)}")
            raise
    
    @classmethod
    async def get_product_by_id(
        cls, 
        db: AsyncSession, 
        product_id: UUID
    ) -> Optional[ProductInDB]:
        """
        Obtiene un producto por su ID.
        
        Args:
            db: Sesión de base de datos asíncrona
            product_id: ID del producto a buscar
            
        Returns:
            El producto si se encuentra, None en caso contrario
        """
        try:
            result = await db.execute(
                select(ProductModel).where(ProductModel.id == product_id)
            )
            product = result.scalar_one_or_none()
            
            if product:
                return ProductInDB.from_orm(product)
            return None
            
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener producto con ID {product_id}: {str(e)}")
            raise
    
    @classmethod
    async def upload_product_image(
        cls,
        file: UploadFile,
        product_id: UUID,
        db: AsyncSession
    ) -> str:
        """
        Sube una imagen para un producto existente.
        
        Args:
            file: Archivo de imagen a subir
            product_id: ID del producto al que se asociará la imagen
            db: Sesión de base de datos
            
        Returns:
            str: URL de la imagen subida
            
        Raises:
            HTTPException: Si el producto no existe o hay un error al subir la imagen
        """
        try:
            # Verificar que el producto exista
            product = await cls.get_product_by_id(db, product_id)
            if not product:
                raise HTTPException(
                    status_code=404,
                    detail=f"Producto con ID {product_id} no encontrado"
                )
            
            # Subir la imagen
            image_url = await file_service.save_upload_file(file, "products")
            
            # Actualizar el producto con la URL de la imagen
            update_data = {"image_url": image_url}
            await cls.update_product(
                db=db,
                product_id=product_id,
                product_data=ProductUpdate(**update_data),
                updated_by=UUID("00000000-0000-0000-0000-000000000000")  # Usar un UUID por defecto
            )
            
            return image_url
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error al subir imagen para producto {product_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error al subir la imagen: {str(e)}"
            )
    
    @classmethod
    async def create_product(
        cls, 
        db: AsyncSession, 
        product_data: ProductCreate
    ) -> ProductInDB:
        """
        Crea un nuevo producto.
        
        Args:
            db: Sesión de base de datos asíncrona
            product_data: Datos del producto a crear
            
        Returns:
            El producto creado
        """
        try:
            # Crear instancia del modelo
            db_product = ProductModel(**product_data.dict())
            
            # Agregar a la sesión
            db.add(db_product)
            await db.commit()
            await db.refresh(db_product)
            
            return ProductInDB.from_orm(db_product)
            
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Error de integridad al crear producto: {str(e)}")
            raise ValueError("Error de integridad: posiblemente el SKU ya existe") from e
            
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Error al crear producto: {str(e)}")
            raise
    
    @classmethod
    async def update_product(
        cls, 
        db: AsyncSession, 
        product_id: UUID,
        product_data: ProductUpdate,
        updated_by: UUID
    ) -> Optional[ProductInDB]:
        """
        Actualiza un producto existente.
        
        Args:
            db: Sesión de base de datos asíncrona
            product_id: ID del producto a actualizar
            product_data: Datos a actualizar
            updated_by: ID del usuario que realiza la actualización
            
        Returns:
            El producto actualizado si existe, None en caso contrario
        """
        try:
            # Preparar datos para la actualización
            update_data = product_data.dict(exclude_unset=True)
            update_data['updated_by'] = updated_by
            update_data['updated_at'] = datetime.utcnow()
            
            # Ejecutar actualización
            result = await db.execute(
                update(ProductModel)
                .where(ProductModel.id == product_id)
                .values(**update_data)
                .returning(ProductModel)
            )
            
            await db.commit()
            
            # Obtener el producto actualizado
            updated_product = result.scalar_one_or_none()
            
            if updated_product:
                await db.refresh(updated_product)
                return ProductInDB.from_orm(updated_product)
            return None
            
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Error al actualizar producto con ID {product_id}: {str(e)}")
            raise
    
    @classmethod
    async def delete_product(
        cls, 
        db: AsyncSession, 
        product_id: UUID,
        deleted_by: UUID
    ) -> bool:
        """
        Elimina un producto (eliminación lógica).
        
        Args:
            db: Sesión de base de datos asíncrona
            product_id: ID del producto a eliminar
            deleted_by: ID del usuario que realiza la eliminación
            
        Returns:
            True si se eliminó correctamente, False si el producto no existe
        """
        try:
            # Realizar eliminación lógica
            result = await db.execute(
                update(ProductModel)
                .where(
                    and_(
                        ProductModel.id == product_id,
                        ProductModel.deleted_at.is_(None)  # Solo si no está ya eliminado
                    )
                )
                .values(
                    deleted_at=datetime.utcnow(),
                    deleted_by=deleted_by,
                    is_active=False
                )
            )
            
            await db.commit()
            
            # Verificar si se actualizó alguna fila
            return result.rowcount > 0
            
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Error al eliminar producto con ID {product_id}: {str(e)}")
            raise
    
    @classmethod
    async def update_stock(
        cls,
        db: AsyncSession,
        product_id: UUID,
        quantity: int,
        action: str = 'add'  # 'add' o 'subtract'
    ) -> bool:
        """
        Actualiza el stock de un producto.
        
        Args:
            db: Sesión de base de datos asíncrona
            product_id: ID del producto
            quantity: Cantidad a agregar o restar
            action: 'add' para sumar, 'subtract' para restar
            
        Returns:
            True si la operación fue exitosa, False en caso contrario
        """
        if action not in ('add', 'subtract'):
            raise ValueError("La acción debe ser 'add' o 'subtract'")
            
        try:
            # Obtener el producto
            product = await cls.get_product_by_id(db, product_id)
            if not product:
                return False
                
            # Calcular nuevo stock
            new_stock = (
                product.stock + quantity 
                if action == 'add' 
                else product.stock - quantity
            )
            
            # Asegurar que el stock no sea negativo
            if new_stock < 0:
                raise ValueError("Stock insuficiente")
                
            # Actualizar stock
            await db.execute(
                update(ProductModel)
                .where(ProductModel.id == product_id)
                .values(stock=new_stock)
            )
            
            await db.commit()
            return True
            
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Error al actualizar stock del producto {product_id}: {str(e)}")
            raise