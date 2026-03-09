"""
Unit tests for search and monitoring API endpoints.

Tests the RESTful endpoints for semantic document search and monitoring operations.

Requirements: 10.1, 16.2, 14.1
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from app.main import app
from app.models.domain import Application, ApplicationStatus, Document, MonitoringAlert


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_application():
    """Create a sample application for testing."""
    return Application(
        id="test-app-123",
        company_name="Test Company",
        loan_amount=1000000.0,
        loan_purpose="Business expansion",
        applicant_email="test@example.com",
        status=ApplicationStatus.APPROVED,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        credit_score=75.0,
        recommendation="approve"
    )


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        Document(
            id="doc-1",
            application_id="test-app-123",
            filename="financial_statement.pdf",
            file_type="pdf",
            storage_path="documents/test-app-123/doc-1.pdf",
            upload_date=datetime.utcnow(),
            processing_status="complete"
        ),
        Document(
            id="doc-2",
            application_id="test-app-123",
            filename="bank_statement.pdf",
            file_type="pdf",
            storage_path="documents/test-app-123/doc-2.pdf",
            upload_date=datetime.utcnow(),
            processing_status="complete"
        )
    ]


@pytest.fixture
def sample_search_results():
    """Create sample search results."""
    return [
        {
            'doc_id': 'doc-1',
            'chunk': 'The company reported revenue of $5 million in 2023.',
            'chunk_index': 0,
            'total_chunks': 10,
            'relevance_score': 0.92
        },
        {
            'doc_id': 'doc-1',
            'chunk': 'Net profit for the year was $500,000.',
            'chunk_index': 1,
            'total_chunks': 10,
            'relevance_score': 0.85
        }
    ]


@pytest.fixture
def sample_monitoring_status():
    """Create sample monitoring status."""
    now = datetime.utcnow()
    return {
        'monitoring_id': str(uuid.uuid4()),
        'application_id': 'test-app-123',
        'company_name': 'Test Company',
        'status': 'active',
        'activated_at': now.isoformat(),
        'last_check': (now - timedelta(days=3)).isoformat(),
        'next_check': (now + timedelta(days=4)).isoformat(),
        'check_interval_days': 7,
        'total_checks': 5,
        'total_alerts': 2,
        'additional_context': {'industry': 'Manufacturing'}
    }


@pytest.fixture
def sample_alerts():
    """Create sample monitoring alerts."""
    now = datetime.utcnow()
    return [
        {
            'id': 'alert-1',
            'application_id': 'test-app-123',
            'alert_type': 'negative_news',
            'severity': 'medium',
            'message': 'Test Company: Multiple negative news items detected',
            'details': {
                'company_name': 'Test Company',
                'change_details': 'Pattern of negative news coverage',
                'source': 'News Analysis',
                'confidence': 0.7
            },
            'created_at': (now - timedelta(days=2)).isoformat(),
            'acknowledged': False
        },
        {
            'id': 'alert-2',
            'application_id': 'test-app-123',
            'alert_type': 'financial_deterioration',
            'severity': 'high',
            'message': 'Test Company: Financial distress indicators detected',
            'details': {
                'company_name': 'Test Company',
                'change_details': 'Significant decline in financial metrics',
                'source': 'Financial Analysis',
                'confidence': 0.85
            },
            'created_at': (now - timedelta(days=1)).isoformat(),
            'acknowledged': True,
            'acknowledged_by': 'user-123',
            'acknowledged_at': now.isoformat()
        }
    ]


@pytest.fixture
def mock_vector_search():
    """Create a mock vector search engine."""
    with patch('app.api.search_monitoring.get_vector_search_engine') as mock:
        engine = MagicMock()
        mock.return_value = engine
        yield engine


@pytest.fixture
def mock_monitoring_service():
    """Create a mock monitoring service."""
    with patch('app.api.search_monitoring.get_monitoring_service') as mock:
        service = MagicMock()
        mock.return_value = service
        yield service


@pytest.fixture
def mock_app_repository():
    """Create a mock application repository."""
    with patch('app.api.search_monitoring.get_application_repository') as mock:
        repo = MagicMock()
        mock.return_value = repo
        yield repo


@pytest.fixture
def mock_doc_repository():
    """Create a mock document repository."""
    with patch('app.api.search_monitoring.get_document_repository') as mock:
        repo = MagicMock()
        mock.return_value = repo
        yield repo


@pytest.fixture
def mock_audit_logger():
    """Create a mock audit logger."""
    with patch('app.api.search_monitoring.get_audit_logger') as mock:
        logger = MagicMock()
        logger.log_user_action = AsyncMock()
        mock.return_value = logger
        yield logger


class TestSemanticSearch:
    """Tests for POST /api/v1/applications/{app_id}/search endpoint."""
    
    def test_semantic_search_success(
        self,
        client,
        mock_vector_search,
        mock_app_repository,
        mock_doc_repository,
        mock_audit_logger,
        sample_application,
        sample_documents,
        sample_search_results
    ):
        """Test successful semantic search."""
        # Setup mocks
        mock_app_repository.get_by_id = AsyncMock(return_value=sample_application)
        mock_doc_repository.list_by_application = AsyncMock(return_value=sample_documents)
        mock_vector_search.get_index_size = MagicMock(return_value=100)
        mock_vector_search.search = AsyncMock(return_value=sample_search_results)
        
        # Make request
        response = client.post(
            "/api/v1/applications/test-app-123/search",
            json={
                "query": "What is the company's revenue?",
                "max_results": 5,
                "min_relevance": 0.5
            }
        )
        
        # Debug print
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["application_id"] == "test-app-123"
        assert data["query"] == "What is the company's revenue?"
        assert data["total_results"] == 2
        assert len(data["results"]) == 2
        
        # Check result structure
        result = data["results"][0]
        assert "doc_id" in result
        assert "chunk" in result
        assert "relevance_score" in result
        assert "filename" in result
        
        # Verify search was called with correct parameters
        mock_vector_search.search.assert_called_once()
        call_args = mock_vector_search.search.call_args
        assert call_args[1]["query"] == "What is the company's revenue?"
        assert call_args[1]["k"] == 5
        assert call_args[1]["min_score"] == 0.5
    
    def test_semantic_search_application_not_found(
        self,
        client,
        mock_app_repository
    ):
        """Test semantic search with non-existent application."""
        # Setup mock
        mock_app_repository.get_by_id = AsyncMock(return_value=None)
        
        # Make request
        response = client.post(
            "/api/v1/applications/nonexistent/search",
            json={
                "query": "test query"
            }
        )
        
        # Debug print
        if response.status_code != 404:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")
        
        # Assertions
        assert response.status_code == 404
        response_data = response.json()
        # Handle both error formats
        error_message = response_data.get("detail") or response_data.get("message", "")
        assert "not found" in error_message.lower()
    
    def test_semantic_search_no_documents_indexed(
        self,
        client,
        mock_vector_search,
        mock_app_repository,
        sample_application
    ):
        """Test semantic search when no documents are indexed."""
        # Setup mocks
        mock_app_repository.get_by_id = AsyncMock(return_value=sample_application)
        mock_vector_search.get_index_size = MagicMock(return_value=0)
        
        # Make request
        response = client.post(
            "/api/v1/applications/test-app-123/search",
            json={
                "query": "test query"
            }
        )
        
        # Debug print
        if response.status_code != 400:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")
        
        # Assertions
        assert response.status_code == 400
        response_data = response.json()
        error_message = response_data.get("detail") or response_data.get("message", "")
        assert "no documents are indexed" in error_message.lower()
    
    def test_semantic_search_filters_by_application(
        self,
        client,
        mock_vector_search,
        mock_app_repository,
        mock_doc_repository,
        mock_audit_logger,
        sample_application,
        sample_documents
    ):
        """Test that search results are filtered to only include documents from the application."""
        # Setup mocks - return results from different applications
        all_search_results = [
            {
                'doc_id': 'doc-1',  # Belongs to test-app-123
                'chunk': 'Revenue data',
                'chunk_index': 0,
                'total_chunks': 5,
                'relevance_score': 0.9
            },
            {
                'doc_id': 'doc-other',  # Belongs to different application
                'chunk': 'Other data',
                'chunk_index': 0,
                'total_chunks': 3,
                'relevance_score': 0.85
            }
        ]
        
        mock_app_repository.get_by_id = AsyncMock(return_value=sample_application)
        mock_doc_repository.list_by_application = AsyncMock(return_value=sample_documents)
        mock_vector_search.get_index_size = MagicMock(return_value=100)
        mock_vector_search.search = AsyncMock(return_value=all_search_results)
        
        # Make request
        response = client.post(
            "/api/v1/applications/test-app-123/search",
            json={
                "query": "test query"
            }
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        # Should only return doc-1, not doc-other
        assert data["total_results"] == 1
        assert data["results"][0]["doc_id"] == "doc-1"
    
    def test_semantic_search_invalid_query(self, client):
        """Test semantic search with invalid query (empty string)."""
        response = client.post(
            "/api/v1/applications/test-app-123/search",
            json={
                "query": ""
            }
        )
        
        # Should return validation error
        assert response.status_code == 422


class TestGetMonitoringAlerts:
    """Tests for GET /api/v1/monitoring/alerts endpoint."""
    
    def test_get_alerts_for_application(
        self,
        client,
        mock_monitoring_service,
        sample_alerts
    ):
        """Test getting alerts for a specific application."""
        # Setup mock
        mock_monitoring_service.get_alerts_for_application = AsyncMock(
            return_value=sample_alerts
        )
        
        # Make request
        response = client.get(
            "/api/v1/monitoring/alerts?application_id=test-app-123&limit=50"
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["alerts"]) == 2
        assert data["application_filter"] == "test-app-123"
        
        # Check alert structure
        alert = data["alerts"][0]
        assert "id" in alert
        assert "application_id" in alert
        assert "alert_type" in alert
        assert "severity" in alert
        assert "message" in alert
        assert "acknowledged" in alert
        
        # Verify service was called
        mock_monitoring_service.get_alerts_for_application.assert_called_once_with(
            application_id="test-app-123",
            limit=50
        )
    
    def test_get_alerts_filter_by_severity(
        self,
        client,
        mock_monitoring_service,
        sample_alerts
    ):
        """Test filtering alerts by severity."""
        # Setup mock
        mock_monitoring_service.get_alerts_for_application = AsyncMock(
            return_value=sample_alerts
        )
        
        # Make request with severity filter
        response = client.get(
            "/api/v1/monitoring/alerts?application_id=test-app-123&severity=high"
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        # Should only return the high severity alert
        assert data["total"] == 1
        assert data["alerts"][0]["severity"] == "high"
    
    def test_get_alerts_no_application_filter(
        self,
        client,
        mock_monitoring_service
    ):
        """Test getting alerts without application filter."""
        # Make request without application_id
        response = client.get("/api/v1/monitoring/alerts")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        # Should return empty list when no application_id specified
        assert data["total"] == 0
        assert data["application_filter"] is None
    
    def test_get_alerts_with_limit(
        self,
        client,
        mock_monitoring_service,
        sample_alerts
    ):
        """Test getting alerts with custom limit."""
        # Setup mock
        mock_monitoring_service.get_alerts_for_application = AsyncMock(
            return_value=sample_alerts[:1]  # Return only first alert
        )
        
        # Make request with limit=1
        response = client.get(
            "/api/v1/monitoring/alerts?application_id=test-app-123&limit=1"
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 1
        assert len(data["alerts"]) == 1


class TestGetMonitoringStatus:
    """Tests for GET /api/v1/monitoring/applications/{app_id} endpoint."""
    
    def test_get_monitoring_status_success(
        self,
        client,
        mock_app_repository,
        mock_monitoring_service,
        sample_application,
        sample_monitoring_status
    ):
        """Test successful retrieval of monitoring status."""
        # Setup mocks
        mock_app_repository.get_by_id = AsyncMock(return_value=sample_application)
        mock_monitoring_service.get_monitoring_status = AsyncMock(
            return_value=sample_monitoring_status
        )
        
        # Make request
        response = client.get("/api/v1/monitoring/applications/test-app-123")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["application_id"] == "test-app-123"
        assert data["company_name"] == "Test Company"
        assert data["status"] == "active"
        assert data["check_interval_days"] == 7
        assert data["total_checks"] == 5
        assert data["total_alerts"] == 2
        assert "activated_at" in data
        assert "last_check" in data
        assert "next_check" in data
    
    def test_get_monitoring_status_application_not_found(
        self,
        client,
        mock_app_repository
    ):
        """Test monitoring status for non-existent application."""
        # Setup mock
        mock_app_repository.get_by_id = AsyncMock(return_value=None)
        
        # Make request
        response = client.get("/api/v1/monitoring/applications/nonexistent")
        
        # Debug print
        if response.status_code != 404:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")
        
        # Assertions
        assert response.status_code == 404
        response_data = response.json()
        error_message = response_data.get("detail") or response_data.get("message", "")
        assert "not found" in error_message.lower()
    
    def test_get_monitoring_status_not_configured(
        self,
        client,
        mock_app_repository,
        mock_monitoring_service,
        sample_application
    ):
        """Test monitoring status when monitoring is not configured."""
        # Setup mocks
        mock_app_repository.get_by_id = AsyncMock(return_value=sample_application)
        mock_monitoring_service.get_monitoring_status = AsyncMock(return_value=None)
        
        # Make request
        response = client.get("/api/v1/monitoring/applications/test-app-123")
        
        # Debug print
        if response.status_code != 404:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")
        
        # Assertions
        assert response.status_code == 404
        response_data = response.json()
        error_message = response_data.get("detail") or response_data.get("message", "")
        assert "not configured" in error_message.lower()
    
    def test_get_monitoring_status_includes_context(
        self,
        client,
        mock_app_repository,
        mock_monitoring_service,
        sample_application,
        sample_monitoring_status
    ):
        """Test that monitoring status includes additional context."""
        # Setup mocks
        mock_app_repository.get_by_id = AsyncMock(return_value=sample_application)
        mock_monitoring_service.get_monitoring_status = AsyncMock(
            return_value=sample_monitoring_status
        )
        
        # Make request
        response = client.get("/api/v1/monitoring/applications/test-app-123")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "additional_context" in data
        assert data["additional_context"]["industry"] == "Manufacturing"


class TestSearchMonitoringIntegration:
    """Integration tests for search and monitoring endpoints."""
    
    def test_search_and_monitoring_workflow(
        self,
        client,
        mock_vector_search,
        mock_monitoring_service,
        mock_app_repository,
        mock_doc_repository,
        mock_audit_logger,
        sample_application,
        sample_documents,
        sample_search_results,
        sample_monitoring_status
    ):
        """Test complete workflow: search documents and check monitoring status."""
        # Setup mocks
        mock_app_repository.get_by_id = AsyncMock(return_value=sample_application)
        mock_doc_repository.list_by_application = AsyncMock(return_value=sample_documents)
        mock_vector_search.get_index_size = MagicMock(return_value=100)
        mock_vector_search.search = AsyncMock(return_value=sample_search_results)
        mock_monitoring_service.get_monitoring_status = AsyncMock(
            return_value=sample_monitoring_status
        )
        
        # 1. Perform semantic search
        search_response = client.post(
            "/api/v1/applications/test-app-123/search",
            json={"query": "revenue"}
        )
        assert search_response.status_code == 200
        
        # 2. Check monitoring status
        monitoring_response = client.get(
            "/api/v1/monitoring/applications/test-app-123"
        )
        assert monitoring_response.status_code == 200
        
        # Verify both operations succeeded
        search_data = search_response.json()
        monitoring_data = monitoring_response.json()
        
        assert search_data["application_id"] == monitoring_data["application_id"]
        assert monitoring_data["status"] == "active"
