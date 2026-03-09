"""
Property-Based Tests for API Endpoints

This module implements property-based tests for API endpoint completeness
and response format consistency.

Feature: intelli-credit-platform
Property 27: API Endpoint Completeness
Property 28: API Response Format Consistency

Requirements: 14.1, 14.2, 14.3
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from datetime import datetime
import json
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from app.main import app
from app.models.domain import Application, ApplicationStatus, CreditRecommendation


# Fixtures
@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_application_repository():
    """Create a mock application repository."""
    with patch('app.api.applications.get_application_repository') as mock:
        repo = MagicMock()
        mock.return_value = repo
        yield repo


@pytest.fixture
def mock_audit_logger():
    """Create a mock audit logger."""
    with patch('app.api.applications.get_audit_logger') as mock:
        logger = MagicMock()
        logger.log_user_action = AsyncMock()
        mock.return_value = logger
        yield logger


# ============================================================================
# Property 27: API Endpoint Completeness
# ============================================================================

def test_api_endpoint_completeness(client):
    """
    Property 27: API Endpoint Completeness
    
    For all core operations (application management, document operations,
    analysis operations, CAM operations, search operations, monitoring
    operations, authentication), the system should expose corresponding
    RESTful API endpoints.
    
    Validates: Requirements 14.1
    """
    # Define all required endpoints by category
    required_endpoints = {
        # Health check
        "health": [
            ("GET", "/"),
            ("GET", "/health"),
        ],
        # Authentication
        "authentication": [
            ("POST", "/api/v1/auth/login"),
            ("POST", "/api/v1/auth/logout"),
            ("GET", "/api/v1/auth/me"),
        ],
        # Application management
        "applications": [
            ("POST", "/api/v1/applications"),
            ("GET", "/api/v1/applications"),
            ("GET", "/api/v1/applications/{app_id}"),
            ("PATCH", "/api/v1/applications/{app_id}"),
            ("DELETE", "/api/v1/applications/{app_id}"),
        ],
        # Document operations
        "documents": [
            ("POST", "/api/v1/applications/{app_id}/documents"),
            ("GET", "/api/v1/applications/{app_id}/documents"),
            ("GET", "/api/v1/documents/{doc_id}"),
            ("DELETE", "/api/v1/documents/{doc_id}"),
        ],
        # Analysis operations
        "analysis": [
            ("POST", "/api/v1/applications/{app_id}/analyze"),
            ("GET", "/api/v1/applications/{app_id}/status"),
            ("GET", "/api/v1/applications/{app_id}/results"),
        ],
        # CAM operations
        "cam": [
            ("POST", "/api/v1/applications/{app_id}/cam"),
            ("GET", "/api/v1/applications/{app_id}/cam"),
            ("GET", "/api/v1/applications/{app_id}/cam/export"),
        ],
        # Search operations
        "search": [
            ("POST", "/api/v1/applications/{app_id}/search"),
        ],
        # Monitoring operations
        "monitoring": [
            ("GET", "/api/v1/monitoring/alerts"),
            ("GET", "/api/v1/monitoring/applications/{app_id}"),
        ],
    }
    
    # Get OpenAPI schema
    response = client.get("/openapi.json")
    assert response.status_code == 200, "OpenAPI schema should be accessible"
    
    openapi_schema = response.json()
    paths = openapi_schema.get("paths", {})
    
    # Track missing endpoints
    missing_endpoints = []
    
    # Check each required endpoint
    for category, endpoints in required_endpoints.items():
        for method, path in endpoints:
            # Normalize path for comparison (replace path parameters)
            normalized_path = path.replace("{app_id}", "{app_id}").replace("{doc_id}", "{doc_id}")
            
            # Check if path exists in OpenAPI schema
            if normalized_path not in paths:
                missing_endpoints.append((category, method, path))
                continue
            
            # Check if method exists for this path
            path_methods = paths[normalized_path]
            if method.lower() not in path_methods:
                missing_endpoints.append((category, method, path))
    
    # Assert all endpoints are present
    assert len(missing_endpoints) == 0, (
        f"Missing API endpoints:\n" +
        "\n".join([f"  - {cat}: {method} {path}" for cat, method, path in missing_endpoints])
    )
    
    print(f"✓ All {sum(len(eps) for eps in required_endpoints.values())} required API endpoints are present")


# ============================================================================
# Property 28: API Response Format Consistency
# ============================================================================

def is_valid_json(response_text: str) -> bool:
    """Check if response text is valid JSON."""
    try:
        json.loads(response_text)
        return True
    except (json.JSONDecodeError, ValueError):
        return False


def has_error_structure(response_json: Dict[str, Any]) -> bool:
    """
    Check if error response has the required structure.
    
    Error responses should include:
    - error: error code/type
    - message: descriptive error message
    - status_code: HTTP status code
    """
    required_fields = ["error", "message", "status_code"]
    return all(field in response_json for field in required_fields)


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    company_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    loan_amount=st.floats(min_value=1000, max_value=100000000, allow_nan=False, allow_infinity=False),
    loan_purpose=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
)
def test_api_response_format_consistency_success(
    client,
    mock_application_repository,
    mock_audit_logger,
    company_name: str,
    loan_amount: float,
    loan_purpose: str
):
    """
    Property 28: API Response Format Consistency (Success Cases)
    
    For any successful API request, the system should return a response
    in valid JSON format with an appropriate HTTP status code (2xx).
    
    Validates: Requirements 14.2
    """
    # Create a mock application to return
    app_id = str(uuid.uuid4())
    mock_app = Application(
        id=app_id,
        company_name=company_name,
        loan_amount=loan_amount,
        loan_purpose=loan_purpose,
        applicant_email="test@example.com",
        status=ApplicationStatus.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Setup mock
    mock_application_repository.create = AsyncMock(return_value=mock_app)
    
    # Create a valid application
    application_data = {
        "company_name": company_name,
        "loan_amount": loan_amount,
        "loan_purpose": loan_purpose,
        "applicant_email": "test@example.com"
    }
    
    # Make POST request to create application
    response = client.post("/api/v1/applications", json=application_data)
    
    # Property: Successful responses should have 2xx status code
    assert 200 <= response.status_code < 300, (
        f"Successful request should return 2xx status code, got {response.status_code}"
    )
    
    # Property: Response should be valid JSON
    assert is_valid_json(response.text), (
        "Response should be valid JSON format"
    )
    
    # Property: Response should be parseable as JSON
    response_json = response.json()
    assert isinstance(response_json, dict), (
        "Response JSON should be a dictionary"
    )
    
    # Property: Response should contain expected fields for application
    expected_fields = ["id", "company_name", "loan_amount", "status", "created_at", "updated_at"]
    for field in expected_fields:
        assert field in response_json, (
            f"Response should contain field '{field}'"
        )


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    invalid_loan_amount=st.one_of(
        st.floats(max_value=0, allow_nan=False, allow_infinity=False),
        st.floats(allow_nan=True, allow_infinity=True)
    ),
)
def test_api_response_format_consistency_validation_errors(client, invalid_loan_amount: float):
    """
    Property 28: API Response Format Consistency (Validation Error Cases)
    
    For any API request with validation errors, the system should return
    a response in valid JSON format with HTTP 400 or 422 status code and
    include descriptive error messages.
    
    Validates: Requirements 14.3
    """
    # Skip if we got a valid loan amount (edge case with hypothesis)
    if invalid_loan_amount > 0 and not (
        str(invalid_loan_amount) == 'nan' or str(invalid_loan_amount) == 'inf'
    ):
        return
    
    # Create application with invalid data
    application_data = {
        "company_name": "Test Company",
        "loan_amount": invalid_loan_amount,
        "loan_purpose": "Business expansion",
        "applicant_email": "test@example.com"
    }
    
    # Make POST request
    response = client.post("/api/v1/applications", json=application_data)
    
    # Property: Validation errors should return 4xx status code
    assert 400 <= response.status_code < 500, (
        f"Validation error should return 4xx status code, got {response.status_code}"
    )
    
    # Property: Response should be valid JSON
    assert is_valid_json(response.text), (
        "Error response should be valid JSON format"
    )
    
    # Property: Response should be parseable as JSON
    response_json = response.json()
    assert isinstance(response_json, dict), (
        "Error response JSON should be a dictionary"
    )
    
    # Property: Error response should have required structure
    assert has_error_structure(response_json), (
        f"Error response should have 'error', 'message', and 'status_code' fields. "
        f"Got: {list(response_json.keys())}"
    )
    
    # Property: Error message should be descriptive (non-empty string)
    assert isinstance(response_json["message"], str), (
        "Error message should be a string"
    )
    assert len(response_json["message"]) > 0, (
        "Error message should not be empty"
    )


def test_api_response_format_consistency_not_found_errors(client, mock_application_repository):
    """
    Property 28: API Response Format Consistency (Not Found Error Cases)
    
    For any API request for a non-existent resource, the system should
    return a response in valid JSON format with HTTP 404 status code and
    include descriptive error messages.
    
    Validates: Requirements 14.3
    """
    # Setup mock to return None (not found)
    mock_application_repository.get_by_id = AsyncMock(return_value=None)
    
    # Request non-existent application
    non_existent_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/v1/applications/{non_existent_id}")
    
    # Property: Not found errors should return 404 status code
    assert response.status_code == 404, (
        f"Not found error should return 404 status code, got {response.status_code}"
    )
    
    # Property: Response should be valid JSON
    assert is_valid_json(response.text), (
        "Error response should be valid JSON format"
    )
    
    # Property: Response should be parseable as JSON
    response_json = response.json()
    assert isinstance(response_json, dict), (
        "Error response JSON should be a dictionary"
    )
    
    # Property: Error response should have required structure
    assert has_error_structure(response_json), (
        f"Error response should have 'error', 'message', and 'status_code' fields. "
        f"Got: {list(response_json.keys())}"
    )
    
    # Property: Error message should mention the resource not found
    assert isinstance(response_json["message"], str), (
        "Error message should be a string"
    )
    assert len(response_json["message"]) > 0, (
        "Error message should not be empty"
    )
    assert "not found" in response_json["message"].lower(), (
        "Error message should indicate resource was not found"
    )


@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    invalid_email=st.one_of(
        st.text(min_size=1, max_size=50).filter(lambda x: '@' not in x),  # No @ symbol
        st.text(min_size=1, max_size=50).filter(lambda x: '@' in x and '.' not in x.split('@')[-1]),  # No dot after @
    )
)
def test_api_response_format_consistency_invalid_email(client, invalid_email: str):
    """
    Property 28: API Response Format Consistency (Invalid Email)
    
    For any API request with invalid email format, the system should
    return a response in valid JSON format with appropriate error code
    and descriptive error message.
    
    Validates: Requirements 14.3
    """
    # Create application with invalid email
    application_data = {
        "company_name": "Test Company",
        "loan_amount": 100000.0,
        "loan_purpose": "Business expansion",
        "applicant_email": invalid_email
    }
    
    # Make POST request
    response = client.post("/api/v1/applications", json=application_data)
    
    # Property: Validation errors should return 4xx status code
    assert 400 <= response.status_code < 500, (
        f"Validation error should return 4xx status code, got {response.status_code}"
    )
    
    # Property: Response should be valid JSON
    assert is_valid_json(response.text), (
        "Error response should be valid JSON format"
    )
    
    # Property: Response should have error structure
    response_json = response.json()
    assert has_error_structure(response_json), (
        f"Error response should have 'error', 'message', and 'status_code' fields"
    )


def test_api_response_http_status_codes(client, mock_application_repository, mock_audit_logger):
    """
    Property 28: API Response Format Consistency (HTTP Status Codes)
    
    For any API request, the system should return appropriate HTTP status codes:
    - 200 OK for successful GET requests
    - 201 Created for successful POST requests
    - 204 No Content for successful DELETE requests
    - 400 Bad Request for validation errors
    - 404 Not Found for missing resources
    - 422 Unprocessable Entity for request validation errors
    
    Validates: Requirements 14.2
    """
    # Setup mocks for list
    mock_application_repository.list_all = AsyncMock(return_value=[])
    
    # Test 200 OK for GET
    response = client.get("/api/v1/applications")
    assert response.status_code == 200, "GET list should return 200 OK"
    assert is_valid_json(response.text), "Response should be valid JSON"
    
    # Setup mocks for create
    app_id = str(uuid.uuid4())
    mock_app = Application(
        id=app_id,
        company_name="Test Company",
        loan_amount=100000.0,
        loan_purpose="Business expansion",
        applicant_email="test@example.com",
        status=ApplicationStatus.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    mock_application_repository.create = AsyncMock(return_value=mock_app)
    
    # Test 201 Created for POST
    application_data = {
        "company_name": "Test Company",
        "loan_amount": 100000.0,
        "loan_purpose": "Business expansion",
        "applicant_email": "test@example.com"
    }
    response = client.post("/api/v1/applications", json=application_data)
    assert response.status_code == 201, "POST create should return 201 Created"
    assert is_valid_json(response.text), "Response should be valid JSON"
    
    # Setup mock for get by id
    mock_application_repository.get_by_id = AsyncMock(return_value=mock_app)
    
    # Test 200 OK for GET single resource
    response = client.get(f"/api/v1/applications/{app_id}")
    assert response.status_code == 200, "GET single resource should return 200 OK"
    assert is_valid_json(response.text), "Response should be valid JSON"
    
    # Setup mock for delete
    mock_application_repository.delete = AsyncMock(return_value=True)
    
    # Test 204 No Content for DELETE
    response = client.delete(f"/api/v1/applications/{app_id}")
    assert response.status_code == 204, "DELETE should return 204 No Content"
    
    # Setup mock for not found
    mock_application_repository.get_by_id = AsyncMock(return_value=None)
    
    # Test 404 Not Found
    response = client.get(f"/api/v1/applications/{app_id}")
    assert response.status_code == 404, "GET deleted resource should return 404 Not Found"
    assert is_valid_json(response.text), "Error response should be valid JSON"
    
    # Test 422 Unprocessable Entity for validation errors
    invalid_data = {
        "company_name": "",  # Empty string should fail validation
        "loan_amount": -1000,  # Negative amount should fail
        "loan_purpose": "",
        "applicant_email": "invalid-email"
    }
    response = client.post("/api/v1/applications", json=invalid_data)
    assert response.status_code in [400, 422], (
        "Invalid data should return 400 or 422"
    )
    assert is_valid_json(response.text), "Error response should be valid JSON"


def test_api_response_content_type_headers(client, mock_application_repository):
    """
    Property 28: API Response Format Consistency (Content-Type Headers)
    
    For any API request returning JSON, the response should include
    appropriate Content-Type header (application/json).
    
    Validates: Requirements 14.2
    """
    # Setup mock
    mock_application_repository.list_all = AsyncMock(return_value=[])
    
    # Test various endpoints
    endpoints = [
        ("GET", "/"),
        ("GET", "/health"),
        ("GET", "/api/v1/applications"),
    ]
    
    for method, path in endpoints:
        if method == "GET":
            response = client.get(path)
        elif method == "POST":
            response = client.post(path, json={})
        
        # Property: JSON responses should have application/json content type
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type.lower(), (
            f"{method} {path} should return application/json content type, "
            f"got: {content_type}"
        )


def test_api_endpoint_documentation(client):
    """
    Property 27: API Endpoint Completeness (Documentation)
    
    For all API endpoints, the system should provide API documentation
    with endpoint descriptions, request/response schemas, and examples.
    
    Validates: Requirements 14.4
    """
    # Get OpenAPI schema
    response = client.get("/openapi.json")
    assert response.status_code == 200, "OpenAPI schema should be accessible"
    
    openapi_schema = response.json()
    
    # Property: OpenAPI schema should have required top-level fields
    required_fields = ["openapi", "info", "paths"]
    for field in required_fields:
        assert field in openapi_schema, (
            f"OpenAPI schema should contain '{field}' field"
        )
    
    # Property: Info section should have title and version
    info = openapi_schema["info"]
    assert "title" in info, "OpenAPI info should have title"
    assert "version" in info, "OpenAPI info should have version"
    
    # Property: Each path should have operation descriptions
    paths = openapi_schema["paths"]
    for path, methods in paths.items():
        for method, operation in methods.items():
            if method in ["get", "post", "put", "patch", "delete"]:
                assert "summary" in operation or "description" in operation, (
                    f"{method.upper()} {path} should have summary or description"
                )
    
    # Property: Documentation UI should be accessible
    docs_response = client.get("/docs")
    assert docs_response.status_code == 200, "API documentation UI should be accessible at /docs"
    
    redoc_response = client.get("/redoc")
    assert redoc_response.status_code == 200, "API documentation UI should be accessible at /redoc"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
