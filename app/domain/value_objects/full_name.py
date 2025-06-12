from dataclasses import dataclass

@dataclass(frozen=True)
class FullName:
    """
    Value Object que representa un nombre completo de persona.
    Valida que el nombre sea válido y lo normaliza.
    """
    first_name: str
    last_name: str
    
    def __post_init__(self):
        self._validate_name(self.first_name, "nombre")
        self._validate_name(self.last_name, "apellido")
        
        # Normalizar nombres (primera letra mayúscula, resto minúsculas)
        object.__setattr__(self, 'first_name', self._normalize(self.first_name))
        object.__setattr__(self, 'last_name', self._normalize(self.last_name))
    
    def _validate_name(self, name: str, field_name: str) -> None:
        """Valida que el nombre o apellido sea válido."""
        if not name or not name.strip():
            raise ValueError(f"El {field_name} no puede estar vacío")
        if len(name.strip()) < 2:
            raise ValueError(f"El {field_name} debe tener al menos 2 caracteres")
        if not all(c.isalpha() or c.isspace() or c in "-'" for c in name):
            raise ValueError(f"El {field_name} contiene caracteres no permitidos")
    
    def _normalize(self, name: str) -> str:
        """Normaliza el formato del nombre o apellido."""
        # Divide el nombre en palabras, capitaliza cada una y las vuelve a unir
        return ' '.join(word.capitalize() for word in name.split())
    
    @property
    def full_name(self) -> str:
        """Devuelve el nombre completo formateado."""
        return f"{self.first_name} {self.last_name}"
    
    def __str__(self) -> str:
        return self.full_name
        
    def __eq__(self, other) -> bool:
        if not isinstance(other, FullName):
            return False
        return (self.first_name.lower(), self.last_name.lower()) == \
               (other.first_name.lower(), other.last_name.lower())
    
    def __hash__(self) -> int:
        return hash((self.first_name.lower(), self.last_name.lower()))
