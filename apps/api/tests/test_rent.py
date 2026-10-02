from datetime import date, timedelta
import uuid
from fastapi.testclient import TestClient
import pytest

from app.services.rent_status import calculate_rent_status, get_today_ist


# ============================================================================
# 1. Centralized Rent Status Engine Unit Tests
# ============================================================================


def test_calculate_rent_status_all_states():
    """Verify all 5 statuses and their boundary conditions per BUSINESS_RULES.md."""
    due = date(2026, 10, 5)

    # 1. PAID (total_paid >= expected_amount)
    assert calculate_rent_status(due, expected_amount_paise=800000, total_paid_paise=800000, today=date(2026, 10, 1)) == "PAID"
    assert calculate_rent_status(due, expected_amount_paise=800000, total_paid_paise=800000, today=date(2026, 10, 5)) == "PAID"
    assert calculate_rent_status(due, expected_amount_paise=800000, total_paid_paise=800000, today=date(2026, 10, 10)) == "PAID"
    # Overpayment
    assert calculate_rent_status(due, expected_amount_paise=800000, total_paid_paise=1000000, today=date(2026, 10, 10)) == "PAID"

    # 2. PARTIALLY_PAID (0 < total_paid < expected_amount AND today <= due_date)
    assert calculate_rent_status(due, expected_amount_paise=800000, total_paid_paise=400000, today=date(2026, 10, 1)) == "PARTIALLY_PAID"
    assert calculate_rent_status(due, expected_amount_paise=800000, total_paid_paise=400000, today=date(2026, 10, 5)) == "PARTIALLY_PAID"

    # 3. OVERDUE (total_paid < expected_amount AND today > due_date)
    # Unpaid overdue
    assert calculate_rent_status(due, expected_amount_paise=800000, total_paid_paise=0, today=date(2026, 10, 6)) == "OVERDUE"
    # Partial overdue (due date passed with remaining balance)
    assert calculate_rent_status(due, expected_amount_paise=800000, total_paid_paise=400000, today=date(2026, 10, 6)) == "OVERDUE"

    # 4. DUE (total_paid == 0 AND today == due_date)
    assert calculate_rent_status(due, expected_amount_paise=800000, total_paid_paise=0, today=date(2026, 10, 5)) == "DUE"

    # 5. PENDING (total_paid == 0 AND today < due_date)
    assert calculate_rent_status(due, expected_amount_paise=800000, total_paid_paise=0, today=date(2026, 10, 4)) == "PENDING"


# ============================================================================
# Helpers for Rent API integration tests
# ============================================================================


def _setup_property_unit_tenant(client: TestClient, headers, rent_paise=800000, due_day=5, move_in="2026-01-01"):
    prop_res = client.post("/api/v1/properties", json={"name": f"Rent Prop {uuid.uuid4().hex[:6]}"}, headers=headers)
    assert prop_res.status_code == 201
    prop_id = prop_res.json()["id"]

    unit_res = client.post(
        f"/api/v1/properties/{prop_id}/units",
        json={"name": "101", "unit_type": "FLAT", "monthly_rent_paise": rent_paise, "rent_due_day": due_day},
        headers=headers,
    )
    assert unit_res.status_code == 201
    unit_id = unit_res.json()["id"]

    tenant_res = client.post(
        "/api/v1/tenants",
        json={"unit_id": unit_id, "name": "Rent Tenant", "phone": "9876543210", "move_in_date": move_in},
        headers=headers,
    )
    assert tenant_res.status_code == 201
    tenant_id = tenant_res.json()["id"]

    return prop_id, unit_id, tenant_id


# ============================================================================
# 2. On-Demand Generation & Rent Snapshot Tests
# ============================================================================


