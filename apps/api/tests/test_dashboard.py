import uuid
from datetime import date, timedelta
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


def test_dashboard_summary_empty_state(client: TestClient, owner_a):
    """Owner with no properties sees all zeroes and empty lists."""
    response = client.get("/api/v1/dashboard/summary", headers=owner_a["headers"])
    assert response.status_code == 200
    data = response.json()

    today = get_today_ist()
    assert data["month"] == today.month
    assert data["year"] == today.year
    assert data["total_expected_paise"] == 0
    assert data["total_collected_paise"] == 0
    assert data["total_pending_paise"] == 0
    assert data["paid_count"] == 0
    assert data["due_count"] == 0
    assert data["overdue_count"] == 0
    assert data["total_units"] == 0
    assert data["occupied_units"] == 0
    assert data["vacant_units"] == 0
    assert data["todays_due"] == []
    assert data["overdue_list"] == []
    assert data["recent_payments"] == []


def test_dashboard_summary_status_scenarios_and_aggregations(client: TestClient, db: Session, owner_a):
    """Test all status combinations (PAID, DUE, OVERDUE, PENDING, PARTIALLY_PAID, overpaid) and metrics."""
    owner_id = owner_a["owner"].id
    today = get_today_ist()

    # Create Property
    prop = Property(id=uuid.uuid4(), owner_id=owner_id, name="Sunset Heights", address="100 Marine Drive")
    db.add(prop)
    db.flush()

    # 1. Tenant Due Today (Unpaid -> status DUE)
    # due day = today.day
    u_due = Unit(id=uuid.uuid4(), property_id=prop.id, name="101", unit_type="FLAT", monthly_rent_paise=1000000, rent_due_day=today.day)
    t_due = Tenant(id=uuid.uuid4(), unit_id=u_due.id, name="Aarav Sharma", phone="9876500001", move_in_date=date(today.year, today.month, 1), status="ACTIVE")

    # 2. Tenant Due Today (Partially paid -> status PARTIALLY_PAID)
    # Expected ₹10,000, Paid ₹4,000 -> Remaining ₹6,000
    u_due_part = Unit(id=uuid.uuid4(), property_id=prop.id, name="102", unit_type="FLAT", monthly_rent_paise=1000000, rent_due_day=today.day)
    t_due_part = Tenant(id=uuid.uuid4(), unit_id=u_due_part.id, name="Bhavna Rao", phone="9876500002", move_in_date=date(today.year, today.month, 1), status="ACTIVE")

    # 3. Tenant Overdue (Unpaid, due 5 days ago -> status OVERDUE)
    # Note: If today.day <= 5, set due_day = 1 and if today.day == 1, handle safely
    overdue_due_day = max(1, today.day - 2) if today.day > 2 else 1
    overdue_expected_paise = 800000
    u_overdue = Unit(id=uuid.uuid4(), property_id=prop.id, name="103", unit_type="FLAT", monthly_rent_paise=overdue_expected_paise, rent_due_day=overdue_due_day)
    t_overdue = Tenant(id=uuid.uuid4(), unit_id=u_overdue.id, name="Chetan Bhagat", phone="9876500003", move_in_date=date(today.year, today.month, 1), status="ACTIVE")

    # 4. Tenant Overdue (Partially paid, due 2 days ago -> status OVERDUE)
    # Expected ₹8,000, Paid ₹3,000 -> Remaining ₹5,000
    u_overdue_part = Unit(id=uuid.uuid4(), property_id=prop.id, name="104", unit_type="FLAT", monthly_rent_paise=800000, rent_due_day=overdue_due_day)
    t_overdue_part = Tenant(id=uuid.uuid4(), unit_id=u_overdue_part.id, name="Deepak Verma", phone="9876500004", move_in_date=date(today.year, today.month, 1), status="ACTIVE")

    # 5. Tenant Fully Paid (status PAID)
    u_paid = Unit(id=uuid.uuid4(), property_id=prop.id, name="105", unit_type="FLAT", monthly_rent_paise=1200000, rent_due_day=min(28, today.day + 1))
    t_paid = Tenant(id=uuid.uuid4(), unit_id=u_paid.id, name="Ekta Kapoor", phone="9876500005", move_in_date=date(today.year, today.month, 1), status="ACTIVE")

    # 6. Tenant Overpaid (Expected ₹5,000, Paid ₹6,000 -> status PAID)
    u_overpaid = Unit(id=uuid.uuid4(), property_id=prop.id, name="106", unit_type="FLAT", monthly_rent_paise=500000, rent_due_day=today.day)
    t_overpaid = Tenant(id=uuid.uuid4(), unit_id=u_overpaid.id, name="Farhan Akhtar", phone="9876500006", move_in_date=date(today.year, today.month, 1), status="ACTIVE")

    db.add_all([u_due, u_due_part, u_overdue, u_overdue_part, u_paid, u_overpaid])
    db.flush()
    db.add_all([t_due, t_due_part, t_overdue, t_overdue_part, t_paid, t_overpaid])
    db.commit()

    # Trigger initial rent generation via dashboard endpoint
    res = client.get("/api/v1/dashboard/summary", headers=owner_a["headers"])
    assert res.status_code == 200

    # Retrieve created rent records to add payments
    rr_due_part = db.query(RentRecord).filter_by(tenant_id=t_due_part.id, month=today.month, year=today.year).first()
    rr_overdue = db.query(RentRecord).filter_by(tenant_id=t_overdue.id, month=today.month, year=today.year).first()
    rr_overdue_part = db.query(RentRecord).filter_by(tenant_id=t_overdue_part.id, month=today.month, year=today.year).first()
    rr_paid = db.query(RentRecord).filter_by(tenant_id=t_paid.id, month=today.month, year=today.year).first()
    rr_overpaid = db.query(RentRecord).filter_by(tenant_id=t_overpaid.id, month=today.month, year=today.year).first()

    # Adjust overdue record due dates if today.day <= 2 to guarantee due_date < today
    past_due_date = today - timedelta(days=3)
    rr_overdue.due_date = past_due_date
    rr_overdue_part.due_date = past_due_date

    # Add partial payment to rr_due_part: ₹4,000 (400000 paise)
    p_due_part = Payment(id=uuid.uuid4(), rent_record_id=rr_due_part.id, amount_paise=400000, payment_method="UPI", paid_date=today)
    # Add partial payment to rr_overdue_part: ₹3,000 (300000 paise)
    p_overdue_part = Payment(id=uuid.uuid4(), rent_record_id=rr_overdue_part.id, amount_paise=300000, payment_method="CASH", paid_date=past_due_date)
    # Add full payment to rr_paid: ₹12,000 (1200000 paise)
    p_paid = Payment(id=uuid.uuid4(), rent_record_id=rr_paid.id, amount_paise=1200000, payment_method="BANK_TRANSFER", paid_date=today)
    # Add excess payment to rr_overpaid: ₹6,000 (600000 paise)
    p_overpaid = Payment(id=uuid.uuid4(), rent_record_id=rr_overpaid.id, amount_paise=600000, payment_method="UPI", paid_date=today)

    db.add_all([p_due_part, p_overdue_part, p_paid, p_overpaid])
    db.commit()

    # Fetch dashboard again
    res2 = client.get("/api/v1/dashboard/summary", headers=owner_a["headers"])
    assert res2.status_code == 200
    data = res2.json()

    # Expected total = 10k + 10k + 8k + 8k + 12k + 5k = 53k (5300000 paise)
    assert data["total_expected_paise"] == 5300000
    # Collected total = 4k + 3k + 12k + 6k = 25k (2500000 paise)
    assert data["total_collected_paise"] == 2500000
    # Pending total = max(0, 5300000 - 2500000) = 2800000 paise
    assert data["total_pending_paise"] == 2800000

    # Paid count = 2 (t_paid, t_overpaid)
    assert data["paid_count"] == 2

    # Due count strictly == 1 (t_due; t_due_part is PARTIALLY_PAID and NOT counted in due_count)
    assert data["due_count"] == 1

    # Overdue count = 2 (t_overdue, t_overdue_part)
    assert data["overdue_count"] == 2

    # Verify todays_due includes both unpaid and partially-paid due today with remaining balance
    # t_due: ₹10,000 remaining
    # t_due_part: ₹6,000 remaining
    todays_due_items = {item["tenant_name"]: item["amount_paise"] for item in data["todays_due"]}
    assert "Aarav Sharma" in todays_due_items
    assert todays_due_items["Aarav Sharma"] == 1000000
    assert "Bhavna Rao" in todays_due_items
    assert todays_due_items["Bhavna Rao"] == 600000  # ₹6,000 remaining balance!

    # Verify overdue_list includes both unpaid and partially-paid overdue with remaining balance
    # t_overdue: ₹8,000 remaining
    # t_overdue_part: ₹5,000 remaining
    overdue_items = {item["tenant_name"]: item["amount_paise"] for item in data["overdue_list"]}
    assert "Chetan Bhagat" in overdue_items
    assert overdue_items["Chetan Bhagat"] == 800000
    assert "Deepak Verma" in overdue_items
    assert overdue_items["Deepak Verma"] == 500000  # ₹5,000 remaining balance!


