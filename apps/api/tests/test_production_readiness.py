"""Tests for Phase 9 Production Readiness Audit and Fixes.

Validates:
1. Settings production security guards (prevent default SECRET_KEY and DEBUG=True in production).
2. Timezone resolution and IST fallback robustness.
3. Default tenant move-out date alignment with IST.
4. Database health check error sanitization (no internal DB error leaks).
5. Extra-field prohibition across all entity create/update payloads.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.db.session import get_db
from app.main import app
from app.models.tenant import Tenant
from app.services.rent_status import get_today_ist


def test_production_settings_validation_blocks_default_secret():
    """Verify Settings rejects production environment when using default SECRET_KEY."""
    with pytest.raises(ValidationError) as exc:
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            SECRET_KEY="rentbook-dev-secret-key-change-in-production-min-32-chars",
        )
    assert "In production, SECRET_KEY must be changed" in str(exc.value)


def test_production_settings_validation_blocks_debug_mode():
    """Verify Settings rejects production environment when DEBUG is True."""
    with pytest.raises(ValidationError) as exc:
        Settings(
            ENVIRONMENT="production",
            DEBUG=True,
            SECRET_KEY="a-secure-production-random-secret-key-min-32-chars",
        )
    assert "DEBUG must be set to False" in str(exc.value)


def test_production_settings_valid_configuration():
    """Verify Settings accepts valid production configuration."""
    prod_settings = Settings(
        ENVIRONMENT="production",
        DEBUG=False,
        SECRET_KEY="a-secure-production-random-secret-key-min-32-chars",
    )
    assert prod_settings.ENVIRONMENT == "production"
    assert prod_settings.DEBUG is False


def test_get_today_ist_returns_correct_ist_date():
    """Verify get_today_ist returns calendar date in Indian Standard Time (UTC+05:30)."""
    expected_ist_date = datetime.now(timezone(timedelta(hours=5, minutes=30))).date()
    today_ist = get_today_ist()
    assert today_ist == expected_ist_date


def test_get_today_ist_fallback_robustness():
    """Verify get_today_ist uses fixed UTC+05:30 offset even if ZoneInfo fails."""
    with patch("app.services.rent_status.IST", timezone(timedelta(hours=5, minutes=30))):
        today_ist = get_today_ist()
        expected = datetime.now(timezone(timedelta(hours=5, minutes=30))).date()
        assert today_ist == expected


def test_health_check_sanitizes_database_errors():
    """Verify /api/v1/health returns 'unreachable' and does not leak internal DB errors."""
    mock_db = MagicMock()
    mock_db.execute.side_effect = Exception("password authentication failed for user 'postgres' at 192.168.1.100:5432")

    def override_broken_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_broken_db
    with TestClient(app) as test_client:
        response = test_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"] == "unreachable"
        # Ensure raw DB connection error / credentials were not leaked
        assert "password" not in data["database"]
        assert "192.168.1.100" not in data["database"]
    app.dependency_overrides.clear()


def test_tenant_deactivation_defaults_to_ist_date(client, owner_a, db):
    """Verify tenant deactivation move-out date defaults to IST today."""
    headers = owner_a["headers"]

    # 1. Create property and unit
    prop_res = client.post("/api/v1/properties", json={"name": "IST Deactivate Prop"}, headers=headers)
    prop_id = prop_res.json()["id"]

    unit_res = client.post(
        f"/api/v1/properties/{prop_id}/units",
        json={"name": "101", "unit_type": "FLAT", "monthly_rent_paise": 1000000, "rent_due_day": 5},
        headers=headers,
    )
    unit_id = unit_res.json()["id"]

    today = get_today_ist()
    move_in_date = today - timedelta(days=30)
    tenant_res = client.post(
        "/api/v1/tenants",
        json={"unit_id": unit_id, "name": "Ramesh", "phone": "9876543210", "move_in_date": str(move_in_date)},
        headers=headers,
    )
    tenant_id = tenant_res.json()["id"]

    # 2. Deactivate without move_out_date
    deact_res = client.post(f"/api/v1/tenants/{tenant_id}/deactivate", json={}, headers=headers)
    assert deact_res.status_code == 200
    assert deact_res.json()["tenant_status"] == "INACTIVE"

    # 3. Verify tenant record in DB has move_out_date == today IST
    import uuid
    tenant_in_db = db.query(Tenant).filter_by(id=uuid.UUID(tenant_id)).one()
    assert tenant_in_db.move_out_date == today


def test_all_entity_schemas_reject_extra_fields(client, owner_a):
    """Verify Pydantic extra='forbid' rejects extra fields across all create and update endpoints."""
    headers = owner_a["headers"]

    # 1. Property extra field
    res = client.post(
        "/api/v1/properties",
        json={"name": "Extra Test Prop", "malicious_field": "injected"},
        headers=headers,
    )
    assert res.status_code == 422
    assert res.json()["code"] == "VALIDATION_ERROR"

    # Create valid property for unit test
    prop_res = client.post("/api/v1/properties", json={"name": "Valid Prop"}, headers=headers)
    prop_id = prop_res.json()["id"]

    # 2. Unit extra field
    res = client.post(
        f"/api/v1/properties/{prop_id}/units",
        json={"name": "101", "unit_type": "FLAT", "monthly_rent_paise": 1000000, "rent_due_day": 5, "extra": "foo"},
        headers=headers,
    )
    assert res.status_code == 422
    assert res.json()["code"] == "VALIDATION_ERROR"

    unit_res = client.post(
        f"/api/v1/properties/{prop_id}/units",
        json={"name": "101", "unit_type": "FLAT", "monthly_rent_paise": 1000000, "rent_due_day": 5},
        headers=headers,
    )
    unit_id = unit_res.json()["id"]

    # 3. Tenant extra field
    res = client.post(
        "/api/v1/tenants",
        json={
            "unit_id": unit_id,
            "name": "Ramesh",
            "phone": "9876543210",
            "move_in_date": "2026-01-01",
            "unknown_attribute": 123,
        },
        headers=headers,
    )
    assert res.status_code == 422
    assert res.json()["code"] == "VALIDATION_ERROR"
