"""
Unit tests for AnalysisRepository with SQLAlchemy.

Tests the SQLite3-based implementation of AnalysisRepository.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Analysis, Application, User
from app.repositories.analysis_repository import AnalysisRepository


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
        application_data='{"industry": "tech"}',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(application)
    db_session.commit()
    return application


@pytest.fixture
def repository(db_session):
    """Create an AnalysisRepository instance."""
    return AnalysisRepository(db_session)


class TestAnalysisRepositoryCreate:
    """Tests for create method."""
    
    def test_create_success(self, repository, test_application):
        """Test successful analysis creation."""
        analysis_data = {
            "id": "analysis-123",
            "application_id": test_application.id,
            "analysis_type": "financial",
            "analysis_results": '{"score": 85}',
            "confidence_score": 0.85,
            "status": "complete",
            "created_at": datetime.utcnow()
        }
        
        result = repository.create(analysis_data)
        
        assert result is not None
        assert result.id == "analysis-123"
        assert result.application_id == test_application.id
        assert result.analysis_type == "financial"
        assert result.confidence_score == 0.85
        assert result.status == "complete"
    
    def test_create_duplicate_id(self, repository, test_application):
        """Test creation fails when analysis ID already exists."""
        analysis_data = {
            "id": "analysis-123",
            "application_id": test_application.id,
            "analysis_type": "financial",
            "analysis_results": '{"score": 85}',
            "status": "complete",
            "created_at": datetime.utcnow()
        }
        
        repository.create(analysis_data)
        
        with pytest.raises(ValueError, match="already exists"):
            repository.create(analysis_data)
    
    def test_create_invalid_application_id(self, repository):
        """Test creation fails with invalid application_id foreign key."""
        analysis_data = {
            "id": "analysis-123",
            "application_id": "nonexistent-app",
            "analysis_type": "financial",
            "analysis_results": '{"score": 85}',
            "status": "complete",
            "created_at": datetime.utcnow()
        }
        
        with pytest.raises(ValueError, match="Invalid application_id"):
            repository.create(analysis_data)


class TestAnalysisRepositoryRead:
    """Tests for read methods."""
    
    def test_get_by_id_found(self, repository, test_application):
        """Test retrieving existing analysis by ID."""
        analysis_data = {
            "id": "analysis-123",
            "application_id": test_application.id,
            "analysis_type": "financial",
            "analysis_results": '{"score": 85}',
            "status": "complete",
            "created_at": datetime.utcnow()
        }
        repository.create(analysis_data)
        
        result = repository.get_by_id("analysis-123")
        
        assert result is not None
        assert result.id == "analysis-123"
        assert result.application_id == test_application.id
    
    def test_get_by_id_not_found(self, repository):
        """Test retrieving non-existent analysis returns None."""
        result = repository.get_by_id("nonexistent")
        assert result is None
    
    def test_get_by_application_id(self, repository, test_application):
        """Test retrieving all analyses for an application."""
        # Create multiple analyses for the same application
        for i in range(3):
            analysis_data = {
                "id": f"analysis-{i}",
                "application_id": test_application.id,
                "analysis_type": "financial",
                "analysis_results": f'{{"score": {80 + i}}}',
                "status": "complete",
                "created_at": datetime.utcnow()
            }
            repository.create(analysis_data)
        
        results = repository.get_by_application_id(test_application.id)
        
        assert len(results) == 3
        assert all(a.application_id == test_application.id for a in results)
    
    def test_get_by_application_id_empty(self, repository, test_application):
        """Test retrieving analyses for application with no analyses."""
        results = repository.get_by_application_id(test_application.id)
        assert results == []


class TestAnalysisRepositoryUpdate:
    """Tests for update method."""
    
    def test_update_success(self, repository, test_application):
        """Test successful analysis update."""
        analysis_data = {
            "id": "analysis-123",
            "application_id": test_application.id,
            "analysis_type": "financial",
            "analysis_results": '{"score": 85}',
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        repository.create(analysis_data)
        
        update_data = {
            "status": "complete",
            "confidence_score": 0.92
        }
        result = repository.update("analysis-123", update_data)
        
        assert result is not None
        assert result.status == "complete"
        assert result.confidence_score == 0.92
    
    def test_update_not_found(self, repository):
        """Test updating non-existent analysis returns None."""
        result = repository.update("nonexistent", {"status": "complete"})
        assert result is None


class TestAnalysisRepositoryIntegration:
    """Integration tests for AnalysisRepository."""
    
    def test_cascade_delete(self, repository, db_session, test_application):
        """Test that deleting an application cascades to analyses."""
        # Create analysis
        analysis_data = {
            "id": "analysis-123",
            "application_id": test_application.id,
            "analysis_type": "financial",
            "analysis_results": '{"score": 85}',
            "status": "complete",
            "created_at": datetime.utcnow()
        }
        repository.create(analysis_data)
        
        # Delete the application
        db_session.delete(test_application)
        db_session.commit()
        
        # Verify analysis is also deleted
        result = repository.get_by_id("analysis-123")
        assert result is None
    
    def test_multiple_analyses_per_application(self, repository, test_application):
        """Test that multiple analyses can be created for one application."""
        # Create multiple analyses
        for i in range(3):
            analysis_data = {
                "id": f"analysis-{i}",
                "application_id": test_application.id,
                "analysis_type": f"type-{i}",
                "analysis_results": f'{{"score": {80 + i}}}',
                "status": "complete",
                "created_at": datetime.utcnow()
            }
            repository.create(analysis_data)
        
        # Verify all analyses exist
        results = repository.get_by_application_id(test_application.id)
        assert len(results) == 3