def test_dashboard_unit_occupancy_and_archived_filtering(client: TestClient, db: Session, owner_a):
    """Test total_units, occupied_units, vacant_units, excluding archived property/unit."""
    owner_id = owner_a["owner"].id
    today = get_today_ist()

    # Active Property
    prop = Property(id=uuid.uuid4(), owner_id=owner_id, name="Green Meadows")
    # Archived Property (should be completely excluded)
    archived_prop = Property(id=uuid.uuid4(), owner_id=owner_id, name="Old Complex", archived_at=today)
    db.add_all([prop, archived_prop])
    db.flush()

    # Units under active prop:
    # 1. Occupied unit (active tenant)
    u_occupied = Unit(id=uuid.uuid4(), property_id=prop.id, name="G1", unit_type="FLAT", monthly_rent_paise=500000, rent_due_day=5)
    t_active = Tenant(id=uuid.uuid4(), unit_id=u_occupied.id, name="Active Tenant", phone="9876511111", move_in_date=date(2026, 1, 1), status="ACTIVE")

    # 2. Vacant unit (no tenant)
    u_vacant_no_tenant = Unit(id=uuid.uuid4(), property_id=prop.id, name="G2", unit_type="FLAT", monthly_rent_paise=500000, rent_due_day=5)

    # 3. Vacant unit (inactive tenant who moved out)
    u_vacant_inactive_tenant = Unit(id=uuid.uuid4(), property_id=prop.id, name="G3", unit_type="FLAT", monthly_rent_paise=500000, rent_due_day=5)
    t_inactive = Tenant(id=uuid.uuid4(), unit_id=u_vacant_inactive_tenant.id, name="Past Tenant", phone="9876522222", move_in_date=date(2026, 1, 1), move_out_date=date(2026, 6, 1), status="INACTIVE")

    # 4. Archived unit (under active property, should be excluded)
    u_archived = Unit(id=uuid.uuid4(), property_id=prop.id, name="G4", unit_type="FLAT", monthly_rent_paise=500000, rent_due_day=5, archived_at=today)

    # 5. Unit under archived property (should be excluded)
    u_under_archived_prop = Unit(id=uuid.uuid4(), property_id=archived_prop.id, name="Old1", unit_type="FLAT", monthly_rent_paise=500000, rent_due_day=5)

    db.add_all([u_occupied, u_vacant_no_tenant, u_vacant_inactive_tenant, u_archived, u_under_archived_prop])
    db.flush()
    db.add_all([t_active, t_inactive])
    db.commit()

    res = client.get("/api/v1/dashboard/summary", headers=owner_a["headers"])
    assert res.status_code == 200
    data = res.json()

    # Active units under active property = G1, G2, G3 = 3 total
    assert data["total_units"] == 3
    # Occupied units (with ACTIVE tenant) = G1 = 1 occupied
    assert data["occupied_units"] == 1
    # Vacant units = 3 - 1 = 2 vacant (G2 and G3)
    assert data["vacant_units"] == 2


