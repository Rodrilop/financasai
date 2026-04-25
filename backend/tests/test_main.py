from fastapi.testclient import TestClient
from main import app
from database import init_db
import pytest

# Initialize DB for tests
init_db()

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_read_settings():
    response = client.get("/api/settings")
    assert response.status_code == 200
    data = response.json()
    assert "salary" in data
    assert "investor_profile" in data

def test_add_and_read_income():
    # Add income
    response = client.post("/api/income", json={"name": "Salário Teste", "amount": 5000.0})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Salário Teste"
    assert data["amount"] == 5000.0
    income_id = data["id"]

    # Read income
    response = client.get("/api/income")
    assert response.status_code == 200
    incomes = response.json()
    assert len(incomes) > 0
    
    # Cleanup (assuming delete_income exists)
    client.delete(f"/api/income/{income_id}")
