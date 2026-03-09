"""
Tests for Application SQLAlchemy model.

Feature: firebase-to-sqlite-migration
Task: 2.2 Create Application model with all fields and relationships
"""

import pytest
from datetime import datetime
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.database.config import DatabaseConfig
from app.database.models import User, Application


@pytest.fixture
def db_session():
    """Create an in-memory database session for testing."""
    db_config = DatabaseConfig("sqlite:///:memory:")
    db_config.create_tables()
    session = db_config.get_session()
    yield session
    session.close()
    db_config.close()


@pytest.fixture
def test_user(db_session):
    """Create a test user for application tests."""
    user = User(
        id="user123",
        email="test@example.com",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    return user


class TestApplicationModel:
    """Unit tests for Application model."""
    
    def test_application_table_created(self, db_session):
        """Test that applications table is created with correct schema."""
        db_config = DatabaseConfig("sqlite:///:memory:")
        db_config.create_tables()
        
        inspector = inspect(db_config.engine)
        tables = inspector.get_table_names()
        assert 'applications' in tables, "Applications table not created"
        
        # Check columns
        columns = inspector.get_columns('applications')
        column_names = [col['name'] for col in columns]
        
        expected_columns = [
            'id', 'user_id', 'company_name', 'status', 'credit_amount',
            'application_data', 'created_at', 'updated_at'
        ]
        for col in expected_columns:
            assert col in column_names, f"Column '{col}' not found in applications table"
        
        db_config.close()
    
    def test_application_indexes_exist(self, db_session):
        """Test that required indexes exist on applications table."""
        db_config = DatabaseConfig("sqlite:///:memory:")
        db_config.create_tables()
        
        inspector = inspect(db_config.engine)
        indexes = inspector.get_indexes('applications')
        
        # Check for indexes on user_id, status, created_at
        indexed_columns = set()
        for idx in indexes:
            indexed_columns.update(idx.get('column_names', []))
        
        assert 'user_id' in indexed_columns, "user_id should have an index"
        assert 'status' in indexed_columns, "status should have an index"
        assert 'created_at' in indexed_columns, "created_at should have an index"
        
        db_config.close()
    
    def test_foreign_key_to_users(self, db_session):
        """Test that foreign key relationship to users table exists."""
        db_config = DatabaseConfig("sqlite:///:memory:")
        db_config.create_tables()
        
        inspector = inspect(db_config.engine)
        foreign_keys = inspector.get_foreign_keys('applications')
        
        # Check for foreign key to users table
        user_fk_exists = any(
            fk['referred_table'] == 'users' and 'user_id' in fk['constrained_columns']
            for fk in foreign_keys
        )
        assert user_fk_exists, "Foreign key to users table should exist"
        
        db_config.close()
    
    def test_create_application(self, db_session, test_user):
        """Test creating an application with all fields."""
        application = Application(
            id="app123",
            user_id=test_user.id,
            company_name="Test Corp",
            status="pending",
            credit_amount=1000000.0,
            application_data='{"loan_purpose": "expansion"}'
        )
        
        db_session.add(application)
        db_session.commit()
        
        # Query it back
        retrieved = db_session.query(Application).filter_by(id="app123").first()
        assert retrieved is not None
        assert retrieved.user_id == test_user.id
        assert retrieved.company_name == "Test Corp"
        assert retrieved.status == "pending"
        assert retrieved.credit_amount == 1000000.0
        assert retrieved.application_data == '{"loan_purpose": "expansion"}'
        assert retrieved.created_at is not None
        assert retrieved.updated_at is not None
    
    def test_user_id_not_null_constraint(self, db_session):
        """Test that user_id cannot be null."""
        application = Application(
            id="app123",
            user_id=None,
            company_name="Test Corp",
            status="pending"
        )
        db_session.add(application)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_company_name_not_null_constraint(self, db_session, test_user):
        """Test that company_name cannot be null."""
        application = Application(
            id="app123",
            user_id=test_user.id,
            company_name=None,
            status="pending"
        )
        db_session.add(application)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_status_not_null_constraint(self, db_session, test_user):
        """Test that status cannot be null."""
        application = Application(
            id="app123",
            user_id=test_user.id,
            company_name="Test Corp",
            status=None
        )
        db_session.add(application)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_application_user_relationship(self, db_session, test_user):
        """Test the relationship between Application and User."""
        application = Application(
            id="app123",
            user_id=test_user.id,
            company_name="Test Corp",
            status="pending"
        )
        
        db_session.add(application)
        db_session.commit()
        
        # Access user through relationship
        retrieved_app = db_session.query(Application).filter_by(id="app123").first()
        assert retrieved_app.user is not None
        assert retrieved_app.user.id == test_user.id
        assert retrieved_app.user.email == test_user.email
    
    def test_user_applications_relationship(self, db_session, test_user):
        """Test accessing applications through user relationship."""
        app1 = Application(
            id="app1",
            user_id=test_user.id,
            company_name="Corp 1",
            status="pending"
        )
        app2 = Application(
            id="app2",
            user_id=test_user.id,
            company_name="Corp 2",
            status="approved"
        )
        
        db_session.add_all([app1, app2])
        db_session.commit()
        
        # Access applications through user
        retrieved_user = db_session.query(User).filter_by(id=test_user.id).first()
        assert len(retrieved_user.applications) == 2
        app_ids = [app.id for app in retrieved_user.applications]
        assert "app1" in app_ids
        assert "app2" in app_ids
    
    def test_application_repr(self, db_session, test_user):
        """Test Application __repr__ method."""
        application = Application(
            id="app123",
            user_id=test_user.id,
            company_name="Test Corp",
            status="pending"
        )
        
        repr_str = repr(application)
        assert "Application" in repr_str
        assert "app123" in repr_str
        assert "Test Corp" in repr_str
        assert "pending" in repr_str
    
    def test_application_update(self, db_session, test_user):
        """Test updating application fields."""
        application = Application(
            id="app123",
            user_id=test_user.id,
            company_name="Test Corp",
            status="pending",
            credit_amount=1000000.0
        )
        
        db_session.add(application)
        db_session.commit()
        
        # Update fields
        application.status = "approved"
        application.credit_amount = 1500000.0
        db_session.commit()
        
        # Verify update
        retrieved = db_session.query(Application).filter_by(id="app123").first()
        assert retrieved.status == "approved"
        assert retrieved.credit_amount == 1500000.0
    
    def test_application_delete(self, db_session, test_user):
        """Test deleting an application."""
        application = Application(
            id="app123",
            user_id=test_user.id,
            company_name="Test Corp",
            status="pending"
        )
        
        db_session.add(application)
        db_session.commit()
        
        # Delete application
        db_session.delete(application)
        db_session.commit()
        
        # Verify deletion
        retrieved = db_session.query(Application).filter_by(id="app123").first()
        assert retrieved is None
    
    def test_optional_fields(self, db_session, test_user):
        """Test that optional fields (credit_amount, application_data) can be null."""
        application = Application(
            id="app123",
            user_id=test_user.id,
            company_name="Test Corp",
            status="pending"
            # credit_amount and application_data are optional
        )
        
        db_session.add(application)
        db_session.commit()
        
        retrieved = db_session.query(Application).filter_by(id="app123").first()
        assert retrieved is not None
        assert retrieved.credit_amount is None
        assert retrieved.application_data is None
