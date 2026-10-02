from datetime import timedelta
import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token


def test_successful_registration(client: TestClient):
    """Registering a new owner returns 201 with access and refresh tokens."""
    payload = {
        "email": "new_landlord@example.com",
        "password": "securePassword123",
        "full_name": "Rajesh Kumar",
        "phone": "9876543210",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new_landlord@example.com"
    assert data["full_name"] == "Rajesh Kumar"
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert "password" not in data
    assert "password_hash" not in data


def test_duplicate_email_registration(client: TestClient, make_owner):
    """Registering with an already registered email returns 409 Conflict."""
    make_owner(email="existing@example.com")

    payload = {
        "email": "existing@example.com",
        "password": "anotherPassword123",
        "full_name": "Another Name",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == "EMAIL_ALREADY_EXISTS"
    assert "already registered" in data["detail"].lower()


def test_invalid_registration_data(client: TestClient):
    """Validation errors return 422 with structured field errors."""
    # Password too short (< 8 chars)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "valid@example.com",
            "password": "short",
            "full_name": "Valid Name",
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert data["code"] == "VALIDATION_ERROR"
    assert any("password" in str(err.get("field")) for err in data["errors"])

    # Invalid email
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "invalid-email-format",
            "password": "securePassword123",
            "full_name": "Valid Name",
        },
    )
    assert response.status_code == 422

    # Name too short (< 2 chars)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "valid2@example.com",
            "password": "securePassword123",
            "full_name": "A",
        },
    )
    assert response.status_code == 422


def test_successful_login(client: TestClient, make_owner):
    """Login with valid credentials returns 200 with tokens and user info."""
    make_owner(
        email="login_user@example.com",
        password="correctPassword123",
        full_name="Login User",
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "login_user@example.com",
            "password": "correctPassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "login_user@example.com"
    assert data["user"]["full_name"] == "Login User"
    assert "password_hash" not in data["user"]


def test_incorrect_password(client: TestClient, make_owner):
    """Login with wrong password returns 401 with standard error format."""
    make_owner(
        email="wrong_pass@example.com",
        password="realPassword123",
    )

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrong_pass@example.com",
            "password": "wrongPassword123",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "INVALID_CREDENTIALS"
    assert "Invalid email or password" in data["detail"]


def test_nonexistent_email_login(client: TestClient):
    """Login with unknown email returns 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "anyPassword123",
        },
    )
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "INVALID_CREDENTIALS"


def test_unauthorized_request(client: TestClient):
    """Accessing protected endpoint without Authorization header returns 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "NOT_AUTHENTICATED"


def test_invalid_jwt(client: TestClient):
    """Request with malformed or tampered JWT returns 401."""
    headers = {"Authorization": "Bearer not.a.valid.jwt.token"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "INVALID_TOKEN"


def test_expired_jwt(client: TestClient, make_owner):
    """Request with expired JWT returns 401."""
    owner, _ = make_owner()
    # Create token expired 1 hour ago
    expired_token = create_access_token(
        subject=owner.id,
        expires_delta=timedelta(hours=-1),
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "INVALID_TOKEN"


def test_refresh_token_flow(client: TestClient, make_owner):
    """Valid refresh token successfully exchanges for a new access token."""
    # First register or login to get refresh token
    payload = {
        "email": "refresher@example.com",
        "password": "securePassword123",
        "full_name": "Refresher User",
    }
    reg_res = client.post("/api/v1/auth/register", json=payload)
    refresh_token = reg_res.json()["refresh_token"]

    # Exchange refresh token
    ref_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert ref_res.status_code == 200
    ref_data = ref_res.json()
    assert "access_token" in ref_data
    assert ref_data["token_type"] == "bearer"

    # Verify the new access token can access /auth/me
    headers = {"Authorization": f"Bearer {ref_data['access_token']}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "refresher@example.com"


def test_refresh_with_access_token_fails(client: TestClient, make_owner):
    """Attempting to refresh with an access token (type='access') fails with 401."""
    owner, access_token = make_owner()
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_TOKEN_TYPE"


def test_password_hash_never_exposed(client: TestClient, owner_a):
    """Verify that password hash is never present in any auth response."""
    # /auth/me
    response = client.get("/api/v1/auth/me", headers=owner_a["headers"])
    assert response.status_code == 200
    data = response.json()
    assert "password_hash" not in data
    assert "password" not in data
    assert data["email"] == "owner_a@example.com"


def test_extra_fields_forbidden_on_register(client: TestClient):
    """Passing client-injected fields like owner_id or role on register is rejected with 422."""
    payload = {
        "email": "forbidden_fields@example.com",
        "password": "securePassword123",
        "full_name": "Test User",
        "owner_id": "00000000-0000-0000-0000-000000000000",
        "role": "SUPERADMIN",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["code"] == "VALIDATION_ERROR"
    assert any("extra" in str(err.get("message")).lower() for err in data["errors"])


def test_extra_fields_forbidden_on_login(client: TestClient):
    """Passing unexpected fields on login is rejected with 422."""
    payload = {
        "email": "login_extra@example.com",
        "password": "securePassword123",
        "inject_role": "ADMIN",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 422


def test_indian_phone_number_validation(client: TestClient):
    """Phone validation enforces Indian phone formats."""
    # Invalid short phone
    res_short = client.post(
        "/api/v1/auth/register",
        json={
            "email": "phone1@example.com",
            "password": "securePassword123",
            "full_name": "Phone Test",
            "phone": "12345",
        },
    )
    assert res_short.status_code == 422

    # Invalid characters in phone
    res_alpha = client.post(
        "/api/v1/auth/register",
        json={
            "email": "phone2@example.com",
            "password": "securePassword123",
            "full_name": "Phone Test",
            "phone": "98765abcde",
        },
    )
    assert res_alpha.status_code == 422

    # Valid Indian phone with +91 prefix
    res_valid_prefix = client.post(
        "/api/v1/auth/register",
        json={
            "email": "phone3@example.com",
            "password": "securePassword123",
            "full_name": "Phone Test",
            "phone": "+919876543210",
        },
    )
    assert res_valid_prefix.status_code == 201


def test_inactive_owner_cannot_login(client: TestClient, make_owner):
    """Inactive owner account receives 403 Forbidden on login."""
    make_owner(
        email="inactive@example.com",
        password="securePassword123",
        is_active=False,
    )
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "inactive@example.com",
            "password": "securePassword123",
        },
    )
    assert response.status_code == 403
    assert response.json()["code"] == "ACCOUNT_INACTIVE"


def test_inactive_owner_cannot_access_protected_endpoint(client: TestClient, make_owner):
    """Inactive owner presenting a valid JWT receives 401 on protected endpoint."""
    owner, token = make_owner(
        email="inactive_token@example.com",
        is_active=False,
    )
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.json()["code"] == "ACCOUNT_INACTIVE"


def test_refresh_token_rotation_returns_new_refresh_token(client: TestClient):
    """Token refresh implements rotation by issuing a new refresh token."""
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "rotate_test@example.com",
            "password": "securePassword123",
            "full_name": "Rotate Tester",
        },
    )
    orig_refresh = reg_res.json()["refresh_token"]

    ref_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": orig_refresh},
    )
    assert ref_res.status_code == 200
    ref_data = ref_res.json()
    assert "access_token" in ref_data
    assert "refresh_token" in ref_data
    assert ref_data["refresh_token"] is not None

