import datetime
import uuid
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.tenant import Tenant


def _create_property_and_unit(client: TestClient, headers, prop_name="Test Prop", unit_name="Flat 101"):
    p_res = client.post("/api/v1/properties", json={"name": prop_name}, headers=headers)
    assert p_res.status_code == 201
    prop_id = p_res.json()["id"]

    u_res = client.post(
        f"/api/v1/properties/{prop_id}/units",
        json={
            "name": unit_name,
            "unit_type": "FLAT",
            "monthly_rent_paise": 1000000,
            "rent_due_day": 5,
        },
        headers=headers,
    )
    assert u_res.status_code == 201
    unit_id = u_res.json()["id"]
    return prop_id, unit_id


def test_create_tenant_success(client: TestClient, owner_a):
    """Owner successfully moves a tenant into a vacant unit."""
    prop_id, unit_id = _create_property_and_unit(client, owner_a["headers"], "Tenant Prop 1", "101")

    payload = {
        "unit_id": unit_id,
        "name": "Rahul Sharma",
        "phone": "9876543210",
        "email": "rahul@example.com",
        "move_in_date": "2026-10-01",
        "security_deposit_paise": 2000000,
        "notes": "Verified Aadhaar and company ID",
    }
    response = client.post("/api/v1/tenants", json=payload, headers=owner_a["headers"])
    assert response.status_code == 201
    data = response.json()

    assert data["name"] == "Rahul Sharma"
    assert data["phone"] == "9876543210"
    assert data["email"] == "rahul@example.com"
    assert data["unit"]["id"] == unit_id
    assert data["unit"]["name"] == "101"
    assert data["unit"]["property_name"] == "Tenant Prop 1"
    assert data["status"] == "ACTIVE"
    assert data["move_in_date"] == "2026-10-01"
    assert data["move_out_date"] is None
    assert data["security_deposit_paise"] == 2000000
    assert data["rent_history"] == []

    # Check unit reflects occupancy
    unit_res = client.get(f"/api/v1/units/{unit_id}", headers=owner_a["headers"])
    assert unit_res.status_code == 200
    unit_data = unit_res.json()
    assert unit_data["is_occupied"] is True
    assert unit_data["current_tenant"]["id"] == data["id"]
    assert unit_data["current_tenant"]["name"] == "Rahul Sharma"


def test_create_tenant_duplicate_active_conflict(client: TestClient, owner_a):
    """Attempting to assign a second active tenant to an already occupied unit fails with 409 Conflict."""
    _, unit_id = _create_property_and_unit(client, owner_a["headers"], "Dup Tenant Prop", "102")

    # First tenant moves in
    res1 = client.post(
        "/api/v1/tenants",
        json={
            "unit_id": unit_id,
            "name": "Amit Patel",
            "phone": "9123456780",
            "move_in_date": "2026-10-01",
        },
        headers=owner_a["headers"],
    )
    assert res1.status_code == 201

    # Second tenant tries to move into same occupied unit
    res2 = client.post(
        "/api/v1/tenants",
        json={
            "unit_id": unit_id,
            "name": "Suresh Kumar",
            "phone": "9876543219",
            "move_in_date": "2026-10-05",
        },
        headers=owner_a["headers"],
    )
    assert res2.status_code == 409
    data = res2.json()
    assert data["code"] == "UNIT_OCCUPIED"
    assert "Amit Patel" in data["detail"]
    assert "102" in data["detail"]


