from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_owner, get_db
from app.models.owner import Owner
from app.schemas.payment import (
    PaymentDetail,
    PaymentUpdate,
    PaymentVoidRequest,
    PaymentVoidResponse,
)
from app.services.payment import payment_service

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/{payment_id}", response_model=PaymentDetail, status_code=status.HTTP_200_OK)
def get_payment(
    payment_id: UUID,
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Get single payment transaction details. Returns 404 for cross-owner resources."""
    return payment_service.get_payment(
        db=db,
        payment_id=payment_id,
        owner_id=current_owner.id,
    )


@router.patch("/{payment_id}", response_model=PaymentDetail, status_code=status.HTTP_200_OK)
def update_payment(
    payment_id: UUID,
    data: PaymentUpdate,
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Edit a payment transaction (correction) with 2x sanity check and status recalculation."""
    return payment_service.update_payment(
        db=db,
        payment_id=payment_id,
        owner_id=current_owner.id,
        data=data,
    )


@router.post("/{payment_id}/void", response_model=PaymentVoidResponse, status_code=status.HTTP_200_OK)
def void_payment(
    payment_id: UUID,
    data: Optional[PaymentVoidRequest] = None,
    current_owner: Owner = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Void a payment transaction. Preserves history while excluding from totals."""
    return payment_service.void_payment(
        db=db,
        payment_id=payment_id,
        owner_id=current_owner.id,
        data=data,
    )
