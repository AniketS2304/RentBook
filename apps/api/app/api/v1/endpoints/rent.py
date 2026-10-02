from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_owner, get_db
from app.models.owner import Owner
from app.schemas.rent import (
    RentListResponse,
    RentRecordDetail,
    RentRecordUpdate,
    RentRecordVoidRequest,
    RentRecordVoidResponse,
)
from app.services.rent import rent_service

router = APIRouter(prefix="/rent", tags=["Rent"])


@router.get("", response_model=RentListResponse, status_code=status.HTTP_200_OK)
def get_monthly_rent(
    month: Optional[int] = Query(None, ge=1, le=12, description="Calendar month (1-12)"),
    year: Optional[int] = Query(None, ge=2020, le=2100, description="Calendar year"),
    property_id: Optional[UUID] = Query(None, description="Filter by property ID"),
    status: Optional[str] = Query(None, description="Filter by status (PENDING, DUE, OVERDUE, PAID, PARTIALLY_PAID)"),
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Get rent records and collection summary for a specific month. Triggers on-demand generation."""
    return rent_service.list_monthly_rent(
        db=db,
        owner_id=current_owner.id,
        month=month,
        year=year,
        property_id=property_id,
        status=status,
    )


@router.get("/{rent_record_id}", response_model=RentRecordDetail, status_code=status.HTTP_200_OK)
def get_rent_record(
    rent_record_id: UUID,
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Detailed view of a single rent record with all payment transactions."""
    return rent_service.get_rent_record(
        db=db,
        rent_record_id=rent_record_id,
        owner_id=current_owner.id,
    )


@router.patch("/{rent_record_id}", response_model=RentRecordDetail, status_code=status.HTTP_200_OK)
def update_rent_record(
    rent_record_id: UUID,
    data: RentRecordUpdate,
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Edit a rent record (e.g. adjust expected amount for a partial month, add notes)."""
    return rent_service.update_rent_record(
        db=db,
        rent_record_id=rent_record_id,
        owner_id=current_owner.id,
        data=data,
    )


@router.post("/{rent_record_id}/void", response_model=RentRecordVoidResponse, status_code=status.HTTP_200_OK)
def void_rent_record(
    rent_record_id: UUID,
    data: Optional[RentRecordVoidRequest] = None,
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Void a rent record (e.g. created by mistake). Preserves history while excluding from calculations."""
    return rent_service.void_rent_record(
        db=db,
        rent_record_id=rent_record_id,
        owner_id=current_owner.id,
        data=data,
    )
