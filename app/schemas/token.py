from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from pydantic.types import UUID4

from app.schemas.response import APIResponse

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

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "expires_at": "2025-06-04T15:30:00.000Z"
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
