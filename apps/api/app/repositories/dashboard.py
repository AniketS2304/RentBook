from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.payment import Payment
from app.models.property import Property
from app.models.rent_record import RentRecord
from app.models.tenant import Tenant
from app.models.unit import Unit


class DashboardRepository:
    """Repository for Dashboard aggregations strictly scoped to authenticated owner."""

    def get_unit_counts(
        self,
        db: Session,
        owner_id: UUID,
        property_id: Optional[UUID] = None,
    ) -> Tuple[int, int, int]:
        """Calculate total, occupied, and vacant units for active properties/units belonging to owner."""
        stmt = (
            select(
                func.count(Unit.id.distinct()).label("total_units"),
                func.count(
                    func.distinct(
                        case((Tenant.status == "ACTIVE", Unit.id), else_=None)
                    )
                ).label("occupied_units"),
            )
            .join(Property, Unit.property_id == Property.id)
            .outerjoin(Tenant, Unit.id == Tenant.unit_id)
            .where(
                Property.owner_id == owner_id,
                Property.archived_at.is_(None),
                Unit.archived_at.is_(None),
            )
        )
        if property_id is not None:
            stmt = stmt.where(Property.id == property_id)

        row = db.execute(stmt).one()
        total_units = row.total_units or 0
        occupied_units = row.occupied_units or 0
        vacant_units = max(0, total_units - occupied_units)
        return total_units, occupied_units, vacant_units

    def get_recent_payments(
        self,
        db: Session,
        owner_id: UUID,
        property_id: Optional[UUID] = None,
        limit: int = 5,
    ) -> List[Payment]:
        """Fetch the most recent non-void payments across the authenticated owner's properties."""
        stmt = (
            select(Payment)
            .join(RentRecord, Payment.rent_record_id == RentRecord.id)
            .join(Unit, RentRecord.unit_id == Unit.id)
            .join(Property, Unit.property_id == Property.id)
            .options(
                joinedload(Payment.rent_record).joinedload(RentRecord.tenant),
                joinedload(Payment.rent_record).joinedload(RentRecord.unit).joinedload(Unit.property),
            )
            .where(
                Property.owner_id == owner_id,
                Payment.is_void.is_(False),
            )
        )
        if property_id is not None:
            stmt = stmt.where(Unit.property_id == property_id)

        stmt = stmt.order_by(
            Payment.paid_date.desc(),
            Payment.created_at.desc(),
        ).limit(limit)

        return list(db.scalars(stmt).unique().all())


dashboard_repo = DashboardRepository()
