from datetime import date
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.property import Property
from app.models.tenant import Tenant
from app.models.unit import Unit


class TenantRepository:
    """Repository for Tenant data access strictly scoped to authenticated owner."""

    def get_by_id(
        self,
        db: Session,
        tenant_id: UUID,
        owner_id: UUID,
    ) -> Optional[Tenant]:
        """Fetch tenant by ID, verifying ownership chain through Unit -> Property."""
        stmt = (
            select(Tenant)
            .join(Unit, Tenant.unit_id == Unit.id)
            .join(Property, Unit.property_id == Property.id)
            .options(
                joinedload(Tenant.unit).joinedload(Unit.property)
            )
            .where(
                Tenant.id == tenant_id,
                Property.owner_id == owner_id,
            )
        )
        return db.scalar(stmt)

    def get_active_tenant_by_unit(
        self,
        db: Session,
        unit_id: UUID,
    ) -> Optional[Tenant]:
        """Fetch the active tenant for a unit, if any."""
        stmt = select(Tenant).where(
            Tenant.unit_id == unit_id,
            Tenant.status == "ACTIVE",
        )
        return db.scalar(stmt)

    def list_by_owner(
        self,
        db: Session,
        owner_id: UUID,
        property_id: Optional[UUID] = None,
        status: Optional[str] = "ACTIVE",
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Tenant], int]:
        """List tenants for the authenticated owner with optional property and status filters."""
        base_stmt = (
            select(Tenant)
            .join(Unit, Tenant.unit_id == Unit.id)
            .join(Property, Unit.property_id == Property.id)
            .where(Property.owner_id == owner_id)
        )
        if property_id is not None:
            base_stmt = base_stmt.where(Unit.property_id == property_id)
        if status is not None:
            base_stmt = base_stmt.where(Tenant.status == status)

        # Count total
        count_stmt = (
            select(func.count(Tenant.id))
            .join(Unit, Tenant.unit_id == Unit.id)
            .join(Property, Unit.property_id == Property.id)
            .where(Property.owner_id == owner_id)
        )
        if property_id is not None:
            count_stmt = count_stmt.where(Unit.property_id == property_id)
        if status is not None:
            count_stmt = count_stmt.where(Tenant.status == status)

        total = db.scalar(count_stmt) or 0

        # Paginate
        offset = (page - 1) * per_page
        stmt = (
            base_stmt.options(
                joinedload(Tenant.unit).joinedload(Unit.property)
            )
            .order_by(Tenant.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
        tenants = list(db.scalars(stmt).all())
        return tenants, total

    def create(
        self,
        db: Session,
        unit_id: UUID,
        name: str,
        phone: str,
        move_in_date: date,
        email: Optional[str] = None,
        security_deposit_paise: int = 0,
        notes: Optional[str] = None,
    ) -> Tenant:
        """Create and persist a new active tenant."""
        tenant = Tenant(
            unit_id=unit_id,
            name=name.strip(),
            phone=phone.strip(),
            email=email.strip() if email else None,
            move_in_date=move_in_date,
            security_deposit_paise=security_deposit_paise,
            status="ACTIVE",
            notes=notes.strip() if notes else None,
        )
        db.add(tenant)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise
        db.refresh(tenant)
        return tenant

    def update(
        self,
        db: Session,
        tenant: Tenant,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        move_in_date: Optional[date] = None,
        security_deposit_paise: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Tenant:
        """Update tenant mutable fields."""
        if name is not None:
            tenant.name = name.strip()
        if phone is not None:
            tenant.phone = phone.strip()
        if email is not None:
            tenant.email = email.strip() if email else None
        if move_in_date is not None:
            tenant.move_in_date = move_in_date
        if security_deposit_paise is not None:
            tenant.security_deposit_paise = security_deposit_paise
        if notes is not None:
            tenant.notes = notes.strip() if notes else None

        db.commit()
        db.refresh(tenant)
        return tenant

    def deactivate(
        self,
        db: Session,
        tenant: Tenant,
        move_out_date: date,
    ) -> Tenant:
        """Deactivate tenant and record move_out_date."""
        tenant.status = "INACTIVE"
        tenant.move_out_date = move_out_date
        db.commit()
        db.refresh(tenant)
        return tenant


tenant_repo = TenantRepository()
