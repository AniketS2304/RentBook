from datetime import date
import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.property import Property
from app.models.unit import Unit
from app.models.tenant import Tenant
from app.models.rent_record import RentRecord
from app.models.payment import Payment


def test_money_stored_as_integer_paise(db: Session, owner_a):
    """Monetary values are stored as integer paise (e.g., Rs 8,000 = 800000 paise)."""
    prop = Property(id=uuid.uuid4(), owner_id=owner_a["owner"].id, name="Test Residency")
    db.add(prop)
    db.commit()

    # Rs 8,000 = 800,000 paise
    expected_paise = 800000
    unit = Unit(
        id=uuid.uuid4(),
        property_id=prop.id,
        name="101",
        unit_type="FLAT",
        monthly_rent_paise=expected_paise,
        rent_due_day=5,
    )
    db.add(unit)
    db.commit()
    db.refresh(unit)

    assert isinstance(unit.monthly_rent_paise, int)
    assert unit.monthly_rent_paise == 800000


def test_unit_rent_due_day_constraint(db: Session, owner_a):
    """rent_due_day must be between 1 and 28; outside this range violates constraint."""
    prop = Property(id=uuid.uuid4(), owner_id=owner_a["owner"].id, name="Constraint Property")
    db.add(prop)
    db.commit()

    # Invalid due day: 29
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            unit_invalid = Unit(
                id=uuid.uuid4(),
                property_id=prop.id,
                name="Invalid Unit 29",
                unit_type="FLAT",
                monthly_rent_paise=500000,
                rent_due_day=29,
            )
            db.add(unit_invalid)
            db.flush()

    # Invalid due day: 0
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            unit_invalid_zero = Unit(
                id=uuid.uuid4(),
                property_id=prop.id,
                name="Invalid Unit 0",
                unit_type="FLAT",
                monthly_rent_paise=500000,
                rent_due_day=0,
            )
            db.add(unit_invalid_zero)
            db.flush()


def test_unit_monthly_rent_positive_constraint(db: Session, owner_a):
    """monthly_rent_paise must be > 0."""
    prop = Property(id=uuid.uuid4(), owner_id=owner_a["owner"].id, name="Rent Check Property")
    db.add(prop)
    db.commit()

    with pytest.raises(IntegrityError):
        with db.begin_nested():
            unit_zero_rent = Unit(
                id=uuid.uuid4(),
                property_id=prop.id,
                name="Zero Rent",
                unit_type="FLAT",
                monthly_rent_paise=0,
                rent_due_day=10,
            )
            db.add(unit_zero_rent)
            db.flush()


def test_rent_record_duplicate_month_constraint(db: Session, owner_a):
    """Unique constraint uq_rent_records_tenant_month prevents duplicate monthly records."""
    prop = Property(id=uuid.uuid4(), owner_id=owner_a["owner"].id, name="Dup Test Property")
    db.add(prop)
    db.commit()

    unit = Unit(
        id=uuid.uuid4(),
        property_id=prop.id,
        name="202",
        unit_type="FLAT",
        monthly_rent_paise=1000000,
        rent_due_day=1,
    )
    db.add(unit)
    db.commit()

    tenant = Tenant(
        id=uuid.uuid4(),
        unit_id=unit.id,
        name="Ramesh Sharma",
        phone="9876543210",
        move_in_date=date(2026, 1, 1),
    )
    db.add(tenant)
    db.commit()

    # First record for October 2026
    r1 = RentRecord(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        unit_id=unit.id,
        month=10,
        year=2026,
        expected_amount_paise=1000000,
        due_date=date(2026, 10, 1),
    )
    db.add(r1)
    db.commit()

    # Second record for same tenant and month/year
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            r2 = RentRecord(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                unit_id=unit.id,
                month=10,
                year=2026,
                expected_amount_paise=1000000,
                due_date=date(2026, 10, 1),
            )
            db.add(r2)
            db.flush()


def test_soft_delete_flags_present(db: Session, owner_a):
    """Rent records and payments have is_void flag, never hard-deleted."""
    prop = Property(id=uuid.uuid4(), owner_id=owner_a["owner"].id, name="Void Prop")
    db.add(prop)
    db.commit()

    unit = Unit(
        id=uuid.uuid4(),
        property_id=prop.id,
        name="303",
        unit_type="ROOM",
        monthly_rent_paise=400000,
        rent_due_day=5,
    )
    db.add(unit)
    db.commit()

    tenant = Tenant(
        id=uuid.uuid4(),
        unit_id=unit.id,
        name="Suresh Patel",
        phone="9876543210",
        move_in_date=date(2026, 2, 1),
    )
    db.add(tenant)
    db.commit()

    rent = RentRecord(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        unit_id=unit.id,
        month=10,
        year=2026,
        expected_amount_paise=400000,
        due_date=date(2026, 10, 5),
        is_void=False,
    )
    db.add(rent)
    db.commit()

    pay = Payment(
        id=uuid.uuid4(),
        rent_record_id=rent.id,
        amount_paise=400000,
        payment_method="UPI",
        paid_date=date(2026, 10, 5),
        is_void=False,
    )
    db.add(pay)
    db.commit()

    # Soft void payment
    pay.is_void = True
    db.commit()
    db.refresh(pay)
    assert pay.is_void is True


