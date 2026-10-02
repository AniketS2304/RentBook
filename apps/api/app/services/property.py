from typing import List
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.property import Property
from app.repositories.property import property_repo
from app.schemas.property import (
    PropertyArchiveResponse,
    PropertyCreate,
    PropertyDetail,
    PropertyListItem,
    PropertyListResponse,
    PropertyUpdate,
)
from app.schemas.unit import CurrentTenantBrief, UnitOut


class PropertyService:
    """Business logic for Property management."""

    def _compute_unit_counts(self, prop: Property, include_archived_units: bool = False):
        """Compute unit counts and occupancy metrics."""
        units = prop.units if include_archived_units else [u for u in prop.units if u.archived_at is None]
        unit_count = len(units)
        occupied_count = sum(
            1 for u in units if any(t.status == "ACTIVE" for t in u.tenants)
        )
        vacant_count = max(0, unit_count - occupied_count)
        return unit_count, occupied_count, vacant_count

    def _format_unit_out(self, unit) -> UnitOut:
        """Format Unit model into UnitOut with occupancy and current tenant info."""
        active_tenant = next((t for t in unit.tenants if t.status == "ACTIVE"), None)
        current_tenant = (
            CurrentTenantBrief(id=active_tenant.id, name=active_tenant.name)
            if active_tenant
            else None
        )
        return UnitOut(
            id=unit.id,
            property_id=unit.property_id,
            name=unit.name,
            unit_type=unit.unit_type,
            monthly_rent_paise=unit.monthly_rent_paise,
            rent_due_day=unit.rent_due_day,
            notes=unit.notes,
            archived_at=unit.archived_at,
            created_at=unit.created_at,
            updated_at=unit.updated_at,
            is_occupied=active_tenant is not None,
            current_tenant=current_tenant,
        )

    def _format_property_detail(self, prop: Property) -> PropertyDetail:
        """Format Property model into full PropertyDetail schema."""
        unit_count, occupied_count, vacant_count = self._compute_unit_counts(prop)
        formatted_units = [self._format_unit_out(u) for u in prop.units if u.archived_at is None]

        return PropertyDetail(
            id=prop.id,
            name=prop.name,
            address=prop.address,
            notes=prop.notes,
            unit_count=unit_count,
            occupied_count=occupied_count,
            vacant_count=vacant_count,
            archived_at=prop.archived_at,
            created_at=prop.created_at,
            updated_at=prop.updated_at,
            units=formatted_units,
        )

    def create_property(
        self,
        db: Session,
        owner_id: UUID,
        data: PropertyCreate,
    ) -> PropertyDetail:
        """Create a new property enforcing active name uniqueness per owner."""
        existing = property_repo.get_active_by_name(db, owner_id=owner_id, name=data.name)
        if existing:
            raise ConflictError(
                detail="Property name already exists for this owner",
                code="PROPERTY_NAME_EXISTS",
                errors=[{"field": "name", "message": "Property name already exists"}],
            )

        prop = property_repo.create(
            db=db,
            owner_id=owner_id,
            name=data.name,
            address=data.address,
            notes=data.notes,
        )
        return self._format_property_detail(prop)

    def list_properties(
        self,
        db: Session,
        owner_id: UUID,
        include_archived: bool = False,
        page: int = 1,
        per_page: int = 20,
    ) -> PropertyListResponse:
        """List properties belonging to the authenticated owner."""
        skip = (page - 1) * per_page
        items, total = property_repo.list_by_owner(
            db=db,
            owner_id=owner_id,
            include_archived=include_archived,
            skip=skip,
            limit=per_page,
        )

        list_items: List[PropertyListItem] = []
        for prop in items:
            unit_count, occupied_count, vacant_count = self._compute_unit_counts(
                prop, include_archived_units=include_archived
            )
            list_items.append(
                PropertyListItem(
                    id=prop.id,
                    name=prop.name,
                    address=prop.address,
                    notes=prop.notes,
                    unit_count=unit_count,
                    occupied_count=occupied_count,
                    vacant_count=vacant_count,
                    archived_at=prop.archived_at,
                    created_at=prop.created_at,
                )
            )

        return PropertyListResponse(
            items=list_items,
            total=total,
            page=page,
            per_page=per_page,
        )

    def get_property(
        self,
        db: Session,
        property_id: UUID,
        owner_id: UUID,
    ) -> PropertyDetail:
        """Get property details with unit list; returns 404 if not found or cross-owner."""
        prop = property_repo.get_by_id(db, property_id=property_id, owner_id=owner_id)
        if not prop:
            raise NotFoundError(
                detail="Property not found",
                code="NOT_FOUND",
            )
        return self._format_property_detail(prop)

    def update_property(
        self,
        db: Session,
        property_id: UUID,
        owner_id: UUID,
        data: PropertyUpdate,
    ) -> PropertyDetail:
        """Update property attributes, enforcing active name uniqueness if name changed."""
        prop = property_repo.get_by_id(db, property_id=property_id, owner_id=owner_id)
        if not prop:
            raise NotFoundError(
                detail="Property not found",
                code="NOT_FOUND",
            )

        if data.name is not None and data.name.strip().lower() != prop.name.lower():
            existing = property_repo.get_active_by_name(db, owner_id=owner_id, name=data.name)
            if existing and existing.id != prop.id:
                raise ConflictError(
                    detail="Property name already exists for this owner",
                    code="PROPERTY_NAME_EXISTS",
                    errors=[{"field": "name", "message": "Property name already exists"}],
                )

        updated_prop = property_repo.update(
            db=db,
            property_obj=prop,
            name=data.name,
            address=data.address,
            notes=data.notes,
        )
        return self._format_property_detail(updated_prop)

    def archive_property(
        self,
        db: Session,
        property_id: UUID,
        owner_id: UUID,
    ) -> PropertyArchiveResponse:
        """Soft-delete property; returns 404 if not found or cross-owner."""
        prop = property_repo.get_by_id(db, property_id=property_id, owner_id=owner_id)
        if not prop:
            raise NotFoundError(
                detail="Property not found",
                code="NOT_FOUND",
            )

        archived = property_repo.archive(db, property_obj=prop)
        return PropertyArchiveResponse(
            message="Property archived successfully",
            archived_at=archived.archived_at,
        )


property_service = PropertyService()
