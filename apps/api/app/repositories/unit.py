from typing import List, Optional
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.property import Property
from app.models.unit import Unit


class UnitRepository:
    """Repository for Unit data access strictly joined to Property.owner_id."""

    def get_by_id(
        self,
        db: Session,
        unit_id: UUID,
        owner_id: UUID,
    ) -> Optional[Unit]:
        """Fetch unit by ID with eager loaded tenants, verifying property belongs to authenticated owner."""
        stmt = (
            select(Unit)
            .join(Property, Unit.property_id == Property.id)
            .options(selectinload(Unit.tenants))
            .where(
                Unit.id == unit_id,
                Property.owner_id == owner_id,
            )
        )
        return db.scalar(stmt)

    def get_active_by_name(
        self,
        db: Session,
        property_id: UUID,
        name: str,
    ) -> Optional[Unit]:
        """Fetch active unit by name within a property."""
        stmt = select(Unit).where(
            Unit.property_id == property_id,
            func.lower(Unit.name) == name.lower().strip(),
            Unit.archived_at.is_(None),
        )
        return db.scalar(stmt)

    def list_by_property(
        self,
        db: Session,
        property_id: UUID,
        owner_id: UUID,
        include_archived: bool = False,
    ) -> List[Unit]:
        """List all units with eager loaded tenants for a property owned by the authenticated owner."""
        stmt = (
            select(Unit)
            .join(Property, Unit.property_id == Property.id)
            .options(selectinload(Unit.tenants))
            .where(
                Unit.property_id == property_id,
                Property.owner_id == owner_id,
            )
        )
        if not include_archived:
            stmt = stmt.where(Unit.archived_at.is_(None))

        stmt = stmt.order_by(Unit.name.asc())
        return list(db.scalars(stmt).all())

    def create(
        self,
        db: Session,
        property_id: UUID,
        name: str,
        unit_type: str,
        monthly_rent_paise: int,
        rent_due_day: int,
        notes: Optional[str] = None,
    ) -> Unit:
        """Create and persist a new unit."""
        unit = Unit(
            property_id=property_id,
            name=name.strip(),
            unit_type=unit_type,
            monthly_rent_paise=monthly_rent_paise,
            rent_due_day=rent_due_day,
            notes=notes.strip() if notes else None,
        )
        db.add(unit)
        db.commit()
        db.refresh(unit)
        return unit

    def update(
        self,
        db: Session,
        unit_obj: Unit,
        name: Optional[str] = None,
        unit_type: Optional[str] = None,
        monthly_rent_paise: Optional[int] = None,
        rent_due_day: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Unit:
        """Update unit attributes."""
        if name is not None:
            unit_obj.name = name.strip()
        if unit_type is not None:
            unit_obj.unit_type = unit_type
        if monthly_rent_paise is not None:
            unit_obj.monthly_rent_paise = monthly_rent_paise
        if rent_due_day is not None:
            unit_obj.rent_due_day = rent_due_day
        if notes is not None:
            unit_obj.notes = notes.strip() if notes else None

        db.commit()
        db.refresh(unit_obj)
        return unit_obj

    def archive(self, db: Session, unit_obj: Unit) -> Unit:
        """Soft-delete unit by setting archived_at."""
        unit_obj.archived_at = func.now()
        db.commit()
        db.refresh(unit_obj)
        return unit_obj


unit_repo = UnitRepository()
