from typing import Any, Optional, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
    error: Optional[str] = None

def wrap_response(data: Any = None, message: str = "Operación exitosa", success: bool = True, error: Optional[str] = None) -> dict:
    return {
        "success": success,
        "message": message,
        "data": data,
        "error": error
    }