def test_on_demand_rent_generation_and_no_duplicates(client: TestClient, owner_a):
    """Calling GET /api/v1/rent triggers on-demand generation without creating duplicates."""
    prop_id, unit_id, tenant_id = _setup_property_unit_tenant(client, owner_a["headers"], rent_paise=800000, due_day=5)

    # 1. First call generates October 2026 records
    res1 = client.get("/api/v1/rent?month=10&year=2026", headers=owner_a["headers"])
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["month"] == 10
    assert data1["year"] == 2026
    assert len(data1["items"]) >= 1

    matching = next(i for i in data1["items"] if i["unit_name"] == "101")
    assert matching["expected_amount_paise"] == 800000
    assert matching["total_paid_paise"] == 0
    assert matching["due_date"] == "2026-10-05"
    record_id = matching["id"]

    # 2. Second call returns the EXACT same record without creating duplicates
    res2 = client.get("/api/v1/rent?month=10&year=2026", headers=owner_a["headers"])
    assert res2.status_code == 200
    data2 = res2.json()
    matching2 = next(i for i in data2["items"] if i["unit_name"] == "101")
    assert matching2["id"] == record_id


def test_rent_snapshot_unaffected_by_unit_rent_change(client: TestClient, owner_a):
    """Critical Domain Rule: RentRecord amount is a snapshot; unit rent change applies only to future records."""
    prop_id, unit_id, tenant_id = _setup_property_unit_tenant(
        client, owner_a["headers"], rent_paise=800000, due_day=5, move_in="2026-09-01"
    )

    # 1. Generate October 2026 record at ₹8,000
    oct_res = client.get("/api/v1/rent?month=10&year=2026", headers=owner_a["headers"])
    assert oct_res.status_code == 200
    oct_record = next(i for i in oct_res.json()["items"] if i["unit_name"] == "101")
    assert oct_record["expected_amount_paise"] == 800000

    # 2. Landlord increases unit rent to ₹9,000 starting in November
    patch_res = client.patch(f"/api/v1/units/{unit_id}", json={"monthly_rent_paise": 900000}, headers=owner_a["headers"])
    assert patch_res.status_code == 200

    # 3. Verify October record remains ₹8,000 (SNAPSHOT UNCHANGED)
    oct_check = client.get(f"/api/v1/rent/{oct_record['id']}", headers=owner_a["headers"])
    assert oct_check.status_code == 200
    assert oct_check.json()["expected_amount_paise"] == 800000

    # 4. Generate November 2026 record: uses new rent ₹9,000
    nov_res = client.get("/api/v1/rent?month=11&year=2026", headers=owner_a["headers"])
    assert nov_res.status_code == 200
    nov_record = next(i for i in nov_res.json()["items"] if i["unit_name"] == "101")
    assert nov_record["expected_amount_paise"] == 900000
    assert nov_record["id"] != oct_record["id"]


def test_vacant_unit_generates_no_rent_record(client: TestClient, owner_a):
    """Vacant units do not generate rent records per BR-RENT-04 and EC-06."""
    prop_res = client.post("/api/v1/properties", json={"name": "Vacant Check Prop"}, headers=owner_a["headers"])
    prop_id = prop_res.json()["id"]

    # Create unit with NO tenant
    client.post(
        f"/api/v1/properties/{prop_id}/units",
        json={"name": "Vacant 102", "unit_type": "FLAT", "monthly_rent_paise": 1000000, "rent_due_day": 5},
        headers=owner_a["headers"],
    )

    res = client.get(f"/api/v1/rent?month=10&year=2026&property_id={prop_id}", headers=owner_a["headers"])
    assert res.status_code == 200
    assert len(res.json()["items"]) == 0
    assert res.json()["summary"]["total_expected_paise"] == 0


# ============================================================================
# 3. Tenant Lifecycle Interactions with Rent
# ============================================================================


def test_mid_month_tenant_move_in_generates_rent(client: TestClient, owner_a):
    """EC-01: Tenant moving in mid-month gets a rent record for that month with snapshot amount."""
    prop_id, unit_id, tenant_id = _setup_property_unit_tenant(
        client, owner_a["headers"], rent_paise=1000000, due_day=10, move_in="2026-10-15"
    )

    res = client.get(f"/api/v1/rent?month=10&year=2026&property_id={prop_id}", headers=owner_a["headers"])
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["expected_amount_paise"] == 1000000


