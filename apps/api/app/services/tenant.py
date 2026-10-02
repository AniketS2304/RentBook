from datetime import date
from typing import Optional
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppException, ConflictError, NotFoundError
from app.models.tenant import Tenant
from app.repositories.property import property_repo
from app.repositories.rent_record import rent_repo
from app.repositories.tenant import tenant_repo
from app.repositories.unit import unit_repo
from app.schemas.tenant import (
    TenantCreate,
    TenantDeactivateRequest,
    TenantDeactivateResponse,
    TenantDetail,
    TenantListItem,
    TenantListResponse,
    TenantRentHistoryItem,
    TenantUnitBrief,
    TenantUpdate,
)
from app.services.rent_status import calculate_rent_status, get_today_ist


class TenantService:
    """Business logic for Tenant lifecycle and unit assignment."""

    def _format_tenant_detail(self, db: Session, tenant: Tenant) -> TenantDetail:
        """Format Tenant model into TenantDetail schema, loading rent history."""
        unit_brief = TenantUnitBrief(
            id=tenant.unit.id,
            name=tenant.unit.name,
            property_name=tenant.unit.property.name,
        )

        # Load non-void rent records for this tenant
        rent_records = rent_repo.list_by_tenant(db, tenant_id=tenant.id, include_void=False)
        rent_history = [
            TenantRentHistoryItem(
                id=rr.id,
                month=rr.month,
                year=rr.year,
                expected_amount_paise=rr.expected_amount_paise,
                total_paid_paise=0,
                due_date=rr.due_date,
                status=calculate_rent_status(
                    due_date=rr.due_date,
                    expected_amount_paise=rr.expected_amount_paise,
                    total_paid_paise=0,
                ),
                payments=[],
            )
            for rr in rent_records
        ]

        return TenantDetail(
            id=tenant.id,
            name=tenant.name,
            phone=tenant.phone,
            email=tenant.email,
            unit=unit_brief,
            move_in_date=tenant.move_in_date,
            move_out_date=tenant.move_out_date,
            security_deposit_paise=tenant.security_deposit_paise,
            status=tenant.status,
            notes=tenant.notes,
            rent_history=rent_history,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
        )

    def create_tenant(
        self,
        db: Session,
        owner_id: UUID,
        data: TenantCreate,
    ) -> TenantDetail:
        """Assign an active tenant to a vacant unit under authenticated owner's property."""
        # Verify unit ownership
        unit = unit_repo.get_by_id(db, unit_id=data.unit_id, owner_id=owner_id)
        if not unit:
            raise NotFoundError(
                detail="Unit not found",
                code="NOT_FOUND",
            )

        # Check unit and property lifecycle
        if unit.archived_at is not None:
            raise AppException(
                status_code=400,
                detail="Cannot assign tenant to an archived unit",
                code="UNIT_ARCHIVED",
            )
        if unit.property.archived_at is not None:
            raise AppException(
                status_code=400,
                detail="Cannot assign tenant to an archived property",
                code="PROPERTY_ARCHIVED",
            )

        # Enforce single active tenant rule at service layer
        active_tenant = tenant_repo.get_active_tenant_by_unit(db, unit_id=data.unit_id)
        if active_tenant:
            raise ConflictError(
                detail=f"Unit {unit.name} already has an active tenant ({active_tenant.name}). Deactivate the current tenant first.",
                code="UNIT_OCCUPIED",
            )

        try:
            tenant = tenant_repo.create(
                db=db,
                unit_id=data.unit_id,
                name=data.name,
                phone=data.phone,
                email=data.email,
                move_in_date=data.move_in_date,
                security_deposit_paise=data.security_deposit_paise,
                notes=data.notes,
            )
        except IntegrityError as exc:
            # Handle concurrent active tenant creation race condition
            raise ConflictError(
                detail=f"Unit {unit.name} already has an active tenant. Deactivate the current tenant first.",
                code="UNIT_OCCUPIED",
            ) from exc

        # Eagerly load relationship data for response formatting
        refreshed = tenant_repo.get_by_id(db, tenant_id=tenant.id, owner_id=owner_id)
        return self._format_tenant_detail(db, refreshed or tenant)

    def get_tenant(
        self,
        db: Session,
        tenant_id: UUID,
        owner_id: UUID,
    ) -> TenantDetail:
        """Get tenant detail by ID with ownership verification."""
        tenant = tenant_repo.get_by_id(db, tenant_id=tenant_id, owner_id=owner_id)
        if not tenant:
            raise NotFoundError(
                detail="Tenant not found",
                code="NOT_FOUND",
            )
        return self._format_tenant_detail(db, tenant)

    def list_tenants(
        self,
        db: Session,
        owner_id: UUID,
        property_id: Optional[UUID] = None,
        status: Optional[str] = "ACTIVE",
        page: int = 1,
        per_page: int = 20,
    ) -> TenantListResponse:
        """List owner's tenants with optional filtering by property and status."""
        if property_id is not None:
            prop = property_repo.get_by_id(db, property_id=property_id, owner_id=owner_id)
            if not prop:
                raise NotFoundError(
                    detail="Property not found",
                    code="NOT_FOUND",
                )

        tenants, total = tenant_repo.list_by_owner(
            db=db,
            owner_id=owner_id,
            property_id=property_id,
            status=status,
            page=page,
            per_page=per_page,
        )

        today = get_today_ist()
        items = []
        for t in tenants:
            # Check if non-void rent record exists for current month
            current_rr = rent_repo.get_by_tenant_month_year(db, tenant_id=t.id, month=today.month, year=today.year)
            current_month_status = None
            if current_rr and not current_rr.is_void:
                current_month_status = calculate_rent_status(
                    due_date=current_rr.due_date,
                    expected_amount_paise=current_rr.expected_amount_paise,
                    total_paid_paise=0,
                )

            items.append(
                TenantListItem(
                    id=t.id,
                    name=t.name,
                    phone=t.phone,
                    email=t.email,
                    unit=TenantUnitBrief(
                        id=t.unit.id,
                        name=t.unit.name,
                        property_name=t.unit.property.name,
                    ),
                    move_in_date=t.move_in_date,
                    status=t.status,
                    current_month_rent_status=current_month_status,
                )
            )

        return TenantListResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
        )

    def update_tenant(
        self,
        db: Session,
        tenant_id: UUID,
        owner_id: UUID,
        data: TenantUpdate,
    ) -> TenantDetail:
        """Update mutable tenant fields; verifies ownership and date consistency."""
        tenant = tenant_repo.get_by_id(db, tenant_id=tenant_id, owner_id=owner_id)
        if not tenant:
            raise NotFoundError(
                detail="Tenant not found",
                code="NOT_FOUND",
            )

        if data.move_in_date is not None and tenant.move_out_date is not None:
            if data.move_in_date > tenant.move_out_date:
                raise AppException(
                    status_code=400,
                    detail="Move-in date cannot be after move-out date",
                    code="INVALID_DATE_RANGE",
                )

        updated_tenant = tenant_repo.update(
            db=db,
            tenant=tenant,
            name=data.name,
            phone=data.phone,
            email=data.email,
            move_in_date=data.move_in_date,
            security_deposit_paise=data.security_deposit_paise,
            notes=data.notes,
        )
        return self._format_tenant_detail(db, updated_tenant)

    def deactivate_tenant(
        self,
        db: Session,
        tenant_id: UUID,
        owner_id: UUID,
        data: Optional[TenantDeactivateRequest] = None,
    ) -> TenantDeactivateResponse:
        """Deactivate tenant (move-out). Unit becomes vacant; history is preserved."""
        tenant = tenant_repo.get_by_id(db, tenant_id=tenant_id, owner_id=owner_id)
        if not tenant:
            raise NotFoundError(
                detail="Tenant not found",
                code="NOT_FOUND",
            )

        if tenant.status == "INACTIVE":
            raise AppException(
                status_code=400,
                detail="Tenant is already inactive",
                code="TENANT_ALREADY_INACTIVE",
            )

        move_out_date = data.move_out_date if (data and data.move_out_date) else date.today()
        if move_out_date < tenant.move_in_date:
            raise AppException(
                status_code=400,
                detail="Move-out date cannot be before move-in date",
                code="INVALID_DATE_RANGE",
            )

        unit_name = tenant.unit.name
        tenant_repo.deactivate(db=db, tenant=tenant, move_out_date=move_out_date)

        return TenantDeactivateResponse(
            message=f"Tenant deactivated. Unit {unit_name} is now vacant.",
            tenant_status="INACTIVE",
            unit_status="VACANT",
        )


tenant_service = TenantService()
