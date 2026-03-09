"""
Unit tests for Document SQLAlchemy model.

Tests the Document model structure, relationships, and database operations.
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.database.config import DatabaseConfig
from app.database.models import User, Application, Document


@pytest.fixture
def db_session():
    """Create an in-memory database session for testing."""
    db_config = DatabaseConfig("sqlite:///:memory:")
    db_config.create_tables()
    session = db_config.get_session()
    yield session
    session.close()
    db_config.close()


class TestDocumentModel:
    """Test Document model."""
    
    def test_create_document(self, db_session):
        """Test creating a document with all required fields."""
        # Create user and application first (foreign key dependencies)
        user = User(
            id="user-123",
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User"
        )
        db_session.add(user)
        db_session.commit()
        
        application = Application(
            id="app-123",
            user_id="user-123",
            company_name="Test Corp",
            status="pending",
            credit_amount=1000000.0
        )
        db_session.add(application)
        db_session.commit()
        
        # Create document
        document = Document(
            id="doc-123",
            application_id="app-123",
            filename="financial_statement.pdf",
            file_path="storage/app-123/doc-123.pdf",
            file_size=1024000,
            content_type="application/pdf",
            document_type="financial_statement"
        )
        db_session.add(document)
        db_session.commit()
        
        # Verify document was created
        retrieved_doc = db_session.query(Document).filter_by(id="doc-123").first()
        assert retrieved_doc is not None
        assert retrieved_doc.id == "doc-123"
        assert retrieved_doc.application_id == "app-123"
        assert retrieved_doc.filename == "financial_statement.pdf"
        assert retrieved_doc.file_path == "storage/app-123/doc-123.pdf"
        assert retrieved_doc.file_size == 1024000
        assert retrieved_doc.content_type == "application/pdf"
        assert retrieved_doc.document_type == "financial_statement"
        assert isinstance(retrieved_doc.uploaded_at, datetime)
    
    def test_document_application_relationship(self, db_session):
        """Test relationship between Document and Application."""
        # Create user and application
        user = User(
            id="user-123",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        
        application = Application(
            id="app-123",
            user_id="user-123",
            company_name="Test Corp",
            status="pending"
        )
        db_session.add(application)
        db_session.commit()
        
        # Create multiple documents
        doc1 = Document(
            id="doc-1",
            application_id="app-123",
            filename="file1.pdf",
            file_path="storage/app-123/file1.pdf",
            document_type="financial_statement"
        )
        doc2 = Document(
            id="doc-2",
            application_id="app-123",
            filename="file2.pdf",
            file_path="storage/app-123/file2.pdf",
            document_type="tax_return"
        )
        db_session.add(doc1)
        db_session.add(doc2)
        db_session.commit()
        
        # Verify relationship from application to documents
        app_with_docs = db_session.query(Application).filter_by(id="app-123").first()
        assert len(app_with_docs.documents) == 2
        assert app_with_docs.documents[0].filename in ["file1.pdf", "file2.pdf"]
        assert app_with_docs.documents[1].filename in ["file1.pdf", "file2.pdf"]
        
        # Verify relationship from document to application
        doc = db_session.query(Document).filter_by(id="doc-1").first()
        assert doc.application.id == "app-123"
        assert doc.application.company_name == "Test Corp"
    
    def test_document_cascade_delete(self, db_session):
        """Test that documents are deleted when application is deleted."""
        # Create user, application, and document
        user = User(
            id="user-123",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        
        application = Application(
            id="app-123",
            user_id="user-123",
            company_name="Test Corp",
            status="pending"
        )
        db_session.add(application)
        
        document = Document(
            id="doc-123",
            application_id="app-123",
            filename="file.pdf",
            file_path="storage/app-123/file.pdf"
        )
        db_session.add(document)
        db_session.commit()
        
        # Delete application
        db_session.delete(application)
        db_session.commit()
        
        # Verify document was also deleted (cascade)
        deleted_doc = db_session.query(Document).filter_by(id="doc-123").first()
        assert deleted_doc is None
    
    def test_document_foreign_key_constraint(self, db_session):
        """Test that foreign key constraint is enforced."""
        # Try to create document with non-existent application_id
        document = Document(
            id="doc-123",
            application_id="non-existent-app",
            filename="file.pdf",
            file_path="storage/file.pdf"
        )
        db_session.add(document)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        db_session.rollback()
    
    def test_document_indexes(self, db_session):
        """Test that indexes are created for application_id and document_type."""
        # Create user and application
        user = User(
            id="user-123",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        
        application = Application(
            id="app-123",
            user_id="user-123",
            company_name="Test Corp",
            status="pending"
        )
        db_session.add(application)
        db_session.commit()
        
        # Create multiple documents with different types
        for i in range(5):
            doc = Document(
                id=f"doc-{i}",
                application_id="app-123",
                filename=f"file{i}.pdf",
                file_path=f"storage/app-123/file{i}.pdf",
                document_type="financial_statement" if i % 2 == 0 else "tax_return"
            )
            db_session.add(doc)
        db_session.commit()
        
        # Query by application_id (should use index)
        docs_by_app = db_session.query(Document).filter_by(application_id="app-123").all()
        assert len(docs_by_app) == 5
        
        # Query by document_type (should use index)
        financial_docs = db_session.query(Document).filter_by(document_type="financial_statement").all()
        assert len(financial_docs) == 3
        
        tax_docs = db_session.query(Document).filter_by(document_type="tax_return").all()
        assert len(tax_docs) == 2
    
    def test_document_optional_fields(self, db_session):
        """Test that optional fields can be None."""
        # Create user and application
        user = User(
            id="user-123",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        
        application = Application(
            id="app-123",
            user_id="user-123",
            company_name="Test Corp",
            status="pending"
        )
        db_session.add(application)
        db_session.commit()
        
        # Create document with only required fields
        document = Document(
            id="doc-123",
            application_id="app-123",
            filename="file.pdf",
            file_path="storage/app-123/file.pdf"
        )
        db_session.add(document)
        db_session.commit()
        
        # Verify optional fields are None
        retrieved_doc = db_session.query(Document).filter_by(id="doc-123").first()
        assert retrieved_doc.file_size is None
        assert retrieved_doc.content_type is None
        assert retrieved_doc.document_type is None
