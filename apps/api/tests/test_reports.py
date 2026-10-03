from datetime import date, timedelta
from urllib.parse import unquote
import uuid
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.property import Property
from app.models.rent_record import RentRecord
from app.models.tenant import Tenant
from app.models.unit import Unit
from app.services.rent_status import get_today_ist


class QueryCounter:
    def __init__(self, engine):
        self.engine = engine
        self.count = 0
        self.queries = []

    def __enter__(self):
        self.count = 0
        self.queries = []
        event.listen(self.engine, "before_cursor_execute", self._callback)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        event.remove(self.engine, "before_cursor_execute", self._callback)

    def _callback(self, conn, cursor, statement, parameters, context, executemany):
        self.count += 1
        self.queries.append(statement)


def test_monthly_report_empty_state(client: TestClient, owner_a):
    """Owner with no properties receives an empty report with all zeroes and empty lists."""
    res = client.get("/api/v1/reports/monthly", headers=owner_a["headers"])
    assert res.status_code == 200
    data = res.json()

    today = get_today_ist()
    assert data["month"] == today.month
    assert data["year"] == today.year

    summary = data["summary"]
    assert summary["total_expected_paise"] == 0
    assert summary["total_collected_paise"] == 0
    assert summary["total_pending_paise"] == 0
    assert summary["paid_count"] == 0
    assert summary["partially_paid_count"] == 0
    assert summary["due_count"] == 0
    assert summary["overdue_count"] == 0

    breakdown = data["payment_breakdown"]
    assert breakdown["cash_paise"] == 0
    assert breakdown["upi_paise"] == 0
    assert breakdown["bank_transfer_paise"] == 0
    assert breakdown["other_paise"] == 0

    outstanding = data["outstanding"]
    assert outstanding["total_count"] == 0
    assert outstanding["total_amount_paise"] == 0
    assert outstanding["tenants"] == []