def test_dashboard_recent_payments_ordering_and_limit(client: TestClient, db: Session, owner_a, owner_b):
    """Verify recent payments returns up to 5 non-void payments ordered by paid_date DESC, created_at DESC."""
    owner_a_id = owner_a["owner"].id
    owner_b_id = owner_b["owner"].id
    today = get_today_ist()

    # Setup Owner A
    prop_a = Property(id=uuid.uuid4(), owner_id=owner_a_id, name="Prop Alpha")
    db.add(prop_a)
    db.flush()
    unit_a = Unit(id=uuid.uuid4(), property_id=prop_a.id, name="A101", unit_type="FLAT", monthly_rent_paise=1000000, rent_due_day=1)
    db.add(unit_a)
    db.flush()
    tenant_a = Tenant(id=uuid.uuid4(), unit_id=unit_a.id, name="Tenant Alpha", phone="9876533331", move_in_date=date(2026, 1, 1), status="ACTIVE")
    db.add(tenant_a)
    db.flush()
    rr_a = RentRecord(id=uuid.uuid4(), tenant_id=tenant_a.id, unit_id=unit_a.id, month=today.month, year=today.year, expected_amount_paise=1000000, due_date=today)
    db.add(rr_a)
    db.flush()

    # Setup Owner B
    prop_b = Property(id=uuid.uuid4(), owner_id=owner_b_id, name="Prop Beta")
    db.add(prop_b)
    db.flush()
    unit_b = Unit(id=uuid.uuid4(), property_id=prop_b.id, name="B101", unit_type="FLAT", monthly_rent_paise=1000000, rent_due_day=1)
    db.add(unit_b)
    db.flush()
    tenant_b = Tenant(id=uuid.uuid4(), unit_id=unit_b.id, name="Tenant Beta", phone="9876533332", move_in_date=date(2026, 1, 1), status="ACTIVE")
    db.add(tenant_b)
    db.flush()
    rr_b = RentRecord(id=uuid.uuid4(), tenant_id=tenant_b.id, unit_id=unit_b.id, month=today.month, year=today.year, expected_amount_paise=1000000, due_date=today)
    db.add(rr_b)
    db.flush()

    # Create 6 payments for Owner A on different dates
    payments_a = []
    for i in range(6):
        pay = Payment(
            id=uuid.uuid4(),
            rent_record_id=rr_a.id,
            amount_paise=(i + 1) * 100000,
            payment_method="UPI",
            paid_date=today - timedelta(days=6 - i),
            is_void=False,
        )
        payments_a.append(pay)

    # 1 voided payment for Owner A (must be excluded)
    void_pay = Payment(
        id=uuid.uuid4(),
        rent_record_id=rr_a.id,
        amount_paise=999999,
        payment_method="CASH",
        paid_date=today,
        is_void=True,
    )
    payments_a.append(void_pay)

    # 1 payment for Owner B (must be excluded from Owner A's dashboard)
    pay_b = Payment(
        id=uuid.uuid4(),
        rent_record_id=rr_b.id,
        amount_paise=888888,
        payment_method="BANK_TRANSFER",
        paid_date=today,
        is_void=False,
    )

    db.add_all(payments_a + [pay_b])
    db.commit()

    # Request Owner A's dashboard
    res = client.get("/api/v1/dashboard/summary", headers=owner_a["headers"])
    assert res.status_code == 200
    data = res.json()
    recent = data["recent_payments"]

    # Maximum 5
    assert len(recent) == 5

    # Check ordering: paid_date DESC
    dates = [p["paid_date"] for p in recent]
    assert dates == sorted(dates, reverse=True)

    # Voided payment not present
    amounts = [p["amount_paise"] for p in recent]
    assert 999999 not in amounts

    # Owner B payment not present
    assert 888888 not in amounts


