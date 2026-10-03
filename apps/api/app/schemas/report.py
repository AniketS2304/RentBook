from datetime import date
from typing import List
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class MonthlyReportSummary(BaseModel):
    total_expected_paise: int
    total_collected_paise: int
    total_pending_paise: int
    paid_count: int
    partially_paid_count: int
    due_count: int
    overdue_count: int

    model_config = ConfigDict(from_attributes=True)


class MonthlyReportPaymentBreakdown(BaseModel):
    cash_paise: int = 0
    upi_paise: int = 0
    bank_transfer_paise: int = 0
    other_paise: int = 0

    model_config = ConfigDict(from_attributes=True)


class OutstandingTenantItem(BaseModel):
    tenant_id: UUID
    tenant_name: str
    property_id: UUID
    property_name: str
    unit_id: UUID
    unit_name: str
    rent_record_id: UUID
    expected_amount_paise: int
    paid_amount_paise: int
    remaining_amount_paise: int
    status: str
    due_date: date
    days_overdue: int

    model_config = ConfigDict(from_attributes=True)


class OutstandingSummary(BaseModel):
    total_count: int
    total_amount_paise: int
    tenants: List[OutstandingTenantItem]

    model_config = ConfigDict(from_attributes=True)


class MonthlyReportResponse(BaseModel):
    month: int
    year: int
    summary: MonthlyReportSummary
    payment_breakdown: MonthlyReportPaymentBreakdown
    outstanding: OutstandingSummary

    model_config = ConfigDict(from_attributes=True)