def test_monthly_report_financial_totals_and_status_counts(client: TestClient, db: Session, owner_a):
    """Test calculations for expected, collected, pending, paid, partially_paid, due, and overdue counts."""
    owner_id = owner_a["owner"].id
    today = get_today_ist()

    prop = Property(id=uuid.uuid4(), owner_id=owner_id, name="Royal Palms", address="1 Palm Avenue")
    db.add(prop)
    db.flush()

    # 1. DUE: Due today, unpaid (₹10,000)
    u_due = Unit(id=uuid.uuid4(), property_id=prop.id, name="101", unit_type="FLAT", monthly_rent_paise=1000000, rent_due_day=today.day)
    t_due = Tenant(id=uuid.uuid4(), unit_id=u_due.id, name="Aarav Sharma", phone="9876500001", move_in_date=date(today.year, today.month, 1), status="ACTIVE")

    # 2. PARTIALLY_PAID: Due today or future, partial payment (Expected ₹10,000, Paid ₹4,000 -> Remaining ₹6,000)
    u_part = Unit(id=uuid.uuid4(), property_id=prop.id, name="102", unit_type="FLAT", monthly_rent_paise=1000000, rent_due_day=today.day)
    t_part = Tenant(id=uuid.uuid4(), unit_id=u_part.id, name="Bhavna Rao", phone="9876500002", move_in_date=date(today.year, today.month, 1), status="ACTIVE")

    # 3. OVERDUE: Due 4 days ago, unpaid (₹8,000)
    overdue_due_day = max(1, today.day - 4) if today.day > 4 else 1
    u_overdue = Unit(id=uuid.uuid4(), property_id=prop.id, name="103", unit_type="FLAT", monthly_rent_paise=800000, rent_due_day=overdue_due_day)
    t_overdue = Tenant(id=uuid.uuid4(), unit_id=u_overdue.id, name="Chetan Bhagat", phone="9876500003", move_in_date=date(today.year, today.month, 1), status="ACTIVE")

    # 4. PAID: Expected ₹12,000, Paid ₹12,000
    u_paid = Unit(id=uuid.uuid4(), property_id=prop.id, name="104", unit_type="FLAT", monthly_rent_paise=1200000, rent_due_day=today.day)
    t_paid = Tenant(id=uuid.uuid4(), unit_id=u_paid.id, name="Deepak Verma", phone="9876500004", move_in_date=date(today.year, today.month, 1), status="ACTIVE")

    # 5. PENDING: Due 10 days in future, unpaid (₹5,000)
    future_day = min(28, today.day + 10)
    u_pending = Unit(id=uuid.uuid4(), property_id=prop.id, name="105", unit_type="FLAT", monthly_rent_paise=500000, rent_due_day=future_day)
    t_pending = Tenant(id=uuid.uuid4(), unit_id=u_pending.id, name="Ekta Kapoor", phone="9876500005", move_in_date=date(today.year, today.month, 1), status="ACTIVE")

    db.add_all([u_due, u_part, u_overdue, u_paid, u_pending])
    db.flush()
    db.add_all([t_due, t_part, t_overdue, t_paid, t_pending])
    db.commit()

    # Trigger rent generation via report endpoint
    res1 = client.get("/api/v1/reports/monthly", headers=owner_a["headers"])
    assert res1.status_code == 200

    # Retrieve rent records to attach payments and fix past due dates
    rr_part = db.query(RentRecord).filter_by(tenant_id=t_part.id, month=today.month, year=today.year).first()
    rr_overdue = db.query(RentRecord).filter_by(tenant_id=t_overdue.id, month=today.month, year=today.year).first()
    rr_paid = db.query(RentRecord).filter_by(tenant_id=t_paid.id, month=today.month, year=today.year).first()
    rr_pending = db.query(RentRecord).filter_by(tenant_id=t_pending.id, month=today.month, year=today.year).first()

    # Explicitly ensure overdue due date is in the past
    past_due_date = today - timedelta(days=3)
    rr_overdue.due_date = past_due_date

    # Explicitly ensure pending due date is in the future
    future_due_date = today + timedelta(days=5)
    rr_pending.due_date = future_due_date

    # Add partial payment to rr_part (₹4,000 via UPI)
    p_part = Payment(id=uuid.uuid4(), rent_record_id=rr_part.id, amount_paise=400000, payment_method="UPI", paid_date=today)
    # Add full payment to rr_paid (₹12,000 via CASH)
    p_paid = Payment(id=uuid.uuid4(), rent_record_id=rr_paid.id, amount_paise=1200000, payment_method="CASH", paid_date=today)

    db.add_all([p_part, p_paid])
    db.commit()

    # Fetch report
    res = client.get("/api/v1/reports/monthly", headers=owner_a["headers"])
    assert res.status_code == 200
    data = res.json()
    summary = data["summary"]

    # Expected: 10k + 10k + 8k + 12k + 5k = 45k (4500000 paise)
    assert summary["total_expected_paise"] == 4500000
    # Collected: 4k + 12k = 16k (1600000 paise)
    assert summary["total_collected_paise"] == 1600000
    # Pending: 45k - 16k = 29k (2900000 paise)
    assert summary["total_pending_paise"] == 2900000

    # Status counts:
    assert summary["paid_count"] == 1          # t_paid
    assert summary["partially_paid_count"] == 1 # t_part
    assert summary["due_count"] == 1            # t_due
    assert summary["overdue_count"] == 1        # t_overdue

    # Outstanding section:
    # Must include PARTIALLY_PAID, DUE, OVERDUE. Must EXCLUDE PAID and PENDING!
    outstanding = data["outstanding"]
    assert outstanding["total_count"] == 3

    # Outstanding amounts:
    # t_due: ₹10,000
    # t_part: ₹6,000
    # t_overdue: ₹8,000
    # Total outstanding = ₹24,000 (2400000 paise)
    assert outstanding["total_amount_paise"] == 2400000

    tenant_names = [t["tenant_name"] for t in outstanding["tenants"]]
    assert "Aarav Sharma" in tenant_names
    assert "Bhavna Rao" in tenant_names
    assert "Chetan Bhagat" in tenant_names
    assert "Deepak Verma" not in tenant_names  # PAID excluded
    assert "Ekta Kapoor" not in tenant_names   # PENDING excluded


