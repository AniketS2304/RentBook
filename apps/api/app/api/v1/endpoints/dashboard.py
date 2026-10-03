from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_owner, get_db
from app.models.owner import Owner
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse, status_code=status.HTTP_200_OK)
def get_dashboard_summary(
    month: Optional[int] = Query(None, ge=1, le=12, description="Target month (1-12), defaults to current IST month"),
    year: Optional[int] = Query(None, ge=2020, le=2100, description="Target year, defaults to current IST year"),
    property_id: Optional[UUID] = Query(None, description="Optional property ID filter"),
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Retrieve collection summary, unit counts, actionable due/overdue lists, and recent payments."""
    return dashboard_service.get_dashboard_summary(
        db=db,
        owner_id=current_owner.id,
        month=month,
        year=year,
        property_id=property_id,
    )
