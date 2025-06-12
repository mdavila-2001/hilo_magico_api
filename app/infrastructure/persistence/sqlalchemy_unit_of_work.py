"""Implementación de Unit of Work para SQLAlchemy."""

from contextlib import contextmanager
from typing import Any, Optional, Type, TypeVar, Generic, Iterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ....domain.repositories.unit_of_work import UnitOfWork

T = TypeVar('T')  # Tipo genérico para el repositorio

class SQLAlchemyUnitOfWork(UnitOfWork):
    """
    Implementación de Unit of Work para SQLAlchemy.
    Maneja sesiones y transacciones de base de datos.
    """
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        """
        Inicializa el Unit of Work con una fábrica de sesiones.
        
        Args:
            session_factory: Fábrica de sesiones de SQLAlchemy
        """
        self.session_factory = session_factory
        self._session: Optional[AsyncSession] = None
    
    @property
    def session(self) -> AsyncSession:
        """Obtiene la sesión actual, creándola si es necesario."""
        if self._session is None:
            raise RuntimeError("La sesión no está inicializada. Use 'async with' o llame a 'begin()'.")
        return self._session
    
    @property
    def is_active(self) -> bool:
        """Indica si hay una transacción activa."""
        return self._session is not None and self._session.in_transaction()
    
    async def begin(self) -> None:
        """Inicia una nueva transacción."""
        if self._session is not None:
            raise RuntimeError("Ya existe una sesión activa")
        self._session = self.session_factory()
        # Iniciar la transacción
        await self._session.begin()
    
    async def commit(self) -> None:
        """Confirma la transacción actual."""
        if not self.is_active:
            raise RuntimeError("No hay una transacción activa para confirmar")
        
        try:
            await self.session.commit()
        except Exception:
            await self.rollback()
            raise
    
    async def rollback(self) -> None:
        """Deshace los cambios de la transacción actual."""
        if self._session is not None:
            await self._session.rollback()
            await self._session.close()
            self._session = None
    
    async def close(self) -> None:
        """Cierra la sesión actual sin confirmar cambios."""
        if self._session is not None:
            await self._session.close()
            self._session = None
    
    @contextmanager
    def repository(self, repo_class: Type[T]) -> Iterator[T]:
        """
        Context manager para obtener un repositorio con la sesión actual.
        
        Args:
            repo_class: Clase del repositorio a instanciar
            
        Yields:
            Repositorio configurado con la sesión actual
            
        Raises:
            RuntimeError: Si no hay una transacción activa
        """
        if not self.is_active:
            raise RuntimeError("No hay una transacción activa")
        
        # Pasar la sesión al repositorio
        repo = repo_class(self.session)
        
        try:
            yield repo
        except Exception as exc:
            # No hacemos rollback aquí, lo maneja el contexto externo
            raise exc