def test_future_move_in_excluded_from_past_rent(client: TestClient, owner_a):
    """Tenants moving in in future months are excluded from past rent generation per ADR-002."""
    prop_id, unit_id, tenant_id = _setup_property_unit_tenant(
        client, owner_a["headers"], rent_paise=1000000, due_day=10, move_in="2026-11-01"
    )

    # Looking at October 2026: tenant moved in in November -> no record generated
    res = client.get(f"/api/v1/rent?month=10&year=2026&property_id={prop_id}", headers=owner_a["headers"])
    assert res.status_code == 200
    assert len(res.json()["items"]) == 0


def test_inactive_tenant_rent_lifecycle(client: TestClient, owner_a):
    """Inactive tenant receives rent for active months, but no records for months after move_out."""
    prop_id, unit_id, tenant_id = _setup_property_unit_tenant(
        client, owner_a["headers"], rent_paise=1000000, due_day=10, move_in="2026-08-01"
    )

    # Deactivate tenant on 2026-10-20
    client.post(f"/api/v1/tenants/{tenant_id}/deactivate", json={"move_out_date": "2026-10-20"}, headers=owner_a["headers"])

    # October 2026 (moved out during October): gets October rent record
    res_oct = client.get(f"/api/v1/rent?month=10&year=2026&property_id={prop_id}", headers=owner_a["headers"])
    assert res_oct.status_code == 200
    assert len(res_oct.json()["items"]) == 1

    # November 2026 (moved out before November): does NOT get November rent record
    res_nov = client.get(f"/api/v1/rent?month=11&year=2026&property_id={prop_id}", headers=owner_a["headers"])
    assert res_nov.status_code == 200
    assert len(res_nov.json()["items"]) == 0


def test_archived_property_units_generate_no_new_records(client: TestClient, owner_a):
    """BR-PROP-04: Archived properties generate no new rent records."""
    prop_id, unit_id, tenant_id = _setup_property_unit_tenant(
        client, owner_a["headers"], rent_paise=1000000, due_day=5, move_in="2026-01-01"
    )

    # Archive the property
    client.delete(f"/api/v1/properties/{prop_id}", headers=owner_a["headers"])

    # Querying rent for that archived property returns 200 OK but NO new rent records are generated
    res = client.get(f"/api/v1/rent?month=10&year=2026&property_id={prop_id}", headers=owner_a["headers"])
    assert res.status_code == 200
    assert len(res.json()["items"]) == 0
    assert res.json()["summary"]["total_expected_paise"] == 0


# ============================================================================
# 4. Rent Editing & Voiding Tests
# ============================================================================


