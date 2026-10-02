from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_owner
from app.db.session import get_db
from app.models.owner import Owner
from app.schemas.unit import UnitArchiveResponse, UnitOut, UnitUpdate
from app.services.unit import unit_service

router = APIRouter(prefix="/units", tags=["Units"])


@router.get(
    "/{unit_id}",
    response_model=UnitOut,
    status_code=status.HTTP_200_OK,
    summary="Get unit details",
)
def get_unit(
    unit_id: UUID,
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Retrieve details for a single unit. Returns 404 for cross-owner resources."""
    return unit_service.get_unit(
        db=db,
        unit_id=unit_id,
        owner_id=current_owner.id,
    )


@router.patch(
    "/{unit_id}",
    response_model=UnitOut,
    status_code=status.HTTP_200_OK,
    summary="Update unit",
)
def update_unit(
    unit_id: UUID,
    data: UnitUpdate,
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Partially update a unit. Rent/due day changes apply to future records only. Returns 404 for cross-owner resources."""
    return unit_service.update_unit(
        db=db,
        unit_id=unit_id,
        owner_id=current_owner.id,
        data=data,
    )


@router.delete(
    "/{unit_id}",
    response_model=UnitArchiveResponse,
    status_code=status.HTTP_200_OK,
    summary="Archive unit",
)
def archive_unit(
    unit_id: UUID,
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Archive a unit (soft delete). Preserves historical rent/tenant data. Returns 404 for cross-owner resources."""
    return unit_service.archive_unit(
        db=db,
        unit_id=unit_id,
        owner_id=current_owner.id,
    )
