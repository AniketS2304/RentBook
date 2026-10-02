from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OwnerBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=15)


class OwnerOut(OwnerBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OwnerBrief(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str

    model_config = ConfigDict(from_attributes=True)
