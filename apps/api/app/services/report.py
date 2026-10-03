from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.exceptions import AppException, NotFoundError
from app.repositories.property import property_repo
from app.repositories.report import report_repo
from app.schemas.report import (
    MonthlyReportPaymentBreakdown,
    MonthlyReportResponse,
    MonthlyReportSummary,
    OutstandingSummary,
    OutstandingTenantItem,
)
from app.services.rent import rent_service
from app.services.rent_status import calculate_rent_status, get_today_ist


class ReportService:
    """Service handling read-only monthly collection reports, status metrics, and outstanding tenant lists."""

    def get_monthly_report(
        self,
        db: Session,
        owner_id: UUID,
        month: Optional[int] = None,
        year: Optional[int] = None,
        property_id: Optional[UUID] = None,
    ) -> MonthlyReportResponse:
        """Generate read-only monthly report with financial totals, status counts, payment breakdown, and outstanding balances."""
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

        # 1. Trigger on-demand rent generation for selected month/year
        records = rent_service.generate_rent_records_for_month(
            db=db,
            owner_id=owner_id,
            month=target_month,
            year=target_year,
            property_id=property_id,
        )

        # 2. Query payment breakdown via SQL aggregation
        breakdown_dict = report_repo.get_payment_breakdown(
            db=db,
            owner_id=owner_id,
            month=target_month,
            year=target_year,
            property_id=property_id,
        )
        payment_breakdown = MonthlyReportPaymentBreakdown(
            cash_paise=breakdown_dict.get("CASH", 0),
            upi_paise=breakdown_dict.get("UPI", 0),
            bank_transfer_paise=breakdown_dict.get("BANK_TRANSFER", 0),
            other_paise=breakdown_dict.get("OTHER", 0),
        )
        total_collected = (
            payment_breakdown.cash_paise
            + payment_breakdown.upi_paise
            + payment_breakdown.bank_transfer_paise
            + payment_breakdown.other_paise
        )

        # 3. Calculate status counts and identify outstanding tenants
        total_expected = 0
        paid_count = 0
        partially_paid_count = 0
        due_count = 0
        overdue_count = 0

        outstanding_tenants: List[OutstandingTenantItem] = []

        for r in records:
            if r.is_void:
                continue

            total_expected += r.expected_amount_paise
            valid_payments = [p for p in r.payments if not p.is_void]
            valid_paid = sum(p.amount_paise for p in valid_payments)

            # Centralized status engine evaluation
            status = calculate_rent_status(
                due_date=r.due_date,
                expected_amount_paise=r.expected_amount_paise,
                total_paid_paise=valid_paid,
                today=today,
            )

            if status == "PAID":
                paid_count += 1
            elif status == "PARTIALLY_PAID":
                partially_paid_count += 1
            elif status == "DUE":
                due_count += 1
            elif status == "OVERDUE":
                overdue_count += 1

            remaining = max(0, r.expected_amount_paise - valid_paid)

            # Outstanding debt: remaining > 0 and status in (PARTIALLY_PAID, DUE, OVERDUE)
            # Exclude future PENDING rent from outstanding debt
            if remaining > 0 and status in ("PARTIALLY_PAID", "DUE", "OVERDUE"):
                days_overdue = max(0, (today - r.due_date).days)
                outstanding_tenants.append(
                    OutstandingTenantItem(
                        tenant_id=r.tenant_id,
                        tenant_name=r.tenant.name,
                        property_id=r.unit.property.id,
                        property_name=r.unit.property.name,
                        unit_id=r.unit.id,
                        unit_name=r.unit.name,
                        rent_record_id=r.id,
                        expected_amount_paise=r.expected_amount_paise,
                        paid_amount_paise=valid_paid,
                        remaining_amount_paise=remaining,
                        status=status,
                        due_date=r.due_date,
                        days_overdue=days_overdue,
                    )
                )

        total_pending = max(0, total_expected - total_collected)

        # Sort outstanding tenants by most overdue first, then due date
        outstanding_tenants.sort(
            key=lambda t: (-t.days_overdue, t.due_date, t.property_name, t.unit_name)
        )

        outstanding_summary = OutstandingSummary(
            total_count=len(outstanding_tenants),
            total_amount_paise=sum(t.remaining_amount_paise for t in outstanding_tenants),
            tenants=outstanding_tenants,
        )

        summary = MonthlyReportSummary(
            total_expected_paise=total_expected,
            total_collected_paise=total_collected,
            total_pending_paise=total_pending,
            paid_count=paid_count,
            partially_paid_count=partially_paid_count,
            due_count=due_count,
            overdue_count=overdue_count,
        )

        return MonthlyReportResponse(
            month=target_month,
            year=target_year,
            summary=summary,
            payment_breakdown=payment_breakdown,
            outstanding=outstanding_summary,
        )


report_service = ReportService()