def test_move_out_and_reoccupy_unit(client: TestClient, owner_a):
    """Deactivating tenant frees the unit, allowing a new active tenant while preserving history."""
    _, unit_id = _create_property_and_unit(client, owner_a["headers"], "Reoccupy Prop", "103")

    # 1. Tenant 1 moves in
    t1_res = client.post(
        "/api/v1/tenants",
        json={
            "unit_id": unit_id,
            "name": "Original Tenant",
            "phone": "9876500001",
            "move_in_date": "2026-01-01",
            "security_deposit_paise": 1500000,
        },
        headers=owner_a["headers"],
    )
    assert t1_res.status_code == 201
    t1_id = t1_res.json()["id"]

    # 2. Deactivate Tenant 1 (move-out)
    deact_res = client.post(
        f"/api/v1/tenants/{t1_id}/deactivate",
        json={"move_out_date": "2026-06-30"},
        headers=owner_a["headers"],
    )
    assert deact_res.status_code == 200
    deact_data = deact_res.json()
    assert deact_data["tenant_status"] == "INACTIVE"
    assert deact_data["unit_status"] == "VACANT"

    # Unit is now vacant
    unit_res = client.get(f"/api/v1/units/{unit_id}", headers=owner_a["headers"])
    assert unit_res.json()["is_occupied"] is False
    assert unit_res.json()["current_tenant"] is None

    # Tenant 1 record is preserved with move_out_date
    t1_get = client.get(f"/api/v1/tenants/{t1_id}", headers=owner_a["headers"])
    assert t1_get.status_code == 200
    assert t1_get.json()["status"] == "INACTIVE"
    assert t1_get.json()["move_out_date"] == "2026-06-30"

    # 3. New tenant moves into same unit successfully
    t2_res = client.post(
        "/api/v1/tenants",
        json={
            "unit_id": unit_id,
            "name": "New Tenant",
            "phone": "9876500002",
            "move_in_date": "2026-07-01",
            "security_deposit_paise": 1800000,
        },
        headers=owner_a["headers"],
    )
    assert t2_res.status_code == 201
    t2_id = t2_res.json()["id"]
    assert t2_id != t1_id

    # Unit is occupied again by Tenant 2
    unit_res2 = client.get(f"/api/v1/units/{unit_id}", headers=owner_a["headers"])
    assert unit_res2.json()["is_occupied"] is True
    assert unit_res2.json()["current_tenant"]["id"] == t2_id


def test_get_tenant_detail(client: TestClient, owner_a):
    """GET /api/v1/tenants/{tenant_id} returns full tenant info."""
    _, unit_id = _create_property_and_unit(client, owner_a["headers"], "Get Detail Prop", "201")

    res = client.post(
        "/api/v1/tenants",
        json={
            "unit_id": unit_id,
            "name": "Priya Nair",
            "phone": "9876543200",
            "move_in_date": "2026-10-15",
            "security_deposit_paise": 1000000,
            "notes": "Key handed over",
        },
        headers=owner_a["headers"],
    )
    tenant_id = res.json()["id"]

    get_res = client.get(f"/api/v1/tenants/{tenant_id}", headers=owner_a["headers"])
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == tenant_id
    assert data["name"] == "Priya Nair"
    assert data["notes"] == "Key handed over"
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


def test_list_tenants_filtering_and_pagination(client: TestClient, owner_a):
    """Test listing tenants with status filtering and property filtering."""
    prop1_id, u1_id = _create_property_and_unit(client, owner_a["headers"], "List Prop 1", "U1")
    prop2_id, u2_id = _create_property_and_unit(client, owner_a["headers"], "List Prop 2", "U2")

    # Add tenant to prop1
    t1 = client.post(
        "/api/v1/tenants",
        json={"unit_id": u1_id, "name": "Tenant One", "phone": "9876511111", "move_in_date": "2026-01-01"},
        headers=owner_a["headers"],
    ).json()

    # Add tenant to prop2 and deactivate
    t2 = client.post(
        "/api/v1/tenants",
        json={"unit_id": u2_id, "name": "Tenant Two", "phone": "9876522222", "move_in_date": "2026-02-01"},
        headers=owner_a["headers"],
    ).json()
    client.post(f"/api/v1/tenants/{t2['id']}/deactivate", json={}, headers=owner_a["headers"])

    # 1. Default list: returns ACTIVE tenants only
    res_default = client.get("/api/v1/tenants", headers=owner_a["headers"])
    assert res_default.status_code == 200
    items_default = res_default.json()["items"]
    assert any(item["id"] == t1["id"] for item in items_default)
    assert not any(item["id"] == t2["id"] for item in items_default)

    # 2. Filter status=INACTIVE
    res_inactive = client.get("/api/v1/tenants?status=INACTIVE", headers=owner_a["headers"])
    assert res_inactive.status_code == 200
    items_inactive = res_inactive.json()["items"]
    assert any(item["id"] == t2["id"] for item in items_inactive)
    assert not any(item["id"] == t1["id"] for item in items_inactive)

    # 3. Filter by property_id
    res_prop1 = client.get(f"/api/v1/tenants?property_id={prop1_id}", headers=owner_a["headers"])
    assert res_prop1.status_code == 200
    items_prop1 = res_prop1.json()["items"]
    assert len(items_prop1) == 1
    assert items_prop1[0]["id"] == t1["id"]