def test_edit_rent_record(client: TestClient, owner_a):
    """PATCH /api/v1/rent/{id} allows editing expected_amount_paise (e.g. mid-month proration) and notes."""
    prop_id, unit_id, tenant_id = _setup_property_unit_tenant(
        client, owner_a["headers"], rent_paise=1000000, due_day=5, move_in="2026-10-15"
    )

    res = client.get(f"/api/v1/rent?month=10&year=2026&property_id={prop_id}", headers=owner_a["headers"])
    record_id = res.json()["items"][0]["id"]

    # Landlord edits expected amount to 500000 (half month)
    patch_res = client.patch(
        f"/api/v1/rent/{record_id}",
        json={"expected_amount_paise": 500000, "notes": "Half month agreement"},
        headers=owner_a["headers"],
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["expected_amount_paise"] == 500000
    assert data["notes"] == "Half month agreement"


def test_void_rent_record(client: TestClient, owner_a):
    """POST /api/v1/rent/{id}/void voids the record and excludes it from active calculations."""
    prop_id, unit_id, tenant_id = _setup_property_unit_tenant(
        client, owner_a["headers"], rent_paise=1000000, due_day=5, move_in="2026-10-01"
    )

    res = client.get(f"/api/v1/rent?month=10&year=2026&property_id={prop_id}", headers=owner_a["headers"])
    record_id = res.json()["items"][0]["id"]

    # Void the record
    void_res = client.post(
        f"/api/v1/rent/{record_id}/void",
        json={"reason": "Created by mistake"},
        headers=owner_a["headers"],
    )
    assert void_res.status_code == 200
    assert void_res.json()["is_void"] is True

    # Voided record is excluded from active monthly rent list and totals
    active_res = client.get(f"/api/v1/rent?month=10&year=2026&property_id={prop_id}", headers=owner_a["headers"])
    assert len(active_res.json()["items"]) == 0
    assert active_res.json()["summary"]["total_expected_paise"] == 0

    # Record can still be retrieved directly by ID
    get_res = client.get(f"/api/v1/rent/{record_id}", headers=owner_a["headers"])
    assert get_res.status_code == 200
    assert get_res.json()["is_void"] is True
    assert "Void reason: Created by mistake" in get_res.json()["notes"]

    # Cannot edit voided record
    bad_edit = client.patch(f"/api/v1/rent/{record_id}", json={"expected_amount_paise": 200000}, headers=owner_a["headers"])
    assert bad_edit.status_code == 400
    assert bad_edit.json()["code"] == "RENT_RECORD_VOIDED"

    # Cannot re-void already voided record
    bad_void = client.post(f"/api/v1/rent/{record_id}/void", json={}, headers=owner_a["headers"])
    assert bad_void.status_code == 400
    assert bad_void.json()["code"] == "RENT_RECORD_ALREADY_VOIDED"


# ============================================================================
# 5. Authorization & Owner Isolation Tests
# ============================================================================


def test_cross_owner_rent_isolation(client: TestClient, owner_a, owner_b):
    """Full cross-owner isolation: Owner A cannot GET, PATCH, or VOID Owner B's rent records."""
    # Setup Owner A and Owner B
    _, _, _ = _setup_property_unit_tenant(client, owner_a["headers"], rent_paise=800000, due_day=5)
    prop_b, _, _ = _setup_property_unit_tenant(client, owner_b["headers"], rent_paise=1200000, due_day=1)

    # Generate rent for Owner B
    res_b = client.get(f"/api/v1/rent?month=10&year=2026&property_id={prop_b}", headers=owner_b["headers"])
    rec_b_id = res_b.json()["items"][0]["id"]

    # 1. Owner A cannot GET Owner B's rent record -> 404
    assert client.get(f"/api/v1/rent/{rec_b_id}", headers=owner_a["headers"]).status_code == 404

    # 2. Owner A cannot PATCH Owner B's rent record -> 404
    assert client.patch(f"/api/v1/rent/{rec_b_id}", json={"expected_amount_paise": 1000}, headers=owner_a["headers"]).status_code == 404

    # 3. Owner A cannot VOID Owner B's rent record -> 404
    assert client.post(f"/api/v1/rent/{rec_b_id}/void", json={}, headers=owner_a["headers"]).status_code == 404

    # 4. Owner A querying with Owner B's property_id returns 404
    assert client.get(f"/api/v1/rent?month=10&year=2026&property_id={prop_b}", headers=owner_a["headers"]).status_code == 404


# ============================================================================
# 6. Tenant Rent History Integration
# ============================================================================


def test_tenant_detail_includes_rent_history(client: TestClient, owner_a):
    """GET /api/v1/tenants/{tenant_id} returns generated rent records in rent_history."""
    prop_id, unit_id, tenant_id = _setup_property_unit_tenant(
        client, owner_a["headers"], rent_paise=750000, due_day=5, move_in="2026-08-01"
    )

    # Generate records for August, September, October
    client.get(f"/api/v1/rent?month=8&year=2026&property_id={prop_id}", headers=owner_a["headers"])
    client.get(f"/api/v1/rent?month=9&year=2026&property_id={prop_id}", headers=owner_a["headers"])
    client.get(f"/api/v1/rent?month=10&year=2026&property_id={prop_id}", headers=owner_a["headers"])

    # GET tenant detail
    tenant_res = client.get(f"/api/v1/tenants/{tenant_id}", headers=owner_a["headers"])
    assert tenant_res.status_code == 200
    history = tenant_res.json()["rent_history"]
    assert len(history) == 3
    # Ordered descending by year, month
    assert history[0]["month"] == 10
    assert history[1]["month"] == 9
    assert history[2]["month"] == 8
    assert all(h["expected_amount_paise"] == 750000 for h in history)