def test_monthly_report_payment_breakdown_and_void_excluded(client: TestClient, db: Session, owner_a):
    """Verify payment methods breakdown matches payments and excludes voided payments."""
    owner_id = owner_a["owner"].id
    today = get_today_ist()

    prop = Property(id=uuid.uuid4(), owner_id=owner_id, name="Metropolis")
    db.add(prop)
    db.flush()
    unit = Unit(id=uuid.uuid4(), property_id=prop.id, name="M1", unit_type="FLAT", monthly_rent_paise=2000000, rent_due_day=today.day)
    db.add(unit)
    db.flush()
    tenant = Tenant(id=uuid.uuid4(), unit_id=unit.id, name="Farhan Akhtar", phone="9876500006", move_in_date=date(today.year, today.month, 1), status="ACTIVE")
    db.add(tenant)
    db.flush()
    rr = RentRecord(id=uuid.uuid4(), tenant_id=tenant.id, unit_id=unit.id, month=today.month, year=today.year, expected_amount_paise=2000000, due_date=today)
    db.add(rr)
    db.flush()

    # Payments across 4 methods:
    # CASH: 500,000
    # UPI: 400,000
    # BANK_TRANSFER: 300,000
    # OTHER: 200,000
    # VOID UPI: 100,000 (should be excluded)
    p_cash = Payment(id=uuid.uuid4(), rent_record_id=rr.id, amount_paise=500000, payment_method="CASH", paid_date=today)
    p_upi = Payment(id=uuid.uuid4(), rent_record_id=rr.id, amount_paise=400000, payment_method="UPI", paid_date=today)
    p_bank = Payment(id=uuid.uuid4(), rent_record_id=rr.id, amount_paise=300000, payment_method="BANK_TRANSFER", paid_date=today)
    p_other = Payment(id=uuid.uuid4(), rent_record_id=rr.id, amount_paise=200000, payment_method="OTHER", paid_date=today)
    p_void = Payment(id=uuid.uuid4(), rent_record_id=rr.id, amount_paise=100000, payment_method="UPI", paid_date=today, is_void=True)

    db.add_all([p_cash, p_upi, p_bank, p_other, p_void])
    db.commit()

    res = client.get("/api/v1/reports/monthly", headers=owner_a["headers"])
    assert res.status_code == 200
    data = res.json()

    breakdown = data["payment_breakdown"]
    assert breakdown["cash_paise"] == 500000
    assert breakdown["upi_paise"] == 400000  # Void 100000 excluded
    assert breakdown["bank_transfer_paise"] == 300000
    assert breakdown["other_paise"] == 200000

    # Total collected equals sum of breakdown
    expected_collected = 500000 + 400000 + 300000 + 200000
    assert data["summary"]["total_collected_paise"] == expected_collected


def test_monthly_report_payment_made_after_rent_month(client: TestClient, db: Session, owner_a):
    """Payment made in a subsequent month still counts toward the rent record's collected amount."""
    owner_id = owner_a["owner"].id

    prop = Property(id=uuid.uuid4(), owner_id=owner_id, name="Springfield")
    db.add(prop)
    db.flush()
    unit = Unit(id=uuid.uuid4(), property_id=prop.id, name="S1", unit_type="FLAT", monthly_rent_paise=1000000, rent_due_day=5)
    db.add(unit)
    db.flush()
    tenant = Tenant(id=uuid.uuid4(), unit_id=unit.id, name="Late Payer", phone="9876500007", move_in_date=date(2026, 1, 1), status="ACTIVE")
    db.add(tenant)
    db.flush()

    # Rent record for May 2026 (Month 5)
    rr = RentRecord(id=uuid.uuid4(), tenant_id=tenant.id, unit_id=unit.id, month=5, year=2026, expected_amount_paise=1000000, due_date=date(2026, 5, 5))
    db.add(rr)
    db.flush()

    # Payment made 2 months later in July 2026
    pay = Payment(id=uuid.uuid4(), rent_record_id=rr.id, amount_paise=1000000, payment_method="BANK_TRANSFER", paid_date=date(2026, 7, 10))
    db.add(pay)
    db.commit()

    # Query report for May 2026
    res = client.get("/api/v1/reports/monthly?month=5&year=2026", headers=owner_a["headers"])
    assert res.status_code == 200
    data = res.json()

    assert data["summary"]["total_expected_paise"] == 1000000
    assert data["summary"]["total_collected_paise"] == 1000000
    assert data["summary"]["total_pending_paise"] == 0
    assert data["summary"]["paid_count"] == 1
    assert data["outstanding"]["total_count"] == 0


