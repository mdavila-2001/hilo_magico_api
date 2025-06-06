from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

# Importar esquemas
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.schemas.response import APIResponse

# Importar utilidades de base de datos
from app.db.session import get_db

# Importar servicios
from app.services.user_service import (
    get_user_by_email,
    get_user_by_id as get_db_user_by_id,
    create_user as create_user_service,  # Renombrar para evitar conflicto
    get_all_users as get_all_db_users,
    update_user as update_db_user,
    delete_user as delete_db_user,
    restore_user as restore_user_service  # Añadir la función de restauración
)

# Configurar logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Usuarios"])

# 🟢 Crear usuario
@router.post(
    "/", 
    response_model=APIResponse[UserOut],
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo usuario",
    description="Crea un nuevo usuario en el sistema con los datos proporcionados.",
    responses={
        201: {"description": "Usuario creado exitosamente"},
        400: {"description": "Datos de entrada no válidos o correo ya registrado"},
        500: {"description": "Error interno del servidor"}
    }
)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Crea un nuevo usuario en el sistema.
    
    Parámetros:
    - **email**: Correo electrónico del usuario (debe ser único)
    - **password**: Contraseña (mínimo 6 caracteres)
    - **first_name**: Nombre del usuario
    - **middle_name**: Segundo nombre (opcional)
    - **last_name**: Apellido paterno
    - **mother_last_name**: Apellido materno (opcional)
    - **role**: Rol del usuario (opcional, por defecto 'user')
    """
    try:
        # Crear el usuario (la verificación de correo ya se hace en create_user_service)
        db_user = await create_user_service(db, user)
        
        # Forzar la carga de la relación si es necesario
        await db.refresh(db_user)
        
        # Convertir el modelo SQLAlchemy a un diccionario
        user_dict = {
            'id': db_user.id,
            'email': db_user.email,
            'first_name': db_user.first_name,
            'middle_name': db_user.middle_name,
            'last_name': db_user.last_name,
            'mother_last_name': db_user.mother_last_name,
            'is_active': db_user.is_active,
            'role': db_user.role.value if hasattr(db_user.role, 'value') else str(db_user.role),
            'created_at': db_user.created_at.isoformat() if db_user.created_at else None,
            'updated_at': db_user.updated_at.isoformat() if db_user.updated_at else None
        }
        
        # Crear un objeto UserOut a partir del diccionario
        try:
            user_out = UserOut(**user_dict)
            
            # Crear respuesta exitosa
            return {
                "data": user_out.model_dump(),
                "message": "Usuario creado exitosamente",
                "success": True,
                "status_code": status.HTTP_201_CREATED
            }
            
        except Exception as e:
            logger.error(f"Error al serializar respuesta: {str(e)}")
            # Si hay error en la serialización, devolver solo datos básicos
            return {
                "data": {
                    "id": str(user_dict.get('id')),
                    "email": user_dict.get('email'),
                    "first_name": user_dict.get('first_name'),
                    "last_name": user_dict.get('last_name'),
                    "is_active": user_dict.get('is_active')
                },
                "message": "Usuario creado exitosamente (respuesta simplificada)",
                "success": True,
                "status_code": status.HTTP_201_CREATED
            }
        
    except HTTPException as http_exc:
        # Re-lanzar excepciones HTTP específicas
        logger.error(f"Error HTTP al crear usuario: {str(http_exc)}")
        raise http_exc
        
    except Exception as e:
        # Manejar otros errores inesperados
        logger.error(f"Error inesperado al crear usuario: {str(e)}")
        if "duplicate key value" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El correo electrónico ya está en uso"
            )
        elif "violates not-null constraint" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Faltan campos requeridos"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno del servidor al crear el usuario"
            )

# Obtener todos los usuarios
@router.get(
    "/",
    response_model=APIResponse[List[UserOut]],
    summary="Listar usuarios",
    description="Obtiene una lista de todos los usuarios registrados en el sistema."
)
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene una lista paginada de usuarios.
    
    - **skip**: Número de registros a saltar (para paginación)
    - **limit**: Número máximo de registros a devolver (máx. 100)
    """
    try:
        # Asegurarse de que el límite no sea mayor a 100
        if limit > 100:
            limit = 100
            
        # Obtener usuarios usando la función importada
        users = await get_all_db_users(db)
        
        # Aplicar paginación
        paginated_users = users[skip:skip + limit]
        
        # Convertir a modelos Pydantic
        users_out = [UserOut.from_orm(user) for user in paginated_users]
        
        return APIResponse[List[UserOut]](
            data=users_out,
            message="Usuarios obtenidos exitosamente"
        )
    except Exception as e:
        # Log the error for debugging
        import traceback
        error_details = f"Error al obtener usuarios: {str(e)}\n{traceback.format_exc()}"
        print(f"\n⚠️ ERROR en get_users: {error_details}\n")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener los usuarios"
        )