def test_unit_type_constraint(db: Session, owner_a):
    """unit_type must be in ('FLAT', 'ROOM', 'SHOP', 'OTHER')."""
    prop = Property(id=uuid.uuid4(), owner_id=owner_a["owner"].id, name="Unit Type Prop")
    db.add(prop)
    db.commit()

    with pytest.raises(IntegrityError):
        with db.begin_nested():
            unit = Unit(
                id=uuid.uuid4(),
                property_id=prop.id,
                name="Invalid Type",
                unit_type="PENTHOUSE",  # Invalid type
                monthly_rent_paise=500000,
                rent_due_day=5,
            )
            db.add(unit)
            db.flush()


def test_payment_method_constraint(db: Session, owner_a):
    """payment_method must be in ('CASH', 'UPI', 'BANK_TRANSFER', 'OTHER')."""
    prop = Property(id=uuid.uuid4(), owner_id=owner_a["owner"].id, name="Pay Method Prop")
    db.add(prop)
    db.commit()

    unit = Unit(
        id=uuid.uuid4(),
        property_id=prop.id,
        name="Unit PM",
        unit_type="FLAT",
        monthly_rent_paise=500000,
        rent_due_day=5,
    )
    tenant = Tenant(
        id=uuid.uuid4(),
        unit_id=unit.id,
        name="Pay Tenant",
        phone="9876543210",
        move_in_date=date(2026, 1, 1),
    )
    rent = RentRecord(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        unit_id=unit.id,
        month=10,
        year=2026,
        expected_amount_paise=500000,
        due_date=date(2026, 10, 5),
    )
    db.add_all([unit, tenant, rent])
    db.commit()

    with pytest.raises(IntegrityError):
        with db.begin_nested():
            pay = Payment(
                id=uuid.uuid4(),
                rent_record_id=rent.id,
                amount_paise=500000,
                payment_method="BITCOIN",  # Invalid payment method
                paid_date=date(2026, 10, 5),
            )
            db.add(pay)
            db.flush()


def test_payment_amount_must_be_positive(db: Session, owner_a):
    """Payment amount_paise must be > 0."""
    prop = Property(id=uuid.uuid4(), owner_id=owner_a["owner"].id, name="Pay Amount Prop")
    db.add(prop)
    db.commit()

    unit = Unit(
        id=uuid.uuid4(),
        property_id=prop.id,
        name="Unit PA",
        unit_type="FLAT",
        monthly_rent_paise=500000,
        rent_due_day=5,
    )
    tenant = Tenant(
        id=uuid.uuid4(),
        unit_id=unit.id,
        name="Pay Tenant 2",
        phone="9876543210",
        move_in_date=date(2026, 1, 1),
    )
    rent = RentRecord(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        unit_id=unit.id,
        month=10,
        year=2026,
        expected_amount_paise=500000,
        due_date=date(2026, 10, 5),
    )
    db.add_all([unit, tenant, rent])
    db.commit()

    with pytest.raises(IntegrityError):
        with db.begin_nested():
            pay = Payment(
                id=uuid.uuid4(),
                rent_record_id=rent.id,
                amount_paise=0,  # Invalid zero amount
                payment_method="CASH",
                paid_date=date(2026, 10, 5),
            )
            db.add(pay)
            db.flush()


def test_tenant_status_constraint(db: Session, owner_a):
    """Tenant status must be 'ACTIVE' or 'INACTIVE'."""
    prop = Property(id=uuid.uuid4(), owner_id=owner_a["owner"].id, name="Tenant Status Prop")
    db.add(prop)
    db.commit()

    unit = Unit(
        id=uuid.uuid4(),
        property_id=prop.id,
        name="Unit TS",
        unit_type="FLAT",
        monthly_rent_paise=500000,
        rent_due_day=5,
    )
    db.add(unit)
    db.commit()

    with pytest.raises(IntegrityError):
        with db.begin_nested():
            tenant = Tenant(
                id=uuid.uuid4(),
                unit_id=unit.id,
                name="Invalid Status Tenant",
                phone="9876543210",
                move_in_date=date(2026, 1, 1),
                status="EVICTED",  # Invalid status
            )
            db.add(tenant)
            db.flush()