def test_dashboard_owner_isolation(client: TestClient, db: Session, owner_a, owner_b):
    """Owner A's dashboard summary contains nothing from Owner B."""
    today = get_today_ist()

    # Owner A data
    prop_a = Property(id=uuid.uuid4(), owner_id=owner_a["owner"].id, name="Alpha Heights")
    db.add(prop_a)
    db.flush()
    unit_a = Unit(id=uuid.uuid4(), property_id=prop_a.id, name="A1", unit_type="FLAT", monthly_rent_paise=600000, rent_due_day=5)
    db.add(unit_a)
    db.flush()
    tenant_a = Tenant(id=uuid.uuid4(), unit_id=unit_a.id, name="Alpha Resident", phone="9876544441", move_in_date=date(2026, 1, 1), status="ACTIVE")
    db.add(tenant_a)
    db.flush()

    # Owner B data
    prop_b = Property(id=uuid.uuid4(), owner_id=owner_b["owner"].id, name="Beta Residency")
    db.add(prop_b)
    db.flush()
    unit_b = Unit(id=uuid.uuid4(), property_id=prop_b.id, name="B1", unit_type="FLAT", monthly_rent_paise=900000, rent_due_day=5)
    db.add(unit_b)
    db.flush()
    tenant_b = Tenant(id=uuid.uuid4(), unit_id=unit_b.id, name="Beta Resident", phone="9876544442", move_in_date=date(2026, 1, 1), status="ACTIVE")
    db.add(tenant_b)
    db.commit()

    # Request Owner A's dashboard
    res_a = client.get("/api/v1/dashboard/summary", headers=owner_a["headers"])
    assert res_a.status_code == 200
    data_a = res_a.json()

    assert data_a["total_units"] == 1
    assert data_a["total_expected_paise"] == 600000

    # Cross-owner property filter returns 404
    res_cross = client.get(f"/api/v1/dashboard/summary?property_id={prop_b.id}", headers=owner_a["headers"])
    assert res_cross.status_code == 404