def test_monthly_report_voided_rent_excluded(client: TestClient, db: Session, owner_a):
    """Voided rent records must not appear in any report metrics."""
    owner_id = owner_a["owner"].id
    today = get_today_ist()

    prop = Property(id=uuid.uuid4(), owner_id=owner_id, name="Echo Valley")
    db.add(prop)
    db.flush()
    unit = Unit(id=uuid.uuid4(), property_id=prop.id, name="E1", unit_type="FLAT", monthly_rent_paise=1000000, rent_due_day=today.day)
    db.add(unit)
    db.flush()
    tenant = Tenant(id=uuid.uuid4(), unit_id=unit.id, name="Void Tenant", phone="9876500008", move_in_date=date(today.year, today.month, 1), status="ACTIVE")
    db.add(tenant)
    db.flush()
    rr = RentRecord(id=uuid.uuid4(), tenant_id=tenant.id, unit_id=unit.id, month=today.month, year=today.year, expected_amount_paise=1000000, due_date=today, is_void=True)
    db.add(rr)
    db.commit()

    res = client.get("/api/v1/reports/monthly", headers=owner_a["headers"])
    assert res.status_code == 200
    data = res.json()

    assert data["summary"]["total_expected_paise"] == 0
    assert data["summary"]["due_count"] == 0
    assert data["outstanding"]["total_count"] == 0


def test_monthly_report_property_filter_and_cross_owner_404(client: TestClient, db: Session, owner_a, owner_b):
    """Property filter limits data to that property; cross-owner property returns 404."""
    today = get_today_ist()

    # Owner A: Prop 1 and Prop 2
    prop_a1 = Property(id=uuid.uuid4(), owner_id=owner_a["owner"].id, name="Prop Alpha 1")
    prop_a2 = Property(id=uuid.uuid4(), owner_id=owner_a["owner"].id, name="Prop Alpha 2")
    # Owner B: Prop 3
    prop_b = Property(id=uuid.uuid4(), owner_id=owner_b["owner"].id, name="Prop Beta")
    db.add_all([prop_a1, prop_a2, prop_b])
    db.flush()

    u_a1 = Unit(id=uuid.uuid4(), property_id=prop_a1.id, name="A101", unit_type="FLAT", monthly_rent_paise=600000, rent_due_day=today.day)
    u_a2 = Unit(id=uuid.uuid4(), property_id=prop_a2.id, name="A201", unit_type="FLAT", monthly_rent_paise=900000, rent_due_day=today.day)
    db.add_all([u_a1, u_a2])
    db.flush()

    t_a1 = Tenant(id=uuid.uuid4(), unit_id=u_a1.id, name="Tenant A1", phone="9876500009", move_in_date=date(today.year, today.month, 1), status="ACTIVE")
    t_a2 = Tenant(id=uuid.uuid4(), unit_id=u_a2.id, name="Tenant A2", phone="9876500010", move_in_date=date(today.year, today.month, 1), status="ACTIVE")
    db.add_all([t_a1, t_a2])
    db.commit()

    # 1. Unfiltered report includes both properties (600k + 900k = 1500k)
    res_all = client.get("/api/v1/reports/monthly", headers=owner_a["headers"])
    assert res_all.status_code == 200
    assert res_all.json()["summary"]["total_expected_paise"] == 1500000

    # 2. Filtered to prop_a1 -> only 600k
    res_p1 = client.get(f"/api/v1/reports/monthly?property_id={prop_a1.id}", headers=owner_a["headers"])
    assert res_p1.status_code == 200
    assert res_p1.json()["summary"]["total_expected_paise"] == 600000
    assert res_p1.json()["outstanding"]["tenants"][0]["property_name"] == "Prop Alpha 1"

    # 3. Cross-owner property filter -> 404 Not Found
    res_cross = client.get(f"/api/v1/reports/monthly?property_id={prop_b.id}", headers=owner_a["headers"])
    assert res_cross.status_code == 404


def test_monthly_report_owner_isolation(client: TestClient, db: Session, owner_a, owner_b):
    """Owner A's report contains zero data from Owner B."""
    today = get_today_ist()

    prop_a = Property(id=uuid.uuid4(), owner_id=owner_a["owner"].id, name="Owner A Building")
    prop_b = Property(id=uuid.uuid4(), owner_id=owner_b["owner"].id, name="Owner B Building")
    db.add_all([prop_a, prop_b])
    db.flush()

    u_a = Unit(id=uuid.uuid4(), property_id=prop_a.id, name="UA", unit_type="FLAT", monthly_rent_paise=500000, rent_due_day=today.day)
    u_b = Unit(id=uuid.uuid4(), property_id=prop_b.id, name="UB", unit_type="FLAT", monthly_rent_paise=800000, rent_due_day=today.day)
    db.add_all([u_a, u_b])
    db.flush()

    t_a = Tenant(id=uuid.uuid4(), unit_id=u_a.id, name="Tenant A", phone="9876500011", move_in_date=date(today.year, today.month, 1), status="ACTIVE")
    t_b = Tenant(id=uuid.uuid4(), unit_id=u_b.id, name="Tenant B", phone="9876500012", move_in_date=date(today.year, today.month, 1), status="ACTIVE")
    db.add_all([t_a, t_b])
    db.commit()

    res_a = client.get("/api/v1/reports/monthly", headers=owner_a["headers"])
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["summary"]["total_expected_paise"] == 500000
    assert len(data_a["outstanding"]["tenants"]) == 1
    assert data_a["outstanding"]["tenants"][0]["tenant_name"] == "Tenant A"


