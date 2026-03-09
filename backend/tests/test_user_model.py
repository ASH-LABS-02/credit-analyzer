"""
Tests for User SQLAlchemy model.

Feature: firebase-to-sqlite-migration
Task: 2.1 Create User model with all fields and relationships
"""

import pytest
from datetime import datetime
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.database.config import DatabaseConfig
from app.database.models import User


@pytest.fixture
def db_session():
    """Create an in-memory database session for testing."""
    db_config = DatabaseConfig("sqlite:///:memory:")
    db_config.create_tables()
    session = db_config.get_session()
    yield session
    session.close()
    db_config.close()


class TestUserModel:
    """Unit tests for User model."""
    
    def test_user_table_created(self, db_session):
        """Test that users table is created with correct schema."""
        db_config = DatabaseConfig("sqlite:///:memory:")
        db_config.create_tables()
        
        inspector = inspect(db_config.engine)
        tables = inspector.get_table_names()
        assert 'users' in tables, "Users table not created"
        
        # Check columns
        columns = inspector.get_columns('users')
        column_names = [col['name'] for col in columns]
        
        expected_columns = [
            'id', 'email', 'hashed_password', 'full_name',
            'is_active', 'created_at', 'updated_at'
        ]
        for col in expected_columns:
            assert col in column_names, f"Column '{col}' not found in users table"
        
        db_config.close()
    
    def test_email_index_exists(self, db_session):
        """Test that email column has an index."""
        db_config = DatabaseConfig("sqlite:///:memory:")
        db_config.create_tables()
        
        inspector = inspect(db_config.engine)
        indexes = inspector.get_indexes('users')
        
        # Check if there's an index on email column
        email_indexed = any(
            'email' in idx.get('column_names', [])
            for idx in indexes
        )
        assert email_indexed, "Email column should have an index"
        
        db_config.close()
    
    def test_create_user(self, db_session):
        """Test creating a user with all fields."""
        user = User(
            id="user123",
            email="test@example.com",
            hashed_password="hashed_password_here",
            full_name="Test User",
            is_active=True
        )
        
        db_session.add(user)
        db_session.commit()
        
        # Query it back
        retrieved = db_session.query(User).filter_by(id="user123").first()
        assert retrieved is not None
        assert retrieved.email == "test@example.com"
        assert retrieved.hashed_password == "hashed_password_here"
        assert retrieved.full_name == "Test User"
        assert retrieved.is_active is True
        assert retrieved.created_at is not None
        assert retrieved.updated_at is not None
    
    def test_email_unique_constraint(self, db_session):
        """Test that email must be unique."""
        user1 = User(
            id="user1",
            email="duplicate@example.com",
            hashed_password="hash1"
        )
        db_session.add(user1)
        db_session.commit()
        
        # Try to create another user with same email
        user2 = User(
            id="user2",
            email="duplicate@example.com",
            hashed_password="hash2"
        )
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_email_not_null_constraint(self, db_session):
        """Test that email cannot be null."""
        user = User(
            id="user123",
            email=None,
            hashed_password="hash"
        )
        db_session.add(user)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_hashed_password_not_null_constraint(self, db_session):
        """Test that hashed_password cannot be null."""
        user = User(
            id="user123",
            email="test@example.com",
            hashed_password=None
        )
        db_session.add(user)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_default_values(self, db_session):
        """Test that default values are set correctly."""
        user = User(
            id="user123",
            email="test@example.com",
            hashed_password="hash"
        )
        
        db_session.add(user)
        db_session.commit()
        
        retrieved = db_session.query(User).filter_by(id="user123").first()
        assert retrieved.is_active is True  # Default value
        assert retrieved.created_at is not None
        assert retrieved.updated_at is not None
    
    def test_user_repr(self, db_session):
        """Test User __repr__ method."""
        user = User(
            id="user123",
            email="test@example.com",
            hashed_password="hash"
        )
        
        repr_str = repr(user)
        assert "User" in repr_str
        assert "user123" in repr_str
        assert "test@example.com" in repr_str
    
    def test_user_update(self, db_session):
        """Test updating user fields."""
        user = User(
            id="user123",
            email="test@example.com",
            hashed_password="hash",
            full_name="Original Name"
        )
        
        db_session.add(user)
        db_session.commit()
        
        # Update fields
        user.full_name = "Updated Name"
        user.is_active = False
        db_session.commit()
        
        # Verify update
        retrieved = db_session.query(User).filter_by(id="user123").first()
        assert retrieved.full_name == "Updated Name"
        assert retrieved.is_active is False
    
    def test_user_delete(self, db_session):
        """Test deleting a user."""
        user = User(
            id="user123",
            email="test@example.com",
            hashed_password="hash"
        )
        
        db_session.add(user)
        db_session.commit()
        
        # Delete user
        db_session.delete(user)
        db_session.commit()
        
        # Verify deletion
        retrieved = db_session.query(User).filter_by(id="user123").first()
        assert retrieved is None
