from datetime import date, datetime, timedelta, timezone
from urllib.parse import unquote
import uuid
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.property import Property
from app.models.reminder import Reminder
from app.models.rent_record import RentRecord
from app.models.tenant import Tenant
from app.models.unit import Unit
from app.services.rent_status import get_today_ist


def test_reminder_due_rent_success(client: TestClient, db: Session, owner_a):
    """Reminder for DUE rent generates deep link and persists reminder log."""
    owner_id = owner_a["owner"].id
    today = get_today_ist()

    prop = Property(id=uuid.uuid4(), owner_id=owner_id, name="Reminder Manor")
    db.add(prop)
    db.flush()
    unit = Unit(id=uuid.uuid4(), property_id=prop.id, name="R101", unit_type="FLAT", monthly_rent_paise=1000000, rent_due_day=today.day)
    db.add(unit)
    db.flush()
    tenant = Tenant(id=uuid.uuid4(), unit_id=unit.id, name="Rohan Joshi", phone="9876543210", move_in_date=date(today.year, today.month, 1), status="ACTIVE")
    db.add(tenant)
    db.flush()
    rr = RentRecord(id=uuid.uuid4(), tenant_id=tenant.id, unit_id=unit.id, month=today.month, year=today.year, expected_amount_paise=1000000, due_date=today)
    db.add(rr)
    db.commit()

    res = client.post(f"/api/v1/rent/{rr.id}/reminders", json={}, headers=owner_a["headers"])
    assert res.status_code == 200
    data = res.json()

    assert data["tenant_id"] == str(tenant.id)
    assert data["rent_record_id"] == str(rr.id)
    assert data["remaining_amount_paise"] == 1000000
    assert "whatsapp_url" in data
    assert data["whatsapp_url"].startswith("https://wa.me/919876543210?text=")

    decoded_msg = unquote(data["whatsapp_url"])
    assert "Rohan Joshi" in decoded_msg
    assert "₹10,000" in decoded_msg
    assert "due on" in decoded_msg

    # Verify persisted in database
    saved_reminder = db.query(Reminder).filter_by(rent_record_id=rr.id).first()
    assert saved_reminder is not None
    assert saved_reminder.channel == "WHATSAPP"
    assert saved_reminder.message == data["message"]


def test_reminder_overdue_rent_success(client: TestClient, db: Session, owner_a):
    """Reminder for OVERDUE rent uses past-tense wording."""
    owner_id = owner_a["owner"].id
    today = get_today_ist()
    past_due_date = today - timedelta(days=5)

    prop = Property(id=uuid.uuid4(), owner_id=owner_id, name="Overdue Plaza")
    db.add(prop)
    db.flush()
    unit = Unit(id=uuid.uuid4(), property_id=prop.id, name="O201", unit_type="FLAT", monthly_rent_paise=1500000, rent_due_day=1)
    db.add(unit)
    db.flush()
    tenant = Tenant(id=uuid.uuid4(), unit_id=unit.id, name="Suresh Kumar", phone="9876543211", move_in_date=date(2026, 1, 1), status="ACTIVE")
    db.add(tenant)
    db.flush()
    rr = RentRecord(id=uuid.uuid4(), tenant_id=tenant.id, unit_id=unit.id, month=past_due_date.month, year=past_due_date.year, expected_amount_paise=1500000, due_date=past_due_date)
    db.add(rr)
    db.commit()

    res = client.post(f"/api/v1/rent/{rr.id}/reminders", json={}, headers=owner_a["headers"])
    assert res.status_code == 200
    data = res.json()

    assert data["remaining_amount_paise"] == 1500000
    assert "was due on" in data["message"]
    assert "earliest" in data["message"]
    assert "₹15,000" in data["message"]


def test_reminder_partially_paid_rent_success(client: TestClient, db: Session, owner_a):
    """Reminder for partially paid rent requests the remaining balance."""
    owner_id = owner_a["owner"].id
    today = get_today_ist()
    past_due_date = today - timedelta(days=2)

    prop = Property(id=uuid.uuid4(), owner_id=owner_id, name="Partial Heights")
    db.add(prop)
    db.flush()
    unit = Unit(id=uuid.uuid4(), property_id=prop.id, name="P301", unit_type="FLAT", monthly_rent_paise=1000000, rent_due_day=1)
    db.add(unit)
    db.flush()
    tenant = Tenant(id=uuid.uuid4(), unit_id=unit.id, name="Neha Gupta", phone="9876543212", move_in_date=date(2026, 1, 1), status="ACTIVE")
    db.add(tenant)
    db.flush()
    rr = RentRecord(id=uuid.uuid4(), tenant_id=tenant.id, unit_id=unit.id, month=past_due_date.month, year=past_due_date.year, expected_amount_paise=1000000, due_date=past_due_date)
    db.add(rr)
    db.flush()
    # Partial payment of ₹4,000 (400000 paise)
    pay = Payment(id=uuid.uuid4(), rent_record_id=rr.id, amount_paise=400000, payment_method="UPI", paid_date=past_due_date)
    db.add(pay)
    db.commit()

    res = client.post(f"/api/v1/rent/{rr.id}/reminders", json={}, headers=owner_a["headers"])
    assert res.status_code == 200
    data = res.json()

    # Remaining balance should be ₹6,000 (600000 paise)
    assert data["remaining_amount_paise"] == 600000
    assert "remaining rent balance of ₹6,000" in data["message"]
    assert "9876543212" in data["whatsapp_url"]


