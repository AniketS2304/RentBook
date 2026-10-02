import uuid
from fastapi.testclient import TestClient


def _create_property(client: TestClient, headers, name: str = "Base Prop"):
    res = client.post("/api/v1/properties", json={"name": name}, headers=headers)
    assert res.status_code == 201
    return res.json()["id"]


def test_create_unit_success(client: TestClient, owner_a):
    """Owner can successfully create a unit under their property."""
    prop_id = _create_property(client, owner_a["headers"], "Unit Parent Prop")

    payload = {
        "name": "Flat 101",
        "unit_type": "FLAT",
        "monthly_rent_paise": 800000,
        "rent_due_day": 5,
        "notes": "First floor corner",
    }
    response = client.post(
        f"/api/v1/properties/{prop_id}/units",
        json=payload,
        headers=owner_a["headers"],
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Flat 101"
    assert data["unit_type"] == "FLAT"
    assert data["monthly_rent_paise"] == 800000
    assert data["rent_due_day"] == 5
    assert data["property_id"] == prop_id
    assert data["is_occupied"] is False
    assert data["current_tenant"] is None
    assert data["archived_at"] is None


def test_create_unit_validation_errors(client: TestClient, owner_a):
    """Validation rejects invalid unit parameters (rent <= 0, due_day not 1-28, bad unit_type)."""
    prop_id = _create_property(client, owner_a["headers"], "Validation Prop")

    # Invalid monthly_rent_paise: 0
    res_rent_zero = client.post(
        f"/api/v1/properties/{prop_id}/units",
        json={"name": "U1", "unit_type": "FLAT", "monthly_rent_paise": 0, "rent_due_day": 5},
        headers=owner_a["headers"],
    )
    assert res_rent_zero.status_code == 422

    # Invalid rent_due_day: 29 (must be 1-28 per BR-UNIT-03)
    res_due_29 = client.post(
        f"/api/v1/properties/{prop_id}/units",
        json={"name": "U2", "unit_type": "FLAT", "monthly_rent_paise": 500000, "rent_due_day": 29},
        headers=owner_a["headers"],
    )
    assert res_due_29.status_code == 422

    # Invalid rent_due_day: 0
    res_due_0 = client.post(
        f"/api/v1/properties/{prop_id}/units",
        json={"name": "U3", "unit_type": "FLAT", "monthly_rent_paise": 500000, "rent_due_day": 0},
        headers=owner_a["headers"],
    )
    assert res_due_0.status_code == 422

    # Invalid unit_type: VILLA (not in FLAT, ROOM, SHOP, OTHER)
    res_bad_type = client.post(
        f"/api/v1/properties/{prop_id}/units",
        json={"name": "U4", "unit_type": "VILLA", "monthly_rent_paise": 500000, "rent_due_day": 10},
        headers=owner_a["headers"],
    )
    assert res_bad_type.status_code == 422


def test_create_unit_duplicate_name_in_same_property(client: TestClient, owner_a):
    """Duplicate active unit name within the same property returns 409 Conflict."""
    prop_id = _create_property(client, owner_a["headers"], "Dup Unit Prop")
    payload = {
        "name": "Shop A",
        "unit_type": "SHOP",
        "monthly_rent_paise": 1500000,
        "rent_due_day": 1,
    }
    res1 = client.post(f"/api/v1/properties/{prop_id}/units", json=payload, headers=owner_a["headers"])
    assert res1.status_code == 201

    res2 = client.post(f"/api/v1/properties/{prop_id}/units", json=payload, headers=owner_a["headers"])
    assert res2.status_code == 409
    assert res2.json()["code"] == "UNIT_NAME_EXISTS"


def test_same_unit_name_after_archive_succeeds(client: TestClient, owner_a):
    """Archiving a unit allows creating a new active unit with the same name in that property."""
    prop_id = _create_property(client, owner_a["headers"], "Unit Archive Name Prop")
    payload = {
        "name": "Room 101",
        "unit_type": "ROOM",
        "monthly_rent_paise": 400000,
        "rent_due_day": 5,
    }
    res1 = client.post(f"/api/v1/properties/{prop_id}/units", json=payload, headers=owner_a["headers"])
    assert res1.status_code == 201
    unit_id = res1.json()["id"]

    # Archive the unit
    del_res = client.delete(f"/api/v1/units/{unit_id}", headers=owner_a["headers"])
    assert del_res.status_code == 200

    # Re-create unit with same name
    res2 = client.post(f"/api/v1/properties/{prop_id}/units", json=payload, headers=owner_a["headers"])
    assert res2.status_code == 201
    assert res2.json()["id"] != unit_id


def test_list_property_units(client: TestClient, owner_a):
    """List units returns active units by default, and includes archived when specified."""
    prop_id = _create_property(client, owner_a["headers"], "Listing Units Prop")

    u1_res = client.post(
        f"/api/v1/properties/{prop_id}/units",
        json={"name": "Unit 1", "unit_type": "FLAT", "monthly_rent_paise": 600000, "rent_due_day": 5},
        headers=owner_a["headers"],
    )
    u2_res = client.post(
        f"/api/v1/properties/{prop_id}/units",
        json={"name": "Unit 2", "unit_type": "FLAT", "monthly_rent_paise": 700000, "rent_due_day": 10},
        headers=owner_a["headers"],
    )
    unit2_id = u2_res.json()["id"]

    # Archive unit 2
    client.delete(f"/api/v1/units/{unit2_id}", headers=owner_a["headers"])

    # Active units
    res_active = client.get(f"/api/v1/properties/{prop_id}/units", headers=owner_a["headers"])
    assert res_active.status_code == 200
    active_items = res_active.json()
    assert len(active_items) == 1
    assert active_items[0]["name"] == "Unit 1"

    # All units including archived
    res_all = client.get(f"/api/v1/properties/{prop_id}/units?include_archived=true", headers=owner_a["headers"])
    assert res_all.status_code == 200
    all_items = res_all.json()
    assert len(all_items) == 2


def test_get_and_update_unit(client: TestClient, owner_a):
    """Get single unit and update attributes."""
    prop_id = _create_property(client, owner_a["headers"], "Get Update Prop")
    u_res = client.post(
        f"/api/v1/properties/{prop_id}/units",
        json={"name": "Initial Unit", "unit_type": "FLAT", "monthly_rent_paise": 800000, "rent_due_day": 5},
        headers=owner_a["headers"],
    )
    unit_id = u_res.json()["id"]

    # GET
    get_res = client.get(f"/api/v1/units/{unit_id}", headers=owner_a["headers"])
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Initial Unit"

    # PATCH
    patch_res = client.patch(
        f"/api/v1/units/{unit_id}",
        json={"name": "Updated Unit", "monthly_rent_paise": 850000, "rent_due_day": 10},
        headers=owner_a["headers"],
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["name"] == "Updated Unit"
    assert data["monthly_rent_paise"] == 850000
    assert data["rent_due_day"] == 10


def test_cannot_create_unit_under_other_owners_property(client: TestClient, owner_a, owner_b):
    """Owner B cannot attach a unit to Owner A's property; returns 404."""
    prop_a_id = _create_property(client, owner_a["headers"], "Owner A Exclusive Prop")

    payload = {
        "name": "Intruder Unit",
        "unit_type": "FLAT",
        "monthly_rent_paise": 1000000,
        "rent_due_day": 1,
    }
    # Owner B tries to create unit under Owner A's property
    cross_create = client.post(
        f"/api/v1/properties/{prop_a_id}/units",
        json=payload,
        headers=owner_b["headers"],
    )
    assert cross_create.status_code == 404
    assert cross_create.json()["code"] == "NOT_FOUND"


def test_cross_owner_unit_access_hierarchy(client: TestClient, owner_a, owner_b):
    """Full cross-owner hierarchy isolation test:

    Owner A: Property A -> Unit A
    Owner B: Property B -> Unit B

    Verify B cannot GET, UPDATE, ARCHIVE Unit A, and A cannot touch Unit B.
    """
    prop_a_id = _create_property(client, owner_a["headers"], "Alpha Prop")
    unit_a_res = client.post(
        f"/api/v1/properties/{prop_a_id}/units",
        json={"name": "A-101", "unit_type": "FLAT", "monthly_rent_paise": 500000, "rent_due_day": 5},
        headers=owner_a["headers"],
    )
    unit_a_id = unit_a_res.json()["id"]

    prop_b_id = _create_property(client, owner_b["headers"], "Beta Prop")
    unit_b_res = client.post(
        f"/api/v1/properties/{prop_b_id}/units",
        json={"name": "B-201", "unit_type": "ROOM", "monthly_rent_paise": 400000, "rent_due_day": 10},
        headers=owner_b["headers"],
    )
    unit_b_id = unit_b_res.json()["id"]

    # 1. B cannot GET A's unit
    res_b_get_a = client.get(f"/api/v1/units/{unit_a_id}", headers=owner_b["headers"])
    assert res_b_get_a.status_code == 404
    assert res_b_get_a.json()["code"] == "NOT_FOUND"

    # 2. B cannot list units of A's property
    res_b_list_a = client.get(f"/api/v1/properties/{prop_a_id}/units", headers=owner_b["headers"])
    assert res_b_list_a.status_code == 404

    # 3. B cannot PATCH A's unit
    res_b_patch_a = client.patch(
        f"/api/v1/units/{unit_a_id}",
        json={"name": "Hacked Unit"},
        headers=owner_b["headers"],
    )
    assert res_b_patch_a.status_code == 404

    # 4. B cannot DELETE/ARCHIVE A's unit
    res_b_del_a = client.delete(f"/api/v1/units/{unit_a_id}", headers=owner_b["headers"])
    assert res_b_del_a.status_code == 404

    # 5. Reverse: A cannot GET, PATCH, DELETE B's unit
    assert client.get(f"/api/v1/units/{unit_b_id}", headers=owner_a["headers"]).status_code == 404
    assert client.patch(f"/api/v1/units/{unit_b_id}", json={"name": "Hack"}, headers=owner_a["headers"]).status_code == 404
    assert client.delete(f"/api/v1/units/{unit_b_id}", headers=owner_a["headers"]).status_code == 404


def test_archive_unit_success(client: TestClient, owner_a):
    """Archiving a unit sets archived_at and returns success response."""
    prop_id = _create_property(client, owner_a["headers"], "Archive Unit Target Prop")
    unit_res = client.post(
        f"/api/v1/properties/{prop_id}/units",
        json={"name": "Archive Target Unit", "unit_type": "FLAT", "monthly_rent_paise": 600000, "rent_due_day": 1},
        headers=owner_a["headers"],
    )
    unit_id = unit_res.json()["id"]

    del_res = client.delete(f"/api/v1/units/{unit_id}", headers=owner_a["headers"])
    assert del_res.status_code == 200
    data = del_res.json()
    assert data["message"] == "Unit archived successfully"
    assert data["archived_at"] is not None

