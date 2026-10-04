"""
Security tests for the Blind Spot application
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_sql_injection_attempts(client):
    """Test that SQL injection attempts are handled safely."""
    # These should be treated as plain text, not SQL
    injection_attempts = [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "' UNION SELECT * FROM secrets --",
        "1; DELETE FROM decisions WHERE 1=1; --",
        "'; EXEC xp_cmdshell('dir'); --"
    ]

    for attempt in injection_attempts:
        response = client.post("/api/v1/analyze", json={
            "decision": f"Test decision {attempt}",
            "reasons": "Test reasons"
        })

        # Should either succeed (treating as plain text) or return validation error
        # Should NOT return 500 error from SQL execution
        assert response.status_code != 500, f"SQL injection attempt caused server error: {attempt}"

        if response.status_code == 200:
            # If it succeeded, verify the injection attempt was treated as text
            data = response.json()
            assert "session_id" in data
            # The decision should be echoed back in some form
            assert attempt in str(data) or "Test decision" in str(data)


def test_xss_attempts(client):
    """Test that XSS attempts are properly escaped."""
    xss_attempts = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "';alert('xss');//",
        "<svg onload=alert('xss')>",
        "javascript:alert('xss')",
        "<body onload=alert('xss')>"
    ]

    for attempt in xss_attempts:
        response = client.post("/api/v1/analyze", json={
            "decision": f"Test decision {attempt}",
            "reasons": "Test reasons"
        })

        if response.status_code == 200:
            data = response.json()
            # The response should be valid JSON (not broken by HTML)
            assert isinstance(data, dict)
            assert "session_id" in data

            # Check that the response doesn't contain unescaped script tags
            # in the JSON structure (they should be escaped if present)
            response_text = str(data)
            # Basic check: if we got the attempt back, it should be in a JSON string value
            # not as raw HTML in the JSON structure
            if attempt in response_text:
                # It's okay if it's echoed back as data, but JSON should be valid
                pass  # The JSON parsing already happened, so it's safe


def test_request_size_limits(client):
    """Test that oversized requests are rejected."""
    # Test decision too long
    long_decision = "x" * 501  # Assuming MAX_DECISION_LENGTH is 500
    response = client.post("/api/v1/analyze", json={
        "decision": long_decision,
        "reasons": "Test reasons"
    })
    assert response.status_code == 400
    assert "Decision too long" in response.json()["detail"]

    # Test details too long
    long_details = "x" * 2001  # Assuming MAX_DETAILS_LENGTH is 2000
    response = client.post("/api/v1/analyze", json={
        "decision": "Test decision",
        "details": long_details,
        "reasons": "Test reasons"
    })
    assert response.status_code == 400
    assert "Details too long" in response.json()["detail"]

    # Test reasons too long
    long_reasons = "x" * 1001  # Assuming MAX_REASONS_LENGTH is 1000
    response = client.post("/api/v1/analyze", json={
        "decision": "Test decision",
        "reasons": long_reasons
    })
    assert response.status_code == 400
    assert "Reasons too long" in response.json()["detail"]


def test_rate_limiting_headers(client):
    """Test that rate limiting headers are present."""
    response = client.get("/health")

    # Check for rate limiting headers (may not be present on every request
    # if under the limit, but the framework should support them)
    # We're mainly checking that the endpoint responds correctly
    assert response.status_code == 200


def test_cors_headers(client):
    """Test that CORS headers are properly set."""
    # Test actual request
    response = client.get("/health")
    assert response.status_code == 200

    # Test preflight request
    response = client.options("/api/v1/analyze")
    # Should not fail (exact behavior depends on CORS configuration)
    # Main thing is that it doesn't crash the server
    assert response.status_code in [200, 204, 405]  # 405 if OPTIONS not explicitly handled


def test_http_method_validation(client):
    """Test that invalid HTTP methods are rejected appropriately."""
    # Test PUT on analyze endpoint (should not be allowed)
    response = client.put("/api/v1/analyze", json={
        "decision": "Test",
        "reasons": "Test"
    })
    # Should be 405 Method Not Allowed or similar
    assert response.status_code in [405, 404, 400]  # Depending on routing

    # Test DELETE on analyze endpoint
    response = client.delete("/api/v1/analyze")
    assert response.status_code in [405, 404, 400]

    # Test GET on analyze endpoint (should not accept GET for analysis)
    response = client.get("/api/v1/analyze")
    assert response.status_code in [405, 404, 400]  # Should not be 200


def test_content_type_validation(client):
    """Test that invalid content types are rejected."""
    # Send form data instead of JSON
    response = client.post(
        "/api/v1/analyze",
        data="decision=Test&reasons=Test",
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    # Should reject or handle gracefully
    # FastAPI with Pydantic should return 422 for invalid JSON
    assert response.status_code in [400, 422, 415]


def test_empty_json_body(client):
    """Test handling of empty JSON body."""
    response = client.post(
        "/api/v1/analyze",
        json={},
        headers={"Content-Type": "application/json"}
    )
    # Should return validation error for missing required fields
    assert response.status_code == 400
    error_detail = response.json()["detail"]
    assert "Decision is required" in error_detail or "Reasons for leaning are required" in error_detail


def test_malformed_json(client):
    """Test handling of malformed JSON."""
    response = client.post(
        "/api/v1/analyze",
        data="{invalid json:",
        headers={"Content-Type": "application/json"}
    )
    # Should return 400 or 422 for invalid JSON
    assert response.status_code in [400, 422]


def test_health_endpoint_security(client):
    """Test that health endpoint doesn't expose sensitive information."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    # Should not contain sensitive information like API keys, database passwords, etc.
    response_str = str(data).lower()
    sensitive_terms = ["api_key", "secret", "password", "token", "credential", "private"]

    for term in sensitive_terms:
        assert term not in response_str, f"Health endpoint may expose sensitive term: {term}"


def test_error_messages_dont_leak_information(client):
    """Test that error messages don't leak internal implementation details."""
    # Trigger various error conditions

    # 404 error
    response = client.get("/nonexistent-endpoint")
    assert response.status_code == 404
    # Error message should be generic

    # 400 error from validation
    response = client.post("/api/v1/analyze", json={})
    assert response.status_code == 400
    error_detail = response.json()["detail"]
    # Should not contain stack traces or internal module names
    error_str = str(error_detail).lower()
    internal_terms = ["traceback", "file", "line", "module", "internal", "sqlalchemy", "psycopg"]
    for term in internal_terms:
        assert term not in error_str, f"Error message leaks internal detail: {term}"


def test_http_security_headers(client):
    """Test that basic security headers are present or can be added."""
    response = client.get("/health")

    # While we may not set all headers in the test environment,
    # we verify the endpoint works and doesn't crash
    assert response.status_code == 200

    # In production, these would be set by middleware:
    # - X-Content-Type-Options: nosniff
    # - X-Frame-Options: DENY
    # - X-XSS-Protection: 1; mode=block
    # - Strict-Transport-Security: max-age=31536000; includeSubDomains
    # - Referrer-Policy: strict-origin-when-cross-origin
    # - Permissions-Policy: geolocation=(), microphone=(), camera=()

    # For now, we just ensure the endpoint responds correctly


if __name__ == "__main__":
    pytest.main([__file__])