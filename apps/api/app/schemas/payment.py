from datetime import date, datetime
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

PaymentMethod = Literal["CASH", "UPI", "BANK_TRANSFER", "OTHER"]


class PaymentCreate(BaseModel):
    amount_paise: int = Field(..., gt=0, description="Payment amount in paise (must be > 0)")
    payment_method: PaymentMethod
    paid_date: date
    notes: Optional[str] = None
    confirm_excess: bool = Field(default=False, description="Explicit confirmation if total payment exceeds 2x expected rent")

    model_config = ConfigDict(extra="forbid")


class PaymentUpdate(BaseModel):
    amount_paise: Optional[int] = Field(None, gt=0, description="Updated payment amount in paise")
    payment_method: Optional[PaymentMethod] = None
    paid_date: Optional[date] = None
    notes: Optional[str] = None
    confirm_excess: bool = Field(default=False, description="Explicit confirmation if total payment exceeds 2x expected rent")

    model_config = ConfigDict(extra="forbid")


class PaymentVoidRequest(BaseModel):
    reason: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class PaymentVoidResponse(BaseModel):
    message: str = "Payment voided successfully"
    id: UUID
    is_void: bool = True


class PaymentDetail(BaseModel):
    id: UUID
    rent_record_id: UUID
    amount_paise: int
    payment_method: str
    paid_date: date
    notes: Optional[str] = None
    is_void: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RentRecordBriefStatus(BaseModel):
    id: UUID
    expected_amount_paise: int
    total_paid_paise: int
    status: str

    model_config = ConfigDict(from_attributes=True)


class PaymentCreateResponse(BaseModel):
    payment: PaymentDetail
    rent_record: RentRecordBriefStatus
