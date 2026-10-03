import calendar
from datetime import date, datetime, timedelta, timezone
import re
from typing import List, Optional
from urllib.parse import quote
from uuid import UUID
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.models.reminder import Reminder
from app.repositories.reminder import reminder_repo
from app.repositories.rent_record import rent_repo
from app.repositories.tenant import tenant_repo
from app.schemas.reminder import (
    ReminderCreateRequest,
    ReminderCreateResponse,
    ReminderListItem,
)
from app.services.rent_status import calculate_rent_status, get_today_ist


def format_reminder_message(
    tenant_name: str,
    remaining_amount_paise: int,
    month: int,
    year: int,
    due_date: date,
    today: date,
    is_partial: bool,
) -> str:
    """Format default polite landlord rent reminder message."""
    month_name = calendar.month_name[month]
    due_day = due_date.day
    formatted_amount = f"{remaining_amount_paise // 100:,}"
    due_date_str = f"{due_day} {month_name}"

    if is_partial:
        if today <= due_date:
            return (
                f"Hi {tenant_name}, your remaining rent balance of ₹{formatted_amount} "
                f"for {month_name} {year} is due on {due_date_str}. "
                f"Please clear the remaining balance by the due date. Thank you."
            )
        else:
            return (
                f"Hi {tenant_name}, your remaining rent balance of ₹{formatted_amount} "
                f"for {month_name} {year} was due on {due_date_str}. "
                f"Please clear the remaining balance at the earliest. Thank you."
            )
    else:
        if today <= due_date:
            return (
                f"Hi {tenant_name}, your monthly rent of ₹{formatted_amount} "
                f"for {month_name} {year} is due on {due_date_str}. "
                f"Please make the payment by the due date. Thank you."
            )
        else:
            return (
                f"Hi {tenant_name}, your monthly rent of ₹{formatted_amount} "
                f"for {month_name} {year} was due on {due_date_str}. "
                f"Please make the payment at the earliest. Thank you."
            )


def generate_whatsapp_url(phone: str, message: str) -> str:
    """Generate WhatsApp deep link with country code and URL-encoded message."""
    clean_digits = re.sub(r"\D", "", phone)
    if len(clean_digits) == 10:
        clean_digits = "91" + clean_digits
    return f"https://wa.me/{clean_digits}?text={quote(message)}"


