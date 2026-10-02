from datetime import date, timedelta
import uuid
from fastapi.testclient import TestClient
import pytest

from app.services.rent_status import get_today_ist


def _setup_rent_record(client: TestClient, headers, rent_paise=800000, due_day=5, move_in="2026-01-01"):
    """Helper to create property -> unit -> tenant -> rent record."""
    prop_res = client.post("/api/v1/properties", json={"name": f"Prop {uuid.uuid4().hex[:6]}"}, headers=headers)
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
        json={
            "unit_id": unit_id,
            "name": "Payment Test Tenant",
            "phone": "9876543210",
            "move_in_date": move_in,
        },
        headers=headers,
    )
    assert tenant_res.status_code == 201
    tenant_id = tenant_res.json()["id"]

    today = get_today_ist()
    rent_list_res = client.get(f"/api/v1/rent?month={today.month}&year={today.year}", headers=headers)
    assert rent_list_res.status_code == 200
    items = rent_list_res.json()["items"]
    assert len(items) >= 1
    rent_record = items[0]
    return prop_id, unit_id, tenant_id, rent_record["id"]


# ============================================================================
# 1. Payment Creation Tests
# ============================================================================


def test_record_payment_all_methods_success(client: TestClient, owner_a):
    """Test recording valid payments with all 4 allowed methods (CASH, UPI, BANK_TRANSFER, OTHER)."""
    _, _, _, rr_id = _setup_rent_record(client, owner_a["headers"], rent_paise=800000)
    today = get_today_ist()

    methods = ["CASH", "UPI", "BANK_TRANSFER", "OTHER"]
    for i, method in enumerate(methods):
        res = client.post(
            f"/api/v1/rent/{rr_id}/payments",
            json={
                "amount_paise": 100000,
                "payment_method": method,
                "paid_date": today.isoformat(),
                "notes": f"Payment via {method}",
                "confirm_excess": False,
            },
            headers=owner_a["headers"],
        )
        assert res.status_code == 201
        data = res.json()
        assert "payment" in data
        assert "rent_record" in data
        assert data["payment"]["payment_method"] == method
        assert data["payment"]["amount_paise"] == 100000
        assert data["payment"]["is_void"] is False
        assert data["rent_record"]["total_paid_paise"] == (i + 1) * 100000


def test_payment_creation_validation_rules(client: TestClient, owner_a):
    """Verify validation boundaries: amount > 0, valid method, no future dates, no extra fields."""
    _, _, _, rr_id = _setup_rent_record(client, owner_a["headers"], rent_paise=800000)
    today = get_today_ist()

    # 1. Amount <= 0 rejected
    res_zero = client.post(
        f"/api/v1/rent/{rr_id}/payments",
        json={"amount_paise": 0, "payment_method": "CASH", "paid_date": today.isoformat()},
        headers=owner_a["headers"],
    )
    assert res_zero.status_code == 422

    res_neg = client.post(
        f"/api/v1/rent/{rr_id}/payments",
        json={"amount_paise": -5000, "payment_method": "CASH", "paid_date": today.isoformat()},
        headers=owner_a["headers"],
    )
    assert res_neg.status_code == 422

    # 2. Invalid payment method rejected
    res_method = client.post(
        f"/api/v1/rent/{rr_id}/payments",
        json={"amount_paise": 100000, "payment_method": "CREDIT_CARD", "paid_date": today.isoformat()},
        headers=owner_a["headers"],
    )
    assert res_method.status_code == 422

    # 3. Future paid_date rejected with 400 INVALID_PAYMENT_DATE
    future_date = (today + timedelta(days=2)).isoformat()
    res_future = client.post(
        f"/api/v1/rent/{rr_id}/payments",
        json={"amount_paise": 100000, "payment_method": "CASH", "paid_date": future_date},
        headers=owner_a["headers"],
    )
    assert res_future.status_code == 400
    assert res_future.json()["code"] == "INVALID_PAYMENT_DATE"

    # 4. Past (backdated) date allowed
    past_date = (today - timedelta(days=5)).isoformat()
    res_past = client.post(
        f"/api/v1/rent/{rr_id}/payments",
        json={"amount_paise": 100000, "payment_method": "CASH", "paid_date": past_date},
        headers=owner_a["headers"],
    )
    assert res_past.status_code == 201

    # 5. Extra fields forbidden (extra="forbid")
    res_extra = client.post(
        f"/api/v1/rent/{rr_id}/payments",
        json={
            "amount_paise": 100000,
            "payment_method": "CASH",
            "paid_date": today.isoformat(),
            "owner_id": str(uuid.uuid4()),
        },
        headers=owner_a["headers"],
    )
    assert res_extra.status_code == 422

    # 6. Non-existent rent record -> 404
    res_not_found = client.post(
        f"/api/v1/rent/{uuid.uuid4()}/payments",
        json={"amount_paise": 100000, "payment_method": "CASH", "paid_date": today.isoformat()},
        headers=owner_a["headers"],
    )
    assert res_not_found.status_code == 404


