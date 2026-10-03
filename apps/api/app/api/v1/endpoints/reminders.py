from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_owner, get_db
from app.models.owner import Owner
from app.schemas.reminder import (
    ReminderCreateRequest,
    ReminderCreateResponse,
    ReminderListItem,
    TenantReminderCreateRequest,
)
from app.services.reminder import reminder_service

router = APIRouter(tags=["Reminders"])


@router.post(
    "/rent/{rent_record_id}/reminders",
    response_model=ReminderCreateResponse,
    status_code=status.HTTP_200_OK,
)
def create_rent_reminder(
    rent_record_id: UUID,
    data: Optional[ReminderCreateRequest] = None,
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Generate and record a tenant reminder for a specific rent record."""
    return reminder_service.create_rent_reminder(
        db=db,
        owner_id=current_owner.id,
        rent_record_id=rent_record_id,
        data=data,
    )


@router.get(
    "/rent/{rent_record_id}/reminders",
    response_model=List[ReminderListItem],
    status_code=status.HTTP_200_OK,
)
def list_rent_reminders(
    rent_record_id: UUID,
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """List reminder history for a specific rent record."""
    return reminder_service.list_reminders_for_rent_record(
        db=db,
        owner_id=current_owner.id,
        rent_record_id=rent_record_id,
    )


@router.post(
    "/tenants/{tenant_id}/reminders",
    response_model=ReminderCreateResponse,
    status_code=status.HTTP_200_OK,
)
def create_tenant_reminder(
    tenant_id: UUID,
    data: TenantReminderCreateRequest,
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Generate and record a reminder for a tenant (alias endpoint)."""
    return reminder_service.create_tenant_reminder(
        db=db,
        owner_id=current_owner.id,
        tenant_id=tenant_id,
        rent_record_id=data.rent_record_id,
        custom_message=data.message,
        channel=data.channel,
    )


@router.get(
    "/tenants/{tenant_id}/reminders",
    response_model=List[ReminderListItem],
    status_code=status.HTTP_200_OK,
)
def list_tenant_reminders(
    tenant_id: UUID,
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """List all reminder history for a tenant."""
    return reminder_service.list_reminders_for_tenant(
        db=db,
        owner_id=current_owner.id,
        tenant_id=tenant_id,
    )
