from datetime import date, datetime
from typing import List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

RentStatus = Literal["PENDING", "DUE", "OVERDUE", "PAID", "PARTIALLY_PAID"]


class RentRecordUpdate(BaseModel):
    expected_amount_paise: Optional[int] = Field(None, gt=0, description="Updated expected rent amount in paise")
    notes: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class RentRecordVoidRequest(BaseModel):
    reason: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class RentRecordVoidResponse(BaseModel):
    message: str = "Rent record voided successfully"
    id: UUID
    is_void: bool = True


class RentRecordListItem(BaseModel):
    id: UUID
    tenant_name: str
    unit_name: str
    property_name: str
    expected_amount_paise: int
    total_paid_paise: int = 0
    due_date: date
    status: str
    last_reminder_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RentSummary(BaseModel):
    total_expected_paise: int
    total_collected_paise: int
    total_pending_paise: int
    paid_count: int
    due_count: int
    overdue_count: int


class RentListResponse(BaseModel):
    month: int
    year: int
    summary: RentSummary
    items: List[RentRecordListItem]


class RentRecordPaymentItem(BaseModel):
    id: UUID
    amount_paise: int
    payment_method: str
    paid_date: date
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RentRecordDetail(BaseModel):
    id: UUID
    tenant_id: UUID
    tenant_name: str
    unit_id: UUID
    unit_name: str
    property_id: UUID
    property_name: str
    month: int
    year: int
    expected_amount_paise: int
    total_paid_paise: int = 0
    due_date: date
    status: str
    notes: Optional[str] = None
    is_void: bool
    payments: List[RentRecordPaymentItem] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
