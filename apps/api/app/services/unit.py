from typing import List
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.unit import Unit
from app.repositories.property import property_repo
from app.repositories.unit import unit_repo
from app.schemas.unit import CurrentTenantBrief, UnitArchiveResponse, UnitCreate, UnitOut, UnitUpdate


class UnitService:
    """Business logic for Unit management."""

    def _format_unit_out(self, unit: Unit) -> UnitOut:
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

    def create_unit(
        self,
        db: Session,
        property_id: UUID,
        owner_id: UUID,
        data: UnitCreate,
    ) -> UnitOut:
        """Create a unit under a property belonging to authenticated owner."""
        # Verify parent property ownership
        prop = property_repo.get_by_id(db, property_id=property_id, owner_id=owner_id)
        if not prop:
            raise NotFoundError(
                detail="Property not found",
                code="NOT_FOUND",
            )

        # Check unique active name within property
        existing = unit_repo.get_active_by_name(db, property_id=property_id, name=data.name)
        if existing:
            raise ConflictError(
                detail="Unit name already exists in this property",
                code="UNIT_NAME_EXISTS",
                errors=[{"field": "name", "message": "Unit name already exists in this property"}],
            )

        unit = unit_repo.create(
            db=db,
            property_id=property_id,
            name=data.name,
            unit_type=data.unit_type,
            monthly_rent_paise=data.monthly_rent_paise,
            rent_due_day=data.rent_due_day,
            notes=data.notes,
        )
        return self._format_unit_out(unit)

    def list_units(
        self,
        db: Session,
        property_id: UUID,
        owner_id: UUID,
        include_archived: bool = False,
    ) -> List[UnitOut]:
        """List units for a property owned by the authenticated owner."""
        prop = property_repo.get_by_id(db, property_id=property_id, owner_id=owner_id)
        if not prop:
            raise NotFoundError(
                detail="Property not found",
                code="NOT_FOUND",
            )

        units = unit_repo.list_by_property(
            db=db,
            property_id=property_id,
            owner_id=owner_id,
            include_archived=include_archived,
        )
        return [self._format_unit_out(u) for u in units]

    def get_unit(
        self,
        db: Session,
        unit_id: UUID,
        owner_id: UUID,
    ) -> UnitOut:
        """Get unit details; returns 404 if not found or belongs to another owner."""
        unit = unit_repo.get_by_id(db, unit_id=unit_id, owner_id=owner_id)
        if not unit:
            raise NotFoundError(
                detail="Unit not found",
                code="NOT_FOUND",
            )
        return self._format_unit_out(unit)

    def update_unit(
        self,
        db: Session,
        unit_id: UUID,
        owner_id: UUID,
        data: UnitUpdate,
    ) -> UnitOut:
        """Update unit attributes, enforcing active name uniqueness if name changed."""
        unit = unit_repo.get_by_id(db, unit_id=unit_id, owner_id=owner_id)
        if not unit:
            raise NotFoundError(
                detail="Unit not found",
                code="NOT_FOUND",
            )

        if data.name is not None and data.name.strip().lower() != unit.name.lower():
            existing = unit_repo.get_active_by_name(
                db, property_id=unit.property_id, name=data.name
            )
            if existing and existing.id != unit.id:
                raise ConflictError(
                    detail="Unit name already exists in this property",
                    code="UNIT_NAME_EXISTS",
                    errors=[{"field": "name", "message": "Unit name already exists in this property"}],
                )

        updated_unit = unit_repo.update(
            db=db,
            unit_obj=unit,
            name=data.name,
            unit_type=data.unit_type,
            monthly_rent_paise=data.monthly_rent_paise,
            rent_due_day=data.rent_due_day,
            notes=data.notes,
        )
        return self._format_unit_out(updated_unit)

    def archive_unit(
        self,
        db: Session,
        unit_id: UUID,
        owner_id: UUID,
    ) -> UnitArchiveResponse:
        """Soft-delete unit; returns 404 if not found or cross-owner."""
        unit = unit_repo.get_by_id(db, unit_id=unit_id, owner_id=owner_id)
        if not unit:
            raise NotFoundError(
                detail="Unit not found",
                code="NOT_FOUND",
            )

        archived = unit_repo.archive(db, unit_obj=unit)
        return UnitArchiveResponse(
            message="Unit archived successfully",
            archived_at=archived.archived_at,
        )


unit_service = UnitService()
