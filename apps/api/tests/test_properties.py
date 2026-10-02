import uuid
from fastapi.testclient import TestClient


def test_create_property_success(client: TestClient, owner_a):
    """Owner can successfully create a property."""
    payload = {
        "name": "Shree Residency",
        "address": "123, MG Road, Pune",
        "notes": "Near railway station",
    }
    response = client.post("/api/v1/properties", json=payload, headers=owner_a["headers"])
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Shree Residency"
    assert data["address"] == "123, MG Road, Pune"
    assert data["notes"] == "Near railway station"
    assert data["unit_count"] == 0
    assert data["occupied_count"] == 0
    assert data["vacant_count"] == 0
    assert data["archived_at"] is None
    assert "id" in data


def test_create_property_duplicate_name_conflict(client: TestClient, owner_a):
    """Creating an active property with duplicate name for same owner returns 409 Conflict."""
    payload = {"name": "Duplicate Residency"}
    res1 = client.post("/api/v1/properties", json=payload, headers=owner_a["headers"])
    assert res1.status_code == 201

    res2 = client.post("/api/v1/properties", json=payload, headers=owner_a["headers"])
    assert res2.status_code == 409
    assert res2.json()["code"] == "PROPERTY_NAME_EXISTS"


def test_create_property_same_name_after_archive(client: TestClient, owner_a):
    """A property can be created with the same name if the previous one is archived."""
    payload = {"name": "Green Valley"}
    res1 = client.post("/api/v1/properties", json=payload, headers=owner_a["headers"])
    assert res1.status_code == 201
    prop_id = res1.json()["id"]

    # Archive first property
    arch_res = client.delete(f"/api/v1/properties/{prop_id}", headers=owner_a["headers"])
    assert arch_res.status_code == 200

    # Create new property with the same name
    res2 = client.post("/api/v1/properties", json=payload, headers=owner_a["headers"])
    assert res2.status_code == 201
    assert res2.json()["id"] != prop_id
    assert res2.json()["name"] == "Green Valley"


def test_create_property_same_name_different_owners(client: TestClient, owner_a, owner_b):
    """Different owners can have properties with the same name."""
    payload = {"name": "Ganesh Heights"}
    res_a = client.post("/api/v1/properties", json=payload, headers=owner_a["headers"])
    assert res_a.status_code == 201

    res_b = client.post("/api/v1/properties", json=payload, headers=owner_b["headers"])
    assert res_b.status_code == 201


def test_list_properties(client: TestClient, owner_a, owner_b):
    """Owner lists only their properties, with pagination and include_archived support."""
    # Create 2 properties for Owner A
    res1 = client.post(
        "/api/v1/properties",
        json={"name": "Owner A Prop 1"},
        headers=owner_a["headers"],
    )
    res2 = client.post(
        "/api/v1/properties",
        json={"name": "Owner A Prop 2"},
        headers=owner_a["headers"],
    )
    # Create 1 property for Owner B
    client.post(
        "/api/v1/properties",
        json={"name": "Owner B Prop 1"},
        headers=owner_b["headers"],
    )

    # Archive Prop 2 of Owner A
    client.delete(f"/api/v1/properties/{res2.json()['id']}", headers=owner_a["headers"])

    # Active listing (default) for Owner A should show only Prop 1
    list_active = client.get("/api/v1/properties", headers=owner_a["headers"])
    assert list_active.status_code == 200
    active_data = list_active.json()
    assert any(p["name"] == "Owner A Prop 1" for p in active_data["items"])
    assert not any(p["name"] == "Owner A Prop 2" for p in active_data["items"])
    assert not any(p["name"] == "Owner B Prop 1" for p in active_data["items"])

    # include_archived=true for Owner A should show both
    list_all = client.get("/api/v1/properties?include_archived=true", headers=owner_a["headers"])
    assert list_all.status_code == 200
    all_data = list_all.json()
    assert any(p["name"] == "Owner A Prop 1" for p in all_data["items"])
    assert any(p["name"] == "Owner A Prop 2" for p in all_data["items"])
    assert not any(p["name"] == "Owner B Prop 1" for p in all_data["items"])