def test_cannot_record_payment_on_voided_rent_record(client: TestClient, owner_a):
    """Voiding a rent record prevents subsequent payment creation against it."""
    _, _, _, rr_id = _setup_rent_record(client, owner_a["headers"])
    today = get_today_ist()

    # Void the rent record
    void_res = client.post(f"/api/v1/rent/{rr_id}/void", json={"reason": "Mistake"}, headers=owner_a["headers"])
    assert void_res.status_code == 200

    # Attempt to record payment
    res = client.post(
        f"/api/v1/rent/{rr_id}/payments",
        json={"amount_paise": 100000, "payment_method": "CASH", "paid_date": today.isoformat()},
        headers=owner_a["headers"],
    )
    assert res.status_code == 400
    assert res.json()["code"] == "RENT_RECORD_VOIDED"


# ============================================================================
# 2. Payment Aggregation & Status Transitions Tests
# ============================================================================


def test_multiple_payments_aggregation_and_status_transitions(client: TestClient, owner_a):
    """Test partial payments, exact settlement, and overpayment with dynamic status transitions."""
    _, _, _, rr_id = _setup_rent_record(client, owner_a["headers"], rent_paise=800000, due_day=15)
    today = get_today_ist()

    # Initial check on rent record detail
    detail_res = client.get(f"/api/v1/rent/{rr_id}", headers=owner_a["headers"])
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["total_paid_paise"] == 0
    assert detail["payments"] == []

    # Payment 1: ₹3,000 (300000 paise)
    p1_res = client.post(
        f"/api/v1/rent/{rr_id}/payments",
        json={"amount_paise": 300000, "payment_method": "CASH", "paid_date": today.isoformat()},
        headers=owner_a["headers"],
    )
    assert p1_res.status_code == 201
    assert p1_res.json()["rent_record"]["total_paid_paise"] == 300000

    # Payment 2: ₹2,000 (200000 paise)
    p2_res = client.post(
        f"/api/v1/rent/{rr_id}/payments",
        json={"amount_paise": 200000, "payment_method": "UPI", "paid_date": today.isoformat()},
        headers=owner_a["headers"],
    )
    assert p2_res.status_code == 201
    assert p2_res.json()["rent_record"]["total_paid_paise"] == 500000

    # Payment 3: ₹3,000 (300000 paise) -> total reaches ₹8,000 (fully paid)
    p3_res = client.post(
        f"/api/v1/rent/{rr_id}/payments",
        json={"amount_paise": 300000, "payment_method": "BANK_TRANSFER", "paid_date": today.isoformat()},
        headers=owner_a["headers"],
    )
    assert p3_res.status_code == 201
    assert p3_res.json()["rent_record"]["total_paid_paise"] == 800000
    assert p3_res.json()["rent_record"]["status"] == "PAID"

    # Verify RentRecordDetail has all 3 payments and reflects total_paid
    detail_res2 = client.get(f"/api/v1/rent/{rr_id}", headers=owner_a["headers"])
    assert detail_res2.status_code == 200
    detail2 = detail_res2.json()
    assert detail2["total_paid_paise"] == 800000
    assert detail2["status"] == "PAID"
    assert len(detail2["payments"]) == 3

    # Verify monthly rent list summary reflects total collected
    list_res = client.get(f"/api/v1/rent?month={today.month}&year={today.year}", headers=owner_a["headers"])
    assert list_res.status_code == 200
    summary = list_res.json()["summary"]
    assert summary["total_collected_paise"] >= 800000

    # Payment 4: ₹2,000 Overpayment -> total = ₹10,000, status remains PAID
    p4_res = client.post(
        f"/api/v1/rent/{rr_id}/payments",
        json={"amount_paise": 200000, "payment_method": "OTHER", "paid_date": today.isoformat()},
        headers=owner_a["headers"],
    )
    assert p4_res.status_code == 201
    assert p4_res.json()["rent_record"]["total_paid_paise"] == 1000000
    assert p4_res.json()["rent_record"]["status"] == "PAID"


