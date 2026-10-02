from datetime import datetime
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

UnitType = Literal["FLAT", "ROOM", "SHOP", "OTHER"]


class UnitCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    unit_type: UnitType
    monthly_rent_paise: int = Field(..., gt=0, description="Rent in paise (Rs 8,000 = 800000)")
    rent_due_day: int = Field(..., ge=1, le=28, description="Day of month rent is due (1-28)")
    notes: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class UnitUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    unit_type: Optional[UnitType] = None
    monthly_rent_paise: Optional[int] = Field(None, gt=0)
    rent_due_day: Optional[int] = Field(None, ge=1, le=28)
    notes: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class CurrentTenantBrief(BaseModel):
    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


class UnitOut(BaseModel):
    id: UUID
    property_id: UUID
    name: str
    unit_type: str
    monthly_rent_paise: int
    rent_due_day: int
    notes: Optional[str] = None
    archived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_occupied: bool = False
    current_tenant: Optional[CurrentTenantBrief] = None

    model_config = ConfigDict(from_attributes=True)


class UnitArchiveResponse(BaseModel):
    message: str = "Unit archived successfully"
    archived_at: datetime
