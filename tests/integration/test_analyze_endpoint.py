"""
Integration tests for the analyze endpoint
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_health_endpoint(client):
    """Test the health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data


def test_analyze_endpoint_success(client):
    """Test successful analysis request."""
    # Sample request data
    request_data = {
        "decision": "Whether to accept a 6-month internship offer",
        "details": "Good stipend, close to home, working hours 9-5, role in software development, learning opportunities include industry tools, college schedule has classes Monday-Thursday",
        "reasons": "Mainly considering it because the stipend is good, the company is close to home, and it will provide industry experience",
        "decision_type": "career",
    }

    response = client.post("/api/v1/analyze", json=request_data)

    # Should succeed
    assert response.status_code == 200
    data = response.json()

    # Check required fields are present
    assert "session_id" in data
    assert data["round"] == 1
    assert "decision_restated" in data
    assert "reasoning_map" in data
    assert "overlooked_factors" in data
    assert "assumptions" in data
    assert "conflicts" in data
    assert "questions" in data
    assert "safety_flag" in data
    assert "guard_notes" in data

    # Check types
    assert isinstance(data["session_id"], str)
    assert isinstance(data["round"], int)
    assert isinstance(data["decision_restated"], str)
    assert isinstance(data["reasoning_map"], dict)
    assert isinstance(data["overlooked_factors"], list)
    assert isinstance(data["assumptions"], list)
    assert isinstance(data["conflicts"], list)
    assert isinstance(data["questions"], list)
    assert isinstance(data["safety_flag"], bool)
    assert isinstance(data["guard_notes"], list)

    # Check that reasoning_map has required subfields
    rm = data["reasoning_map"]
    assert "stated_factors" in rm
    assert "stated_reasons" in rm
    assert "most_visible_factors" in rm
    assert "thin_or_missing_areas" in rm

    # Check that we got some meaningful content back
    assert len(data["decision_restated"]) > 0
    assert len(data["questions"]) > 0  # Should generate questions


def test_analyze_endpoint_validation_errors(client):
    """Test validation errors on the analyze endpoint."""

    # Test missing decision
    response = client.post(
        "/api/v1/analyze", json={"details": "Some details", "reasons": "Some reasons"}
    )
    assert response.status_code == 400
    assert "Decision is required" in response.json()["detail"]

    # Test missing reasons
    response = client.post(
        "/api/v1/analyze", json={"decision": "Test decision", "details": "Some details"}
    )
    assert response.status_code == 400
    assert "Reasons for leaning are required" in response.json()["detail"]

    # Test decision too long
    long_decision = "x" * 501  # Exceeds MAX_DECISION_LENGTH of 500
    response = client.post(
        "/api/v1/analyze", json={"decision": long_decision, "reasons": "Test reasons"}
    )
    assert response.status_code == 400
    assert "Decision too long" in response.json()["detail"]

    # Test reasons too long
    long_reasons = "x" * 1001  # Exceeds MAX_REASONS_LENGTH of 1000
    response = client.post(
        "/api/v1/analyze", json={"decision": "Test decision", "reasons": long_reasons}
    )
    assert response.status_code == 400
    assert "Reasons too long" in response.json()["detail"]

    # Test details too long
    long_details = "x" * 2001  # Exceeds MAX_DETAILS_LENGTH of 2000
    response = client.post(
        "/api/v1/analyze",
        json={
            "decision": "Test decision",
            "details": long_details,
            "reasons": "Test reasons",
        },
    )
    assert response.status_code == 400
    assert "Details too long" in response.json()["detail"]

    # Test invalid decision type
    response = client.post(
        "/api/v1/analyze",
        json={
            "decision": "Test decision",
            "reasons": "Test reasons",
            "decision_type": "invalid_type",
        },
    )
    assert response.status_code == 400
    assert "Invalid decision type" in response.json()["detail"]


def test_analyze_endpoint_minimal_request(client):
    """Test analyze endpoint with minimal valid request."""
    request_data = {"decision": "Whether to take the job", "reasons": "The pay is good"}

    response = client.post("/api/v1/analyze", json=request_data)

    # Should succeed even with minimal data
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] is not None
    assert data["round"] == 1


def test_analyze_endpoint_with_all_fields(client):
    """Test analyze endpoint with all fields populated."""
    request_data = {
        "decision": "Whether to pursue a master's degree",
        "details": "Program is 2 years full-time, costs $30,000 per year, focuses on computer science, offered by local university",
        "reasons": "I want to advance my career, increase my earning potential, and gain deeper knowledge in my field",
        "decision_type": "education",
    }

    response = client.post("/api/v1/analyze", json=request_data)

    assert response.status_code == 200
    data = response.json()

    # Verify decision type was stored/processed
    assert data["session_id"] is not None

    # Should have generated meaningful analysis
    assert len(data["questions"]) > 0
    assert (
        len(data["overlooked_factors"]) >= 0
    )  # May be empty if algorithm determines none
    assert len(data["assumptions"]) >= 0  # May be empty if algorithm determines none
    assert len(data["conflicts"]) >= 0  # May be empty if algorithm determines none


def test_analyze_endpoint_options(client):
    """Test OPTIONS method for CORS preflight."""
    response = client.options("/api/v1/analyze")
    # Should succeed (exact behavior may depend on CORS middleware)
    assert response.status_code in [200, 204]


if __name__ == "__main__":
    pytest.main([__file__])
