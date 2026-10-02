import uuid
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RentRecord(Base):
    __tablename__ = "rent_records"

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
    unit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    month: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    expected_amount_paise: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    due_date: Mapped[Date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_void: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("false"),
        nullable=False,
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    tenant = relationship("Tenant", back_populates="rent_records")
    unit = relationship("Unit", back_populates="rent_records")
    payments = relationship("Payment", back_populates="rent_record", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="rent_record", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "month >= 1 AND month <= 12",
            name="chk_rent_records_month",
        ),
        CheckConstraint(
            "year >= 2020 AND year <= 2100",
            name="chk_rent_records_year",
        ),
        CheckConstraint(
            "expected_amount_paise > 0",
            name="chk_rent_records_expected_amount_positive",
        ),
        UniqueConstraint(
            "tenant_id",
            "month",
            "year",
            name="uq_rent_records_tenant_month",
        ),
        Index("idx_rent_records_tenant_id", "tenant_id"),
        Index("idx_rent_records_unit_id", "unit_id"),
        Index("idx_rent_records_month_year", "month", "year"),
        Index("idx_rent_records_due_date", "due_date"),
    )