# ============================================================================
# 3. 2x Excess Payment Sanity Check Tests
# ============================================================================


def test_two_x_excess_payment_sanity_check(client: TestClient, owner_a):
    """If total payments exceed 2x expected rent and confirm_excess=False, return 422 warning."""
    # Expected rent = ₹8,000 (800000 paise). 2x threshold = ₹16,000 (1600000 paise)
    _, _, _, rr_id = _setup_rent_record(client, owner_a["headers"], rent_paise=800000)
    today = get_today_ist()

    # 1. Payment 1 = ₹8,000 (total = ₹8,000 <= ₹16,000) -> succeeds without confirmation
    res1 = client.post(
        f"/api/v1/rent/{rr_id}/payments",
        json={"amount_paise": 800000, "payment_method": "CASH", "paid_date": today.isoformat(), "confirm_excess": False},
        headers=owner_a["headers"],
    )
    assert res1.status_code == 201
    assert res1.json()["rent_record"]["total_paid_paise"] == 800000

    # 2. Payment 2 = ₹9,000 (new total = ₹17,000 > ₹16,000) with confirm_excess=False
    # -> Must return 422 EXCESSIVE_AMOUNT_WARNING and payment NOT created!
    res_warn = client.post(
        f"/api/v1/rent/{rr_id}/payments",
        json={"amount_paise": 900000, "payment_method": "UPI", "paid_date": today.isoformat(), "confirm_excess": False},
        headers=owner_a["headers"],
    )
    assert res_warn.status_code == 422
    assert res_warn.json()["code"] == "EXCESSIVE_AMOUNT_WARNING"

    # Verify payment was NOT created
    detail_res = client.get(f"/api/v1/rent/{rr_id}", headers=owner_a["headers"])
    assert detail_res.status_code == 200
    assert detail_res.json()["total_paid_paise"] == 800000
    assert len(detail_res.json()["payments"]) == 1

    # 3. Same Payment 2 with confirm_excess=True -> Succeeds!
    res_confirm = client.post(
        f"/api/v1/rent/{rr_id}/payments",
        json={"amount_paise": 900000, "payment_method": "UPI", "paid_date": today.isoformat(), "confirm_excess": True},
        headers=owner_a["headers"],
    )
    assert res_confirm.status_code == 201
    assert res_confirm.json()["rent_record"]["total_paid_paise"] == 1700000
    assert res_confirm.json()["rent_record"]["status"] == "PAID"

    # Verify payment now exists in rent record
    detail_res2 = client.get(f"/api/v1/rent/{rr_id}", headers=owner_a["headers"])
    assert detail_res2.status_code == 200
    assert detail_res2.json()["total_paid_paise"] == 1700000
    assert len(detail_res2.json()["payments"]) == 2


# ============================================================================
# 4. Payment Editing (Corrections) Tests
# ============================================================================


