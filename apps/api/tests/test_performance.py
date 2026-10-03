import uuid
from datetime import date
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.models.property import Property
from app.models.unit import Unit
from app.models.tenant import Tenant
from app.models.rent_record import RentRecord
from app.models.payment import Payment
from app.services.rent import rent_service
from app.services.property import property_service
from app.services.unit import unit_service
from app.services.tenant import tenant_service


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


def test_bulk_rent_generation_and_listings_performance(db: Session, owner_a):
    """Verify performance with realistic data (10 properties, 100 units, 100 tenants).

    Ensures:
    - Monthly rent generation does not perform 100+ individual existence queries.
    - Property, unit, and tenant listings do not suffer from N+1 query patterns.
    """
    owner_id = owner_a["owner"].id
    engine = db.get_bind()

    # 1. Bulk insert realistic dataset: 10 properties, 10 units each = 100 units, 100 active tenants
    properties = []
    units = []
    tenants = []

    for p_idx in range(10):
        prop = Property(
            id=uuid.uuid4(),
            owner_id=owner_id,
            name=f"Perf Complex {p_idx}_{uuid.uuid4().hex[:4]}",
            address="123 Performance Way",
        )
        properties.append(prop)

    db.add_all(properties)
    db.flush()

    for p_idx, prop in enumerate(properties):
        for u_idx in range(10):
            unit = Unit(
                id=uuid.uuid4(),
                property_id=prop.id,
                name=f"{p_idx * 10 + u_idx + 1}",
                unit_type="FLAT",
                monthly_rent_paise=800000,
                rent_due_day=5,
            )
            units.append(unit)

    db.add_all(units)
    db.flush()

    for u_idx, unit in enumerate(units):
        tenant = Tenant(
            id=uuid.uuid4(),
            unit_id=unit.id,
            name=f"Tenant {u_idx + 1}",
            phone=f"98765{u_idx:05d}",
            move_in_date=date(2026, 1, 1),
            status="ACTIVE",
        )
        tenants.append(tenant)

    db.add_all(tenants)
    db.commit()

    # 2. Test generate_rent_records_for_month performance (initial creation of 100 records)
    with QueryCounter(engine) as qc:
        records = rent_service.generate_rent_records_for_month(
            db=db,
            owner_id=owner_id,
            month=10,
            year=2026,
        )

    assert len(records) == 100
    # Print queries to inspect
    # print("\n".join(f"{i+1}: {q}" for i, q in enumerate(qc.queries)))
    assert qc.count <= 10, f"Rent generation query count {qc.count} exceeded expectation (N+1 regression)"

    # 3. Test subsequent generate_rent_records_for_month (all records already exist)
    with QueryCounter(engine) as qc_existing:
        records_existing = rent_service.generate_rent_records_for_month(
            db=db,
            owner_id=owner_id,
            month=10,
            year=2026,
        )

    assert len(records_existing) == 100
    # Should execute ~3 queries (units, existing records map, list) with 0 new inserts
    assert qc_existing.count <= 5, f"Existing rent check query count {qc_existing.count} exceeded expectation"

    # 4. Test Property listing N+1 optimization (10 properties with 100 units and 100 tenants)
    with QueryCounter(engine) as qc_prop:
        prop_list_res = property_service.list_properties(
            db=db,
            owner_id=owner_id,
            page=1,
            per_page=20,
        )

    assert prop_list_res.total == 10
    assert len(prop_list_res.items) == 10
    # Must use selectinload (1 count + 1 properties + 1 units + 1 tenants = 4 queries), NOT 111 queries
    assert qc_prop.count <= 5, f"Property list query count {qc_prop.count} indicates N+1 query issue"

    # 5. Test Unit listing N+1 optimization (10 units under a property)
    target_prop = properties[0]
    with QueryCounter(engine) as qc_units:
        unit_items = unit_service.list_units(
            db=db,
            property_id=target_prop.id,
            owner_id=owner_id,
        )

    assert len(unit_items) == 10
    # Must use selectinload (1 prop check + 2 eager load + 1 units + 1 eager load = 5 queries), NOT 1 + 10 = 11 queries
    assert qc_units.count <= 6, f"Unit list query count {qc_units.count} indicates N+1 query issue"

    # 6. Test Tenant listing N+1 optimization (paginated page of 20 tenants with current month status)
    with QueryCounter(engine) as qc_tenants:
        tenant_list_res = tenant_service.list_tenants(
            db=db,
            owner_id=owner_id,
            page=1,
            per_page=20,
        )

    assert tenant_list_res.total >= 100
    assert len(tenant_list_res.items) == 20
    # Must batch load rent records (1 count + 1 tenants with unit/prop + 1 rent records batch = 3 queries)
    # NOT 1 + 20 = 21 queries!
    assert qc_tenants.count <= 5, f"Tenant list query count {qc_tenants.count} indicates N+1 query issue"