class ReminderService:
    """Service handling tenant rent reminders, WhatsApp deep-link generation, and cooldown enforcement."""

    def create_rent_reminder(
        self,
        db: Session,
        owner_id: UUID,
        rent_record_id: UUID,
        data: Optional[ReminderCreateRequest] = None,
    ) -> ReminderCreateResponse:
        """Create and record a reminder for an unpaid rent record."""
        # 1. Fetch rent record strictly scoped to authenticated owner
        record = rent_repo.get_by_id(db, rent_record_id=rent_record_id, owner_id=owner_id)
        if not record:
            raise NotFoundError(detail="Rent record not found", code="NOT_FOUND")

        # 2. Reject voided rent records
        if record.is_void:
            raise BadRequestError(detail="Cannot send reminder for a voided rent record", code="RENT_RECORD_VOIDED")

        # 3. Calculate remaining balance (expected - valid payments)
        valid_payments = [p for p in record.payments if not p.is_void]
        valid_paid = sum(p.amount_paise for p in valid_payments)
        remaining_balance = max(0, record.expected_amount_paise - valid_paid)

        if remaining_balance <= 0:
            raise BadRequestError(detail="Cannot send reminder for fully paid rent", code="RENT_ALREADY_PAID")

        # 4. Check status eligibility using centralized engine
        today = get_today_ist()
        status = calculate_rent_status(
            due_date=record.due_date,
            expected_amount_paise=record.expected_amount_paise,
            total_paid_paise=valid_paid,
            today=today,
        )

        if status not in ("DUE", "OVERDUE", "PARTIALLY_PAID"):
            raise BadRequestError(
                detail=f"Reminders are not allowed for rent records with status {status}",
                code="REMINDER_NOT_ELIGIBLE",
            )

        # 5. Verify tenant phone number
        if not record.tenant.phone or not record.tenant.phone.strip():
            raise BadRequestError(detail="Tenant does not have a phone number", code="TENANT_PHONE_REQUIRED")

        channel = data.channel if (data and data.channel) else "WHATSAPP"

        # 6. Enforce 24-hour cooldown
        last_reminder = reminder_repo.get_last_reminder_for_rent_record(
            db=db,
            rent_record_id=record.id,
            channel=channel,
        )
        if last_reminder is not None:
            now = datetime.now(timezone.utc)
            last_sent = last_reminder.sent_at
            if last_sent.tzinfo is None:
                last_sent = last_sent.replace(tzinfo=timezone.utc)
            if (now - last_sent) < timedelta(hours=24):
                raise BadRequestError(
                    detail="Reminder was already sent in the last 24 hours. Cooldown active.",
                    code="REMINDER_COOLDOWN_ACTIVE",
                )

        # 7. Construct message
        if data and data.message and data.message.strip():
            message = data.message.strip()
        else:
            is_partial = (valid_paid > 0)
            message = format_reminder_message(
                tenant_name=record.tenant.name,
                remaining_amount_paise=remaining_balance,
                month=record.month,
                year=record.year,
                due_date=record.due_date,
                today=today,
                is_partial=is_partial,
            )

        # 8. Generate WhatsApp URL
        whatsapp_url = generate_whatsapp_url(phone=record.tenant.phone, message=message)

        # 9. Persist reminder record
        sent_at = datetime.now(timezone.utc)
        reminder = reminder_repo.create(
            db=db,
            tenant_id=record.tenant_id,
            rent_record_id=record.id,
            channel=channel,
            message=message,
            sent_at=sent_at,
        )

        return ReminderCreateResponse(
            id=reminder.id,
            tenant_id=reminder.tenant_id,
            rent_record_id=reminder.rent_record_id,
            whatsapp_url=whatsapp_url,
            message=reminder.message,
            remaining_amount_paise=remaining_balance,
            sent_at=reminder.sent_at,
        )

    def list_reminders_for_rent_record(
        self,
        db: Session,
        owner_id: UUID,
        rent_record_id: UUID,
    ) -> List[ReminderListItem]:
        """List reminder history for a rent record belonging to the authenticated owner."""
        record = rent_repo.get_by_id(db, rent_record_id=rent_record_id, owner_id=owner_id)
        if not record:
            raise NotFoundError(detail="Rent record not found", code="NOT_FOUND")

        reminders = reminder_repo.list_by_rent_record(db, rent_record_id=record.id)
        phone = record.tenant.phone

        return [
            ReminderListItem(
                id=r.id,
                tenant_id=r.tenant_id,
                rent_record_id=r.rent_record_id,
                channel=r.channel,
                message=r.message,
                sent_at=r.sent_at,
                created_at=r.created_at,
                whatsapp_url=generate_whatsapp_url(phone, r.message) if phone else None,
            )
            for r in reminders
        ]

    def create_tenant_reminder(
        self,
        db: Session,
        owner_id: UUID,
        tenant_id: UUID,
        rent_record_id: UUID,
        custom_message: Optional[str] = None,
        channel: str = "WHATSAPP",
    ) -> ReminderCreateResponse:
        """Alias for creating a reminder by tenant ID and rent record ID."""
        tenant = tenant_repo.get_by_id(db, tenant_id=tenant_id, owner_id=owner_id)
        if not tenant:
            raise NotFoundError(detail="Tenant not found", code="NOT_FOUND")

        record = rent_repo.get_by_id(db, rent_record_id=rent_record_id, owner_id=owner_id)
        if not record or record.tenant_id != tenant_id:
            raise NotFoundError(detail="Rent record not found for tenant", code="NOT_FOUND")

        data = ReminderCreateRequest(message=custom_message, channel=channel)
        return self.create_rent_reminder(
            db=db,
            owner_id=owner_id,
            rent_record_id=rent_record_id,
            data=data,
        )

    def list_reminders_for_tenant(
        self,
        db: Session,
        owner_id: UUID,
        tenant_id: UUID,
    ) -> List[ReminderListItem]:
        """List all reminder history for a tenant belonging to the authenticated owner."""
        tenant = tenant_repo.get_by_id(db, tenant_id=tenant_id, owner_id=owner_id)
        if not tenant:
            raise NotFoundError(detail="Tenant not found", code="NOT_FOUND")

        reminders = reminder_repo.list_by_tenant(db, tenant_id=tenant.id)
        phone = tenant.phone

        return [
            ReminderListItem(
                id=r.id,
                tenant_id=r.tenant_id,
                rent_record_id=r.rent_record_id,
                channel=r.channel,
                message=r.message,
                sent_at=r.sent_at,
                created_at=r.created_at,
                whatsapp_url=generate_whatsapp_url(phone, r.message) if phone else None,
            )
            for r in reminders
        ]


reminder_service = ReminderService()
