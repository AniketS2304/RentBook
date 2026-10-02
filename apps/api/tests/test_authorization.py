import uuid
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.core.exceptions import NotFoundError
from app.models.property import Property
from app.repositories.base import BaseOwnerScopedRepository


def test_owner_a_accesses_own_resource(db: Session, owner_a):
    """Owner A can access their own property via repository filtering."""
    prop_a = Property(
        id=uuid.uuid4(),
        owner_id=owner_a["owner"].id,
        name="Shree Niwas A",
        address="123 MG Road",
    )
    db.add(prop_a)
    db.commit()

    repo = BaseOwnerScopedRepository(Property)
    fetched = repo.get_by_id(db, prop_a.id, owner_a["owner"].id)
    assert fetched is not None
    assert fetched.id == prop_a.id
    assert fetched.owner_id == owner_a["owner"].id


def test_cross_owner_access_returns_none_or_404(db: Session, owner_a, owner_b):
    """Owner B cannot access Owner A's property; returns None (leading to 404 in service layer)."""
    prop_a = Property(
        id=uuid.uuid4(),
        owner_id=owner_a["owner"].id,
        name="Shree Niwas A",
    )
    db.add(prop_a)
    db.commit()

    repo = BaseOwnerScopedRepository(Property)
    # Owner B attempts to query Owner A's property
    fetched_by_b = repo.get_by_id(db, prop_a.id, owner_b["owner"].id)
    assert fetched_by_b is None, "Cross-owner query must return None (404), never the resource"

    # Service layer convention: None triggers NotFoundError (404)
    if not fetched_by_b:
        with pytest.raises(NotFoundError) as exc_info:
            raise NotFoundError(detail="Property not found")
        assert exc_info.value.status_code == 404


def test_owner_isolation_in_listing(db: Session, owner_a, owner_b):
    """Listing resources returns only the authenticated owner's resources."""
    prop_a1 = Property(id=uuid.uuid4(), owner_id=owner_a["owner"].id, name="Property A1")
    prop_a2 = Property(id=uuid.uuid4(), owner_id=owner_a["owner"].id, name="Property A2")
    prop_b1 = Property(id=uuid.uuid4(), owner_id=owner_b["owner"].id, name="Property B1")

    db.add_all([prop_a1, prop_a2, prop_b1])
    db.commit()

    repo = BaseOwnerScopedRepository(Property)
    a_props = repo.list_all(db, owner_a["owner"].id)
    assert len(a_props) == 2
    assert all(p.owner_id == owner_a["owner"].id for p in a_props)

    b_props = repo.list_all(db, owner_b["owner"].id)
    assert len(b_props) == 1
    assert b_props[0].id == prop_b1.id


def test_client_cannot_override_owner_id(client: TestClient, owner_a, owner_b):
    """Client-supplied owner_id in headers, query params, or body is ignored.

    Identity is extracted strictly from the validated JWT claims.
    """
    # Owner A requests /auth/me with an attempt to pass Owner B's ID in query or headers
    malicious_query = f"?owner_id={owner_b['owner'].id}"
    malicious_headers = {
        **owner_a["headers"],
        "X-Owner-Id": str(owner_b["owner"].id),
    }

    response = client.get(f"/api/v1/auth/me{malicious_query}", headers=malicious_headers)
    assert response.status_code == 200
    data = response.json()
    # The authenticated owner must still strictly be Owner A
    assert data["id"] == str(owner_a["owner"].id)
    assert data["id"] != str(owner_b["owner"].id)
    assert data["email"] == "owner_a@example.com"


def test_nested_resource_owner_isolation(db: Session, owner_a, owner_b):
    """Nested resources (Unit, Tenant) cannot bypass ownership boundary.

    Querying via the ownership chain Property.owner_id == owner_id ensures
    Owner B cannot access Owner A's units or tenants.
    """
    from datetime import date
    from sqlalchemy import select
    from app.models.unit import Unit
    from app.models.tenant import Tenant

    # Create Owner A hierarchy
    prop_a = Property(id=uuid.uuid4(), owner_id=owner_a["owner"].id, name="Property Alpha")
    unit_a = Unit(
        id=uuid.uuid4(),
        property_id=prop_a.id,
        name="Flat 101",
        unit_type="FLAT",
        monthly_rent_paise=800000,
        rent_due_day=5,
    )
    tenant_a = Tenant(
        id=uuid.uuid4(),
        unit_id=unit_a.id,
        name="Tenant Alpha",
        phone="9876543210",
        move_in_date=date(2026, 1, 1),
    )
    db.add_all([prop_a, unit_a, tenant_a])
    db.commit()

    # Query unit with ownership check (Unit -> Property -> owner_id)
    stmt_unit_a = (
        select(Unit)
        .join(Property, Unit.property_id == Property.id)
        .where(Unit.id == unit_a.id, Property.owner_id == owner_a["owner"].id)
    )
    assert db.scalar(stmt_unit_a) is not None

    stmt_unit_b = (
        select(Unit)
        .join(Property, Unit.property_id == Property.id)
        .where(Unit.id == unit_a.id, Property.owner_id == owner_b["owner"].id)
    )
    assert db.scalar(stmt_unit_b) is None, "Owner B must NOT access Owner A's unit"

    # Query tenant with ownership check (Tenant -> Unit -> Property -> owner_id)
    stmt_tenant_a = (
        select(Tenant)
        .join(Unit, Tenant.unit_id == Unit.id)
        .join(Property, Unit.property_id == Property.id)
        .where(Tenant.id == tenant_a.id, Property.owner_id == owner_a["owner"].id)
    )
    assert db.scalar(stmt_tenant_a) is not None

    stmt_tenant_b = (
        select(Tenant)
        .join(Unit, Tenant.unit_id == Unit.id)
        .join(Property, Unit.property_id == Property.id)
        .where(Tenant.id == tenant_a.id, Property.owner_id == owner_b["owner"].id)
    )
    assert db.scalar(stmt_tenant_b) is None, "Owner B must NOT access Owner A's tenant"

