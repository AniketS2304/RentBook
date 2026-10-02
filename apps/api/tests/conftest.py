import os
import uuid
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment
os.environ["ENVIRONMENT"] = "testing"
os.environ["SECRET_KEY"] = "test-secret-key-with-minimum-32-characters-for-testing"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "7"

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.owner import Owner
from app.models.property import Property
from app.models.unit import Unit
from app.models.tenant import Tenant
from app.models.rent_record import RentRecord
from app.models.payment import Payment

# In-memory SQLite for fast, isolated tests
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


# Enable foreign key enforcement for SQLite
@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables before test session and drop after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """Provide a fresh database session with savepoint rollback."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, trans):
        nonlocal nested
        if connection.closed:
            return
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    """TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_owner(db: Session):
    """Helper to create an owner and generate an access token."""
    def _make(
        email: str = None,
        password: str = "password123",
        full_name: str = "Test Owner",
        phone: str = "9876543210",
        is_active: bool = True,
    ):
        owner_id = uuid.uuid4()
        owner_email = email or f"owner_{owner_id.hex[:8]}@example.com"
        owner = Owner(
            id=owner_id,
            email=owner_email,
            password_hash=get_password_hash(password),
            full_name=full_name,
            phone=phone,
            is_active=is_active,
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)
        token = create_access_token(subject=owner.id)
        return owner, token

    return _make


@pytest.fixture
def owner_a(make_owner):
    """Fixture providing Owner A with auth token."""
    owner, token = make_owner(
        email="owner_a@example.com",
        full_name="Owner Alpha",
        phone="9876543210",
    )
    return {"owner": owner, "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
def owner_b(make_owner):
    """Fixture providing Owner B with auth token."""
    owner, token = make_owner(
        email="owner_b@example.com",
        full_name="Owner Beta",
        phone="9876543211",
    )
    return {"owner": owner, "token": token, "headers": {"Authorization": f"Bearer {token}"}}