# Obtener usuario por ID
@router.get(
    "/{user_id}",
    response_model=APIResponse[UserOut],
    summary="Obtener usuario por ID",
    description="Obtiene la información detallada de un usuario específico por su ID.",
    responses={
        200: {"description": "Usuario encontrado exitosamente"},
        404: {"description": "Usuario no encontrado"},
        500: {"description": "Error interno del servidor"}
    }
)
async def read_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Obtiene la información de un usuario por su ID.
    
    - **user_id**: ID del usuario a consultar (UUID)
    """
    try:
        # Obtener el usuario por ID
        db_user = await get_db_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
            
        # Convertir a modelo Pydantic para la respuesta
        user_out = UserOut.from_orm(db_user)
        
        return APIResponse[UserOut](
            data=user_out,
            message="Usuario encontrado exitosamente"
        )
        
    except HTTPException:
        # Re-lanzar excepciones HTTP
        raise
        
    except Exception as e:
        # Log the error for debugging
        import traceback
        error_details = f"Error al obtener usuario {user_id}: {str(e)}\n{traceback.format_exc()}"
        print(f"\n⚠️ ERROR en read_user: {error_details}\n")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener el usuario"
        )

# Actualizar usuario
@router.put(
    "/{user_id}",
    response_model=APIResponse[UserOut],
    summary="Actualizar usuario",
    description="Actualiza la información de un usuario existente.",
    responses={
        200: {"description": "Usuario actualizado exitosamente"},
        400: {"description": "Datos de entrada inválidos"},
        404: {"description": "Usuario no encontrado"},
        500: {"description": "Error interno del servidor"}
    }
)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza un usuario existente.
    
    - **user_id**: ID del usuario a actualizar (UUID)
    - **user_update**: Datos a actualizar (todos los campos son opcionales)
    """
    try:
        # Verificar si el usuario existe
        db_user = await get_db_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Actualizar el usuario
        updated_user = await update_db_user(db, user_id, user_update)
        
        # Convertir a modelo Pydantic para la respuesta
        user_out = UserOut.from_orm(updated_user)
        
        return APIResponse[UserOut](
            data=user_out,
            message="Usuario actualizado exitosamente"
        )
        
    except HTTPException:
        # Re-lanzar excepciones HTTP
        raise
        
    except Exception as e:
        # Log the error for debugging
        import traceback
        error_details = f"Error al actualizar usuario {user_id}: {str(e)}\n{traceback.format_exc()}"
        print(f"\n⚠️ ERROR en update_user: {error_details}\n")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar el usuario"
        )

# Restaurar usuario eliminado
@router.post(
    "/restore/{email}",
    response_model=APIResponse[UserOut],
    status_code=status.HTTP_200_OK,
    summary="Restaurar usuario eliminado",
    description="Reactiva un usuario que fue eliminado lógicamente.",
    responses={
        200: {"description": "Usuario restaurado exitosamente"},
        400: {"description": "El usuario ya está activo"},
        404: {"description": "Usuario no encontrado"},
        500: {"description": "Error interno del servidor"}
    }
)
async def restore_user(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Reactiva un usuario que fue eliminado lógicamente.
    
    - **email**: Correo electrónico del usuario a restaurar
    """
    try:
        restored_user = await restore_user_service(db, email)
        
        # Convertir el usuario a un diccionario para la respuesta
        user_dict = {
            "id": str(restored_user.id),
            "email": restored_user.email,
            "first_name": restored_user.first_name,
            "last_name": restored_user.last_name,
            "is_active": restored_user.is_active,
            "created_at": restored_user.created_at.isoformat() if restored_user.created_at else None,
            "updated_at": restored_user.updated_at.isoformat() if restored_user.updated_at else None,
            "deleted_at": restored_user.deleted_at.isoformat() if restored_user.deleted_at else None
        }
        
        return APIResponse[UserOut](
            data=UserOut(**user_dict),
            message="Usuario restaurado exitosamente",
            status_code=status.HTTP_200_OK
        )
        
    except HTTPException as http_exc:
        # Re-lanzar excepciones HTTP
        raise http_exc
        
    except Exception as e:
        logger.error(f"Error al restaurar usuario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al restaurar el usuario"
        )

# Eliminar usuario (lógicamente)
@router.delete(
    "/{user_id}",
    response_model=APIResponse[Dict[str, Any]],
    summary="Eliminar usuario",
    description="Elimina un usuario del sistema (eliminación lógica).",
    responses={
        200: {"description": "Usuario desactivado exitosamente"},
        404: {"description": "Usuario no encontrado"},
        500: {"description": "Error interno del servidor"}
    }
)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Elimina un usuario (eliminación lógica).
    
    - **user_id**: ID del usuario a eliminar (UUID)
    """
    try:
        # Verificar si el usuario existe
        db_user = await get_db_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Eliminar (desactivar) el usuario
        result = await delete_db_user(db, user_id)
        
        return APIResponse[Dict[str, Any]](
            data={"user_id": user_id},
            message=result.get("message", "Usuario desactivado exitosamente")
        )
        
    except HTTPException:
        # Re-lanzar excepciones HTTP
        raise
        
    except Exception as e:
        # Log the error for debugging
        import traceback
        error_details = f"Error al eliminar usuario {user_id}: {str(e)}\n{traceback.format_exc()}"
        print(f"\n⚠️ ERROR en delete_user: {error_details}\n")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar el usuario"
        )