from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_owner, get_db
from app.models.owner import Owner
from app.schemas.tenant import (
    TenantCreate,
    TenantDeactivateRequest,
    TenantDeactivateResponse,
    TenantDetail,
    TenantListResponse,
    TenantUpdate,
)
from app.services.tenant import tenant_service

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.get("", response_model=TenantListResponse, status_code=status.HTTP_200_OK)
def list_tenants(
    property_id: Optional[UUID] = Query(None, description="Filter by property ID"),
    status: Optional[str] = Query("ACTIVE", description="Filter by status (ACTIVE, INACTIVE)"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """List tenants for the authenticated owner."""
    return tenant_service.list_tenants(
        db=db,
        owner_id=current_owner.id,
        property_id=property_id,
        status=status,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=TenantDetail, status_code=status.HTTP_201_CREATED)
def create_tenant(
    data: TenantCreate,
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Assign an active tenant to a unit (move-in)."""
    return tenant_service.create_tenant(
        db=db,
        owner_id=current_owner.id,
        data=data,
    )


@router.get("/{tenant_id}", response_model=TenantDetail, status_code=status.HTTP_200_OK)
def get_tenant(
    tenant_id: UUID,
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Get tenant details including unit information."""
    return tenant_service.get_tenant(
        db=db,
        tenant_id=tenant_id,
        owner_id=current_owner.id,
    )


@router.patch("/{tenant_id}", response_model=TenantDetail, status_code=status.HTTP_200_OK)
def update_tenant(
    tenant_id: UUID,
    data: TenantUpdate,
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Update tenant contact info, move-in date, deposit, or notes."""
    return tenant_service.update_tenant(
        db=db,
        tenant_id=tenant_id,
        owner_id=current_owner.id,
        data=data,
    )


@router.post("/{tenant_id}/deactivate", response_model=TenantDeactivateResponse, status_code=status.HTTP_200_OK)
def deactivate_tenant(
    tenant_id: UUID,
    data: Optional[TenantDeactivateRequest] = None,
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Deactivate tenant (move-out). Frees the unit for future tenancies while preserving history."""
    return tenant_service.deactivate_tenant(
        db=db,
        tenant_id=tenant_id,
        owner_id=current_owner.id,
        data=data,
    )
