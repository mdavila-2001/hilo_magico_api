from typing import List, Optional, Any, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_
from sqlalchemy.sql.expression import text
import logging

from app.models.store import Store
from app.schemas.store import StoreCreate, StoreUpdate, StoreInDB
from app.core.security import get_password_hash
from app.core.exceptions import NotFoundException, DatabaseError
from datetime import datetime

logger = logging.getLogger(__name__)

class StoreService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_store(self, store_in: StoreCreate, owner_id: UUID) -> StoreInDB:
        """
        Crea una nueva tienda.
        
        Args:
            store_in: Datos de la tienda a crear
            owner_id: ID del usuario que será el propietario
            
        Returns:
            StoreInDB con los datos de la tienda creada
            
        Raises:
            DatabaseError: Si ocurre un error al crear la tienda
        """
        try:
            # Crear la tienda
            db_store = Store(
                **store_in.dict(exclude_unset=True)
            )
            self.db.add(db_store)
            
            # TODO: Asignar el owner a la tienda en la tabla user_stores
            # Esto debería manejarse en una transacción separada
            
            await self.db.commit()
            await self.db.refresh(db_store)
            
            logger.info(f"Tienda creada exitosamente: {db_store.id}")
            return StoreInDB.from_orm(db_store)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error al crear tienda: {str(e)}")
            raise DatabaseError(f"No se pudo crear la tienda: {str(e)}")
    
    async def get_store(self, store_id: UUID) -> Optional[StoreInDB]:
        """
        Obtiene una tienda por su ID.
        
        Args:
            store_id: UUID de la tienda a buscar
            
        Returns:
            StoreInDB si se encuentra la tienda, None en caso contrario
            
        Raises:
            DatabaseError: Si ocurre un error al consultar la base de datos
        """
        try:
            result = await self.db.execute(
                select(Store).where(and_(
                    Store.id == store_id,
                    Store.deleted_at.is_(None)
                ))
            )
            db_store = result.scalars().first()
            
            if db_store is None:
                logger.info(f"Tienda no encontrada: {store_id}")
                return None
                
            return StoreInDB.from_orm(db_store)
            
        except Exception as e:
            logger.error(f"Error al obtener tienda {store_id}: {str(e)}")
            raise DatabaseError(f"Error al recuperar la tienda: {str(e)}")
    
    async def get_stores(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[List[Any]] = None,
        order_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene una lista de tiendas con paginación y filtrado opcional.
        
        Args:
            skip: Número de registros a omitir
            limit: Número máximo de registros a devolver
            filters: Lista de condiciones de filtrado SQLAlchemy
            order_by: Campo por el que ordenar (ej: 'name', '-created_at')
            
        Returns:
            Dict con las tiendas encontradas y metadatos de paginación
            
        Raises:
            DatabaseError: Si ocurre un error al consultar la base de datos
        """
        try:
            # Construir consulta base para conteo (sin paginación)
            count_query = select([func.count()]).select_from(Store).where(Store.deleted_at.is_(None))
            
            # Construir consulta principal
            query = select(Store).where(Store.deleted_at.is_(None))
            
            # Aplicar filtros si se proporcionan
            if filters:
                query = query.where(and_(*filters))
                count_query = count_query.where(and_(*filters))
            
            # Aplicar ordenamiento si se especifica
            if order_by:
                order_field = order_by[1:] if order_by.startswith('-') else order_by
                if hasattr(Store, order_field):
                    order_attr = getattr(Store, order_field)
                    if order_by.startswith('-'):
                        query = query.order_by(order_attr.desc())
                    else:
                        query = query.order_by(order_attr)
            
            # Aplicar paginación
            query = query.offset(skip).limit(limit)
            
            # Obtener el total de registros
            total_count = (await self.db.execute(count_query)).scalar()
            
            # Ejecutar consulta principal
            result = await self.db.execute(query)
            stores = result.scalars().all()
            
            # Convertir a Pydantic
            stores_data = [StoreInDB.from_orm(store) for store in stores]
            
            return {
                "data": stores_data,
                "total": total_count,
                "skip": skip,
                "limit": limit,
                "has_more": (skip + len(stores_data)) < total_count if total_count is not None else False
            }
            
        except Exception as e:
            logger.error(f"Error al obtener tiendas: {str(e)}", exc_info=True)
            raise DatabaseError(f"Error al recuperar tiendas: {str(e)}")
    
    async def update_store(
        self,
        store_id: UUID,
        store_in: StoreUpdate
    ) -> Optional[StoreInDB]:
        """
        Actualiza una tienda existente.
        
        Args:
            store_id: ID de la tienda a actualizar
            store_in: Datos a actualizar
            
        Returns:
            StoreInDB con los datos actualizados, o None si no se encontró la tienda
            
        Raises:
            DatabaseError: Si ocurre un error al actualizar
        """
        try:
            # Obtener la tienda existente
            result = await self.db.execute(
                select(Store).where(and_(
                    Store.id == store_id,
                    Store.deleted_at.is_(None)
                ))
            )
            db_store = result.scalars().first()
            
            if db_store is None:
                logger.warning(f"Intento de actualizar tienda no encontrada: {store_id}")
                return None
                
            # Actualizar campos
            update_data = store_in.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_store, field, value)
                
            db_store.updated_at = datetime.utcnow()
            
            self.db.add(db_store)
            await self.db.commit()
            await self.db.refresh(db_store)
            
            logger.info(f"Tienda actualizada exitosamente: {store_id}")
            return StoreInDB.from_orm(db_store)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error al actualizar tienda {store_id}: {str(e)}")
            raise DatabaseError(f"No se pudo actualizar la tienda: {str(e)}")
    
    async def delete_store(self, store_id: UUID) -> bool:
        """
        Elimina lógicamente una tienda.
        
        Args:
            store_id: ID de la tienda a eliminar
            
        Returns:
            bool: True si se eliminó correctamente, False si no se encontró la tienda
            
        Raises:
            DatabaseError: Si ocurre un error al eliminar
        """
        try:
            # Obtener la tienda existente
            result = await self.db.execute(
                select(Store).where(and_(
                    Store.id == store_id,
                    Store.deleted_at.is_(None)
                ))
            )
            db_store = result.scalars().first()
            
            if db_store is None:
                logger.warning(f"Intento de eliminar tienda no encontrada: {store_id}")
                return False
                
            # Marcar como eliminada lógicamente
            db_store.deleted_at = datetime.utcnow()
            db_store.is_active = False
            
            # TODO: Inhabilitar también a los usuarios asociados a esta tienda
            
            self.db.add(db_store)
            await self.db.commit()
            
            logger.info(f"Tienda eliminada exitosamente: {store_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error al eliminar tienda {store_id}: {str(e)}")
            raise DatabaseError(f"No se pudo eliminar la tienda: {str(e)}")
