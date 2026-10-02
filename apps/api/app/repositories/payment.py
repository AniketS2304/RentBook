from datetime import date
from typing import List, Optional
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.payment import Payment
from app.models.property import Property
from app.models.rent_record import RentRecord
from app.models.unit import Unit


class PaymentRepository:
    """Repository for Payment data access strictly scoped to authenticated owner."""

    def get_by_id(
        self,
        db: Session,
        payment_id: UUID,
        owner_id: UUID,
    ) -> Optional[Payment]:
        """Fetch payment by ID, verifying ownership through RentRecord -> Unit -> Property."""
        stmt = (
            select(Payment)
            .join(RentRecord, Payment.rent_record_id == RentRecord.id)
            .join(Unit, RentRecord.unit_id == Unit.id)
            .join(Property, Unit.property_id == Property.id)
            .options(
                joinedload(Payment.rent_record),
            )
            .where(
                Payment.id == payment_id,
                Property.owner_id == owner_id,
            )
        )
        return db.scalar(stmt)

    def get_total_paid_for_rent_record(
        self,
        db: Session,
        rent_record_id: UUID,
        exclude_payment_id: Optional[UUID] = None,
    ) -> int:
        """Calculate SUM of valid (non-void) payments for a rent record in paise."""
        stmt = (
            select(func.coalesce(func.sum(Payment.amount_paise), 0))
            .where(
                Payment.rent_record_id == rent_record_id,
                Payment.is_void.is_(False),
            )
        )
        if exclude_payment_id is not None:
            stmt = stmt.where(Payment.id != exclude_payment_id)
        return int(db.scalar(stmt) or 0)

    def list_by_rent_record(
        self,
        db: Session,
        rent_record_id: UUID,
        owner_id: UUID,
        include_void: bool = True,
    ) -> List[Payment]:
        """List all payments for a rent record belonging to the authenticated owner."""
        stmt = (
            select(Payment)
            .join(RentRecord, Payment.rent_record_id == RentRecord.id)
            .join(Unit, RentRecord.unit_id == Unit.id)
            .join(Property, Unit.property_id == Property.id)
            .where(
                Payment.rent_record_id == rent_record_id,
                Property.owner_id == owner_id,
            )
        )
        if not include_void:
            stmt = stmt.where(Payment.is_void.is_(False))

        stmt = stmt.order_by(Payment.paid_date.asc(), Payment.created_at.asc())
        return list(db.scalars(stmt).all())

    def create(
        self,
        db: Session,
        rent_record_id: UUID,
        amount_paise: int,
        payment_method: str,
        paid_date: date,
        notes: Optional[str] = None,
    ) -> Payment:
        """Create and persist a new payment transaction."""
        payment = Payment(
            rent_record_id=rent_record_id,
            amount_paise=amount_paise,
            payment_method=payment_method,
            paid_date=paid_date,
            notes=notes.strip() if notes else None,
            is_void=False,
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    def update(
        self,
        db: Session,
        payment: Payment,
        amount_paise: Optional[int] = None,
        payment_method: Optional[str] = None,
        paid_date: Optional[date] = None,
        notes: Optional[str] = None,
    ) -> Payment:
        """Update mutable fields of a payment."""
        if amount_paise is not None:
            payment.amount_paise = amount_paise
        if payment_method is not None:
            payment.payment_method = payment_method
        if paid_date is not None:
            payment.paid_date = paid_date
        if notes is not None:
            payment.notes = notes.strip() if notes else None

        db.commit()
        db.refresh(payment)
        return payment

    def void(
        self,
        db: Session,
        payment: Payment,
        reason: Optional[str] = None,
    ) -> Payment:
        """Mark payment as void and record reason."""
        payment.is_void = True
        if reason:
            formatted_reason = f"Void reason: {reason.strip()}"
            payment.notes = f"{payment.notes}\n{formatted_reason}" if payment.notes else formatted_reason

        db.commit()
        db.refresh(payment)
        return payment


payment_repo = PaymentRepository()
