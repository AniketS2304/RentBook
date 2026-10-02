import uuid
from sqlalchemy import DateTime, ForeignKey, Index, String, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rent_record_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("rent_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sent_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    channel: Mapped[str] = mapped_column(
        String(20),
        default="WHATSAPP",
        server_default=text("'WHATSAPP'"),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="reminders")
    rent_record = relationship("RentRecord", back_populates="reminders")

    __table_args__ = (
        Index("idx_reminders_tenant_id", "tenant_id"),
        Index("idx_reminders_rent_record_id", "rent_record_id"),
    )
