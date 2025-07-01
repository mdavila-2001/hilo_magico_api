from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
import logging

# Importación de esquemas
from app.schemas.product import Product, ProductCreate, ProductUpdate, ProductInDB
from app.schemas.response import APIResponse
from app.schemas.user import UserRole

# Importar utilidades de base de datos y autenticación
from app.db.session import get_db
from app.core.security import (
    get_current_active_user,
    get_current_admin_user,
    get_current_superuser,
    get_current_seller_user
)

# Importar modelos
from app.models.user import User

# Importar servicios
from app.services.product_service import ProductService
from app.services.file_service import file_service

# Configurar logging
logger = logging.getLogger(__name__)

router = APIRouter()

def check_store_owner_or_admin(
    current_user: User,
    store_id: Optional[UUID] = None,
    product_id: Optional[UUID] = None,
    db: AsyncSession = None
):
    """
    Verifica si el usuario es administrador o dueño de la tienda del producto.
    
    Args:
        current_user: Usuario autenticado
        store_id: ID de la tienda (opcional)
        product_id: ID del producto (opcional)
        db: Sesión de base de datos (opcional, solo necesario si se proporciona product_id)
        
    Returns:
        bool: True si el usuario tiene permiso
        
    Raises:
        HTTPException: Si el usuario no tiene permisos
    """
    # Superusuarios y administradores tienen acceso completo
    if current_user.role in [UserRole.ADMIN]:
        return True
        
    # Dueños pueden acceder a sus propias tiendas
    if current_user.role == UserRole.OWNER and store_id:
        # Verificar si el usuario es dueño de la tienda
        # Aquí necesitarías implementar la lógica para verificar la propiedad de la tienda
        # Por ahora, asumimos que el usuario tiene acceso
        return True
        
    # Vendedores pueden acceder a productos de sus tiendas
    if current_user.role == UserRole.SELLER and (store_id or product_id):
        # Verificar si el usuario es vendedor de la tienda
        # Implementar lógica de verificación de vendedor
        # Por ahora, asumimos que el usuario tiene acceso
        return True
        
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tiene permisos para realizar esta acción"
    )

# ==============================================
# ENDPOINTS PÚBLICOS
# ==============================================

