"""
Unit tests for document operation API endpoints.

Tests the RESTful endpoints for uploading, listing, retrieving, and deleting
documents associated with credit applications.

Requirements: 1.1, 1.4, 14.1
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
import io

from app.main import app
from app.models.domain import Document, Application, ApplicationStatus


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
def sample_document(sample_application):
    """Create a sample document for testing."""
    return Document(
        id=str(uuid.uuid4()),
        application_id=sample_application.id,
        filename="financial_statement.pdf",
        file_type="pdf",
        storage_path=f"documents/{sample_application.id}/test_doc.pdf",
        upload_date=datetime.utcnow(),
        processing_status="pending"
    )


@pytest.fixture
def mock_document_repository():
    """Create a mock document repository."""
    with patch('app.api.documents.get_document_repository') as mock:
        repo = MagicMock()
        mock.return_value = repo
        yield repo


@pytest.fixture
def mock_application_repository():
    """Create a mock application repository."""
    with patch('app.api.documents.get_application_repository') as mock:
        repo = MagicMock()
        mock.return_value = repo
        yield repo


@pytest.fixture
def mock_storage_service():
    """Create a mock storage service."""
    with patch('app.api.documents.get_storage_service') as mock:
        service = MagicMock()
        mock.return_value = service
        yield service


@pytest.fixture
def mock_audit_logger():
    """Create a mock audit logger."""
    with patch('app.api.documents.get_audit_logger') as mock:
        logger = MagicMock()
        logger.log_user_action = AsyncMock()
        mock.return_value = logger
        yield logger


class TestUploadDocument:
    """Tests for POST /api/v1/applications/{app_id}/documents endpoint."""
    
    def test_upload_document_success(
        self,
        client,
        sample_application,
        sample_document,
        mock_application_repository,
        mock_document_repository,
        mock_storage_service,
        mock_audit_logger
    ):
        """Test successful document upload."""
        # Setup mocks
        mock_application_repository.get_by_id = AsyncMock(return_value=sample_application)
        mock_document_repository.create = AsyncMock(return_value=sample_document)
        mock_storage_service.upload_file = AsyncMock(return_value={
            'storage_path': sample_document.storage_path,
            'signed_url': 'https://storage.example.com/signed-url',
            'content_type': 'application/pdf',
            'file_size': 1024,
            'metadata': {}
        })
        
        # Create test file
        file_content = b"PDF file content"
        files = {
            'file': ('financial_statement.pdf', io.BytesIO(file_content), 'application/pdf')
        }
        data = {
            'document_type': 'financial_statement'
        }
        
        # Make request
        response = client.post(
            f"/api/v1/applications/{sample_application.id}/documents",
            files=files,
            data=data
        )
        
        # Assertions
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["application_id"] == sample_application.id
        assert response_data["filename"] == "financial_statement.pdf"
        assert response_data["file_type"] == "pdf"
        assert response_data["processing_status"] == "pending"
        assert "signed_url" in response_data
        
        # Verify mocks were called
        mock_application_repository.get_by_id.assert_called_once_with(sample_application.id)
        mock_storage_service.upload_file.assert_called_once()
        mock_document_repository.create.assert_called_once()
        mock_audit_logger.log_user_action.assert_called_once()
    
    def test_upload_document_application_not_found(
        self,
        client,
        mock_application_repository,
        mock_storage_service
    ):
        """Test document upload when application doesn't exist."""
        # Setup mock
        mock_application_repository.get_by_id = AsyncMock(return_value=None)
        
        # Create test file
        file_content = b"PDF file content"
        files = {
            'file': ('test.pdf', io.BytesIO(file_content), 'application/pdf')
        }
        data = {
            'document_type': 'financial_statement'
        }
        
        # Make request
        response = client.post(
            "/api/v1/applications/nonexistent-id/documents",
            files=files,
            data=data
        )
        
        # Assertions
        assert response.status_code == 404
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("message", "")
        assert "not found" in error_msg.lower()
    
    def test_upload_document_invalid_file_type(
        self,
        client,
        sample_application,
        mock_application_repository,
        mock_storage_service
    ):
        """Test document upload with invalid file type."""
        # Setup mocks
        mock_application_repository.get_by_id = AsyncMock(return_value=sample_application)
        mock_storage_service.upload_file = AsyncMock(
            side_effect=ValueError("Invalid file type. Allowed types: pdf, docx, xlsx, csv, jpg, png")
        )
        
        # Create test file with invalid extension
        file_content = b"Invalid file content"
        files = {
            'file': ('test.exe', io.BytesIO(file_content), 'application/octet-stream')
        }
        data = {
            'document_type': 'financial_statement'
        }
        
        # Make request
        response = client.post(
            f"/api/v1/applications/{sample_application.id}/documents",
            files=files,
            data=data
        )
        
        # Assertions
        assert response.status_code == 400
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("message", "")
        assert "Invalid file type" in error_msg
    
    def test_upload_document_file_too_large(
        self,
        client,
        sample_application,
        mock_application_repository,
        mock_storage_service
    ):
        """Test document upload with file exceeding size limit."""
        # Setup mocks
        mock_application_repository.get_by_id = AsyncMock(return_value=sample_application)
        mock_storage_service.upload_file = AsyncMock(
            side_effect=ValueError("File size must be between 1 byte and 50MB")
        )
        
        # Create test file
        file_content = b"Large file content"
        files = {
            'file': ('large_file.pdf', io.BytesIO(file_content), 'application/pdf')
        }
        data = {
            'document_type': 'financial_statement'
        }
        
        # Make request
        response = client.post(
            f"/api/v1/applications/{sample_application.id}/documents",
            files=files,
            data=data
        )
        
        # Assertions
        assert response.status_code == 400
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("message", "")
        assert "File size" in error_msg


