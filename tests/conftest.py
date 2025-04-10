# tests/conftest.py
import os
import pytest
from typing import Dict, Generator, Any

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app
from backend.app.core.config import settings
from backend.app.models.user import User
from backend.app.core.security import get_password_hash

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the dependency
@pytest.fixture(scope="function")
def db() -> Generator:
    # Create the database
    Base.metadata.create_all(bind=engine)
    
    # Create a session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up the database after the test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db) -> Generator:
    # Override the get_db dependency
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    # Reset the dependency override
    app.dependency_overrides = {}

@pytest.fixture(scope="function")
def test_user(db) -> Dict[str, Any]:
    """Create a test user and return user data."""
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("password"),
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "password": "password",
    }

@pytest.fixture(scope="function")
def test_admin(db) -> Dict[str, Any]:
    """Create a test admin user and return user data."""
    admin = User(
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=get_password_hash("adminpass"),
        is_active=True,
        is_admin=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    return {
        "id": admin.id,
        "email": admin.email,
        "full_name": admin.full_name,
        "password": "adminpass",
    }

@pytest.fixture(scope="function")
def token_headers(client, test_user) -> Dict[str, str]:
    """Get token headers for authenticated requests."""
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"],
    }
    response = client.post("/api/auth/login", data=login_data)
    data = response.json()
    access_token = data["access_token"]
    
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture(scope="function")
def admin_token_headers(client, test_admin) -> Dict[str, str]:
    """Get token headers for admin authenticated requests."""
    login_data = {
        "username": test_admin["email"],
        "password": test_admin["password"],
    }
    response = client.post("/api/auth/login", data=login_data)
    data = response.json()
    access_token = data["access_token"]
    
    return {"Authorization": f"Bearer {access_token}"}