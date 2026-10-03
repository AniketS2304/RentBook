from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.exceptions import AppException, NotFoundError
from app.repositories.dashboard import dashboard_repo
from app.repositories.property import property_repo
from app.schemas.dashboard import (
    DashboardDueItem,
    DashboardOverdueItem,
    DashboardRecentPaymentItem,
    DashboardSummaryBreakdown,
    DashboardSummaryResponse,
)
from app.services.rent import rent_service
from app.services.rent_status import calculate_rent_status, get_today_ist



class DashboardService:
    """Service handling dashboard aggregation metrics, unit counts, and actionable lists."""

    def get_dashboard_summary(
        self,
        db: Session,
        owner_id: UUID,
        month: Optional[int] = None,
        year: Optional[int] = None,
        property_id: Optional[UUID] = None,
    ) -> DashboardSummaryResponse:
        """Fetch dashboard summary metrics for the owner, triggering on-demand rent generation."""
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

        # 1. Trigger on-demand rent generation for target month and retrieve active rent records
        records = rent_service.generate_rent_records_for_month(
            db=db,
            owner_id=owner_id,
            month=target_month,
            year=target_year,
            property_id=property_id,
        )

        total_expected_paise = 0
        total_collected_paise = 0
        paid_count = 0
        due_count = 0
        overdue_count = 0

        todays_due: List[DashboardDueItem] = []
        overdue_list: List[DashboardOverdueItem] = []

        for r in records:
            if r.is_void:
                continue

            total_expected_paise += r.expected_amount_paise
            valid_paid = sum(p.amount_paise for p in r.payments if not p.is_void)
            total_collected_paise += valid_paid

            # Centralized status engine computation
            status = calculate_rent_status(
                due_date=r.due_date,
                expected_amount_paise=r.expected_amount_paise,
                total_paid_paise=valid_paid,
                today=today,
            )

            if status == "PAID":
                paid_count += 1
            elif status == "DUE":
                due_count += 1
            elif status == "OVERDUE":
                overdue_count += 1

            remaining_balance = max(0, r.expected_amount_paise - valid_paid)

            # Actionable: Today's Due (due today and not fully settled)
            if r.due_date == today and valid_paid < r.expected_amount_paise:
                todays_due.append(
                    DashboardDueItem(
                        tenant_name=r.tenant.name,
                        unit_name=r.unit.name,
                        property_name=r.unit.property.name,
                        amount_paise=remaining_balance,
                        rent_record_id=r.id,
                        tenant_id=r.tenant.id,
                        tenant_phone=r.tenant.phone,
                        due_date=r.due_date,
                    )
                )

            # Actionable: Overdue (past due date and not fully settled)
            if today > r.due_date and valid_paid < r.expected_amount_paise:
                days_overdue = (today - r.due_date).days
                overdue_list.append(
                    DashboardOverdueItem(
                        tenant_name=r.tenant.name,
                        unit_name=r.unit.name,
                        property_name=r.unit.property.name,
                        amount_paise=remaining_balance,
                        due_date=r.due_date,
                        rent_record_id=r.id,
                        tenant_id=r.tenant.id,
                        tenant_phone=r.tenant.phone,
                        days_overdue=days_overdue,
                    )
                )

        total_pending_paise = max(0, total_expected_paise - total_collected_paise)

        # Order actionable lists logically
        todays_due.sort(key=lambda x: (x.property_name, x.unit_name))
        overdue_list.sort(key=lambda x: (x.due_date, x.property_name, x.unit_name))

        # 2. Query unit occupancy counts
        total_units, occupied_units, vacant_units = dashboard_repo.get_unit_counts(
            db=db,
            owner_id=owner_id,
            property_id=property_id,
        )

        # 3. Query recent non-void payments
        recent_payments = dashboard_repo.get_recent_payments(
            db=db,
            owner_id=owner_id,
            property_id=property_id,
            limit=5,
        )
        recent_payment_items = [
            DashboardRecentPaymentItem(
                id=p.id,
                tenant_name=p.rent_record.tenant.name,
                unit_name=p.rent_record.unit.name,
                property_name=p.rent_record.unit.property.name,
                amount_paise=p.amount_paise,
                payment_method=p.payment_method,
                paid_date=p.paid_date,
            )
            for p in recent_payments
        ]

        summary_breakdown = DashboardSummaryBreakdown(
            total_expected_paise=total_expected_paise,
            total_collected_paise=total_collected_paise,
            total_pending_paise=total_pending_paise,
            paid_count=paid_count,
            due_count=due_count,
            overdue_count=overdue_count,
        )

        return DashboardSummaryResponse(
            month=target_month,
            year=target_year,
            total_expected_paise=total_expected_paise,
            total_collected_paise=total_collected_paise,
            total_pending_paise=total_pending_paise,
            paid_count=paid_count,
            due_count=due_count,
            overdue_count=overdue_count,
            total_units=total_units,
            occupied_units=occupied_units,
            vacant_units=vacant_units,
            todays_due=todays_due,
            overdue_list=overdue_list,
            recent_payments=recent_payment_items,
            summary=summary_breakdown,
        )


dashboard_service = DashboardService()
