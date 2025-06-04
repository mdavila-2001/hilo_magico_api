from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

# Definir el tipo genérico para la respuesta
T = TypeVar('T')

class APIResponse(GenericModel, Generic[T]):
    """
    Modelo base para estandarizar todas las respuestas de la API.
    
    Args:
        data (T, optional): Datos de la respuesta. Defaults to None.
        success (bool, optional): Indica si la operación fue exitosa. Defaults to True.
        message (str, optional): Mensaje descriptivo de la operación. Defaults to "Operación exitosa".
        debug_querys (List[Dict[str, Any]], optional): Información de depuración. Defaults to None.
        status_code (int, optional): Código de estado HTTP. Defaults to 200.
    """
    data: Optional[T] = None
    success: bool = True
    message: str = "Operación exitosa"
    debug_querys: Optional[List[Dict[str, Any]]] = None
    status_code: int = 200
    
    class Config:
        json_encoders = {
            # Agregar codificadores personalizados si es necesario
        }
        schema_extra = {
            "example": {
                "data": None,
                "success": True,
                "message": "Operación exitosa",
                "status_code": 200
            }
        }
    
    @classmethod
    def success(
        cls,
        data: Optional[Any] = None,
        message: str = "Operación exitosa",
        status_code: int = 200
    ) -> 'APIResponse':
        """
        Crea una respuesta de éxito.
        
        Args:
            data: Datos de la respuesta.
            message: Mensaje descriptivo.
            status_code: Código de estado HTTP.
            
        Returns:
            APIResponse: Instancia de la respuesta exitosa.
        """
        return cls(
            data=data,
            success=True,
            message=message,
            status_code=status_code
        )
    
    @classmethod
    def error(
        cls,
        message: str = "Error en la operación",
        status_code: int = 400,
        data: Optional[Any] = None,
        debug_info: Optional[Dict[str, Any]] = None
    ) -> 'APIResponse':
        """
        Crea una respuesta de error.
        
        Args:
            message: Mensaje de error descriptivo.
            status_code: Código de estado HTTP.
            data: Datos adicionales del error.
            debug_info: Información de depuración opcional.
            
        Returns:
            APIResponse: Instancia de la respuesta de error.
        """
        return cls(
            data=data,
            success=False,
            message=message,
            status_code=status_code,
            debug_querys=[debug_info] if debug_info else None
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la respuesta a un diccionario.
        
        Returns:
            Dict[str, Any]: Diccionario con los datos de la respuesta.
        """
        return self.dict(exclude_none=True)
    
    def to_json(self) -> str:
        """
        Convierte la respuesta a una cadena JSON.
        
        Returns:
            str: Representación JSON de la respuesta.
        """
        return self.json(exclude_none=True)