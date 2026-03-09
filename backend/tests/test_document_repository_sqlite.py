"""
Unit tests for DocumentRepository with SQLAlchemy.

Tests the SQLite3-based implementation of DocumentRepository.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Document, Application, User
from app.repositories.document_repository import DocumentRepository


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    
    # Enable foreign key constraints for SQLite
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user in the database."""
    user = User(
        id="user-123",
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_application(db_session, test_user):
    """Create a test application in the database."""
    application = Application(
        id="app-123",
        user_id=test_user.id,
        company_name="Test Company",
        status="pending",
        credit_amount=50000.0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(application)
    db_session.commit()
    return application


@pytest.fixture
def repository(db_session):
    """Create a DocumentRepository instance."""
    return DocumentRepository(db_session)


class TestDocumentRepositoryCreate:
    """Tests for create method."""
    
    def test_create_success(self, repository, test_application):
        """Test successful document creation."""
        doc_data = {
            "id": "doc-123",
            "application_id": test_application.id,
            "filename": "test.pdf",
            "file_path": "app-123/test.pdf",
            "file_size": 1024,
            "content_type": "application/pdf",
            "document_type": "financial_statement",
            "uploaded_at": datetime.utcnow()
        }
        
        result = repository.create(doc_data)
        
        assert result is not None
        assert result.id == "doc-123"
        assert result.filename == "test.pdf"
        assert result.file_path == "app-123/test.pdf"
        assert result.application_id == test_application.id
    
    def test_create_duplicate_id(self, repository, test_application):
        """Test creation fails when document ID already exists."""
        doc_data = {
            "id": "doc-123",
            "application_id": test_application.id,
            "filename": "test.pdf",
            "file_path": "app-123/test.pdf",
            "uploaded_at": datetime.utcnow()
        }
        
        repository.create(doc_data)
        
        with pytest.raises(ValueError, match="already exists"):
            repository.create(doc_data)
    
    def test_create_invalid_application_id(self, repository):
        """Test creation fails with invalid application_id."""
        doc_data = {
            "id": "doc-123",
            "application_id": "nonexistent-app",
            "filename": "test.pdf",
            "file_path": "app-123/test.pdf",
            "uploaded_at": datetime.utcnow()
        }
        
        with pytest.raises(ValueError, match="Invalid application_id"):
            repository.create(doc_data)


class TestDocumentRepositoryRead:
    """Tests for read methods."""
    
    def test_get_by_id_found(self, repository, test_application):
        """Test retrieving an existing document."""
        doc_data = {
            "id": "doc-123",
            "application_id": test_application.id,
            "filename": "test.pdf",
            "file_path": "app-123/test.pdf",
            "uploaded_at": datetime.utcnow()
        }
        repository.create(doc_data)
        
        result = repository.get_by_id("doc-123")
        
        assert result is not None
        assert result.id == "doc-123"
        assert result.filename == "test.pdf"
    
    def test_get_by_id_not_found(self, repository):
        """Test retrieving a non-existent document."""
        result = repository.get_by_id("nonexistent")
        assert result is None
    
    def test_get_by_application_id(self, repository, test_application):
        """Test retrieving documents by application ID."""
        # Create multiple documents
        for i in range(3):
            doc_data = {
                "id": f"doc-{i}",
                "application_id": test_application.id,
                "filename": f"test-{i}.pdf",
                "file_path": f"app-123/test-{i}.pdf",
                "uploaded_at": datetime.utcnow()
            }
            repository.create(doc_data)
        
        results = repository.get_by_application_id(test_application.id)
        
        assert len(results) == 3
        assert all(doc.application_id == test_application.id for doc in results)
    
    def test_get_by_application_id_empty(self, repository, test_application):
        """Test retrieving documents for application with no documents."""
        results = repository.get_by_application_id(test_application.id)
        assert len(results) == 0


class TestDocumentRepositoryDelete:
    """Tests for delete method."""
    
    def test_delete_success(self, repository, test_application):
        """Test successful document deletion."""
        doc_data = {
            "id": "doc-123",
            "application_id": test_application.id,
            "filename": "test.pdf",
            "file_path": "app-123/test.pdf",
            "uploaded_at": datetime.utcnow()
        }
        repository.create(doc_data)
        
        result = repository.delete("doc-123")
        
        assert result is True
        assert repository.get_by_id("doc-123") is None
    
    def test_delete_not_found(self, repository):
        """Test deleting a non-existent document."""
        result = repository.delete("nonexistent")
        assert result is False
    
    def test_delete_cascade_on_application_delete(self, repository, test_application, db_session):
        """Test that documents are deleted when application is deleted (cascade)."""
        # Create documents
        for i in range(3):
            doc_data = {
                "id": f"doc-{i}",
                "application_id": test_application.id,
                "filename": f"test-{i}.pdf",
                "file_path": f"app-123/test-{i}.pdf",
                "uploaded_at": datetime.utcnow()
            }
            repository.create(doc_data)
        
        # Delete the application
        db_session.delete(test_application)
        db_session.commit()
        
        # Verify documents are also deleted
        results = repository.get_by_application_id(test_application.id)
        assert len(results) == 0
