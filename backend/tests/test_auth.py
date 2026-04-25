from fastapi.testclient import TestClient
from main import app
from database import init_db, get_connection
import pytest

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM users")
    conn.commit()
    conn.close()

client = TestClient(app)

def test_register_user():
    response = client.post("/api/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert response.json() == {"ok": True}

def test_register_duplicate_user():
    client.post("/api/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    })
    response = client.post("/api/auth/register", json={
        "name": "Test User 2",
        "email": "test@example.com",
        "password": "password456"
    })
    assert response.status_code == 400

def test_login_success():
    client.post("/api/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    })
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["name"] == "Test User"

def test_login_wrong_password():
    client.post("/api/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    })
    response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_protected_route_without_token():
    response = client.get("/api/settings")
    assert response.status_code == 403

def test_protected_route_with_token():
    client.post("/api/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    })
    login_res = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    
    response = client.get("/api/settings", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