def test_payment_editing_and_recalculation(client: TestClient, owner_a):
    """Edit amount, method, date, and verify rent total and status recalculate dynamically."""
    _, _, _, rr_id = _setup_rent_record(client, owner_a["headers"], rent_paise=800000)
    today = get_today_ist()

    # Record initial payment of ₹8,000 -> status is PAID
    p_res = client.post(
        f"/api/v1/rent/{rr_id}/payments",
        json={"amount_paise": 800000, "payment_method": "CASH", "paid_date": today.isoformat()},
        headers=owner_a["headers"],
    )
    assert p_res.status_code == 201
    payment_id = p_res.json()["payment"]["id"]
    assert p_res.json()["rent_record"]["status"] == "PAID"

    # Edit payment: reduce amount from ₹8,000 to ₹5,000
    edit_res = client.patch(
        f"/api/v1/payments/{payment_id}",
        json={"amount_paise": 500000, "notes": "Corrected entry"},
        headers=owner_a["headers"],
    )
    assert edit_res.status_code == 200
    assert edit_res.json()["amount_paise"] == 500000
    assert edit_res.json()["notes"] == "Corrected entry"

    # Verify rent record total paid decreased and status recalculated
    detail_res = client.get(f"/api/v1/rent/{rr_id}", headers=owner_a["headers"])
    assert detail_res.status_code == 200
    assert detail_res.json()["total_paid_paise"] == 500000
    assert detail_res.json()["status"] in ["PARTIALLY_PAID", "OVERDUE"]

    # Edit with future date -> 400 INVALID_PAYMENT_DATE
    future_date = (today + timedelta(days=3)).isoformat()
    edit_future = client.patch(
        f"/api/v1/payments/{payment_id}",
        json={"paid_date": future_date},
        headers=owner_a["headers"],
    )
    assert edit_future.status_code == 400
    assert edit_future.json()["code"] == "INVALID_PAYMENT_DATE"

    # Edit amount causing total to exceed 2x expected (₹20,000 > ₹16,000) without confirm_excess -> 422
    edit_excess = client.patch(
        f"/api/v1/payments/{payment_id}",
        json={"amount_paise": 2000000, "confirm_excess": False},
        headers=owner_a["headers"],
    )
    assert edit_excess.status_code == 422
    assert edit_excess.json()["code"] == "EXCESSIVE_AMOUNT_WARNING"

    # Edit amount with confirm_excess=True -> succeeds!
    edit_excess_ok = client.patch(
        f"/api/v1/payments/{payment_id}",
        json={"amount_paise": 2000000, "confirm_excess": True},
        headers=owner_a["headers"],
    )
    assert edit_excess_ok.status_code == 200
    assert edit_excess_ok.json()["amount_paise"] == 2000000

    # Verify updated rent record
    detail_res2 = client.get(f"/api/v1/rent/{rr_id}", headers=owner_a["headers"])
    assert detail_res2.status_code == 200
    assert detail_res2.json()["total_paid_paise"] == 2000000
    assert detail_res2.json()["status"] == "PAID"


# ============================================================================
# 5. Payment Voiding Tests
# ============================================================================


def test_payment_voiding_and_recalculation(client: TestClient, owner_a):
    """Voiding soft-cancels payment, excludes it from totals, and recalculates status."""
    _, _, _, rr_id = _setup_rent_record(client, owner_a["headers"], rent_paise=800000)
    today = get_today_ist()

    # Payment A: ₹5,000
    p1 = client.post(
        f"/api/v1/rent/{rr_id}/payments",
        json={"amount_paise": 500000, "payment_method": "CASH", "paid_date": today.isoformat()},
        headers=owner_a["headers"],
    )
    assert p1.status_code == 201

    # Payment B: ₹3,000 (total reaches ₹8,000 -> PAID)
    p2 = client.post(
        f"/api/v1/rent/{rr_id}/payments",
        json={"amount_paise": 300000, "payment_method": "UPI", "paid_date": today.isoformat()},
        headers=owner_a["headers"],
    )
    assert p2.status_code == 201
    assert p2.json()["rent_record"]["status"] == "PAID"
    p2_id = p2.json()["payment"]["id"]

    # Void Payment B
    void_res = client.post(
        f"/api/v1/payments/{p2_id}/void",
        json={"reason": "Check bounced / duplicate entry"},
        headers=owner_a["headers"],
    )
    assert void_res.status_code == 200
    assert void_res.json()["is_void"] is True
    assert void_res.json()["message"] == "Payment voided successfully"

    # Rent record must now only sum Payment A (₹5,000)
    detail_res = client.get(f"/api/v1/rent/{rr_id}", headers=owner_a["headers"])
    assert detail_res.status_code == 200
    assert detail_res.json()["total_paid_paise"] == 500000
    assert detail_res.json()["status"] in ["PARTIALLY_PAID", "OVERDUE"]
    # RentRecordDetail payments list only contains non-void payments
    assert len(detail_res.json()["payments"]) == 1

    # Payment sub-resource GET /rent/{id}/payments returns both payments including voided
    payments_list_res = client.get(f"/api/v1/rent/{rr_id}/payments", headers=owner_a["headers"])
    assert payments_list_res.status_code == 200
    all_payments = payments_list_res.json()
    assert len(all_payments) == 2
    voided_item = next(p for p in all_payments if p["id"] == p2_id)
    assert voided_item["is_void"] is True

    # Repeated void attempt -> 400 PAYMENT_ALREADY_VOIDED
    void_again = client.post(
        f"/api/v1/payments/{p2_id}/void",
        json={"reason": "Void again"},
        headers=owner_a["headers"],
    )
    assert void_again.status_code == 400
    assert void_again.json()["code"] == "PAYMENT_ALREADY_VOIDED"

    # Attempt to edit voided payment -> 400 PAYMENT_VOIDED
    edit_voided = client.patch(
        f"/api/v1/payments/{p2_id}",
        json={"amount_paise": 400000},
        headers=owner_a["headers"],
    )
    assert edit_voided.status_code == 400
    assert edit_voided.json()["code"] == "PAYMENT_VOIDED"