def test_monthly_report_inactive_tenant_historical_rent(client: TestClient, db: Session, owner_a):
    """Historical month report correctly includes debt from an inactive tenant."""
    owner_id = owner_a["owner"].id

    prop = Property(id=uuid.uuid4(), owner_id=owner_id, name="Past Residency")
    db.add(prop)
    db.flush()
    unit = Unit(id=uuid.uuid4(), property_id=prop.id, name="PR-1", unit_type="FLAT", monthly_rent_paise=1000000, rent_due_day=5)
    db.add(unit)
    db.flush()

    # Tenant moved out on 2026-06-15, but has unpaid rent from 2026-04
    tenant = Tenant(
        id=uuid.uuid4(),
        unit_id=unit.id,
        name="Moved Out Tenant",
        phone="9876500013",
        move_in_date=date(2026, 1, 1),
        move_out_date=date(2026, 6, 15),
        status="INACTIVE",
    )
    db.add(tenant)
    db.flush()

    rr = RentRecord(id=uuid.uuid4(), tenant_id=tenant.id, unit_id=unit.id, month=4, year=2026, expected_amount_paise=1000000, due_date=date(2026, 4, 5))
    db.add(rr)
    db.commit()

    res = client.get("/api/v1/reports/monthly?month=4&year=2026", headers=owner_a["headers"])
    assert res.status_code == 200
    data = res.json()

    assert data["summary"]["total_expected_paise"] == 1000000
    assert data["summary"]["overdue_count"] == 1
    assert data["outstanding"]["total_count"] == 1
    assert data["outstanding"]["tenants"][0]["tenant_name"] == "Moved Out Tenant"


def test_monthly_report_validation_errors(client: TestClient, owner_a):
    """Invalid month and year return proper validation errors."""
    res_month = client.get("/api/v1/reports/monthly?month=13&year=2026", headers=owner_a["headers"])
    assert res_month.status_code in [400, 422]

    res_year = client.get("/api/v1/reports/monthly?month=5&year=1990", headers=owner_a["headers"])
    assert res_year.status_code in [400, 422]


def test_monthly_report_performance_with_bulk_dataset(client: TestClient, db: Session, owner_a):
    """Verify monthly report query executes in O(1) constant queries without N+1 regression."""
    owner_id = owner_a["owner"].id
    engine = db.get_bind()

    properties = []
    units = []
    tenants = []

    for p_idx in range(5):
        prop = Property(id=uuid.uuid4(), owner_id=owner_id, name=f"Report Bulk Prop {p_idx}_{uuid.uuid4().hex[:4]}")
        properties.append(prop)
    db.add_all(properties)
    db.flush()

    for p_idx, prop in enumerate(properties):
        for u_idx in range(10):
            unit = Unit(id=uuid.uuid4(), property_id=prop.id, name=f"RU-{p_idx}-{u_idx}", unit_type="FLAT", monthly_rent_paise=800000, rent_due_day=5)
            units.append(unit)
    db.add_all(units)
    db.flush()

    for u_idx, unit in enumerate(units):
        tenant = Tenant(id=uuid.uuid4(), unit_id=unit.id, name=f"Report Bulk Tenant {u_idx}", phone=f"98765{u_idx:05d}", move_in_date=date(2026, 1, 1), status="ACTIVE")
        tenants.append(tenant)
    db.add_all(tenants)
    db.commit()

    with QueryCounter(engine) as qc:
        res = client.get("/api/v1/reports/monthly", headers=owner_a["headers"])

    assert res.status_code == 200
    data = res.json()
    assert data["summary"]["total_expected_paise"] >= 40000000
    # Must execute in constant O(1) queries (<= 10 queries), NOT 50+ queries
    assert qc.count <= 10, f"Report query count {qc.count} indicates N+1 query regression"
