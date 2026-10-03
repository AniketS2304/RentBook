from datetime import date
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class DashboardDueItem(BaseModel):
    tenant_name: str
    unit_name: str
    property_name: str
    amount_paise: int
    rent_record_id: UUID
    tenant_id: Optional[UUID] = None
    tenant_phone: Optional[str] = None
    due_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class DashboardOverdueItem(BaseModel):
    tenant_name: str
    unit_name: str
    property_name: str
    amount_paise: int
    due_date: date
    rent_record_id: UUID
    tenant_id: Optional[UUID] = None
    tenant_phone: Optional[str] = None
    days_overdue: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class DashboardRecentPaymentItem(BaseModel):
    tenant_name: str
    amount_paise: int
    payment_method: str
    paid_date: date
    id: Optional[UUID] = None
    unit_name: Optional[str] = None
    property_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DashboardSummaryBreakdown(BaseModel):
    total_expected_paise: int
    total_collected_paise: int
    total_pending_paise: int
    paid_count: int
    due_count: int
    overdue_count: int

    model_config = ConfigDict(from_attributes=True)


class DashboardSummaryResponse(BaseModel):
    month: int
    year: int
    total_expected_paise: int
    total_collected_paise: int
    total_pending_paise: int
    paid_count: int
    due_count: int
    overdue_count: int
    total_units: int
    occupied_units: int
    vacant_units: int
    todays_due: List[DashboardDueItem]
    overdue_list: List[DashboardOverdueItem]
    recent_payments: List[DashboardRecentPaymentItem]
    summary: Optional[DashboardSummaryBreakdown] = None

    model_config = ConfigDict(from_attributes=True)
