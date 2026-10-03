from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.reminder import Reminder


class ReminderRepository:
    """Repository for Reminder data access and history."""

    def get_last_reminder_for_rent_record(
        self,
        db: Session,
        rent_record_id: UUID,
        channel: str = "WHATSAPP",
    ) -> Optional[Reminder]:
        """Fetch the most recent reminder for a rent record by channel to enforce cooldown."""
        stmt = (
            select(Reminder)
            .where(
                Reminder.rent_record_id == rent_record_id,
                Reminder.channel == channel,
            )
            .order_by(Reminder.sent_at.desc(), Reminder.created_at.desc())
            .limit(1)
        )
        return db.scalar(stmt)

    def create(
        self,
        db: Session,
        tenant_id: UUID,
        rent_record_id: UUID,
        channel: str,
        message: str,
        sent_at: Optional[datetime] = None,
    ) -> Reminder:
        """Create and persist a new reminder record."""
        effective_sent_at = sent_at or datetime.now(timezone.utc)
        reminder = Reminder(
            tenant_id=tenant_id,
            rent_record_id=rent_record_id,
            channel=channel,
            message=message.strip(),
            sent_at=effective_sent_at,
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        return reminder

    def list_by_rent_record(
        self,
        db: Session,
        rent_record_id: UUID,
    ) -> List[Reminder]:
        """List all reminders recorded for a rent record, newest first."""
        stmt = (
            select(Reminder)
            .where(Reminder.rent_record_id == rent_record_id)
            .order_by(Reminder.sent_at.desc(), Reminder.created_at.desc())
        )
        return list(db.scalars(stmt).all())

    def list_by_tenant(
        self,
        db: Session,
        tenant_id: UUID,
    ) -> List[Reminder]:
        """List all reminders recorded for a tenant, newest first."""
        stmt = (
            select(Reminder)
            .where(Reminder.tenant_id == tenant_id)
            .order_by(Reminder.sent_at.desc(), Reminder.created_at.desc())
        )
        return list(db.scalars(stmt).all())


reminder_repo = ReminderRepository()