@router.get("/", response_model=APIResponse[List[ProductInDB]])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    store_id: Optional[UUID] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene una lista paginada de productos.
    
    - **skip**: Número de registros a saltar (para paginación)
    - **limit**: Número máximo de registros a devolver (máx. 100)
    - **store_id**: Filtrar por ID de tienda (opcional)
    - **active_only**: Mostrar solo productos activos (por defecto: True)
    """
    try:
        products = await ProductService.get_products(
            db=db,
            skip=skip,
            limit=min(limit, 100),  # Limitar a 100 como máximo
            store_id=store_id,
            active_only=active_only
        )
        
        return APIResponse(
            success=True,
            message="Productos obtenidos exitosamente",
            data=products
        )
        
    except Exception as e:
        logger.error(f"Error al obtener productos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener productos"
        )

@router.get("/{product_id}", response_model=APIResponse[ProductInDB])
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene un producto por su ID.
    
    - **product_id**: ID del producto a consultar (UUID)
    """
    try:
        product = await ProductService.get_product_by_id(db, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
            
        # Verificar si el producto está activo o si el usuario tiene permisos para verlo
        if not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
            
        return APIResponse(
            success=True,
            message="Producto obtenido exitosamente",
            data=product
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener producto con ID {product_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener el producto"
        )

# ==============================================
# ENDPOINTS PROTEGIDOS
# ==============================================

@router.post("/", response_model=APIResponse[ProductInDB], status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Crea un nuevo producto.
    
    Requiere autenticación y permisos de vendedor, dueño o administrador.
    
    - **name**: Nombre del producto (obligatorio)
    - **description**: Descripción del producto (opcional)
    - **sku**: Código SKU único (opcional)
    - **price**: Precio del producto (mayor a 0)
    - **stock**: Cantidad en inventario (por defecto: 0)
    - **is_active**: Si el producto está activo (por defecto: True)
    - **store_id**: ID de la tienda a la que pertenece el producto (obligatorio)
    """
    try:
        # Verificar permisos
        check_store_owner_or_admin(current_user, store_id=product_data.store_id)
        
        # Crear el producto
        product = await ProductService.create_product(
            db=db,
            product_data=product_data
        )
        
        return APIResponse(
            success=True,
            message="Producto creado exitosamente",
            data=product,
            status_code=status.HTTP_201_CREATED
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error al crear producto: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear el producto"
        )

@router.put("/{product_id}", response_model=APIResponse[ProductInDB])
async def update_product(
    product_id: UUID,
    product_data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Actualiza un producto existente.
    
    Requiere autenticación y permisos de vendedor, dueño o administrador.
    
    - **product_id**: ID del producto a actualizar (UUID)
    - **product_data**: Datos a actualizar (todos los campos son opcionales)
    """
    try:
        # Obtener el producto existente
        existing_product = await ProductService.get_product_by_id(db, product_id)
        if not existing_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
            
        # Verificar permisos
        check_store_owner_or_admin(current_user, product_id=product_id, db=db)
        
        # Actualizar el producto
        updated_product = await ProductService.update_product(
            db=db,
            product_id=product_id,
            product_data=product_data,
            updated_by=current_user.id
        )
        
        if not updated_product:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar el producto"
            )
            
        return APIResponse(
            success=True,
            message="Producto actualizado exitosamente",
            data=updated_product
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error al actualizar producto con ID {product_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar el producto"
        )

@router.delete("/{product_id}", response_model=APIResponse[dict])
async def delete_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Elimina un producto (eliminación lógica).
    
    Requiere autenticación y permisos de vendedor, dueño o administrador.
    
    - **product_id**: ID del producto a eliminar (UUID)
    """
    try:
        # Verificar si el producto existe
        existing_product = await ProductService.get_product_by_id(db, product_id)
        if not existing_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
            
        # Verificar permisos
        check_store_owner_or_admin(current_user, product_id=product_id, db=db)
        
        # Eliminar el producto (eliminación lógica)
        success = await ProductService.delete_product(
            db=db,
            product_id=product_id,
            deleted_by=current_user.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al eliminar el producto"
            )
            
        return APIResponse(
            success=True,
            message="Producto eliminado exitosamente",
            data={"id": str(product_id)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar producto con ID {product_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar el producto"
        )

# ==============================================
# ENDPOINTS PARA GESTIÓN DE IMÁGENES
# ==============================================

@router.post("/test-upload/", status_code=200)
async def test_upload_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint de prueba para subir una imagen.
    
    - **file**: Archivo de imagen a subir (obligatorio)
    """
    try:
        # Guardar el archivo usando el servicio
        file_path = await file_service.save_upload_file(file, "test")
        
        return {
            "success": True,
            "message": "Archivo subido exitosamente",
            "file_path": file_path
        }
        
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(f"Error al subir archivo de prueba: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar el archivo: {str(e)}"
        )

@router.post(
    "/{product_id}/upload-image",
    response_model=APIResponse[str],
    status_code=status.HTTP_200_OK,
    summary="Subir imagen de producto",
    description="Sube una imagen para un producto existente"
)
async def upload_product_image(
    product_id: UUID,
    file: UploadFile = File(..., description="Archivo de imagen a subir"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Sube una imagen para un producto existente.
    
    Formatos soportados: PNG, JPG, JPEG, GIF, WEBP
    Tamaño máximo: 5MB
    
    - **file**: Archivo de imagen a subir (obligatorio)
    """
    try:
        # Verificar permisos
        product = await ProductService.get_product_by_id(db, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {product_id} no encontrado"
            )
            
        # Verificar que el usuario tenga permisos sobre la tienda del producto
        check_store_owner_or_admin(current_user, store_id=product.store_id)
        
        # Subir la imagen
        image_url = await ProductService.upload_product_image(
            file=file,
            product_id=product_id,
            db=db
        )
        
        return APIResponse(
            success=True,
            message="Imagen subida exitosamente",
            data=image_url,
            status_code=status.HTTP_200_OK
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al subir imagen para producto {product_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir la imagen: {str(e)}"
        )

# ==============================================
# ENDPOINTS PARA GESTIÓN DE INVENTARIO
# ==============================================

@router.post("/{product_id}/stock/add", response_model=APIResponse[ProductInDB])
async def add_stock(
    product_id: UUID,
    quantity: int = Query(..., gt=0, description="Cantidad a agregar al inventario"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Agrega stock a un producto existente.
    
    Requiere autenticación y permisos de vendedor, dueño o administrador.
    
    - **product_id**: ID del producto (UUID)
    - **quantity**: Cantidad a agregar (debe ser mayor a 0)
    """
    try:
        # Verificar si el producto existe
        existing_product = await ProductService.get_product_by_id(db, product_id)
        if not existing_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
            
        # Verificar permisos
        check_store_owner_or_admin(current_user, product_id=product_id, db=db)
        
        # Actualizar el stock
        success = await ProductService.update_stock(
            db=db,
            product_id=product_id,
            quantity=quantity,
            action='add'
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar el inventario"
            )
            
        # Obtener el producto actualizado
        updated_product = await ProductService.get_product_by_id(db, product_id)
        
        return APIResponse(
            success=True,
            message=f"Se agregaron {quantity} unidades al inventario",
            data=updated_product
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar inventario del producto {product_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar el inventario"
        )

@router.post("/{product_id}/stock/subtract", response_model=APIResponse[ProductInDB])
async def subtract_stock(
    product_id: UUID,
    quantity: int = Query(..., gt=0, description="Cantidad a restar del inventario"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Resta stock a un producto existente.
    
    Requiere autenticación y permisos de vendedor, dueño o administrador.
    
    - **product_id**: ID del producto (UUID)
    - **quantity**: Cantidad a restar (debe ser mayor a 0)
    """
    try:
        # Verificar si el producto existe
        existing_product = await ProductService.get_product_by_id(db, product_id)
        if not existing_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
            
        # Verificar permisos
        check_store_owner_or_admin(current_user, product_id=product_id, db=db)
        
        # Actualizar el stock
        success = await ProductService.update_stock(
            db=db,
            product_id=product_id,
            quantity=quantity,
            action='subtract'
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al actualizar el inventario"
            )
            
        # Obtener el producto actualizado
        updated_product = await ProductService.get_product_by_id(db, product_id)
        
        return APIResponse(
            success=True,
            message=f"Se restaron {quantity} unidades del inventario",
            data=updated_product
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar inventario del producto {product_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar el inventario"
        )