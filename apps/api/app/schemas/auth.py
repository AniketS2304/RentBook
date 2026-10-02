from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.owner import OwnerBrief


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(
        None,
        pattern=r"^(\+91[\-\s]?)?[6789]\d{9}$",
        description="Valid 10-digit Indian phone number (optionally with +91 prefix)",
    )

    model_config = ConfigDict(extra="forbid")


class RegisterResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    model_config = ConfigDict(extra="forbid")


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: OwnerBrief


class RefreshRequest(BaseModel):
    refresh_token: str

    model_config = ConfigDict(extra="forbid")


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: int
    iat: int
    type: str = "access"
