import calendar
from datetime import date
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import AppException, NotFoundError
from app.models.property import Property
from app.models.rent_record import RentRecord
from app.models.unit import Unit
from app.repositories.property import property_repo
from app.repositories.rent_record import rent_repo
from app.schemas.rent import (
    RentListResponse,
    RentRecordDetail,
    RentRecordListItem,
    RentRecordPaymentItem,
    RentRecordUpdate,
    RentRecordVoidRequest,
    RentRecordVoidResponse,
    RentSummary,
)
from app.services.rent_status import calculate_rent_status, get_today_ist


class RentService:
    """Business logic for on-demand rent generation, rent records, and editing."""

    def _format_rent_record_detail(self, record: RentRecord) -> RentRecordDetail:
        """Format RentRecord into RentRecordDetail with computed status and non-void payments."""
        valid_payments = [p for p in record.payments if not p.is_void]
        total_paid = sum(p.amount_paise for p in valid_payments)
        status = calculate_rent_status(
            due_date=record.due_date,
            expected_amount_paise=record.expected_amount_paise,
            total_paid_paise=total_paid,
        )
        formatted_payments = [
            RentRecordPaymentItem(
                id=p.id,
                amount_paise=p.amount_paise,
                payment_method=p.payment_method,
                paid_date=p.paid_date,
                notes=p.notes,
            )
            for p in sorted(valid_payments, key=lambda x: (x.paid_date, x.created_at))
        ]
        return RentRecordDetail(
            id=record.id,
            tenant_id=record.tenant_id,
            tenant_name=record.tenant.name,
            unit_id=record.unit_id,
            unit_name=record.unit.name,
            property_id=record.unit.property_id,
            property_name=record.unit.property.name,
            month=record.month,
            year=record.year,
            expected_amount_paise=record.expected_amount_paise,
            total_paid_paise=total_paid,
            due_date=record.due_date,
            status=status,
            notes=record.notes,
            is_void=record.is_void,
            payments=formatted_payments,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _format_rent_record_list_item(self, record: RentRecord) -> RentRecordListItem:
        """Format RentRecord into RentRecordListItem for monthly list."""
        valid_payments = [p for p in record.payments if not p.is_void]
        total_paid = sum(p.amount_paise for p in valid_payments)
        status = calculate_rent_status(
            due_date=record.due_date,
            expected_amount_paise=record.expected_amount_paise,
            total_paid_paise=total_paid,
        )
        # Check last reminder timestamp if any
        last_reminder_at = None
        if record.reminders:
            sorted_reminders = sorted(record.reminders, key=lambda r: r.sent_at, reverse=True)
            last_reminder_at = sorted_reminders[0].sent_at

        return RentRecordListItem(
            id=record.id,
            tenant_name=record.tenant.name,
            unit_name=record.unit.name,
            property_name=record.unit.property.name,
            expected_amount_paise=record.expected_amount_paise,
            total_paid_paise=total_paid,
            due_date=record.due_date,
            status=status,
            last_reminder_at=last_reminder_at,
        )

    def generate_rent_records_for_month(
        self,
        db: Session,
        owner_id: UUID,
        month: int,
        year: int,
        property_id: Optional[UUID] = None,
    ) -> List[RentRecord]:
        """On-demand rent record generation for eligible tenants in given month/year."""
        if not (1 <= month <= 12):
            raise AppException(status_code=400, detail="Month must be between 1 and 12", code="INVALID_MONTH")
        if not (2020 <= year <= 2100):
            raise AppException(status_code=400, detail="Year must be between 2020 and 2100", code="INVALID_YEAR")

        if property_id is not None:
            prop = property_repo.get_by_id(db, property_id=property_id, owner_id=owner_id)
            if not prop:
                raise NotFoundError(detail="Property not found", code="NOT_FOUND")

        # Determine start and end of the target month
        month_start = date(year, month, 1)
        _, last_day = calendar.monthrange(year, month)
        month_end = date(year, month, last_day)

        # Query all active units of active properties belonging to this owner
        stmt = (
            select(Unit)
            .join(Property, Unit.property_id == Property.id)
            .options(
                joinedload(Unit.property),
                joinedload(Unit.tenants),
            )
            .where(
                Property.owner_id == owner_id,
                Property.archived_at.is_(None),  # BR-PROP-04: archived properties generate no new records
                Unit.archived_at.is_(None),      # Archived units generate no new records
            )
        )
        if property_id is not None:
            stmt = stmt.where(Unit.property_id == property_id)

        units = list(db.scalars(stmt).unique().all())

        for unit in units:
            for tenant in unit.tenants:
                # Eligibility check per BR-RENT-03 & ADR-002:
                # 1. move_in_date must be on or before the end of the viewed month
                if tenant.move_in_date > month_end:
                    continue

                # 2. If inactive, tenant must NOT have moved out before the start of this month
                if tenant.status == "INACTIVE":
                    if tenant.move_out_date is None or tenant.move_out_date < month_start:
                        continue

                # 3. Check if rent record already exists (avoid duplicates per EC-05 and ADR-002)
                existing = rent_repo.get_by_tenant_month_year(db, tenant_id=tenant.id, month=month, year=year)
                if existing is None:
                    # Snapshot the unit's current monthly rent and compute due date
                    due_day = min(unit.rent_due_day, last_day)
                    due_date = date(year, month, due_day)
                    rent_repo.create(
                        db=db,
                        tenant_id=tenant.id,
                        unit_id=unit.id,
                        month=month,
                        year=year,
                        expected_amount_paise=unit.monthly_rent_paise,
                        due_date=due_date,
                    )

        # Return all non-void records for this month
        return rent_repo.list_by_month(
            db=db,
            owner_id=owner_id,
            month=month,
            year=year,
            property_id=property_id,
            include_void=False,
        )

    def list_monthly_rent(
        self,
        db: Session,
        owner_id: UUID,
        month: Optional[int] = None,
        year: Optional[int] = None,
        property_id: Optional[UUID] = None,
        status: Optional[str] = None,
    ) -> RentListResponse:
        """List rent records for a specific month with summary metrics and on-demand generation."""
        today = get_today_ist()
        target_month = month if month is not None else today.month
        target_year = year if year is not None else today.year

        if not (1 <= target_month <= 12):
            raise AppException(status_code=400, detail="Month must be between 1 and 12", code="INVALID_MONTH")
        if not (2020 <= target_year <= 2100):
            raise AppException(status_code=400, detail="Year must be between 2020 and 2100", code="INVALID_YEAR")

        if property_id is not None:
            prop = property_repo.get_by_id(db, property_id=property_id, owner_id=owner_id)
            if not prop:
                raise NotFoundError(detail="Property not found", code="NOT_FOUND")

        # Trigger on-demand generation for eligible tenants
        records = self.generate_rent_records_for_month(
            db=db,
            owner_id=owner_id,
            month=target_month,
            year=target_year,
            property_id=property_id,
        )

        # Compute summary aggregations across ALL non-void records for this month
        total_expected = sum(r.expected_amount_paise for r in records)
        total_collected = sum(
            sum(p.amount_paise for p in r.payments if not p.is_void)
            for r in records
        )
        total_pending = max(0, total_expected - total_collected)

        paid_count = 0
        due_count = 0
        overdue_count = 0

        formatted_items: List[RentRecordListItem] = []
        for r in records:
            item = self._format_rent_record_list_item(r)
            if item.status == "PAID":
                paid_count += 1
            elif item.status == "DUE":
                due_count += 1
            elif item.status == "OVERDUE":
                overdue_count += 1

            # Filter items if status filter is specified
            if status is None or item.status == status:
                formatted_items.append(item)

        summary = RentSummary(
            total_expected_paise=total_expected,
            total_collected_paise=total_collected,
            total_pending_paise=total_pending,
            paid_count=paid_count,
            due_count=due_count,
            overdue_count=overdue_count,
        )

        return RentListResponse(
            month=target_month,
            year=target_year,
            summary=summary,
            items=formatted_items,
        )

    def get_rent_record(
        self,
        db: Session,
        rent_record_id: UUID,
        owner_id: UUID,
    ) -> RentRecordDetail:
        """Fetch a specific rent record by ID with ownership verification."""
        record = rent_repo.get_by_id(db, rent_record_id=rent_record_id, owner_id=owner_id)
        if not record:
            raise NotFoundError(detail="Rent record not found", code="NOT_FOUND")
        return self._format_rent_record_detail(record)

    def update_rent_record(
        self,
        db: Session,
        rent_record_id: UUID,
        owner_id: UUID,
        data: RentRecordUpdate,
    ) -> RentRecordDetail:
        """Edit expected rent amount or notes on an existing active rent record."""
        record = rent_repo.get_by_id(db, rent_record_id=rent_record_id, owner_id=owner_id)
        if not record:
            raise NotFoundError(detail="Rent record not found", code="NOT_FOUND")

        if record.is_void:
            raise AppException(status_code=400, detail="Cannot edit a voided rent record", code="RENT_RECORD_VOIDED")

        updated = rent_repo.update(
            db=db,
            record=record,
            expected_amount_paise=data.expected_amount_paise,
            notes=data.notes,
        )
        return self._format_rent_record_detail(updated)

    def void_rent_record(
        self,
        db: Session,
        rent_record_id: UUID,
        owner_id: UUID,
        data: Optional[RentRecordVoidRequest] = None,
    ) -> RentRecordVoidResponse:
        """Void a rent record (soft cancellation). Excludes it from active rent calculations."""
        record = rent_repo.get_by_id(db, rent_record_id=rent_record_id, owner_id=owner_id)
        if not record:
            raise NotFoundError(detail="Rent record not found", code="NOT_FOUND")

        if record.is_void:
            raise AppException(status_code=400, detail="Rent record is already voided", code="RENT_RECORD_ALREADY_VOIDED")

        reason = data.reason if data else None
        rent_repo.void(db, record=record, reason=reason)

        return RentRecordVoidResponse(
            message="Rent record voided successfully",
            id=record.id,
            is_void=True,
        )


rent_service = RentService()