class TestListDocuments:
    """Tests for GET /api/v1/applications/{app_id}/documents endpoint."""
    
    def test_list_documents_success(
        self,
        client,
        sample_application,
        sample_document,
        mock_application_repository,
        mock_document_repository
    ):
        """Test successful document listing."""
        # Setup mocks
        mock_application_repository.get_by_id = AsyncMock(return_value=sample_application)
        
        # Create multiple documents
        doc2 = Document(
            id=str(uuid.uuid4()),
            application_id=sample_application.id,
            filename="bank_statement.pdf",
            file_type="pdf",
            storage_path=f"documents/{sample_application.id}/bank_statement.pdf",
            upload_date=datetime.utcnow(),
            processing_status="complete"
        )
        
        mock_document_repository.list_by_application = AsyncMock(
            return_value=[sample_document, doc2]
        )
        
        # Make request
        response = client.get(f"/api/v1/applications/{sample_application.id}/documents")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["application_id"] == sample_application.id
        assert len(data["documents"]) == 2
        assert data["documents"][0]["filename"] == "financial_statement.pdf"
        assert data["documents"][1]["filename"] == "bank_statement.pdf"
        
        # Verify mocks were called
        mock_application_repository.get_by_id.assert_called_once_with(sample_application.id)
        mock_document_repository.list_by_application.assert_called_once_with(sample_application.id)
    
    def test_list_documents_empty(
        self,
        client,
        sample_application,
        mock_application_repository,
        mock_document_repository
    ):
        """Test listing documents when none exist."""
        # Setup mocks
        mock_application_repository.get_by_id = AsyncMock(return_value=sample_application)
        mock_document_repository.list_by_application = AsyncMock(return_value=[])
        
        # Make request
        response = client.get(f"/api/v1/applications/{sample_application.id}/documents")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["documents"]) == 0
    
    def test_list_documents_application_not_found(
        self,
        client,
        mock_application_repository
    ):
        """Test listing documents when application doesn't exist."""
        # Setup mock
        mock_application_repository.get_by_id = AsyncMock(return_value=None)
        
        # Make request
        response = client.get("/api/v1/applications/nonexistent-id/documents")
        
        # Assertions
        assert response.status_code == 404
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("message", "")
        assert "not found" in error_msg.lower()


class TestGetDocument:
    """Tests for GET /api/v1/documents/{doc_id} endpoint."""
    
    def test_get_document_success(
        self,
        client,
        sample_document,
        mock_document_repository,
        mock_storage_service
    ):
        """Test successful document retrieval."""
        # Setup mocks
        mock_document_repository.get_by_id = AsyncMock(return_value=sample_document)
        mock_storage_service.generate_signed_url = AsyncMock(
            return_value='https://storage.example.com/signed-url'
        )
        
        # Make request
        response = client.get(f"/api/v1/documents/{sample_document.id}")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_document.id
        assert data["filename"] == sample_document.filename
        assert data["file_type"] == sample_document.file_type
        assert "signed_url" in data
        
        # Verify mocks were called
        mock_document_repository.get_by_id.assert_called_once_with(sample_document.id)
        mock_storage_service.generate_signed_url.assert_called_once_with(sample_document.storage_path)
    
    def test_get_document_not_found(
        self,
        client,
        mock_document_repository
    ):
        """Test getting document that doesn't exist."""
        # Setup mock
        mock_document_repository.get_by_id = AsyncMock(return_value=None)
        
        # Make request
        response = client.get("/api/v1/documents/nonexistent-id")
        
        # Assertions
        assert response.status_code == 404
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("message", "")
        assert "not found" in error_msg.lower()


