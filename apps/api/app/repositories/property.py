from typing import Optional, Tuple, List
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.property import Property


class PropertyRepository:
    """Repository for Property data access strictly scoped to owner_id."""

    def get_by_id(
        self,
        db: Session,
        property_id: UUID,
        owner_id: UUID,
    ) -> Optional[Property]:
        """Fetch property by ID, strictly enforcing owner_id."""
        stmt = select(Property).where(
            Property.id == property_id,
            Property.owner_id == owner_id,
        )
        return db.scalar(stmt)

    def get_active_by_name(
        self,
        db: Session,
        owner_id: UUID,
        name: str,
    ) -> Optional[Property]:
        """Fetch active (non-archived) property by owner_id and exact name."""
        stmt = select(Property).where(
            Property.owner_id == owner_id,
            func.lower(Property.name) == name.lower().strip(),
            Property.archived_at.is_(None),
        )
        return db.scalar(stmt)

    def list_by_owner(
        self,
        db: Session,
        owner_id: UUID,
        include_archived: bool = False,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Property], int]:
        """List properties belonging to owner with pagination and optional archive filter."""
        base_stmt = select(Property).where(Property.owner_id == owner_id)
        if not include_archived:
            base_stmt = base_stmt.where(Property.archived_at.is_(None))

        # Total count
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = db.scalar(count_stmt) or 0

        # Items paginated
        query_stmt = (
            base_stmt.order_by(Property.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        items = list(db.scalars(query_stmt).all())
        return items, total

    def create(
        self,
        db: Session,
        owner_id: UUID,
        name: str,
        address: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Property:
        """Create a new property for the authenticated owner."""
        prop = Property(
            owner_id=owner_id,
            name=name.strip(),
            address=address.strip() if address else None,
            notes=notes.strip() if notes else None,
        )
        db.add(prop)
        db.commit()
        db.refresh(prop)
        return prop

    def update(
        self,
        db: Session,
        property_obj: Property,
        name: Optional[str] = None,
        address: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Property:
        """Update property attributes."""
        if name is not None:
            property_obj.name = name.strip()
        if address is not None:
            property_obj.address = address.strip() if address else None
        if notes is not None:
            property_obj.notes = notes.strip() if notes else None

        db.commit()
        db.refresh(property_obj)
        return property_obj

    def archive(self, db: Session, property_obj: Property) -> Property:
        """Soft-delete property by setting archived_at."""
        property_obj.archived_at = func.now()
        db.commit()
        db.refresh(property_obj)
        return property_obj


property_repo = PropertyRepository()