def test_reminder_rejected_when_paid(client: TestClient, db: Session, owner_a):
    """Cannot remind a tenant who has already fully paid."""
    owner_id = owner_a["owner"].id
    today = get_today_ist()

    prop = Property(id=uuid.uuid4(), owner_id=owner_id, name="Paid Towers")
    db.add(prop)
    db.flush()
    unit = Unit(id=uuid.uuid4(), property_id=prop.id, name="P1", unit_type="FLAT", monthly_rent_paise=800000, rent_due_day=today.day)
    db.add(unit)
    db.flush()
    tenant = Tenant(id=uuid.uuid4(), unit_id=unit.id, name="Vikas Khanna", phone="9876543213", move_in_date=date(today.year, today.month, 1), status="ACTIVE")
    db.add(tenant)
    db.flush()
    rr = RentRecord(id=uuid.uuid4(), tenant_id=tenant.id, unit_id=unit.id, month=today.month, year=today.year, expected_amount_paise=800000, due_date=today)
    db.add(rr)
    db.flush()
    pay = Payment(id=uuid.uuid4(), rent_record_id=rr.id, amount_paise=800000, payment_method="CASH", paid_date=today)
    db.add(pay)
    db.commit()

    res = client.post(f"/api/v1/rent/{rr.id}/reminders", json={}, headers=owner_a["headers"])
    assert res.status_code == 400
    assert res.json()["code"] == "RENT_ALREADY_PAID"


def test_reminder_rejected_when_void(client: TestClient, db: Session, owner_a):
    """Cannot remind for a voided rent record."""
    owner_id = owner_a["owner"].id
    today = get_today_ist()

    prop = Property(id=uuid.uuid4(), owner_id=owner_id, name="Void Court")
    db.add(prop)
    db.flush()
    unit = Unit(id=uuid.uuid4(), property_id=prop.id, name="V1", unit_type="FLAT", monthly_rent_paise=800000, rent_due_day=today.day)
    db.add(unit)
    db.flush()
    tenant = Tenant(id=uuid.uuid4(), unit_id=unit.id, name="Void Resident", phone="9876543214", move_in_date=date(today.year, today.month, 1), status="ACTIVE")
    db.add(tenant)
    db.flush()
    rr = RentRecord(id=uuid.uuid4(), tenant_id=tenant.id, unit_id=unit.id, month=today.month, year=today.year, expected_amount_paise=800000, due_date=today, is_void=True)
    db.add(rr)
    db.commit()

    res = client.post(f"/api/v1/rent/{rr.id}/reminders", json={}, headers=owner_a["headers"])
    assert res.status_code == 400
    assert res.json()["code"] == "RENT_RECORD_VOIDED"


def test_reminder_rejected_when_pending(client: TestClient, db: Session, owner_a):
    """Cannot remind before due date if status is PENDING (unpaid before due date)."""
    owner_id = owner_a["owner"].id
    today = get_today_ist()
    future_due_date = today + timedelta(days=10)

    prop = Property(id=uuid.uuid4(), owner_id=owner_id, name="Future Villas")
    db.add(prop)
    db.flush()
    unit = Unit(id=uuid.uuid4(), property_id=prop.id, name="F1", unit_type="FLAT", monthly_rent_paise=900000, rent_due_day=min(28, future_due_date.day))
    db.add(unit)
    db.flush()
    tenant = Tenant(id=uuid.uuid4(), unit_id=unit.id, name="Future Tenant", phone="9876543215", move_in_date=date(today.year, today.month, 1), status="ACTIVE")
    db.add(tenant)
    db.flush()
    rr = RentRecord(id=uuid.uuid4(), tenant_id=tenant.id, unit_id=unit.id, month=today.month, year=today.year, expected_amount_paise=900000, due_date=future_due_date)
    db.add(rr)
    db.commit()

    res = client.post(f"/api/v1/rent/{rr.id}/reminders", json={}, headers=owner_a["headers"])
    assert res.status_code == 400
    assert res.json()["code"] == "REMINDER_NOT_ELIGIBLE"