# ============================================================================
# 6. Inactive Tenant Late Settlement Test (BR-PAY-10 / EC-17)
# ============================================================================


def test_inactive_tenant_late_settlement(client: TestClient, owner_a):
    """Deactivated tenants can still have payments recorded against existing historical rent records."""
    _, _, tenant_id, rr_id = _setup_rent_record(client, owner_a["headers"], rent_paise=800000)
    today = get_today_ist()

    # Deactivate tenant
    deact_res = client.post(
        f"/api/v1/tenants/{tenant_id}/deactivate",
        json={"move_out_date": today.isoformat()},
        headers=owner_a["headers"],
    )
    assert deact_res.status_code == 200

    # Record payment against inactive tenant's rent record (debt settlement)
    pay_res = client.post(
        f"/api/v1/rent/{rr_id}/payments",
        json={"amount_paise": 800000, "payment_method": "UPI", "paid_date": today.isoformat()},
        headers=owner_a["headers"],
    )
    assert pay_res.status_code == 201
    assert pay_res.json()["rent_record"]["total_paid_paise"] == 800000
    assert pay_res.json()["rent_record"]["status"] == "PAID"


# ============================================================================
# 7. Authorization & Cross-Owner Isolation Tests
# ============================================================================


def test_cross_owner_payment_isolation(client: TestClient, owner_a, owner_b):
    """Verify Owner A cannot create, view, list, edit, or void Owner B's payments (all return 404)."""
    # Owner A creates rent record and payment
    _, _, _, owner_a_rr_id = _setup_rent_record(client, owner_a["headers"], rent_paise=800000)
    today = get_today_ist()

    p_res = client.post(
        f"/api/v1/rent/{owner_a_rr_id}/payments",
        json={"amount_paise": 500000, "payment_method": "CASH", "paid_date": today.isoformat()},
        headers=owner_a["headers"],
    )
    assert p_res.status_code == 201
    owner_a_payment_id = p_res.json()["payment"]["id"]

    # 1. Owner B cannot create payment against Owner A's rent record -> 404
    b_create = client.post(
        f"/api/v1/rent/{owner_a_rr_id}/payments",
        json={"amount_paise": 200000, "payment_method": "CASH", "paid_date": today.isoformat()},
        headers=owner_b["headers"],
    )
    assert b_create.status_code == 404

    # 2. Owner B cannot list payments of Owner A's rent record -> 404
    b_list = client.get(
        f"/api/v1/rent/{owner_a_rr_id}/payments",
        headers=owner_b["headers"],
    )
    assert b_list.status_code == 404

    # 3. Owner B cannot get Owner A's payment -> 404
    b_get = client.get(
        f"/api/v1/payments/{owner_a_payment_id}",
        headers=owner_b["headers"],
    )
    assert b_get.status_code == 404

    # 4. Owner B cannot edit Owner A's payment -> 404
    b_edit = client.patch(
        f"/api/v1/payments/{owner_a_payment_id}",
        json={"amount_paise": 300000},
        headers=owner_b["headers"],
    )
    assert b_edit.status_code == 404

    # 5. Owner B cannot void Owner A's payment -> 404
    b_void = client.post(
        f"/api/v1/payments/{owner_a_payment_id}/void",
        json={"reason": "Malicious void"},
        headers=owner_b["headers"],
    )
    assert b_void.status_code == 404