def test_get_property_detail(client: TestClient, owner_a):
    """Get property detail returns full object with units."""
    create_res = client.post(
        "/api/v1/properties",
        json={"name": "Detail Prop", "address": "Detailed St"},
        headers=owner_a["headers"],
    )
    prop_id = create_res.json()["id"]

    get_res = client.get(f"/api/v1/properties/{prop_id}", headers=owner_a["headers"])
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == prop_id
    assert data["name"] == "Detail Prop"
    assert isinstance(data["units"], list)


def test_update_property(client: TestClient, owner_a):
    """Owner can update property name and address."""
    create_res = client.post(
        "/api/v1/properties",
        json={"name": "Old Prop Name", "address": "Old Address"},
        headers=owner_a["headers"],
    )
    prop_id = create_res.json()["id"]

    patch_res = client.patch(
        f"/api/v1/properties/{prop_id}",
        json={"name": "New Prop Name", "notes": "Added notes"},
        headers=owner_a["headers"],
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["name"] == "New Prop Name"
    assert data["address"] == "Old Address"
    assert data["notes"] == "Added notes"


def test_update_property_duplicate_name(client: TestClient, owner_a):
    """Updating property name to another existing active property name fails with 409."""
    client.post("/api/v1/properties", json={"name": "Existing One"}, headers=owner_a["headers"])
    res2 = client.post("/api/v1/properties", json={"name": "Existing Two"}, headers=owner_a["headers"])
    prop2_id = res2.json()["id"]

    patch_res = client.patch(
        f"/api/v1/properties/{prop2_id}",
        json={"name": "Existing One"},
        headers=owner_a["headers"],
    )
    assert patch_res.status_code == 409
    assert patch_res.json()["code"] == "PROPERTY_NAME_EXISTS"


def test_archive_property(client: TestClient, owner_a):
    """Archiving property sets archived_at timestamp."""
    create_res = client.post(
        "/api/v1/properties",
        json={"name": "Archive Target"},
        headers=owner_a["headers"],
    )
    prop_id = create_res.json()["id"]

    del_res = client.delete(f"/api/v1/properties/{prop_id}", headers=owner_a["headers"])
    assert del_res.status_code == 200
    assert del_res.json()["message"] == "Property archived successfully"
    assert del_res.json()["archived_at"] is not None


def test_cross_owner_get_property_returns_404(client: TestClient, owner_a, owner_b):
    """Owner B requesting Owner A's property receives 404 (not 403)."""
    res = client.post(
        "/api/v1/properties",
        json={"name": "Owner A Secret Prop"},
        headers=owner_a["headers"],
    )
    prop_id = res.json()["id"]

    # Owner B tries to GET Owner A's property
    cross_res = client.get(f"/api/v1/properties/{prop_id}", headers=owner_b["headers"])
    assert cross_res.status_code == 404
    assert cross_res.json()["code"] == "NOT_FOUND"


def test_cross_owner_update_property_returns_404(client: TestClient, owner_a, owner_b):
    """Owner B patching Owner A's property receives 404 (not 403)."""
    res = client.post(
        "/api/v1/properties",
        json={"name": "Owner A Patch Target"},
        headers=owner_a["headers"],
    )
    prop_id = res.json()["id"]

    cross_res = client.patch(
        f"/api/v1/properties/{prop_id}",
        json={"name": "Hacked Name"},
        headers=owner_b["headers"],
    )
    assert cross_res.status_code == 404
    assert cross_res.json()["code"] == "NOT_FOUND"


def test_cross_owner_archive_property_returns_404(client: TestClient, owner_a, owner_b):
    """Owner B deleting Owner A's property receives 404 (not 403)."""
    res = client.post(
        "/api/v1/properties",
        json={"name": "Owner A Delete Target"},
        headers=owner_a["headers"],
    )
    prop_id = res.json()["id"]

    cross_res = client.delete(f"/api/v1/properties/{prop_id}", headers=owner_b["headers"])
    assert cross_res.status_code == 404
    assert cross_res.json()["code"] == "NOT_FOUND"


def test_property_not_found_returns_404(client: TestClient, owner_a):
    """Requesting nonexistent property ID returns 404."""
    random_id = uuid.uuid4()
    res = client.get(f"/api/v1/properties/{random_id}", headers=owner_a["headers"])
    assert res.status_code == 404
    assert res.json()["code"] == "NOT_FOUND"


def test_property_unauthenticated_request_returns_401(client: TestClient):
    """Unauthenticated requests to properties endpoints return 401."""
    res = client.get("/api/v1/properties")
    assert res.status_code == 401