def test_reminder_rejected_when_tenant_has_no_phone(client: TestClient, db: Session, owner_a):
    """Cannot generate WhatsApp reminder if tenant does not have a phone number."""
    owner_id = owner_a["owner"].id
    today = get_today_ist()

    prop = Property(id=uuid.uuid4(), owner_id=owner_id, name="No Phone House")
    db.add(prop)
    db.flush()
    unit = Unit(id=uuid.uuid4(), property_id=prop.id, name="N1", unit_type="FLAT", monthly_rent_paise=900000, rent_due_day=today.day)
    db.add(unit)
    db.flush()
    tenant = Tenant(id=uuid.uuid4(), unit_id=unit.id, name="Silent Tenant", phone="", move_in_date=date(today.year, today.month, 1), status="ACTIVE")
    db.add(tenant)
    db.flush()
    rr = RentRecord(id=uuid.uuid4(), tenant_id=tenant.id, unit_id=unit.id, month=today.month, year=today.year, expected_amount_paise=900000, due_date=today)
    db.add(rr)
    db.commit()

    res = client.post(f"/api/v1/rent/{rr.id}/reminders", json={}, headers=owner_a["headers"])
    assert res.status_code == 400
    assert res.json()["code"] == "TENANT_PHONE_REQUIRED"


def test_reminder_24h_cooldown_and_allowed_after_expiry(client: TestClient, db: Session, owner_a):
    """Verifies that 24-hour cooldown prevents spam, and allows reminder once 24h expires."""
    owner_id = owner_a["owner"].id
    today = get_today_ist()

    prop = Property(id=uuid.uuid4(), owner_id=owner_id, name="Cooldown Residency")
    db.add(prop)
    db.flush()
    unit = Unit(id=uuid.uuid4(), property_id=prop.id, name="C1", unit_type="FLAT", monthly_rent_paise=1100000, rent_due_day=today.day)
    db.add(unit)
    db.flush()
    tenant = Tenant(id=uuid.uuid4(), unit_id=unit.id, name="Anil Kapoor", phone="9876543216", move_in_date=date(today.year, today.month, 1), status="ACTIVE")
    db.add(tenant)
    db.flush()
    rr = RentRecord(id=uuid.uuid4(), tenant_id=tenant.id, unit_id=unit.id, month=today.month, year=today.year, expected_amount_paise=1100000, due_date=today)
    db.add(rr)
    db.commit()

    # 1. First reminder succeeds
    res1 = client.post(f"/api/v1/rent/{rr.id}/reminders", json={}, headers=owner_a["headers"])
    assert res1.status_code == 200

    # 2. Immediate second reminder is blocked by cooldown
    res2 = client.post(f"/api/v1/rent/{rr.id}/reminders", json={}, headers=owner_a["headers"])
    assert res2.status_code in [400, 429]
    assert res2.json()["code"] == "REMINDER_COOLDOWN_ACTIVE"

    # 3. Fast-forward reminder timestamp past 24 hours
    reminder_in_db = db.query(Reminder).filter_by(rent_record_id=rr.id).first()
    reminder_in_db.sent_at = datetime.now(timezone.utc) - timedelta(hours=25)
    db.commit()

    # 4. Reminder now succeeds
    res3 = client.post(f"/api/v1/rent/{rr.id}/reminders", json={}, headers=owner_a["headers"])
    assert res3.status_code == 200


def test_reminder_history_listing_and_tenant_alias(client: TestClient, db: Session, owner_a):
    """Test listing reminder history for rent record and tenant alias endpoint."""
    owner_id = owner_a["owner"].id
    today = get_today_ist()

    prop = Property(id=uuid.uuid4(), owner_id=owner_id, name="History Gardens")
    db.add(prop)
    db.flush()
    unit = Unit(id=uuid.uuid4(), property_id=prop.id, name="H1", unit_type="FLAT", monthly_rent_paise=750000, rent_due_day=today.day)
    db.add(unit)
    db.flush()
    tenant = Tenant(id=uuid.uuid4(), unit_id=unit.id, name="Maya Sarabhai", phone="9876543217", move_in_date=date(today.year, today.month, 1), status="ACTIVE")
    db.add(tenant)
    db.flush()
    rr = RentRecord(id=uuid.uuid4(), tenant_id=tenant.id, unit_id=unit.id, month=today.month, year=today.year, expected_amount_paise=750000, due_date=today)
    db.add(rr)
    db.commit()

    # Create reminder via tenant alias endpoint
    res_alias = client.post(
        f"/api/v1/tenants/{tenant.id}/reminders",
        json={"rent_record_id": str(rr.id), "message": "Custom reminder for Maya"},
        headers=owner_a["headers"],
    )
    assert res_alias.status_code == 200
    assert res_alias.json()["message"] == "Custom reminder for Maya"

    # List history via rent record endpoint
    res_list_rr = client.get(f"/api/v1/rent/{rr.id}/reminders", headers=owner_a["headers"])
    assert res_list_rr.status_code == 200
    items_rr = res_list_rr.json()
    assert len(items_rr) == 1
    assert items_rr[0]["message"] == "Custom reminder for Maya"
    assert items_rr[0]["whatsapp_url"] is not None

    # List history via tenant endpoint
    res_list_t = client.get(f"/api/v1/tenants/{tenant.id}/reminders", headers=owner_a["headers"])
    assert res_list_t.status_code == 200
    items_t = res_list_t.json()
    assert len(items_t) == 1
    assert items_t[0]["rent_record_id"] == str(rr.id)