def test_update_tenant(client: TestClient, owner_a):
    """PATCH /api/v1/tenants/{tenant_id} allows updating contact info, notes, and deposit."""
    _, unit_id = _create_property_and_unit(client, owner_a["headers"], "Update Prop", "301")

    create_res = client.post(
        "/api/v1/tenants",
        json={
            "unit_id": unit_id,
            "name": "Old Name",
            "phone": "9876543210",
            "move_in_date": "2026-05-01",
            "security_deposit_paise": 1000000,
        },
        headers=owner_a["headers"],
    )
    tenant_id = create_res.json()["id"]

    patch_res = client.patch(
        f"/api/v1/tenants/{tenant_id}",
        json={
            "name": "New Name",
            "phone": "9876543211",
            "email": "updated@example.com",
            "security_deposit_paise": 1200000,
            "notes": "Added company letter",
        },
        headers=owner_a["headers"],
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["name"] == "New Name"
    assert data["phone"] == "9876543211"
    assert data["email"] == "updated@example.com"
    assert data["security_deposit_paise"] == 1200000
    assert data["notes"] == "Added company letter"


def test_deactivate_tenant_validations(client: TestClient, owner_a):
    """Deactivation rejects already inactive tenant or move_out_date before move_in_date."""
    _, unit_id = _create_property_and_unit(client, owner_a["headers"], "Deact Val Prop", "401")

    create_res = client.post(
        "/api/v1/tenants",
        json={
            "unit_id": unit_id,
            "name": "Deact Tenant",
            "phone": "9876543210",
            "move_in_date": "2026-06-01",
        },
        headers=owner_a["headers"],
    )
    tenant_id = create_res.json()["id"]

    # 1. Invalid move_out_date (before move_in_date)
    bad_date_res = client.post(
        f"/api/v1/tenants/{tenant_id}/deactivate",
        json={"move_out_date": "2026-05-31"},
        headers=owner_a["headers"],
    )
    assert bad_date_res.status_code == 400
    assert bad_date_res.json()["code"] == "INVALID_DATE_RANGE"

    # 2. Successful deactivation
    good_res = client.post(
        f"/api/v1/tenants/{tenant_id}/deactivate",
        json={"move_out_date": "2026-06-15"},
        headers=owner_a["headers"],
    )
    assert good_res.status_code == 200

    # 3. Repeated deactivation fails
    repeat_res = client.post(
        f"/api/v1/tenants/{tenant_id}/deactivate",
        json={"move_out_date": "2026-06-20"},
        headers=owner_a["headers"],
    )
    assert repeat_res.status_code == 400
    assert repeat_res.json()["code"] == "TENANT_ALREADY_INACTIVE"


def test_update_tenant_invalid_date_range(client: TestClient, owner_a):
    """Updating move_in_date after move_out_date on an inactive tenant returns 400."""
    _, unit_id = _create_property_and_unit(client, owner_a["headers"], "Date Range Prop", "501")

    t = client.post(
        "/api/v1/tenants",
        json={"unit_id": unit_id, "name": "Date Test", "phone": "9876543210", "move_in_date": "2026-01-01"},
        headers=owner_a["headers"],
    ).json()

    # Move out on 2026-03-01
    client.post(f"/api/v1/tenants/{t['id']}/deactivate", json={"move_out_date": "2026-03-01"}, headers=owner_a["headers"])

    # Try updating move_in_date to 2026-04-01 (after move_out_date)
    res = client.patch(
        f"/api/v1/tenants/{t['id']}",
        json={"move_in_date": "2026-04-01"},
        headers=owner_a["headers"],
    )
    assert res.status_code == 400
    assert res.json()["code"] == "INVALID_DATE_RANGE"


def test_cannot_create_tenant_in_archived_unit(client: TestClient, owner_a):
    """Cannot assign a tenant to an archived unit; returns 400 UNIT_ARCHIVED."""
    _, unit_id = _create_property_and_unit(client, owner_a["headers"], "Arch Unit Prop", "Archived 101")

    # Archive unit
    client.delete(f"/api/v1/units/{unit_id}", headers=owner_a["headers"])

    # Attempt to move in tenant
    res = client.post(
        "/api/v1/tenants",
        json={"unit_id": unit_id, "name": "Blocked Tenant", "phone": "9876543210", "move_in_date": "2026-10-01"},
        headers=owner_a["headers"],
    )
    assert res.status_code == 400
    assert res.json()["code"] == "UNIT_ARCHIVED"


def test_cannot_create_tenant_in_archived_property(client: TestClient, owner_a):
    """Cannot assign a tenant to a unit in an archived property; returns 400 PROPERTY_ARCHIVED."""
    prop_id, unit_id = _create_property_and_unit(client, owner_a["headers"], "Arch Prop Test", "Unit 99")

    # Archive property
    client.delete(f"/api/v1/properties/{prop_id}", headers=owner_a["headers"])

    # Attempt to move in tenant
    res = client.post(
        "/api/v1/tenants",
        json={"unit_id": unit_id, "name": "Blocked Tenant", "phone": "9876543210", "move_in_date": "2026-10-01"},
        headers=owner_a["headers"],
    )
    assert res.status_code == 400
    assert res.json()["code"] == "PROPERTY_ARCHIVED"


def test_tenant_validation_errors(client: TestClient, owner_a):
    """Validation rejects invalid tenant inputs."""
    _, unit_id = _create_property_and_unit(client, owner_a["headers"], "Val Errors Prop", "601")

    # 1. Invalid phone number (not 10 digits)
    res_phone = client.post(
        "/api/v1/tenants",
        json={"unit_id": unit_id, "name": "Bad Phone", "phone": "12345", "move_in_date": "2026-10-01"},
        headers=owner_a["headers"],
    )
    assert res_phone.status_code == 422

    # 2. Negative security deposit
    res_dep = client.post(
        "/api/v1/tenants",
        json={"unit_id": unit_id, "name": "Bad Dep", "phone": "9876543210", "move_in_date": "2026-10-01", "security_deposit_paise": -500},
        headers=owner_a["headers"],
    )
    assert res_dep.status_code == 422

    # 3. Extra forbidden field (status injected by client)
    res_extra = client.post(
        "/api/v1/tenants",
        json={"unit_id": unit_id, "name": "Extra Injected", "phone": "9876543210", "move_in_date": "2026-10-01", "status": "INACTIVE"},
        headers=owner_a["headers"],
    )
    assert res_extra.status_code == 422

    # 4. Unknown unit_id
    res_missing_unit = client.post(
        "/api/v1/tenants",
        json={"unit_id": str(uuid.uuid4()), "name": "Ghost Unit", "phone": "9876543210", "move_in_date": "2026-10-01"},
        headers=owner_a["headers"],
    )
    assert res_missing_unit.status_code == 404


def test_cross_owner_tenant_hierarchy_isolation(client: TestClient, owner_a, owner_b):
    """Full cross-owner hierarchy isolation test:

    Owner A: Property A -> Unit A -> Tenant A
    Owner B: Property B -> Unit B -> Tenant B

    Verify B cannot GET, UPDATE, DEACTIVATE Tenant A, and cannot assign a tenant to Unit A.
    Verify A cannot touch Tenant B.
    All cross-owner attempts must return 404 (never leaking existence).
    """
    prop_a_id, unit_a_id = _create_property_and_unit(client, owner_a["headers"], "Alpha Prop", "A-101")
    t_a_res = client.post(
        "/api/v1/tenants",
        json={"unit_id": unit_a_id, "name": "Tenant Alpha", "phone": "9876511111", "move_in_date": "2026-01-01"},
        headers=owner_a["headers"],
    )
    assert t_a_res.status_code == 201
    t_a_id = t_a_res.json()["id"]

    prop_b_id, unit_b_id = _create_property_and_unit(client, owner_b["headers"], "Beta Prop", "B-201")
    t_b_res = client.post(
        "/api/v1/tenants",
        json={"unit_id": unit_b_id, "name": "Tenant Beta", "phone": "9876522222", "move_in_date": "2026-02-01"},
        headers=owner_b["headers"],
    )
    assert t_b_res.status_code == 201
    t_b_id = t_b_res.json()["id"]

    # 1. B cannot GET A's tenant -> 404
    assert client.get(f"/api/v1/tenants/{t_a_id}", headers=owner_b["headers"]).status_code == 404

    # 2. B cannot PATCH A's tenant -> 404
    assert client.patch(f"/api/v1/tenants/{t_a_id}", json={"name": "Hacked"}, headers=owner_b["headers"]).status_code == 404

    # 3. B cannot DEACTIVATE A's tenant -> 404
    assert client.post(f"/api/v1/tenants/{t_a_id}/deactivate", json={}, headers=owner_b["headers"]).status_code == 404

    # 4. B cannot create a tenant in A's unit -> 404
    cross_create = client.post(
        "/api/v1/tenants",
        json={"unit_id": unit_a_id, "name": "Intruder", "phone": "9876533333", "move_in_date": "2026-03-01"},
        headers=owner_b["headers"],
    )
    assert cross_create.status_code == 404

    # 5. B cannot filter tenants by A's property_id -> 404
    assert client.get(f"/api/v1/tenants?property_id={prop_a_id}", headers=owner_b["headers"]).status_code == 404

    # 6. Listing isolation: A sees only Tenant Alpha; B sees only Tenant Beta
    list_a = client.get("/api/v1/tenants", headers=owner_a["headers"]).json()["items"]
    assert any(item["id"] == t_a_id for item in list_a)
    assert not any(item["id"] == t_b_id for item in list_a)

    list_b = client.get("/api/v1/tenants", headers=owner_b["headers"]).json()["items"]
    assert any(item["id"] == t_b_id for item in list_b)
    assert not any(item["id"] == t_a_id for item in list_b)

    # 7. Reverse: A cannot touch Tenant Beta
    assert client.get(f"/api/v1/tenants/{t_b_id}", headers=owner_a["headers"]).status_code == 404
    assert client.patch(f"/api/v1/tenants/{t_b_id}", json={"name": "Hacked"}, headers=owner_a["headers"]).status_code == 404
    assert client.post(f"/api/v1/tenants/{t_b_id}/deactivate", json={}, headers=owner_a["headers"]).status_code == 404


def test_db_unique_constraint_concurrency(db):
    """Direct database test verifying uq_tenants_unit_active rejects concurrent active tenants."""
    from app.models.owner import Owner
    from app.models.property import Property
    from app.models.unit import Unit

    owner = Owner(email="concurrent@example.com", password_hash="hash", full_name="Owner C")
    db.add(owner)
    db.flush()

    prop = Property(owner_id=owner.id, name="Concurrent Prop")
    db.add(prop)
    db.flush()

    unit = Unit(
        property_id=prop.id,
        name="Unit C1",
        unit_type="FLAT",
        monthly_rent_paise=500000,
        rent_due_day=5,
    )
    db.add(unit)
    db.flush()

    t1 = Tenant(
        unit_id=unit.id,
        name="Active Tenant 1",
        phone="9876500010",
        move_in_date=datetime.date(2026, 1, 1),
        status="ACTIVE",
    )
    db.add(t1)
    db.commit()

    # Second active tenant on same unit directly at DB level must raise IntegrityError
    t2 = Tenant(
        unit_id=unit.id,
        name="Active Tenant 2",
        phone="9876500020",
        move_in_date=datetime.date(2026, 1, 1),
        status="ACTIVE",
    )
    db.add(t2)
    with pytest.raises(IntegrityError):
        db.commit()

    db.rollback()
