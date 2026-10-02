from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_owner
from app.db.session import get_db
from app.models.owner import Owner
from app.schemas.property import (
    PropertyArchiveResponse,
    PropertyCreate,
    PropertyDetail,
    PropertyListResponse,
    PropertyUpdate,
)
from app.schemas.unit import UnitCreate, UnitOut
from app.services.property import property_service
from app.services.unit import unit_service

router = APIRouter(prefix="/properties", tags=["Properties"])


@router.get(
    "",
    response_model=PropertyListResponse,
    status_code=status.HTTP_200_OK,
    summary="List properties for authenticated owner",
)
def list_properties(
    include_archived: bool = Query(False, description="Include archived properties"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """List properties belonging to the authenticated owner with pagination and metrics."""
    return property_service.list_properties(
        db=db,
        owner_id=current_owner.id,
        include_archived=include_archived,
        page=page,
        per_page=per_page,
    )


@router.post(
    "",
    response_model=PropertyDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new property",
)
def create_property(
    data: PropertyCreate,
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Create a new property belonging to the authenticated owner."""
    return property_service.create_property(
        db=db,
        owner_id=current_owner.id,
        data=data,
    )


@router.get(
    "/{property_id}",
    response_model=PropertyDetail,
    status_code=status.HTTP_200_OK,
    summary="Get property details with unit list",
)
def get_property(
    property_id: UUID,
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Get full property details including units. Returns 404 for cross-owner resources."""
    return property_service.get_property(
        db=db,
        property_id=property_id,
        owner_id=current_owner.id,
    )


@router.patch(
    "/{property_id}",
    response_model=PropertyDetail,
    status_code=status.HTTP_200_OK,
    summary="Update property",
)
def update_property(
    property_id: UUID,
    data: PropertyUpdate,
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Update property attributes. Returns 404 for cross-owner resources."""
    return property_service.update_property(
        db=db,
        property_id=property_id,
        owner_id=current_owner.id,
        data=data,
    )


@router.delete(
    "/{property_id}",
    response_model=PropertyArchiveResponse,
    status_code=status.HTTP_200_OK,
    summary="Archive property",
)
def archive_property(
    property_id: UUID,
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Archive property (soft delete). Preserves historical data. Returns 404 for cross-owner resources."""
    return property_service.archive_property(
        db=db,
        property_id=property_id,
        owner_id=current_owner.id,
    )


# --- Sub-resource routes: /properties/{property_id}/units per API.md ---


@router.get(
    "/{property_id}/units",
    response_model=List[UnitOut],
    status_code=status.HTTP_200_OK,
    summary="List units in a property",
)
def list_property_units(
    property_id: UUID,
    include_archived: bool = Query(False, description="Include archived units"),
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """List units for a property owned by the authenticated owner. Returns 404 for cross-owner properties."""
    return unit_service.list_units(
        db=db,
        property_id=property_id,
        owner_id=current_owner.id,
        include_archived=include_archived,
    )


@router.post(
    "/{property_id}/units",
    response_model=UnitOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a unit within a property",
)
def create_property_unit(
    property_id: UUID,
    data: UnitCreate,
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Create a new unit within an authenticated owner's property. Returns 404 for cross-owner properties."""
    return unit_service.create_unit(
        db=db,
        property_id=property_id,
        owner_id=current_owner.id,
        data=data,
    )
