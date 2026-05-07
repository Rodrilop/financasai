from fastapi.testclient import TestClient
from main import app
from database import init_db, get_connection
import pytest

# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def setup_db():
    """Initialize DB and clean users before each test."""
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM users")
    conn.execute("DELETE FROM income")
    conn.commit()
    conn.close()

client = TestClient(app)

# ── Helpers ───────────────────────────────────────────────────────────────────

def register_and_login(email="test@example.com", password="password123", name="Test User"):
    """Register a user and return the Bearer auth header."""
    client.post("/api/auth/register", json={"name": name, "email": email, "password": password})
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# ── Tests ─────────────────────────────────────────────────────────────────────

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_protected_route_without_token():
    """Accessing a protected route without token must return 403."""
    response = client.get("/api/settings")
    assert response.status_code == 403

def test_read_settings():
    """Authenticated user can read settings."""
    headers = register_and_login()
    response = client.get("/api/settings", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "salary" in data
    assert "investor_profile" in data

def test_add_and_read_income():
    """Authenticated user can add and list income entries."""
    headers = register_and_login()
    today = "2026-05-01"

    # Add income
    response = client.post("/api/income", json={"name": "Salário Teste", "amount": 5000.0, "date": today}, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Salário Teste"
    assert data["amount"] == 5000.0
    assert data["date"] == today
    income_id = data["id"]

    # Read income
    response = client.get("/api/income", headers=headers)
    assert response.status_code == 200
    incomes = response.json()
    assert any(i["id"] == income_id for i in incomes)

    # Cleanup
    client.delete(f"/api/income/{income_id}", headers=headers)
