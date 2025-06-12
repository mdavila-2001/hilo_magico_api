import re
from dataclasses import dataclass
from passlib.context import CryptContext

# Configuración de hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@dataclass(frozen=True)
class Password:
    """
    Value Object que representa una contraseña segura.
    Se encarga de la validación y el hashing de contraseñas.
    """
    _hashed_password: str
    
    def __post_init__(self):
        if not self._hashed_password:
            raise ValueError("La contraseña no puede estar vacía")
    
    @classmethod
    def from_plain_text(cls, plain_password: str) -> 'Password':
        """Crea una nueva contraseña a partir de texto plano."""
        if not plain_password:
            raise ValueError("La contraseña no puede estar vacía")
        if len(plain_password) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        if not any(char.isdigit() for char in plain_password):
            raise ValueError("La contraseña debe contener al menos un número")
        if not any(char.isupper() for char in plain_password):
            raise ValueError("La contraseña debe contener al menos una letra mayúscula")
        if not any(char.islower() for char in plain_password):
            raise ValueError("La contraseña debe contener al menos una letra minúscula")
            
        hashed = pwd_context.hash(plain_password)
        return cls(hashed)
    
    def verify(self, plain_password: str) -> bool:
        """Verifica si la contraseña en texto plano coincide con el hash."""
        return pwd_context.verify(plain_password, self._hashed_password)
    
    @property
    def hashed_password(self) -> str:
        """Devuelve la contraseña hasheada."""
        return self._hashed_password
    
    def __str__(self) -> str:
        return "[HIDDEN]"  # Por seguridad, no exponemos el hash
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Password):
            return False
        # Comparación segura de hashes
        return pwd_context.verify("dummy", self._hashed_password) == pwd_context.verify("dummy", other._hashed_password)
