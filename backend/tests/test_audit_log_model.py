"""
Tests for AuditLog SQLAlchemy model.

Feature: firebase-to-sqlite-migration
Task: 2.5 Create AuditLog model with all fields and relationships
"""

import pytest
from datetime import datetime
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.database.config import DatabaseConfig
from app.database.models import User, AuditLog


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
    """Create a test user for foreign key relationships."""
    user = User(
        id="user123",
        email="test@example.com",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    return user


class TestAuditLogModel:
    """Unit tests for AuditLog model."""
    
    def test_audit_logs_table_created(self, db_session):
        """Test that audit_logs table is created with correct schema."""
        db_config = DatabaseConfig("sqlite:///:memory:")
        db_config.create_tables()
        
        inspector = inspect(db_config.engine)
        tables = inspector.get_table_names()
        assert 'audit_logs' in tables, "AuditLog table not created"
        
        # Check columns
        columns = inspector.get_columns('audit_logs')
        column_names = [col['name'] for col in columns]
        
        expected_columns = [
            'id', 'user_id', 'action', 'resource_type',
            'resource_id', 'details', 'timestamp'
        ]
        for col in expected_columns:
            assert col in column_names, f"Column '{col}' not found in audit_logs table"
        
        db_config.close()
    
    def test_indexes_exist(self, db_session):
        """Test that required indexes exist on audit_logs table."""
        db_config = DatabaseConfig("sqlite:///:memory:")
        db_config.create_tables()
        
        inspector = inspect(db_config.engine)
        indexes = inspector.get_indexes('audit_logs')
        
        # Check if there are indexes on user_id, action, and timestamp columns
        indexed_columns = set()
        for idx in indexes:
            indexed_columns.update(idx.get('column_names', []))
        
        assert 'user_id' in indexed_columns, "user_id column should have an index"
        assert 'action' in indexed_columns, "action column should have an index"
        assert 'timestamp' in indexed_columns, "timestamp column should have an index"
        
        db_config.close()
    
    def test_create_audit_log_with_user(self, db_session, test_user):
        """Test creating an audit log with a user reference."""
        audit_log = AuditLog(
            user_id=test_user.id,
            action="CREATE_APPLICATION",
            resource_type="application",
            resource_id="app123",
            details='{"company_name": "Test Corp"}'
        )
        
        db_session.add(audit_log)
        db_session.commit()
        
        # Query it back
        retrieved = db_session.query(AuditLog).filter_by(id=audit_log.id).first()
        assert retrieved is not None
        assert retrieved.user_id == test_user.id
        assert retrieved.action == "CREATE_APPLICATION"
        assert retrieved.resource_type == "application"
        assert retrieved.resource_id == "app123"
        assert retrieved.details == '{"company_name": "Test Corp"}'
        assert retrieved.timestamp is not None
    
    def test_create_audit_log_without_user(self, db_session):
        """Test creating an audit log without a user (system action)."""
        audit_log = AuditLog(
            user_id=None,
            action="SYSTEM_CLEANUP",
            resource_type="database",
            resource_id=None,
            details='{"records_deleted": 100}'
        )
        
        db_session.add(audit_log)
        db_session.commit()
        
        # Query it back
        retrieved = db_session.query(AuditLog).filter_by(id=audit_log.id).first()
        assert retrieved is not None
        assert retrieved.user_id is None
        assert retrieved.action == "SYSTEM_CLEANUP"
    
    def test_action_not_null_constraint(self, db_session):
        """Test that action cannot be null."""
        audit_log = AuditLog(
            user_id=None,
            action=None,
            resource_type="test"
        )
        db_session.add(audit_log)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_foreign_key_to_users(self, db_session, test_user):
        """Test foreign key relationship to users table."""
        audit_log = AuditLog(
            user_id=test_user.id,
            action="LOGIN",
            resource_type="user",
            resource_id=test_user.id
        )
        
        db_session.add(audit_log)
        db_session.commit()
        
        # Access user through relationship
        retrieved = db_session.query(AuditLog).filter_by(id=audit_log.id).first()
        assert retrieved.user is not None
        assert retrieved.user.id == test_user.id
        assert retrieved.user.email == test_user.email
    
    def test_foreign_key_set_null_on_delete(self, db_session, test_user):
        """Test that user_id is set to NULL when user is deleted."""
        audit_log = AuditLog(
            user_id=test_user.id,
            action="CREATE_APPLICATION",
            resource_type="application",
            resource_id="app123"
        )
        
        db_session.add(audit_log)
        db_session.commit()
        audit_log_id = audit_log.id
        
        # Delete the user
        db_session.delete(test_user)
        db_session.commit()
        
        # Audit log should still exist but user_id should be NULL
        retrieved = db_session.query(AuditLog).filter_by(id=audit_log_id).first()
        assert retrieved is not None
        assert retrieved.user_id is None
    
    def test_audit_log_default_timestamp(self, db_session):
        """Test that timestamp is set automatically."""
        before = datetime.utcnow()
        
        audit_log = AuditLog(
            user_id=None,
            action="TEST_ACTION"
        )
        
        db_session.add(audit_log)
        db_session.commit()
        
        after = datetime.utcnow()
        
        retrieved = db_session.query(AuditLog).filter_by(id=audit_log.id).first()
        assert retrieved.timestamp is not None
        assert before <= retrieved.timestamp <= after
    
    def test_audit_log_repr(self, db_session, test_user):
        """Test AuditLog __repr__ method."""
        audit_log = AuditLog(
            user_id=test_user.id,
            action="TEST_ACTION"
        )
        
        db_session.add(audit_log)
        db_session.commit()
        
        repr_str = repr(audit_log)
        assert "AuditLog" in repr_str
        assert "TEST_ACTION" in repr_str
        assert test_user.id in repr_str
    
    def test_audit_log_autoincrement_id(self, db_session):
        """Test that id is auto-incremented."""
        log1 = AuditLog(action="ACTION1")
        log2 = AuditLog(action="ACTION2")
        log3 = AuditLog(action="ACTION3")
        
        db_session.add_all([log1, log2, log3])
        db_session.commit()
        
        assert log1.id is not None
        assert log2.id is not None
        assert log3.id is not None
        assert log2.id > log1.id
        assert log3.id > log2.id
    
    def test_query_audit_logs_by_user(self, db_session, test_user):
        """Test querying audit logs by user_id."""
        # Create multiple audit logs for the user
        log1 = AuditLog(user_id=test_user.id, action="ACTION1")
        log2 = AuditLog(user_id=test_user.id, action="ACTION2")
        log3 = AuditLog(user_id=None, action="SYSTEM_ACTION")
        
        db_session.add_all([log1, log2, log3])
        db_session.commit()
        
        # Query logs for the user
        user_logs = db_session.query(AuditLog).filter_by(user_id=test_user.id).all()
        assert len(user_logs) == 2
        assert all(log.user_id == test_user.id for log in user_logs)
    
    def test_query_audit_logs_by_action(self, db_session):
        """Test querying audit logs by action."""
        log1 = AuditLog(action="LOGIN")
        log2 = AuditLog(action="LOGIN")
        log3 = AuditLog(action="LOGOUT")
        
        db_session.add_all([log1, log2, log3])
        db_session.commit()
        
        # Query logs by action
        login_logs = db_session.query(AuditLog).filter_by(action="LOGIN").all()
        assert len(login_logs) == 2
    
    def test_query_audit_logs_by_timestamp_range(self, db_session):
        """Test querying audit logs by timestamp range."""
        from datetime import timedelta
        
        now = datetime.utcnow()
        
        log1 = AuditLog(action="ACTION1")
        db_session.add(log1)
        db_session.commit()
        
        # Query logs within time range
        start_time = now - timedelta(minutes=1)
        end_time = now + timedelta(minutes=1)
        
        logs = db_session.query(AuditLog).filter(
            AuditLog.timestamp >= start_time,
            AuditLog.timestamp <= end_time
        ).all()
        
        assert len(logs) >= 1
        assert log1 in logs
    
    def test_user_relationship_back_populates(self, db_session, test_user):
        """Test that User.audit_logs relationship works."""
        log1 = AuditLog(user_id=test_user.id, action="ACTION1")
        log2 = AuditLog(user_id=test_user.id, action="ACTION2")
        
        db_session.add_all([log1, log2])
        db_session.commit()
        
        # Access audit logs through user
        db_session.refresh(test_user)
        assert len(test_user.audit_logs) == 2
        assert all(log.user_id == test_user.id for log in test_user.audit_logs)
