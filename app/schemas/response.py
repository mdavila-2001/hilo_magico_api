from typing import Any, Optional, List, Dict
from pydantic import BaseModel

class APIResponse(BaseModel):
    """Modelo base para estandarizar todas las respuestas de la API"""
    data: Optional[Any] = None
    success: bool = True
    debug_querys: Optional[List[Dict[str, Any]]] = None
    message: str = "Operación exitosa"