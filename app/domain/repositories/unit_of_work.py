from abc import ABC, abstractmethod
from typing import Any

class UnitOfWork(ABC):
    """
    Interfaz para el patrón Unit of Work.
    Proporciona una forma de agrupar operaciones en una sola transacción.
    """
    
    def __enter__(self) -> 'UnitOfWork':
        return self
    
    def __exit__(self, *args: Any) -> None:
        self.rollback()
    
    @abstractmethod
    def commit(self) -> None:
        """Confirma todos los cambios realizados en la transacción actual."""
        pass
    
    @abstractmethod
    def rollback(self) -> None:
        """Descarta todos los cambios realizados en la transacción actual."""
        pass
    
    @property
    @abstractmethod
    def is_active(self) -> bool:
        """Indica si hay una transacción activa."""
        pass
    
    @abstractmethod
    def begin(self) -> None:
        """Inicia una nueva transacción."""
        pass
