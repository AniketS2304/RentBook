from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.unit import UnitOut


class PropertyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = None
    notes: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class PropertyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    address: Optional[str] = None
    notes: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class PropertyListItem(BaseModel):
    id: UUID
    name: str
    address: Optional[str] = None
    notes: Optional[str] = None
    unit_count: int = 0
    occupied_count: int = 0
    vacant_count: int = 0
    archived_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PropertyListResponse(BaseModel):
    items: List[PropertyListItem]
    total: int
    page: int
    per_page: int


class PropertyDetail(BaseModel):
    id: UUID
    name: str
    address: Optional[str] = None
    notes: Optional[str] = None
    unit_count: int = 0
    occupied_count: int = 0
    vacant_count: int = 0
    archived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    units: List[UnitOut] = []

    model_config = ConfigDict(from_attributes=True)


class PropertyArchiveResponse(BaseModel):
    message: str = "Property archived successfully"
    archived_at: datetime
