import uuid
from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("units.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    phone: Mapped[str] = mapped_column(
        String(15),
        nullable=False,
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    move_in_date: Mapped[Date] = mapped_column(
        Date,
        nullable=False,
    )
    move_out_date: Mapped[Date | None] = mapped_column(
        Date,
        nullable=True,
    )
    security_deposit_paise: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="ACTIVE",
        server_default=text("'ACTIVE'"),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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
    unit = relationship("Unit", back_populates="tenants")
    rent_records = relationship("RentRecord", back_populates="tenant", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="tenant", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')",
            name="chk_tenants_status",
        ),
        Index("idx_tenants_unit_id", "unit_id"),
        Index("idx_tenants_unit_active", "unit_id", "status"),
        Index("idx_tenants_status", "status"),
        Index(
            "uq_tenants_unit_active",
            "unit_id",
            unique=True,
            postgresql_where=(status == "ACTIVE"),
            sqlite_where=(status == "ACTIVE"),
        ),
    )