def test_get_single_payment_detail(client: TestClient, owner_a):
    """GET /api/v1/payments/{payment_id} returns accurate PaymentDetail."""
    _, _, _, rr_id = _setup_rent_record(client, owner_a["headers"], rent_paise=800000)
    today = get_today_ist()

    create_res = client.post(
        f"/api/v1/rent/{rr_id}/payments",
        json={
            "amount_paise": 650000,
            "payment_method": "UPI",
            "paid_date": today.isoformat(),
            "notes": "Single get test",
        },
        headers=owner_a["headers"],
    )
    assert create_res.status_code == 201
    payment_id = create_res.json()["payment"]["id"]

    get_res = client.get(f"/api/v1/payments/{payment_id}", headers=owner_a["headers"])
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == payment_id
    assert data["amount_paise"] == 650000
    assert data["payment_method"] == "UPI"
    assert data["notes"] == "Single get test"
    assert data["is_void"] is False


def test_list_payments_include_void_filter(client: TestClient, owner_a):
    """GET /api/v1/rent/{rr_id}/payments honors include_void filter query param."""
    _, _, _, rr_id = _setup_rent_record(client, owner_a["headers"], rent_paise=800000)
    today = get_today_ist()

    # Create 2 payments
    p1 = client.post(
        f"/api/v1/rent/{rr_id}/payments",
        json={"amount_paise": 400000, "payment_method": "CASH", "paid_date": today.isoformat()},
        headers=owner_a["headers"],
    ).json()["payment"]["id"]
    p2 = client.post(
        f"/api/v1/rent/{rr_id}/payments",
        json={"amount_paise": 400000, "payment_method": "UPI", "paid_date": today.isoformat()},
        headers=owner_a["headers"],
    ).json()["payment"]["id"]

    # Void payment 2
    client.post(f"/api/v1/payments/{p2}/void", json={"reason": "Void p2"}, headers=owner_a["headers"])

    # include_void=True (default) -> both payments returned
    res_all = client.get(f"/api/v1/rent/{rr_id}/payments?include_void=true", headers=owner_a["headers"])
    assert res_all.status_code == 200
    assert len(res_all.json()) == 2

    # include_void=False -> only p1 returned
    res_active = client.get(f"/api/v1/rent/{rr_id}/payments?include_void=false", headers=owner_a["headers"])
    assert res_active.status_code == 200
    active_items = res_active.json()
    assert len(active_items) == 1
    assert active_items[0]["id"] == p1


def test_tenant_detail_and_list_reflects_payment_status(client: TestClient, owner_a):
    """GET /api/v1/tenants and /api/v1/tenants/{id} reflect dynamically computed payment status and history."""
    _, _, tenant_id, rr_id = _setup_rent_record(client, owner_a["headers"], rent_paise=800000)
    today = get_today_ist()

    # Record full payment
    client.post(
        f"/api/v1/rent/{rr_id}/payments",
        json={"amount_paise": 800000, "payment_method": "BANK_TRANSFER", "paid_date": today.isoformat()},
        headers=owner_a["headers"],
    )

    # Check tenant list: current_month_rent_status should be PAID
    t_list_res = client.get("/api/v1/tenants", headers=owner_a["headers"])
    assert t_list_res.status_code == 200
    tenant_item = next(t for t in t_list_res.json()["items"] if t["id"] == tenant_id)
    assert tenant_item["current_month_rent_status"] == "PAID"

    # Check tenant detail: rent_history should have 800000 total_paid and PAID status
    t_detail_res = client.get(f"/api/v1/tenants/{tenant_id}", headers=owner_a["headers"])
    assert t_detail_res.status_code == 200
    rh_item = t_detail_res.json()["rent_history"][0]
    assert rh_item["total_paid_paise"] == 800000
    assert rh_item["status"] == "PAID"
    assert len(rh_item["payments"]) == 1
    assert rh_item["payments"][0]["amount_paise"] == 800000

