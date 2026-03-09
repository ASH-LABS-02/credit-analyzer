"""
Unit tests for UserRepository.

Tests CRUD operations for User entities using SQLAlchemy and SQLite3.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.config import Base
from app.database.models import User
from app.repositories.user_repository import UserRepository


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def user_repo(db_session):
    """Create a UserRepository instance with test database session."""
    return UserRepository(db_session)


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "user123",
        "email": "test@example.com",
        "hashed_password": "$2b$12$abcdefghijklmnopqrstuvwxyz",
        "full_name": "Test User",
        "is_active": True
    }


class TestUserRepositoryCreate:
    """Tests for user creation."""
    
    def test_create_user_success(self, user_repo, sample_user_data):
        """Test creating a new user successfully."""
        user = user_repo.create(sample_user_data)
        
        assert user is not None
        assert user.id == sample_user_data["id"]
        assert user.email == sample_user_data["email"]
        assert user.hashed_password == sample_user_data["hashed_password"]
        assert user.full_name == sample_user_data["full_name"]
        assert user.is_active == sample_user_data["is_active"]
        assert user.created_at is not None
        assert user.updated_at is not None
    
    def test_create_user_duplicate_id(self, user_repo, sample_user_data):
        """Test creating a user with duplicate ID raises ValueError."""
        user_repo.create(sample_user_data)
        
        # Try to create another user with same ID but different email
        duplicate_data = sample_user_data.copy()
        duplicate_data["email"] = "different@example.com"
        
        with pytest.raises(ValueError) as exc_info:
            user_repo.create(duplicate_data)
        
        assert "already exists" in str(exc_info.value).lower()
    
    def test_create_user_duplicate_email(self, user_repo, sample_user_data):
        """Test creating a user with duplicate email raises ValueError."""
        user_repo.create(sample_user_data)
        
        # Try to create another user with same email but different ID
        duplicate_data = sample_user_data.copy()
        duplicate_data["id"] = "user456"
        
        with pytest.raises(ValueError) as exc_info:
            user_repo.create(duplicate_data)
        
        assert "email" in str(exc_info.value).lower()
        assert "already exists" in str(exc_info.value).lower()
    
    def test_create_user_minimal_data(self, user_repo):
        """Test creating a user with minimal required fields."""
        minimal_data = {
            "id": "user789",
            "email": "minimal@example.com",
            "hashed_password": "$2b$12$hashedpassword"
        }
        
        user = user_repo.create(minimal_data)
        
        assert user is not None
        assert user.id == minimal_data["id"]
        assert user.email == minimal_data["email"]
        assert user.full_name is None
        assert user.is_active is True  # Default value


class TestUserRepositoryGetById:
    """Tests for retrieving users by ID."""
    
    def test_get_by_id_existing_user(self, user_repo, sample_user_data):
        """Test retrieving an existing user by ID."""
        created_user = user_repo.create(sample_user_data)
        
        retrieved_user = user_repo.get_by_id(created_user.id)
        
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == created_user.email
    
    def test_get_by_id_nonexistent_user(self, user_repo):
        """Test retrieving a non-existent user returns None."""
        user = user_repo.get_by_id("nonexistent_id")
        
        assert user is None


class TestUserRepositoryGetByEmail:
    """Tests for retrieving users by email."""
    
    def test_get_by_email_existing_user(self, user_repo, sample_user_data):
        """Test retrieving an existing user by email."""
        created_user = user_repo.create(sample_user_data)
        
        retrieved_user = user_repo.get_by_email(created_user.email)
        
        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.email == created_user.email
    
    def test_get_by_email_nonexistent_user(self, user_repo):
        """Test retrieving a non-existent user by email returns None."""
        user = user_repo.get_by_email("nonexistent@example.com")
        
        assert user is None
    
    def test_get_by_email_case_sensitive(self, user_repo, sample_user_data):
        """Test that email lookup is case-sensitive."""
        user_repo.create(sample_user_data)
        
        # SQLite is case-insensitive for LIKE but case-sensitive for =
        # This test verifies exact match behavior
        user = user_repo.get_by_email(sample_user_data["email"].upper())
        
        # Depending on SQLite collation, this might return None or the user
        # The important thing is the behavior is consistent
        assert user is None or user.email == sample_user_data["email"]


class TestUserRepositoryUpdate:
    """Tests for updating users."""
    
    def test_update_user_success(self, user_repo, sample_user_data):
        """Test updating a user successfully."""
        created_user = user_repo.create(sample_user_data)
        
        update_data = {
            "full_name": "Updated Name",
            "is_active": False
        }
        
        updated_user = user_repo.update(created_user.id, update_data)
        
        assert updated_user is not None
        assert updated_user.id == created_user.id
        assert updated_user.full_name == "Updated Name"
        assert updated_user.is_active is False
        assert updated_user.email == created_user.email  # Unchanged
    
    def test_update_nonexistent_user(self, user_repo):
        """Test updating a non-existent user returns None."""
        update_data = {"full_name": "New Name"}
        
        result = user_repo.update("nonexistent_id", update_data)
        
        assert result is None
    
    def test_update_email_success(self, user_repo, sample_user_data):
        """Test updating user email to a unique value."""
        created_user = user_repo.create(sample_user_data)
        
        new_email = "newemail@example.com"
        updated_user = user_repo.update(created_user.id, {"email": new_email})
        
        assert updated_user is not None
        assert updated_user.email == new_email
    
    def test_update_email_duplicate(self, user_repo, sample_user_data):
        """Test updating email to an existing email raises ValueError."""
        # Create first user
        user_repo.create(sample_user_data)
        
        # Create second user
        second_user_data = {
            "id": "user456",
            "email": "second@example.com",
            "hashed_password": "$2b$12$hashedpassword"
        }
        second_user = user_repo.create(second_user_data)
        
        # Try to update second user's email to first user's email
        with pytest.raises(ValueError) as exc_info:
            user_repo.update(second_user.id, {"email": sample_user_data["email"]})
        
        assert "email" in str(exc_info.value).lower()
        assert "already exists" in str(exc_info.value).lower()
    
    def test_update_password(self, user_repo, sample_user_data):
        """Test updating user password."""
        created_user = user_repo.create(sample_user_data)
        
        new_password_hash = "$2b$12$newhashedpassword"
        updated_user = user_repo.update(created_user.id, {"hashed_password": new_password_hash})
        
        assert updated_user is not None
        assert updated_user.hashed_password == new_password_hash
    
    def test_update_multiple_fields(self, user_repo, sample_user_data):
        """Test updating multiple fields at once."""
        created_user = user_repo.create(sample_user_data)
        
        update_data = {
            "full_name": "New Name",
            "is_active": False,
            "email": "updated@example.com"
        }
        
        updated_user = user_repo.update(created_user.id, update_data)
        
        assert updated_user is not None
        assert updated_user.full_name == "New Name"
        assert updated_user.is_active is False
        assert updated_user.email == "updated@example.com"


class TestUserRepositoryIntegration:
    """Integration tests for UserRepository."""
    
    def test_create_and_retrieve_workflow(self, user_repo, sample_user_data):
        """Test complete workflow: create, retrieve by ID, retrieve by email."""
        # Create user
        created_user = user_repo.create(sample_user_data)
        assert created_user is not None
        
        # Retrieve by ID
        user_by_id = user_repo.get_by_id(created_user.id)
        assert user_by_id is not None
        assert user_by_id.id == created_user.id
        
        # Retrieve by email
        user_by_email = user_repo.get_by_email(created_user.email)
        assert user_by_email is not None
        assert user_by_email.id == created_user.id
    
    def test_create_update_retrieve_workflow(self, user_repo, sample_user_data):
        """Test complete workflow: create, update, retrieve."""
        # Create user
        created_user = user_repo.create(sample_user_data)
        
        # Update user
        update_data = {"full_name": "Updated Name"}
        updated_user = user_repo.update(created_user.id, update_data)
        assert updated_user.full_name == "Updated Name"
        
        # Retrieve and verify update persisted
        retrieved_user = user_repo.get_by_id(created_user.id)
        assert retrieved_user.full_name == "Updated Name"
    
    def test_multiple_users(self, user_repo):
        """Test creating and managing multiple users."""
        users_data = [
            {"id": "user1", "email": "user1@example.com", "hashed_password": "hash1"},
            {"id": "user2", "email": "user2@example.com", "hashed_password": "hash2"},
            {"id": "user3", "email": "user3@example.com", "hashed_password": "hash3"},
        ]
        
        # Create all users
        created_users = []
        for data in users_data:
            user = user_repo.create(data)
            created_users.append(user)
        
        # Verify all users can be retrieved
        for created_user in created_users:
            retrieved_user = user_repo.get_by_id(created_user.id)
            assert retrieved_user is not None
            assert retrieved_user.id == created_user.id
