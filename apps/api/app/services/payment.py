from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.exceptions import AppException, NotFoundError
from app.repositories.payment import payment_repo
from app.repositories.rent_record import rent_repo
from app.schemas.payment import (
    PaymentCreate,
    PaymentCreateResponse,
    PaymentDetail,
    PaymentUpdate,
    PaymentVoidRequest,
    PaymentVoidResponse,
    RentRecordBriefStatus,
)
from app.services.rent_status import calculate_rent_status, get_today_ist


class PaymentService:
    """Business logic for payment recording, corrections, voiding, and rent status integration."""

    def record_payment(
        self,
        db: Session,
        rent_record_id: UUID,
        owner_id: UUID,
        data: PaymentCreate,
    ) -> PaymentCreateResponse:
        """Record a new payment transaction against a rent record with 2x sanity check."""
        # 1. Verify rent record exists and belongs to authenticated owner (BR-OWN-04, BR-OWN-05)
        rent_record = rent_repo.get_by_id(db, rent_record_id=rent_record_id, owner_id=owner_id)
        if not rent_record:
            raise NotFoundError(detail="Rent record not found", code="NOT_FOUND")

        # 2. Cannot record payments on a voided rent record
        if rent_record.is_void:
            raise AppException(
                status_code=400,
                detail="Cannot record payment on a voided rent record",
                code="RENT_RECORD_VOIDED",
            )

        # 3. Validate payment date is not in the future (BR-PAY-05)
        today = get_today_ist()
        if data.paid_date > today:
            raise AppException(
                status_code=400,
                detail="Payment date cannot be in the future",
                code="INVALID_PAYMENT_DATE",
            )

        # 4. 2x excess payment sanity check (BR-PAY-08, EC-07)
        current_total = payment_repo.get_total_paid_for_rent_record(db, rent_record_id=rent_record.id)
        new_total = current_total + data.amount_paise
        threshold = 2 * rent_record.expected_amount_paise

        if new_total > threshold and not data.confirm_excess:
            raise AppException(
                status_code=422,
                detail="Payment amount significantly exceeds expected rent. Please confirm to proceed.",
                code="EXCESSIVE_AMOUNT_WARNING",
            )

        # 5. Persist payment
        payment = payment_repo.create(
            db=db,
            rent_record_id=rent_record.id,
            amount_paise=data.amount_paise,
            payment_method=data.payment_method,
            paid_date=data.paid_date,
            notes=data.notes,
        )

        # 6. Recalculate rent status dynamically using single source of truth
        status = calculate_rent_status(
            due_date=rent_record.due_date,
            expected_amount_paise=rent_record.expected_amount_paise,
            total_paid_paise=new_total,
        )

        return PaymentCreateResponse(
            payment=PaymentDetail.model_validate(payment),
            rent_record=RentRecordBriefStatus(
                id=rent_record.id,
                expected_amount_paise=rent_record.expected_amount_paise,
                total_paid_paise=new_total,
                status=status,
            ),
        )

    def get_payment(
        self,
        db: Session,
        payment_id: UUID,
        owner_id: UUID,
    ) -> PaymentDetail:
        """Fetch single payment details. Returns 404 for cross-owner access."""
        payment = payment_repo.get_by_id(db, payment_id=payment_id, owner_id=owner_id)
        if not payment:
            raise NotFoundError(detail="Payment not found", code="NOT_FOUND")

        return PaymentDetail.model_validate(payment)

    def list_payments_for_rent_record(
        self,
        db: Session,
        rent_record_id: UUID,
        owner_id: UUID,
        include_void: bool = True,
    ) -> List[PaymentDetail]:
        """List all payments for a rent record. Verifies rent record belongs to authenticated owner."""
        rent_record = rent_repo.get_by_id(db, rent_record_id=rent_record_id, owner_id=owner_id)
        if not rent_record:
            raise NotFoundError(detail="Rent record not found", code="NOT_FOUND")

        payments = payment_repo.list_by_rent_record(
            db=db,
            rent_record_id=rent_record_id,
            owner_id=owner_id,
            include_void=include_void,
        )
        return [PaymentDetail.model_validate(p) for p in payments]

    def update_payment(
        self,
        db: Session,
        payment_id: UUID,
        owner_id: UUID,
        data: PaymentUpdate,
    ) -> PaymentDetail:
        """Edit an existing payment with validation, 2x sanity check, and status recalculation."""
        payment = payment_repo.get_by_id(db, payment_id=payment_id, owner_id=owner_id)
        if not payment:
            raise NotFoundError(detail="Payment not found", code="NOT_FOUND")

        if payment.is_void:
            raise AppException(
                status_code=400,
                detail="Cannot edit a voided payment",
                code="PAYMENT_VOIDED",
            )

        if data.paid_date is not None:
            today = get_today_ist()
            if data.paid_date > today:
                raise AppException(
                    status_code=400,
                    detail="Payment date cannot be in the future",
                    code="INVALID_PAYMENT_DATE",
                )

        if data.amount_paise is not None:
            other_total = payment_repo.get_total_paid_for_rent_record(
                db,
                rent_record_id=payment.rent_record_id,
                exclude_payment_id=payment.id,
            )
            new_total = other_total + data.amount_paise
            threshold = 2 * payment.rent_record.expected_amount_paise

            if new_total > threshold and not data.confirm_excess:
                raise AppException(
                    status_code=422,
                    detail="Payment amount significantly exceeds expected rent. Please confirm to proceed.",
                    code="EXCESSIVE_AMOUNT_WARNING",
                )

        updated = payment_repo.update(
            db=db,
            payment=payment,
            amount_paise=data.amount_paise,
            payment_method=data.payment_method,
            paid_date=data.paid_date,
            notes=data.notes,
        )
        return PaymentDetail.model_validate(updated)

    def void_payment(
        self,
        db: Session,
        payment_id: UUID,
        owner_id: UUID,
        data: Optional[PaymentVoidRequest] = None,
    ) -> PaymentVoidResponse:
        """Void a payment (soft deletion). Preserves historical record while excluding from totals."""
        payment = payment_repo.get_by_id(db, payment_id=payment_id, owner_id=owner_id)
        if not payment:
            raise NotFoundError(detail="Payment not found", code="NOT_FOUND")

        if payment.is_void:
            raise AppException(
                status_code=400,
                detail="Payment is already voided",
                code="PAYMENT_ALREADY_VOIDED",
            )

        reason = data.reason if data else None
        payment_repo.void(db=db, payment=payment, reason=reason)

        return PaymentVoidResponse(
            message="Payment voided successfully",
            id=payment.id,
            is_void=True,
        )


payment_service = PaymentService()
