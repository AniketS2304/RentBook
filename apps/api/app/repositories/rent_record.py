from datetime import date
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.property import Property
from app.models.rent_record import RentRecord
from app.models.unit import Unit


class RentRecordRepository:
    """Repository for RentRecord data access strictly scoped to authenticated owner."""

    def get_by_id(
        self,
        db: Session,
        rent_record_id: UUID,
        owner_id: UUID,
    ) -> Optional[RentRecord]:
        """Fetch rent record by ID, verifying ownership through Unit -> Property."""
        stmt = (
            select(RentRecord)
            .join(Unit, RentRecord.unit_id == Unit.id)
            .join(Property, Unit.property_id == Property.id)
            .options(
                joinedload(RentRecord.tenant),
                joinedload(RentRecord.unit).joinedload(Unit.property),
                joinedload(RentRecord.payments),
                joinedload(RentRecord.reminders),
            )
            .where(
                RentRecord.id == rent_record_id,
                Property.owner_id == owner_id,
            )
        )
        return db.scalar(stmt)

    def get_by_tenant_month_year(
        self,
        db: Session,
        tenant_id: UUID,
        month: int,
        year: int,
    ) -> Optional[RentRecord]:
        """Fetch rent record by unique (tenant_id, month, year)."""
        stmt = (
            select(RentRecord)
            .options(
                joinedload(RentRecord.tenant),
                joinedload(RentRecord.unit).joinedload(Unit.property),
                joinedload(RentRecord.payments),
                joinedload(RentRecord.reminders),
            )
            .where(
                RentRecord.tenant_id == tenant_id,
                RentRecord.month == month,
                RentRecord.year == year,
            )
        )
        return db.scalar(stmt)

    def get_records_by_tenants_month_year(
        self,
        db: Session,
        tenant_ids: List[UUID],
        month: int,
        year: int,
    ) -> dict[UUID, RentRecord]:
        """Fetch rent records for multiple tenants in a specific month/year with payments eager-loaded."""
        if not tenant_ids:
            return {}
        stmt = (
            select(RentRecord)
            .options(
                joinedload(RentRecord.payments),
            )
            .where(
                RentRecord.tenant_id.in_(tenant_ids),
                RentRecord.month == month,
                RentRecord.year == year,
            )
        )
        records = db.scalars(stmt).unique().all()
        return {r.tenant_id: r for r in records}

    def list_by_month(
        self,
        db: Session,
        owner_id: UUID,
        month: int,
        year: int,
        property_id: Optional[UUID] = None,
        include_void: bool = False,
    ) -> List[RentRecord]:
        """List rent records for a specific month/year belonging to the owner."""
        stmt = (
            select(RentRecord)
            .join(Unit, RentRecord.unit_id == Unit.id)
            .join(Property, Unit.property_id == Property.id)
            .options(
                joinedload(RentRecord.tenant),
                joinedload(RentRecord.unit).joinedload(Unit.property),
                joinedload(RentRecord.payments),
                joinedload(RentRecord.reminders),
            )
            .where(
                Property.owner_id == owner_id,
                RentRecord.month == month,
                RentRecord.year == year,
            )
        )
        if property_id is not None:
            stmt = stmt.where(Unit.property_id == property_id)
        if not include_void:
            stmt = stmt.where(RentRecord.is_void.is_(False))

        stmt = stmt.order_by(Unit.name.asc(), RentRecord.created_at.asc())
        return list(db.scalars(stmt).unique().all())

    def list_by_tenant(
        self,
        db: Session,
        tenant_id: UUID,
        include_void: bool = False,
    ) -> List[RentRecord]:
        """List all rent records for a tenant, ordered chronologically descending."""
        stmt = (
            select(RentRecord)
            .options(
                joinedload(RentRecord.payments),
            )
            .where(RentRecord.tenant_id == tenant_id)
        )
        if not include_void:
            stmt = stmt.where(RentRecord.is_void.is_(False))

        stmt = stmt.order_by(RentRecord.year.desc(), RentRecord.month.desc())
        return list(db.scalars(stmt).unique().all())

    def create(
        self,
        db: Session,
        tenant_id: UUID,
        unit_id: UUID,
        month: int,
        year: int,
        expected_amount_paise: int,
        due_date: date,
        notes: Optional[str] = None,
    ) -> RentRecord:
        """Create and persist a new rent record. Handles concurrent race condition gracefully."""
        record = RentRecord(
            tenant_id=tenant_id,
            unit_id=unit_id,
            month=month,
            year=year,
            expected_amount_paise=expected_amount_paise,
            due_date=due_date,
            notes=notes.strip() if notes else None,
            is_void=False,
        )
        db.add(record)
        try:
            db.commit()
            db.refresh(record)
            return record
        except IntegrityError:
            db.rollback()
            existing = self.get_by_tenant_month_year(db, tenant_id=tenant_id, month=month, year=year)
            if existing:
                return existing
            raise

    def update(
        self,
        db: Session,
        record: RentRecord,
        expected_amount_paise: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> RentRecord:
        """Update mutable fields on a rent record."""
        if expected_amount_paise is not None:
            record.expected_amount_paise = expected_amount_paise
        if notes is not None:
            record.notes = notes.strip() if notes else None

        db.commit()
        db.refresh(record)
        return record

    def void(
        self,
        db: Session,
        record: RentRecord,
        reason: Optional[str] = None,
    ) -> RentRecord:
        """Mark a rent record as void and append reason to notes."""
        record.is_void = True
        if reason:
            formatted_reason = f"Void reason: {reason.strip()}"
            record.notes = f"{record.notes}\n{formatted_reason}" if record.notes else formatted_reason

        db.commit()
        db.refresh(record)
        return record


rent_repo = RentRecordRepository()