def test_dashboard_month_and_year_parameters(client: TestClient, db: Session, owner_a):
    """Test dashboard with explicit month/year, past historical month, and empty future month."""
    owner_id = owner_a["owner"].id

    prop = Property(id=uuid.uuid4(), owner_id=owner_id, name="Cosmo Apartments")
    db.add(prop)
    db.flush()
    unit = Unit(id=uuid.uuid4(), property_id=prop.id, name="101", unit_type="FLAT", monthly_rent_paise=700000, rent_due_day=10)
    db.add(unit)
    db.flush()
    tenant = Tenant(id=uuid.uuid4(), unit_id=unit.id, name="Cosmo Tenant", phone="9876555551", move_in_date=date(2026, 1, 1), status="ACTIVE")
    db.add(tenant)
    db.commit()

    # Historical month: May 2026
    res_may = client.get("/api/v1/dashboard/summary?month=5&year=2026", headers=owner_a["headers"])
    assert res_may.status_code == 200
    data_may = res_may.json()
    assert data_may["month"] == 5
    assert data_may["year"] == 2026
    assert data_may["total_expected_paise"] == 700000

    # Month with no records / tenant moved in after target month (e.g., year 2020)
    res_2020 = client.get("/api/v1/dashboard/summary?month=1&year=2020", headers=owner_a["headers"])
    assert res_2020.status_code == 200
    data_2020 = res_2020.json()
    assert data_2020["total_expected_paise"] == 0
    assert data_2020["total_collected_paise"] == 0
    assert data_2020["total_pending_paise"] == 0
    assert data_2020["paid_count"] == 0
    assert data_2020["due_count"] == 0
    assert data_2020["overdue_count"] == 0
    assert data_2020["todays_due"] == []
    assert data_2020["overdue_list"] == []

    # Invalid month / year parameters
    res_invalid_month = client.get("/api/v1/dashboard/summary?month=13&year=2026", headers=owner_a["headers"])
    assert res_invalid_month.status_code in [400, 422]

    res_invalid_year = client.get("/api/v1/dashboard/summary?month=5&year=1990", headers=owner_a["headers"])
    assert res_invalid_year.status_code in [400, 422]


