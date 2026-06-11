import pytest
from fastapi.testclient import TestClient
from api_server import app

# Create a TestClient using the FastAPI app
client = TestClient(app)

def test_health_check():
    """Test the /health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "port" in data
    assert "timestamp" in data

def test_status_endpoint():
    """Test the /api/status endpoint"""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "taxi-analytics-api"
    assert "running" in data
    assert "spending_limit_ok" in data

def test_costs_endpoint():
    """Test the /api/costs endpoint"""
    response = client.get("/api/costs")
    assert response.status_code == 200
    data = response.json()
    assert "spending_summary" in data
    assert "total_cost" in data["spending_summary"]
    assert "budget_status" in data
    assert "within_limit" in data["budget_status"]
    assert "daily_limit" in data["budget_status"]

def test_analyze_invalid_vehicle():
    """Test validation errors for /api/analyze endpoint with invalid inputs"""
    payload = {
        "vehicle_type": "invalid_vehicle_type", # Valid are green, yellow, fhv, fhvhv
        "month": 1,
        "task": "Test task",
        "provider": "anthropic"
    }
    
    # We expect a 400 or 422 Bad Request due to validation, 
    # but based on current code, we return 400 for invalid vehicle type
    response = client.post(
        "/api/analyze",
        params={
            "vehicle_type": payload["vehicle_type"],
            "month": payload["month"],
            "task": payload["task"],
            "provider": payload["provider"]
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Must be one of: green, yellow, fhv, fhvhv" in data["detail"]

def test_analyze_invalid_month():
    """Test validation errors for /api/analyze endpoint with invalid month"""
    response = client.post(
        "/api/analyze",
        params={
            "vehicle_type": "yellow",
            "month": 13, # Invalid month
            "task": "Test task",
            "provider": "anthropic"
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Must be between 1 and 12" in data["detail"]
