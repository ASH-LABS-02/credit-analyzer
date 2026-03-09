"""
Unit tests for application management API endpoints.

Tests the RESTful endpoints for creating, reading, updating, and deleting
credit applications.

Requirements: 9.1, 14.1
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from app.main import app
from app.models.domain import Application, ApplicationStatus, CreditRecommendation


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_application():
    """Create a sample application for testing."""
    return Application(
        id=str(uuid.uuid4()),
        company_name="Test Company",
        loan_amount=1000000.0,
        loan_purpose="Business expansion",
        applicant_email="test@example.com",
        status=ApplicationStatus.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def mock_repository():
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


class TestCreateApplication:
    """Tests for POST /api/v1/applications endpoint."""
    
    def test_create_application_success(self, client, mock_repository, mock_audit_logger, sample_application):
        """Test successful application creation."""
        # Setup mock
        mock_repository.create = AsyncMock(return_value=sample_application)
        
        # Make request
        response = client.post(
            "/api/v1/applications",
            json={
                "company_name": "Test Company",
                "loan_amount": 1000000.0,
                "loan_purpose": "Business expansion",
                "applicant_email": "test@example.com"
            }
        )
        
        # Debug: print response if not 201
        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")
        
        # Assertions
        assert response.status_code == 201
        data = response.json()
        assert data["company_name"] == "Test Company"
        assert data["loan_amount"] == 1000000.0
        assert data["status"] == "pending"
        assert "id" in data
        assert "created_at" in data
        
        # Verify repository was called
        mock_repository.create.assert_called_once()
        
        # Verify audit logging was called
        mock_audit_logger.log_user_action.assert_called_once()
    
    def test_create_application_invalid_email(self, client, mock_repository):
        """Test application creation with invalid email."""
        response = client.post(
            "/api/v1/applications",
            json={
                "company_name": "Test Company",
                "loan_amount": 1000000.0,
                "loan_purpose": "Business expansion",
                "applicant_email": "invalid-email"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_create_application_negative_loan_amount(self, client, mock_repository):
        """Test application creation with negative loan amount."""
        response = client.post(
            "/api/v1/applications",
            json={
                "company_name": "Test Company",
                "loan_amount": -1000.0,
                "loan_purpose": "Business expansion",
                "applicant_email": "test@example.com"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_create_application_missing_fields(self, client, mock_repository):
        """Test application creation with missing required fields."""
        response = client.post(
            "/api/v1/applications",
            json={
                "company_name": "Test Company"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_create_application_repository_error(self, client, mock_repository, mock_audit_logger):
        """Test application creation when repository fails."""
        mock_repository.create = AsyncMock(side_effect=Exception("Database error"))
        
        response = client.post(
            "/api/v1/applications",
            json={
                "company_name": "Test Company",
                "loan_amount": 1000000.0,
                "loan_purpose": "Business expansion",
                "applicant_email": "test@example.com"
            }
        )
        
        assert response.status_code == 500


class TestListApplications:
    """Tests for GET /api/v1/applications endpoint."""
    
    def test_list_applications_success(self, client, mock_repository, sample_application):
        """Test successful application listing."""
        # Setup mock
        mock_repository.list_all = AsyncMock(return_value=[sample_application])
        
        # Make request
        response = client.get("/api/v1/applications")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "applications" in data
        assert "total" in data
        assert len(data["applications"]) == 1
        assert data["total"] == 1
        assert data["applications"][0]["company_name"] == "Test Company"
    
    def test_list_applications_with_limit(self, client, mock_repository, sample_application):
        """Test application listing with limit parameter."""
        mock_repository.list_all = AsyncMock(return_value=[sample_application])
        
        response = client.get("/api/v1/applications?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        
        # Verify repository was called with limit
        mock_repository.list_all.assert_called_once()
        call_args = mock_repository.list_all.call_args
        assert call_args.kwargs.get("limit") == 10
    
    def test_list_applications_with_status_filter(self, client, mock_repository, sample_application):
        """Test application listing with status filter."""
        mock_repository.list_all = AsyncMock(return_value=[sample_application])
        
        response = client.get("/api/v1/applications?status=pending")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status_filter"] == "pending"
        
        # Verify repository was called with status filter
        mock_repository.list_all.assert_called_once()
        call_args = mock_repository.list_all.call_args
        assert call_args.kwargs.get("status") == ApplicationStatus.PENDING
    
    def test_list_applications_empty(self, client, mock_repository):
        """Test application listing when no applications exist."""
        mock_repository.list_all = AsyncMock(return_value=[])
        
        response = client.get("/api/v1/applications")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["applications"]) == 0
    
    def test_list_applications_repository_error(self, client, mock_repository):
        """Test application listing when repository fails."""
        mock_repository.list_all = AsyncMock(side_effect=Exception("Database error"))
        
        response = client.get("/api/v1/applications")
        
        assert response.status_code == 500


class TestGetApplication:
    """Tests for GET /api/v1/applications/{app_id} endpoint."""
    
    def test_get_application_success(self, client, mock_repository, sample_application):
        """Test successful application retrieval."""
        mock_repository.get_by_id = AsyncMock(return_value=sample_application)
        
        response = client.get(f"/api/v1/applications/{sample_application.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_application.id
        assert data["company_name"] == "Test Company"
        assert data["status"] == "pending"
    
    def test_get_application_not_found(self, client, mock_repository):
        """Test application retrieval when application doesn't exist."""
        mock_repository.get_by_id = AsyncMock(return_value=None)
        
        response = client.get("/api/v1/applications/nonexistent-id")
        
        assert response.status_code == 404
        response_data = response.json()
        assert "message" in response_data
        assert "not found" in response_data["message"].lower()
    
    def test_get_application_with_credit_score(self, client, mock_repository, sample_application):
        """Test application retrieval with credit score and recommendation."""
        sample_application.credit_score = 75.5
        sample_application.recommendation = CreditRecommendation.APPROVE
        mock_repository.get_by_id = AsyncMock(return_value=sample_application)
        
        response = client.get(f"/api/v1/applications/{sample_application.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["credit_score"] == 75.5
        assert data["recommendation"] == "approve"
    
    def test_get_application_repository_error(self, client, mock_repository):
        """Test application retrieval when repository fails."""
        mock_repository.get_by_id = AsyncMock(side_effect=Exception("Database error"))
        
        response = client.get("/api/v1/applications/some-id")
        
        assert response.status_code == 500


class TestUpdateApplication:
    """Tests for PATCH /api/v1/applications/{app_id} endpoint."""
    
    def test_update_application_success(self, client, mock_repository, mock_audit_logger, sample_application):
        """Test successful application update."""
        updated_app = sample_application.model_copy()
        updated_app.company_name = "Updated Company"
        mock_repository.update = AsyncMock(return_value=updated_app)
        
        response = client.patch(
            f"/api/v1/applications/{sample_application.id}",
            json={"company_name": "Updated Company"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["company_name"] == "Updated Company"
        
        # Verify repository was called
        mock_repository.update.assert_called_once()
        
        # Verify audit logging was called
        mock_audit_logger.log_user_action.assert_called_once()
    
    def test_update_application_multiple_fields(self, client, mock_repository, mock_audit_logger, sample_application):
        """Test updating multiple fields at once."""
        updated_app = sample_application.model_copy()
        updated_app.loan_amount = 2000000.0
        updated_app.status = ApplicationStatus.PROCESSING
        mock_repository.update = AsyncMock(return_value=updated_app)
        
        response = client.patch(
            f"/api/v1/applications/{sample_application.id}",
            json={
                "loan_amount": 2000000.0,
                "status": "processing"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["loan_amount"] == 2000000.0
        assert data["status"] == "processing"
    
    def test_update_application_not_found(self, client, mock_repository, mock_audit_logger):
        """Test updating non-existent application."""
        mock_repository.update = AsyncMock(return_value=None)
        
        response = client.patch(
            "/api/v1/applications/nonexistent-id",
            json={"company_name": "Updated Company"}
        )
        
        assert response.status_code == 404
    
    def test_update_application_no_fields(self, client, mock_repository, mock_audit_logger):
        """Test update with no fields provided."""
        response = client.patch(
            "/api/v1/applications/some-id",
            json={}
        )
        
        assert response.status_code == 400
        response_data = response.json()
        assert "message" in response_data
        assert "no fields" in response_data["message"].lower()
    
    def test_update_application_invalid_email(self, client, mock_repository, mock_audit_logger):
        """Test update with invalid email."""
        response = client.patch(
            "/api/v1/applications/some-id",
            json={"applicant_email": "invalid-email"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_update_application_repository_error(self, client, mock_repository, mock_audit_logger):
        """Test update when repository fails."""
        mock_repository.update = AsyncMock(side_effect=Exception("Database error"))
        
        response = client.patch(
            "/api/v1/applications/some-id",
            json={"company_name": "Updated Company"}
        )
        
        assert response.status_code == 500


class TestDeleteApplication:
    """Tests for DELETE /api/v1/applications/{app_id} endpoint."""
    
    def test_delete_application_success(self, client, mock_repository, mock_audit_logger):
        """Test successful application deletion."""
        mock_repository.delete = AsyncMock(return_value=True)
        
        response = client.delete("/api/v1/applications/some-id")
        
        assert response.status_code == 204
        assert response.content == b''
        
        # Verify repository was called
        mock_repository.delete.assert_called_once_with("some-id")
        
        # Verify audit logging was called
        mock_audit_logger.log_user_action.assert_called_once()
    
    def test_delete_application_not_found(self, client, mock_repository, mock_audit_logger):
        """Test deleting non-existent application."""
        mock_repository.delete = AsyncMock(return_value=False)
        
        response = client.delete("/api/v1/applications/nonexistent-id")
        
        assert response.status_code == 404
    
    def test_delete_application_repository_error(self, client, mock_repository, mock_audit_logger):
        """Test deletion when repository fails."""
        mock_repository.delete = AsyncMock(side_effect=Exception("Database error"))
        
        response = client.delete("/api/v1/applications/some-id")
        
        assert response.status_code == 500


class TestEndToEndWorkflow:
    """End-to-end tests for application management workflow."""
    
    def test_create_list_get_update_delete_workflow(self, client, mock_repository, mock_audit_logger):
        """Test complete CRUD workflow."""
        app_id = str(uuid.uuid4())
        
        # Create
        created_app = Application(
            id=app_id,
            company_name="Test Company",
            loan_amount=1000000.0,
            loan_purpose="Business expansion",
            applicant_email="test@example.com",
            status=ApplicationStatus.PENDING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        mock_repository.create = AsyncMock(return_value=created_app)
        
        create_response = client.post(
            "/api/v1/applications",
            json={
                "company_name": "Test Company",
                "loan_amount": 1000000.0,
                "loan_purpose": "Business expansion",
                "applicant_email": "test@example.com"
            }
        )
        assert create_response.status_code == 201
        
        # List
        mock_repository.list_all = AsyncMock(return_value=[created_app])
        list_response = client.get("/api/v1/applications")
        assert list_response.status_code == 200
        assert list_response.json()["total"] == 1
        
        # Get
        mock_repository.get_by_id = AsyncMock(return_value=created_app)
        get_response = client.get(f"/api/v1/applications/{app_id}")
        assert get_response.status_code == 200
        
        # Update
        updated_app = created_app.model_copy()
        updated_app.status = ApplicationStatus.PROCESSING
        mock_repository.update = AsyncMock(return_value=updated_app)
        update_response = client.patch(
            f"/api/v1/applications/{app_id}",
            json={"status": "processing"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "processing"
        
        # Delete
        mock_repository.delete = AsyncMock(return_value=True)
        delete_response = client.delete(f"/api/v1/applications/{app_id}")
        assert delete_response.status_code == 204
