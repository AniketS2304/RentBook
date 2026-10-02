from datetime import date, datetime
from typing import Any, List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field

TenantStatus = Literal["ACTIVE", "INACTIVE"]


class TenantUnitBrief(BaseModel):
    id: UUID
    name: str
    property_name: str

    model_config = ConfigDict(from_attributes=True)


class TenantCreate(BaseModel):
    unit_id: UUID
    name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(
        ...,
        pattern=r"^(\+91[\-\s]?)?[6789]\d{9}$",
        description="Valid 10-digit Indian phone number (optionally with +91 prefix)",
    )
    email: Optional[EmailStr] = None
    move_in_date: date
    security_deposit_paise: int = Field(default=0, ge=0, description="Security deposit in paise (integer)")
    notes: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class TenantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(
        None,
        pattern=r"^(\+91[\-\s]?)?[6789]\d{9}$",
        description="Valid 10-digit Indian phone number (optionally with +91 prefix)",
    )
    email: Optional[EmailStr] = None
    move_in_date: Optional[date] = None
    security_deposit_paise: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class TenantDeactivateRequest(BaseModel):
    move_out_date: Optional[date] = None

    model_config = ConfigDict(extra="forbid")


class TenantDeactivateResponse(BaseModel):
    message: str
    tenant_status: str
    unit_status: str


class TenantListItem(BaseModel):
    id: UUID
    name: str
    phone: str
    email: Optional[str] = None
    unit: TenantUnitBrief
    move_in_date: date
    status: str
    current_month_rent_status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TenantListResponse(BaseModel):
    items: List[TenantListItem]
    total: int
    page: int
    per_page: int


class TenantRentHistoryItem(BaseModel):
    id: UUID
    month: int
    year: int
    expected_amount_paise: int
    total_paid_paise: int = 0
    due_date: date
    status: str
    payments: List[Any] = []

    model_config = ConfigDict(from_attributes=True)


class TenantDetail(BaseModel):
    id: UUID
    name: str
    phone: str
    email: Optional[str] = None
    unit: TenantUnitBrief
    move_in_date: date
    move_out_date: Optional[date] = None
    security_deposit_paise: int
    status: str
    notes: Optional[str] = None
    rent_history: List[TenantRentHistoryItem] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
