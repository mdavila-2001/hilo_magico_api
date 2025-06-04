from fastapi import status
from fastapi.exceptions import HTTPException
from typing import Any, Dict, Optional

class BaseAPIException(HTTPException):
    """Base exception class for all API exceptions"""
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "An unexpected error occurred"
    
    def __init__(
        self,
        status_code: Optional[int] = None,
        detail: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.status_code = status_code or self.status_code
        self.detail = detail or self.detail
        self.headers = headers
        super().__init__(status_code=self.status_code, detail=self.detail, headers=self.headers)


# 4xx Client Errors
class BadRequestException(BaseAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Bad Request"

class UnauthorizedException(BaseAPIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Not authenticated"

class ForbiddenException(BaseAPIException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Permission denied"

class NotFoundException(BaseAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found"

class ConflictException(BaseAPIException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Conflict with existing resource"

class ValidationException(BaseAPIException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "Validation error"

# 5xx Server Errors
class InternalServerError(BaseAPIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Internal server error"

class ServiceUnavailableError(BaseAPIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    detail = "Service temporarily unavailable"

# Custom business logic exceptions
class InvalidCredentialsException(UnauthorizedException):
    detail = "Invalid authentication credentials"

class InactiveUserException(ForbiddenException):
    detail = "Inactive user"

class InvalidTokenException(UnauthorizedException):
    detail = "Invalid or expired token"

class RateLimitExceededException(ForbiddenException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    detail = "Rate limit exceeded"
