"""
PyTest Configuration and Fixtures
Sets up an isolated in-memory SQLite database using StaticPool to share state across sessions.
"""
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.database.session import Base, get_db
from backend.app.main import app
from backend.app.core.security import get_password_hash, create_access_token
from backend.app.models.models import User, Organization, OrganizationMember

TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Provides a fresh database session for each test function."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Provides FastAPI TestClient with overridden database dependency."""
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_and_org(db_session):
    """Creates a standard test organization and owner user."""
    user = User(
        email="dev@cloudpulse.io",
        hashed_password=get_password_hash("SecretPassword123!"),
        full_name="Lead Engineer",
        role="admin"
    )
    db_session.add(user)
    db_session.flush()

    org = Organization(
        name="Test Engineering Org",
        slug="test-org-01"
    )
    db_session.add(org)
    db_session.flush()

    membership = OrganizationMember(
        user_id=user.id,
        organization_id=org.id,
        role="owner"
    )
    db_session.add(membership)
    db_session.commit()

    token = create_access_token(user.id, org_id=org.id, role=user.role)
    return {
        "user": user,
        "org": org,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"}
    }
