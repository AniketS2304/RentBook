import uuid
from sqlalchemy import (
    Boolean,
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


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    rent_record_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("rent_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    amount_paise: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    payment_method: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    paid_date: Mapped[Date] = mapped_column(
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
    rent_record = relationship("RentRecord", back_populates="payments")

    __table_args__ = (
        CheckConstraint(
            "amount_paise > 0",
            name="chk_payments_amount_positive",
        ),
        CheckConstraint(
            "payment_method IN ('CASH', 'UPI', 'BANK_TRANSFER', 'OTHER')",
            name="chk_payments_payment_method",
        ),
        Index("idx_payments_rent_record_id", "rent_record_id"),
        Index("idx_payments_paid_date", "paid_date"),
    )
