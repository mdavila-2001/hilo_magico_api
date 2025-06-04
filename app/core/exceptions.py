"""Custom exceptions for the application."""

class AppException(Exception):
    """Base exception for the application."""
    def __init__(self, message: str, status_code: int = 400, **kwargs):
        self.message = message
        self.status_code = status_code
        self.extra = kwargs
        super().__init__(message)

class NotFoundException(AppException):
    """Raised when a resource is not found."""
    def __init__(self, message: str = "Resource not found", **kwargs):
        super().__init__(message=message, status_code=404, **kwargs)

class ConflictException(AppException):
    """Raised when a resource conflict occurs."""
    def __init__(self, message: str = "Resource already exists", **kwargs):
        super().__init__(message=message, status_code=409, **kwargs)

class ForbiddenException(AppException):
    """Raised when a user doesn't have permission to access a resource."""
    def __init__(self, message: str = "Forbidden", **kwargs):
        super().__init__(message=message, status_code=403, **kwargs)

class UnauthorizedException(AppException):
    """Raised when authentication is required but not provided or invalid."""
    def __init__(self, message: str = "Unauthorized", **kwargs):
        super().__init__(message=message, status_code=401, **kwargs)

class BadRequestException(AppException):
    """Raised when the request is invalid."""
    def __init__(self, message: str = "Bad request", **kwargs):
        super().__init__(message=message, status_code=400, **kwargs)

class ValidationException(AppException):
    """Raised when data validation fails."""
    def __init__(self, message: str = "Validation error", **kwargs):
        super().__init__(message=message, status_code=422, **kwargs)
        
class DatabaseException(AppException):
    """Raised when a database error occurs."""
    def __init__(self, message: str = "Database error", **kwargs):
        super().__init__(message=message, status_code=500, **kwargs)

class ServiceException(AppException):
    """Raised when a service-level error occurs."""
    def __init__(self, message: str = "Service error", **kwargs):
        super().__init__(message=message, status_code=500, **kwargs)
