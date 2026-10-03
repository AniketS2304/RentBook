from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_owner, get_db
from app.models.owner import Owner
from app.schemas.report import MonthlyReportResponse
from app.services.report import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get(
    "/monthly",
    response_model=MonthlyReportResponse,
    status_code=status.HTTP_200_OK,
)
def get_monthly_report(
    month: Optional[int] = Query(None, ge=1, le=12, description="Report month (1-12), defaults to current IST month"),
    year: Optional[int] = Query(None, ge=2020, le=2100, description="Report year, defaults to current IST year"),
    property_id: Optional[UUID] = Query(None, description="Optional property filter"),
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Generate read-only monthly collection report with financial totals, status counts, payment breakdown, and outstanding tenants."""
    return report_service.get_monthly_report(
        db=db,
        owner_id=current_owner.id,
        month=month,
        year=year,
        property_id=property_id,
    )