class TestDeleteDocument:
    """Tests for DELETE /api/v1/documents/{doc_id} endpoint."""
    
    def test_delete_document_success(
        self,
        client,
        sample_document,
        mock_document_repository,
        mock_storage_service,
        mock_audit_logger
    ):
        """Test successful document deletion."""
        # Setup mocks
        mock_document_repository.get_by_id = AsyncMock(return_value=sample_document)
        mock_storage_service.delete_file = AsyncMock(return_value=True)
        mock_document_repository.delete = AsyncMock(return_value=True)
        
        # Make request
        response = client.delete(f"/api/v1/documents/{sample_document.id}")
        
        # Assertions
        assert response.status_code == 204
        
        # Verify mocks were called
        mock_document_repository.get_by_id.assert_called_once_with(sample_document.id)
        mock_storage_service.delete_file.assert_called_once_with(sample_document.storage_path)
        mock_document_repository.delete.assert_called_once_with(sample_document.id)
        mock_audit_logger.log_user_action.assert_called_once()
    
    def test_delete_document_not_found(
        self,
        client,
        mock_document_repository
    ):
        """Test deleting document that doesn't exist."""
        # Setup mock
        mock_document_repository.get_by_id = AsyncMock(return_value=None)
        
        # Make request
        response = client.delete("/api/v1/documents/nonexistent-id")
        
        # Assertions
        assert response.status_code == 404
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("message", "")
        assert "not found" in error_msg.lower()
    
    def test_delete_document_storage_error(
        self,
        client,
        sample_document,
        mock_document_repository,
        mock_storage_service
    ):
        """Test document deletion when storage deletion fails."""
        # Setup mocks
        mock_document_repository.get_by_id = AsyncMock(return_value=sample_document)
        mock_storage_service.delete_file = AsyncMock(
            side_effect=Exception("Storage deletion failed")
        )
        
        # Make request
        response = client.delete(f"/api/v1/documents/{sample_document.id}")
        
        # Assertions
        assert response.status_code == 500
        response_data = response.json()
        error_msg = response_data.get("detail") or response_data.get("message", "")
        assert "Failed to delete document" in error_msg or "error" in error_msg.lower()


class TestDocumentEndpointsIntegration:
    """Integration tests for document endpoints workflow."""
    
    def test_upload_list_get_delete_workflow(
        self,
        client,
        sample_application,
        mock_application_repository,
        mock_document_repository,
        mock_storage_service,
        mock_audit_logger
    ):
        """Test complete document workflow: upload -> list -> get -> delete."""
        # Setup mocks for upload
        mock_application_repository.get_by_id = AsyncMock(return_value=sample_application)
        
        doc_id = str(uuid.uuid4())
        uploaded_doc = Document(
            id=doc_id,
            application_id=sample_application.id,
            filename="test.pdf",
            file_type="pdf",
            storage_path=f"documents/{sample_application.id}/{doc_id}_test.pdf",
            upload_date=datetime.utcnow(),
            processing_status="pending"
        )
        
        mock_document_repository.create = AsyncMock(return_value=uploaded_doc)
        mock_storage_service.upload_file = AsyncMock(return_value={
            'storage_path': uploaded_doc.storage_path,
            'signed_url': 'https://storage.example.com/signed-url',
            'content_type': 'application/pdf',
            'file_size': 1024,
            'metadata': {}
        })
        
        # 1. Upload document
        file_content = b"PDF content"
        files = {'file': ('test.pdf', io.BytesIO(file_content), 'application/pdf')}
        data = {'document_type': 'financial_statement'}
        
        upload_response = client.post(
            f"/api/v1/applications/{sample_application.id}/documents",
            files=files,
            data=data
        )
        assert upload_response.status_code == 201
        
        # 2. List documents
        mock_document_repository.list_by_application = AsyncMock(return_value=[uploaded_doc])
        list_response = client.get(f"/api/v1/applications/{sample_application.id}/documents")
        assert list_response.status_code == 200
        assert list_response.json()["total"] == 1
        
        # 3. Get document
        mock_document_repository.get_by_id = AsyncMock(return_value=uploaded_doc)
        mock_storage_service.generate_signed_url = AsyncMock(
            return_value='https://storage.example.com/signed-url'
        )
        get_response = client.get(f"/api/v1/documents/{doc_id}")
        assert get_response.status_code == 200
        
        # 4. Delete document
        mock_storage_service.delete_file = AsyncMock(return_value=True)
        mock_document_repository.delete = AsyncMock(return_value=True)
        delete_response = client.delete(f"/api/v1/documents/{doc_id}")
        assert delete_response.status_code == 204
