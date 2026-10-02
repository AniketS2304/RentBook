import uuid
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    unit_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    monthly_rent_paise: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    rent_due_day: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    archived_at: Mapped[DateTime | None] = mapped_column(
        DateTime(timezone=True),
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
    property = relationship("Property", back_populates="units")
    tenants = relationship("Tenant", back_populates="unit", cascade="all, delete-orphan")
    rent_records = relationship("RentRecord", back_populates="unit", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "unit_type IN ('FLAT', 'ROOM', 'SHOP', 'OTHER')",
            name="chk_units_unit_type",
        ),
        CheckConstraint(
            "monthly_rent_paise > 0",
            name="chk_units_monthly_rent_positive",
        ),
        CheckConstraint(
            "rent_due_day >= 1 AND rent_due_day <= 28",
            name="chk_units_rent_due_day",
        ),
        Index("idx_units_property_id", "property_id"),
        Index(
            "uq_units_property_name",
            "property_id",
            "name",
            unique=True,
            postgresql_where=(archived_at.is_(None)),
            sqlite_where=(archived_at.is_(None)),
        ),
    )
