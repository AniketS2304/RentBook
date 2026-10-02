"""Initial database schema for RentBook

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-02 19:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=15), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_users_email", "users", ["email"], unique=True)

    # 2. properties
    op.create_table(
        "properties",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_properties_owner_id", "properties", ["owner_id"])
    op.create_index("idx_properties_owner_active", "properties", ["owner_id", "archived_at"])
    op.create_index(
        "uq_properties_owner_name",
        "properties",
        ["owner_id", "name"],
        unique=True,
        postgresql_where=sa.text("archived_at IS NULL"),
    )

    # 3. units
    op.create_table(
        "units",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("property_id", sa.Uuid(), sa.ForeignKey("properties.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("unit_type", sa.String(length=20), nullable=False),
        sa.Column("monthly_rent_paise", sa.Integer(), nullable=False),
        sa.Column("rent_due_day", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("unit_type IN ('FLAT', 'ROOM', 'SHOP', 'OTHER')", name="chk_units_unit_type"),
        sa.CheckConstraint("monthly_rent_paise > 0", name="chk_units_monthly_rent_positive"),
        sa.CheckConstraint("rent_due_day >= 1 AND rent_due_day <= 28", name="chk_units_rent_due_day"),
    )
    op.create_index("idx_units_property_id", "units", ["property_id"])
    op.create_index(
        "uq_units_property_name",
        "units",
        ["property_id", "name"],
        unique=True,
        postgresql_where=sa.text("archived_at IS NULL"),
    )

    # 4. tenants
    op.create_table(
        "tenants",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("unit_id", sa.Uuid(), sa.ForeignKey("units.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=15), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("move_in_date", sa.Date(), nullable=False),
        sa.Column("move_out_date", sa.Date(), nullable=True),
        sa.Column("security_deposit_paise", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("status", sa.String(length=20), server_default=sa.text("'ACTIVE'"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status IN ('ACTIVE', 'INACTIVE')", name="chk_tenants_status"),
    )
    op.create_index("idx_tenants_unit_id", "tenants", ["unit_id"])
    op.create_index("idx_tenants_unit_active", "tenants", ["unit_id", "status"])
    op.create_index("idx_tenants_status", "tenants", ["status"])
    op.create_index(
        "uq_tenants_unit_active",
        "tenants",
        ["unit_id"],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )

    # 5. rent_records
    op.create_table(
        "rent_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("unit_id", sa.Uuid(), sa.ForeignKey("units.id", ondelete="CASCADE"), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("expected_amount_paise", sa.Integer(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_void", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("month >= 1 AND month <= 12", name="chk_rent_records_month"),
        sa.CheckConstraint("year >= 2020 AND year <= 2100", name="chk_rent_records_year"),
        sa.CheckConstraint("expected_amount_paise > 0", name="chk_rent_records_expected_amount_positive"),
        sa.UniqueConstraint("tenant_id", "month", "year", name="uq_rent_records_tenant_month"),
    )
    op.create_index("idx_rent_records_tenant_id", "rent_records", ["tenant_id"])
    op.create_index("idx_rent_records_unit_id", "rent_records", ["unit_id"])
    op.create_index("idx_rent_records_month_year", "rent_records", ["month", "year"])
    op.create_index("idx_rent_records_due_date", "rent_records", ["due_date"])

    # 6. payments
    op.create_table(
        "payments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("rent_record_id", sa.Uuid(), sa.ForeignKey("rent_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount_paise", sa.Integer(), nullable=False),
        sa.Column("payment_method", sa.String(length=20), nullable=False),
        sa.Column("paid_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_void", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("amount_paise > 0", name="chk_payments_amount_positive"),
        sa.CheckConstraint("payment_method IN ('CASH', 'UPI', 'BANK_TRANSFER', 'OTHER')", name="chk_payments_payment_method"),
    )
    op.create_index("idx_payments_rent_record_id", "payments", ["rent_record_id"])
    op.create_index("idx_payments_paid_date", "payments", ["paid_date"])

    # 7. reminders
    op.create_table(
        "reminders",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rent_record_id", sa.Uuid(), sa.ForeignKey("rent_records.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("channel", sa.String(length=20), server_default=sa.text("'WHATSAPP'"), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_reminders_tenant_id", "reminders", ["tenant_id"])
    op.create_index("idx_reminders_rent_record_id", "reminders", ["rent_record_id"])


def downgrade() -> None:
    op.drop_table("reminders")
    op.drop_table("payments")
    op.drop_table("rent_records")
    op.drop_table("tenants")
    op.drop_table("units")
    op.drop_table("properties")
    op.drop_table("users")
