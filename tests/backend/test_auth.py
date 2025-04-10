# tests/backend/test_auth.py
import pytest
from fastapi.testclient import TestClient

def test_login(client: TestClient, test_user):
    """Test user login."""
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"],
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_wrong_password(client: TestClient, test_user):
    """Test login with wrong password."""
    login_data = {
        "username": test_user["email"],
        "password": "wrongpassword",
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 401
    assert "detail" in response.json()

def test_register(client: TestClient):
    """Test user registration."""
    user_data = {
        "email": "newuser@example.com",
        "password": "newpassword",
        "full_name": "New User",
    }
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["full_name"] == user_data["full_name"]
    assert "id" in data

def test_register_existing_email(client: TestClient, test_user):
    """Test registration with existing email."""
    user_data = {
        "email": test_user["email"],
        "password": "newpassword",
        "full_name": "Another User",
    }
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 400
    assert "detail" in response.json()

def test_get_me(client: TestClient, token_headers, test_user):
    """Test get current user info."""
    response = client.get("/api/auth/me", headers=token_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["email"]
    assert data["full_name"] == test_user["full_name"]
    assert "id" in data

def test_get_me_unauthorized(client: TestClient):
    """Test get current user info without token."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert "detail" in response.json()