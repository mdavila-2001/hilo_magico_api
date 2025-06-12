import re
from dataclasses import dataclass

@dataclass(frozen=True)
class Email:
    """
    Value Object que representa una dirección de correo electrónico.
    Garantiza que el email tenga un formato válido.
    """
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("El email no puede estar vacío")
            
        if not self._is_valid():
            raise ValueError("Formato de email inválido")
    
    def _is_valid(self) -> bool:
        """Valida el formato del email usando una expresión regular simple."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, self.value))
    
    def __str__(self) -> str:
        return self.value
        
    def __eq__(self, other) -> bool:
        if not isinstance(other, Email):
            return False
        return self.value.lower() == other.value.lower()
        
    def __hash__(self) -> int:
        return hash(self.value.lower())
