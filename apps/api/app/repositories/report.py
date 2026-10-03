from typing import Dict, Optional
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.property import Property
from app.models.rent_record import RentRecord
from app.models.unit import Unit


class ReportRepository:
    """Repository for Report SQL aggregation queries strictly scoped to authenticated owner."""

    def get_payment_breakdown(
        self,
        db: Session,
        owner_id: UUID,
        month: int,
        year: int,
        property_id: Optional[UUID] = None,
    ) -> Dict[str, int]:
        """Aggregate total non-void payments by payment method for non-void rent records of month/year."""
        stmt = (
            select(
                Payment.payment_method,
                func.coalesce(func.sum(Payment.amount_paise), 0).label("total_amount"),
            )
            .join(RentRecord, Payment.rent_record_id == RentRecord.id)
            .join(Unit, RentRecord.unit_id == Unit.id)
            .join(Property, Unit.property_id == Property.id)
            .where(
                Property.owner_id == owner_id,
                RentRecord.month == month,
                RentRecord.year == year,
                RentRecord.is_void.is_(False),
                Payment.is_void.is_(False),
            )
        )
        if property_id is not None:
            stmt = stmt.where(Unit.property_id == property_id)

        stmt = stmt.group_by(Payment.payment_method)
        rows = db.execute(stmt).all()

        breakdown = {
            "CASH": 0,
            "UPI": 0,
            "BANK_TRANSFER": 0,
            "OTHER": 0,
        }
        for method, total in rows:
            if method in breakdown:
                breakdown[method] = total
        return breakdown

    def get_total_expected(
        self,
        db: Session,
        owner_id: UUID,
        month: int,
        year: int,
        property_id: Optional[UUID] = None,
    ) -> int:
        """Aggregate total expected paise for non-void rent records belonging to owner in month/year."""
        stmt = (
            select(func.coalesce(func.sum(RentRecord.expected_amount_paise), 0))
            .join(Unit, RentRecord.unit_id == Unit.id)
            .join(Property, Unit.property_id == Property.id)
            .where(
                Property.owner_id == owner_id,
                RentRecord.month == month,
                RentRecord.year == year,
                RentRecord.is_void.is_(False),
            )
        )
        if property_id is not None:
            stmt = stmt.where(Unit.property_id == property_id)

        return db.scalar(stmt) or 0


report_repo = ReportRepository()