def test_dashboard_voided_rent_and_payment_excluded(client: TestClient, db: Session, owner_a):
    """Verify voided rent records and payments are completely excluded from dashboard metrics."""
    owner_id = owner_a["owner"].id
    today = get_today_ist()

    prop = Property(id=uuid.uuid4(), owner_id=owner_id, name="Zenith Plaza")
    db.add(prop)
    db.flush()
    unit = Unit(id=uuid.uuid4(), property_id=prop.id, name="Z1", unit_type="FLAT", monthly_rent_paise=1000000, rent_due_day=today.day)
    db.add(unit)
    db.flush()
    tenant = Tenant(id=uuid.uuid4(), unit_id=unit.id, name="Zenith Tenant", phone="9876566661", move_in_date=date(2026, 1, 1), status="ACTIVE")
    db.add(tenant)
    db.flush()

    # Create rent record
    rr = RentRecord(id=uuid.uuid4(), tenant_id=tenant.id, unit_id=unit.id, month=today.month, year=today.year, expected_amount_paise=1000000, due_date=today)
    db.add(rr)
    db.flush()

    # Payment: 1 non-void (₹4,000) and 1 void (₹6,000)
    p_valid = Payment(id=uuid.uuid4(), rent_record_id=rr.id, amount_paise=400000, payment_method="CASH", paid_date=today, is_void=False)
    p_void = Payment(id=uuid.uuid4(), rent_record_id=rr.id, amount_paise=600000, payment_method="UPI", paid_date=today, is_void=True)
    db.add_all([p_valid, p_void])
    db.commit()

    res = client.get("/api/v1/dashboard/summary", headers=owner_a["headers"])
    assert res.status_code == 200
    data = res.json()

    # Collected should only be 400000, not 1000000
    assert data["total_collected_paise"] == 400000
    assert data["total_pending_paise"] == 600000

    # Void the rent record itself
    rr.is_void = True
    db.commit()

    res_void = client.get("/api/v1/dashboard/summary", headers=owner_a["headers"])
    assert res_void.status_code == 200
    data_void = res_void.json()

    # Once rent record is voided, it contributes 0 to expected/collected/pending
    assert data_void["total_expected_paise"] == 0
    assert data_void["total_collected_paise"] == 0
    assert data_void["total_pending_paise"] == 0
    assert data_void["due_count"] == 0
    assert len(data_void["todays_due"]) == 0


def test_dashboard_performance_with_bulk_dataset(client: TestClient, db: Session, owner_a):
    """Verify that Dashboard summary executes in O(1) constant queries without N+1 regression."""
    owner_id = owner_a["owner"].id
    engine = db.get_bind()

    # Reuse 10 properties with 10 units each = 100 units, 100 tenants
    properties = []
    units = []
    tenants = []

    for p_idx in range(5):
        prop = Property(id=uuid.uuid4(), owner_id=owner_id, name=f"Bulk Dash Prop {p_idx}_{uuid.uuid4().hex[:4]}")
        properties.append(prop)
    db.add_all(properties)
    db.flush()

    for p_idx, prop in enumerate(properties):
        for u_idx in range(10):
            unit = Unit(id=uuid.uuid4(), property_id=prop.id, name=f"U-{p_idx}-{u_idx}", unit_type="FLAT", monthly_rent_paise=800000, rent_due_day=5)
            units.append(unit)
    db.add_all(units)
    db.flush()

    for u_idx, unit in enumerate(units):
        tenant = Tenant(id=uuid.uuid4(), unit_id=unit.id, name=f"Bulk Tenant {u_idx}", phone=f"98765{u_idx:05d}", move_in_date=date(2026, 1, 1), status="ACTIVE")
        tenants.append(tenant)
    db.add_all(tenants)
    db.commit()

    # Measure query count on dashboard call
    with QueryCounter(engine) as qc:
        res = client.get("/api/v1/dashboard/summary", headers=owner_a["headers"])

    assert res.status_code == 200
    data = res.json()
    assert data["total_units"] >= 50
    assert data["occupied_units"] >= 50
    # Must execute ≤ 10 queries total, NOT 50+ queries
    assert qc.count <= 10, f"Dashboard query count {qc.count} indicates N+1 query regression"
