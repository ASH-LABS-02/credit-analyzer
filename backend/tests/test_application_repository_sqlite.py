"""
Unit tests for ApplicationRepository with SQLAlchemy.

Tests the SQLite3-based implementation of ApplicationRepository.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base, Application, User
from app.repositories.application_repository import ApplicationRepository


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
def repository(db_session):
    """Create an ApplicationRepository instance."""
    return ApplicationRepository(db_session)


class TestApplicationRepositoryCreate:
    """Tests for create method."""
    
    def test_create_success(self, repository, test_user):
        """Test successful application creation."""
        app_data = {
            "id": "app-123",
            "user_id": test_user.id,
            "company_name": "Test Company",
            "status": "pending",
            "credit_amount": 50000.0,
            "application_data": '{"industry": "tech"}',
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = repository.create(app_data)
        
        assert result is not None
        assert result.id == "app-123"
        assert result.company_name == "Test Company"
        assert result.status == "pending"
        assert result.user_id == test_user.id
    
    def test_create_duplicate_id(self, repository, test_user):
        """Test creation fails when application ID already exists."""
        app_data = {
            "id": "app-123",
            "user_id": test_user.id,
            "company_name": "Test Company",
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        repository.create(app_data)
        
        with pytest.raises(ValueError, match="already exists"):
            repository.create(app_data)
    
    def test_create_invalid_user_id(self, repository):
        """Test creation fails with invalid user_id."""
        app_data = {
            "id": "app-123",
            "user_id": "nonexistent-user",
            "company_name": "Test Company",
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        with pytest.raises(ValueError, match="Invalid user_id"):
            repository.create(app_data)


class TestApplicationRepositoryRead:
    """Tests for read methods."""
    
    def test_get_by_id_found(self, repository, test_user):
        """Test retrieving an existing application."""
        app_data = {
            "id": "app-123",
            "user_id": test_user.id,
            "company_name": "Test Company",
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        repository.create(app_data)
        
        result = repository.get_by_id("app-123")
        
        assert result is not None
        assert result.id == "app-123"
        assert result.company_name == "Test Company"
    
    def test_get_by_id_not_found(self, repository):
        """Test retrieving a non-existent application."""
        result = repository.get_by_id("nonexistent")
        assert result is None
    
    def test_get_by_user_id(self, repository, test_user):
        """Test retrieving applications by user ID."""
        # Create multiple applications
        for i in range(3):
            app_data = {
                "id": f"app-{i}",
                "user_id": test_user.id,
                "company_name": f"Company {i}",
                "status": "pending",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            repository.create(app_data)
        
        results = repository.get_by_user_id(test_user.id)
        
        assert len(results) == 3
        assert all(app.user_id == test_user.id for app in results)


class TestApplicationRepositoryUpdate:
    """Tests for update method."""
    
    def test_update_success(self, repository, test_user):
        """Test successful application update."""
        app_data = {
            "id": "app-123",
            "user_id": test_user.id,
            "company_name": "Test Company",
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        repository.create(app_data)
        
        result = repository.update("app-123", {"status": "approved"})
        
        assert result is not None
        assert result.status == "approved"
    
    def test_update_not_found(self, repository):
        """Test updating a non-existent application."""
        result = repository.update("nonexistent", {"status": "approved"})
        assert result is None


class TestApplicationRepositoryDelete:
    """Tests for delete method."""
    
    def test_delete_success(self, repository, test_user):
        """Test successful application deletion."""
        app_data = {
            "id": "app-123",
            "user_id": test_user.id,
            "company_name": "Test Company",
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        repository.create(app_data)
        
        result = repository.delete("app-123")
        
        assert result is True
        assert repository.get_by_id("app-123") is None
    
    def test_delete_not_found(self, repository):
        """Test deleting a non-existent application."""
        result = repository.delete("nonexistent")
        assert result is False


class TestApplicationRepositoryListWithFilters:
    """Tests for list_with_filters method."""
    
    def test_list_all(self, repository, test_user):
        """Test listing all applications."""
        for i in range(5):
            app_data = {
                "id": f"app-{i}",
                "user_id": test_user.id,
                "company_name": f"Company {i}",
                "status": "pending",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            repository.create(app_data)
        
        results = repository.list_with_filters()
        
        assert len(results) == 5
    
    def test_list_with_status_filter(self, repository, test_user):
        """Test listing with status filter."""
        statuses = ["pending", "approved", "pending", "rejected", "pending"]
        for i, status in enumerate(statuses):
            app_data = {
                "id": f"app-{i}",
                "user_id": test_user.id,
                "company_name": f"Company {i}",
                "status": status,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            repository.create(app_data)
        
        results = repository.list_with_filters(filters={"status": "pending"})
        
        assert len(results) == 3
        assert all(app.status == "pending" for app in results)
    
    def test_list_with_user_filter(self, repository, test_user, db_session):
        """Test listing with user_id filter."""
        # Create another user
        user2 = User(
            id="user-456",
            email="user2@example.com",
            hashed_password="hashed",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(user2)
        db_session.commit()
        
        # Create applications for both users
        for i in range(3):
            app_data = {
                "id": f"app-user1-{i}",
                "user_id": test_user.id,
                "company_name": f"Company {i}",
                "status": "pending",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            repository.create(app_data)
        
        for i in range(2):
            app_data = {
                "id": f"app-user2-{i}",
                "user_id": user2.id,
                "company_name": f"Company {i}",
                "status": "pending",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            repository.create(app_data)
        
        results = repository.list_with_filters(filters={"user_id": test_user.id})
        
        assert len(results) == 3
        assert all(app.user_id == test_user.id for app in results)
    
    def test_list_with_limit(self, repository, test_user):
        """Test listing with limit."""
        for i in range(10):
            app_data = {
                "id": f"app-{i}",
                "user_id": test_user.id,
                "company_name": f"Company {i}",
                "status": "pending",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            repository.create(app_data)
        
        results = repository.list_with_filters(limit=5)
        
        assert len(results) == 5
    
    def test_list_with_offset(self, repository, test_user):
        """Test listing with offset."""
        for i in range(10):
            app_data = {
                "id": f"app-{i}",
                "user_id": test_user.id,
                "company_name": f"Company {i}",
                "status": "pending",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            repository.create(app_data)
        
        results = repository.list_with_filters(limit=5, offset=5)
        
        assert len(results) == 5