def test_reminder_owner_isolation(client: TestClient, db: Session, owner_a, owner_b):
    """Owner B cannot create or view reminders for Owner A's rent records or tenants."""
    today = get_today_ist()

    prop_a = Property(id=uuid.uuid4(), owner_id=owner_a["owner"].id, name="Alpha Tower")
    db.add(prop_a)
    db.flush()
    unit_a = Unit(id=uuid.uuid4(), property_id=prop_a.id, name="A101", unit_type="FLAT", monthly_rent_paise=800000, rent_due_day=today.day)
    db.add(unit_a)
    db.flush()
    tenant_a = Tenant(id=uuid.uuid4(), unit_id=unit_a.id, name="Tenant A", phone="9876543218", move_in_date=date(today.year, today.month, 1), status="ACTIVE")
    db.add(tenant_a)
    db.flush()
    rr_a = RentRecord(id=uuid.uuid4(), tenant_id=tenant_a.id, unit_id=unit_a.id, month=today.month, year=today.year, expected_amount_paise=800000, due_date=today)
    db.add(rr_a)
    db.commit()

    # Owner B attempts to send reminder on Owner A's rent record -> 404
    res_create = client.post(f"/api/v1/rent/{rr_a.id}/reminders", json={}, headers=owner_b["headers"])
    assert res_create.status_code == 404

    # Owner B attempts to view reminders on Owner A's rent record -> 404
    res_list = client.get(f"/api/v1/rent/{rr_a.id}/reminders", headers=owner_b["headers"])
    assert res_list.status_code == 404

    # Owner B attempts tenant alias on Owner A's tenant -> 404
    res_alias = client.post(
        f"/api/v1/tenants/{tenant_a.id}/reminders",
        json={"rent_record_id": str(rr_a.id)},
        headers=owner_b["headers"],
    )
    assert res_alias.status_code == 404

    # Owner B attempts tenant history on Owner A's tenant -> 404
    res_t_list = client.get(f"/api/v1/tenants/{tenant_a.id}/reminders", headers=owner_b["headers"])
    assert res_t_list.status_code == 404


def test_reminder_inactive_tenant_historical_rent(client: TestClient, db: Session, owner_a):
    """Can remind an inactive tenant for a historical overdue rent obligation."""
    owner_id = owner_a["owner"].id
    today = get_today_ist()
    past_due_date = today - timedelta(days=20)

    prop = Property(id=uuid.uuid4(), owner_id=owner_id, name="Historical Palace")
    db.add(prop)
    db.flush()
    unit = Unit(id=uuid.uuid4(), property_id=prop.id, name="HP1", unit_type="FLAT", monthly_rent_paise=1200000, rent_due_day=1)
    db.add(unit)
    db.flush()
    tenant = Tenant(
        id=uuid.uuid4(),
        unit_id=unit.id,
        name="Past Tenant Dave",
        phone="9876543219",
        move_in_date=date(2026, 1, 1),
        move_out_date=today - timedelta(days=5),
        status="INACTIVE",
    )
    db.add(tenant)
    db.flush()
    rr = RentRecord(id=uuid.uuid4(), tenant_id=tenant.id, unit_id=unit.id, month=past_due_date.month, year=past_due_date.year, expected_amount_paise=1200000, due_date=past_due_date)
    db.add(rr)
    db.commit()

    res = client.post(f"/api/v1/rent/{rr.id}/reminders", json={}, headers=owner_a["headers"])
    assert res.status_code == 200
    data = res.json()
    assert data["remaining_amount_paise"] == 1200000
    assert "Past Tenant Dave" in data["message"]
