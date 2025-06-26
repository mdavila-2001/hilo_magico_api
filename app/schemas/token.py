from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from pydantic.types import UUID4

from app.schemas.response import APIResponse

class UserInfo(BaseModel):
    """Modelo para la información básica del usuario en la respuesta de autenticación."""
    id: str = Field(..., description="ID único del usuario")
    email: str = Field(..., description="Correo electrónico del usuario")
    first_name: Optional[str] = Field(None, description="Nombre del usuario")
    middle_name: Optional[str] = Field(None, description="Segundo nombre del usuario")
    last_name: Optional[str] = Field(None, description="Apellido del usuario")
    mother_last_name: Optional[str] = Field(None, description="Apellido materno del usuario")
    role: str = Field(..., description="Rol del usuario (admin, seller, customer, etc.)")
    is_active: bool = Field(..., description="Indica si el usuario está activo")


class Token(BaseModel):
    """Modelo para la respuesta de autenticación con tokens JWT."""
    access_token: str = Field(..., description="Token de acceso JWT para autenticación")
    token_type: str = Field("bearer", description="Tipo de token, siempre 'bearer'")
    refresh_token: Optional[str] = Field(
        None, 
        description="Token de actualización para obtener un nuevo access_token sin volver a autenticarse"
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="Fecha y hora de expiración del token de acceso"
    )
    user: UserInfo = Field(..., description="Información básica del usuario autenticado")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "expires_at": "2025-06-04T15:30:00.000Z",
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "usuario@ejemplo.com",
                    "first_name": "Juan",
                    "middle_name": "Daniel",
                    "last_name": "Pérez",
                    "mother_last_name": "García",
                    "role": 1,
                    "is_active": True
                }
            }
        }


class TokenPayload(BaseModel):
    """Modelo para el payload del token JWT."""
    sub: Optional[UUID4] = Field(
        None, 
        description="Identificador único del usuario (subject)"
    )
    exp: Optional[datetime] = Field(
        None,
        description="Fecha y hora de expiración del token"
    )
    iat: Optional[datetime] = Field(
        None,
        description="Fecha y hora de emisión del token"
    )
    jti: Optional[str] = Field(
        None,
        description="Identificador único del token (JWT ID)"
    )
    
    @validator('sub', pre=True)
    def convert_uuid_to_str(cls, v):
        """Convierte el UUID a string si es necesario."""
        if v is not None and not isinstance(v, str):
            return str(v)
        return v


class TokenData(BaseModel):
    """Modelo para los datos del token decodificado."""
    user_id: Optional[UUID4] = Field(
        None,
        description="ID del usuario autenticado"
    )
    exp: Optional[datetime] = Field(
        None,
        description="Fecha y hora de expiración del token"
    )
    scopes: list[str] = Field(
        [],
        description="Lista de permisos (scopes) del token"
    )
    
    class Config:
        json_encoders = {
            UUID4: lambda v: str(v) if v else None
        }


class RefreshTokenRequest(BaseModel):
    """Modelo para la solicitud de actualización de token."""
    refresh_token: str = Field(
        ...,
        description="Token de actualización válido"
    )


class TokenResponse(APIResponse[Token]):
    """Modelo para la respuesta de autenticación que incluye tokens."""
    pass
