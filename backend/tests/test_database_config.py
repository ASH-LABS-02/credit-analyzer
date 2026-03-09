"""
Tests for database configuration and initialization.

Feature: firebase-to-sqlite-migration
"""

import pytest
from hypothesis import given, strategies as st
from sqlalchemy import Column, String, Integer, inspect
from sqlalchemy.exc import IntegrityError

from app.database.config import (
    DatabaseConfig,
    Base,
    init_database,
    get_db_config,
    get_db
)


# Test model for database initialization tests
class TestModel(Base):
    """Simple test model for verifying table creation."""
    __tablename__ = 'test_table'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


@pytest.fixture
def in_memory_db():
    """Create an in-memory database for testing."""
    db_config = DatabaseConfig("sqlite:///:memory:")
    db_config.create_tables()
    yield db_config
    db_config.close()


@pytest.fixture
def clean_global_db():
    """Clean up global database configuration after test."""
    yield
    # Reset global state
    import app.database.config as config_module
    config_module._db_config = None


class TestDatabaseConfig:
    """Unit tests for DatabaseConfig class."""
    
    def test_database_config_initialization(self):
        """Test that DatabaseConfig initializes correctly."""
        db_config = DatabaseConfig("sqlite:///:memory:")
        assert db_config.database_url == "sqlite:///:memory:"
        assert db_config.engine is not None
        assert db_config.SessionLocal is not None
        db_config.close()
    
    def test_create_tables(self, in_memory_db):
        """Test that create_tables creates all defined tables."""
        # Verify the test table was created
        inspector = inspect(in_memory_db.engine)
        tables = inspector.get_table_names()
        assert 'test_table' in tables
    
    def test_get_session(self, in_memory_db):
        """Test that get_session returns a valid session."""
        session = in_memory_db.get_session()
        assert session is not None
        session.close()
    
    def test_drop_tables(self, in_memory_db):
        """Test that drop_tables removes all tables."""
        # First verify table exists
        inspector = inspect(in_memory_db.engine)
        tables_before = inspector.get_table_names()
        assert len(tables_before) > 0
        
        # Drop tables
        in_memory_db.drop_tables()
        
        # Verify tables are gone
        inspector = inspect(in_memory_db.engine)
        tables_after = inspector.get_table_names()
        assert len(tables_after) == 0


class TestDatabaseInitialization:
    """Unit tests for global database initialization."""
    
    def test_init_database(self, clean_global_db):
        """Test that init_database initializes global config."""
        db_config = init_database("sqlite:///:memory:")
        assert db_config is not None
        assert db_config.database_url == "sqlite:///:memory:"
        db_config.close()
    
    def test_get_db_config_before_init(self, clean_global_db):
        """Test that get_db_config raises error before initialization."""
        with pytest.raises(RuntimeError, match="Database not initialized"):
            get_db_config()
    
    def test_get_db_config_after_init(self, clean_global_db):
        """Test that get_db_config returns config after initialization."""
        init_database("sqlite:///:memory:")
        db_config = get_db_config()
        assert db_config is not None
        db_config.close()
    
    def test_get_db_dependency(self, clean_global_db):
        """Test that get_db dependency yields a session."""
        init_database("sqlite:///:memory:")
        
        # Use the generator
        gen = get_db()
        session = next(gen)
        assert session is not None
        
        # Clean up
        try:
            next(gen)
        except StopIteration:
            pass  # Expected
        
        get_db_config().close()


class TestForeignKeyEnforcement:
    """Unit tests for foreign key constraint enforcement."""
    
    def test_foreign_keys_enabled(self, in_memory_db):
        """Test that foreign key constraints are enforced."""
        # Create tables with foreign key relationship
        from sqlalchemy import ForeignKey
        
        class Parent(Base):
            __tablename__ = 'parent'
            id = Column(Integer, primary_key=True)
        
        class Child(Base):
            __tablename__ = 'child'
            id = Column(Integer, primary_key=True)
            parent_id = Column(Integer, ForeignKey('parent.id'), nullable=False)
        
        # Create tables
        Base.metadata.create_all(bind=in_memory_db.engine)
        
        # Try to insert child without parent - should fail
        session = in_memory_db.get_session()
        try:
            child = Child(id=1, parent_id=999)  # Non-existent parent
            session.add(child)
            session.commit()
            pytest.fail("Expected IntegrityError for foreign key violation")
        except IntegrityError:
            session.rollback()
            # Expected - foreign key constraint enforced
        finally:
            session.close()


# Property-Based Tests

@given(
    st.text(min_size=1, max_size=100),
    st.integers(min_value=1, max_value=10),
    st.booleans()
)
def test_property_database_initialization_creates_tables(table_name, num_columns, use_foreign_key):
    """
    Feature: firebase-to-sqlite-migration, Property: Database initialization creates tables
    **Validates: Requirements 1.4**
    
    For any valid table definition with varying numbers of columns and relationships,
    database initialization should create the table and make it queryable.
    
    This property verifies that:
    1. Tables are created when database is initialized
    2. Created tables have the correct schema
    3. Tables are immediately usable for CRUD operations
    4. Foreign key relationships are properly established
    """
    # Sanitize table name to be SQL-safe
    safe_table_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in table_name)
    if not safe_table_name or safe_table_name[0].isdigit():
        safe_table_name = 'table_' + safe_table_name
    
    # Initialize database
    db_config = DatabaseConfig("sqlite:///:memory:")
    
    try:
        # Create parent table if testing foreign keys
        parent_table_name = None
        ParentModel = None
        if use_foreign_key:
            from sqlalchemy import ForeignKey
            parent_table_name = f"{safe_table_name}_parent"
            
            class ParentModel(Base):
                __tablename__ = parent_table_name
                __table_args__ = {'extend_existing': True}
                id = Column(Integer, primary_key=True)
                name = Column(String)
        
        # Create a dynamic model with variable columns
        columns_dict = {
            '__tablename__': safe_table_name,
            '__table_args__': {'extend_existing': True},
            'id': Column(Integer, primary_key=True)
        }
        
        # Add variable number of columns
        for i in range(num_columns):
            columns_dict[f'col_{i}'] = Column(String)
        
        # Add foreign key if requested
        if use_foreign_key and parent_table_name:
            from sqlalchemy import ForeignKey
            columns_dict['parent_id'] = Column(Integer, ForeignKey(f'{parent_table_name}.id'))
        
        DynamicModel = type('DynamicModel', (Base,), columns_dict)
        
        # Initialize tables
        db_config.create_tables()
        
        # Verify parent table was created if needed
        inspector = inspect(db_config.engine)
        tables = inspector.get_table_names()
        
        if use_foreign_key and parent_table_name:
            assert parent_table_name in tables, f"Parent table {parent_table_name} not created"
        
        # Verify main table was created
        assert safe_table_name in tables, f"Table {safe_table_name} not created"
        
        # Verify table schema has correct columns
        columns = inspector.get_columns(safe_table_name)
        column_names = [col['name'] for col in columns]
        assert 'id' in column_names, "Primary key column 'id' not found"
        for i in range(num_columns):
            assert f'col_{i}' in column_names, f"Column 'col_{i}' not found"
        
        # Verify table is usable for CRUD operations
        session = db_config.get_session()
        try:
            # If using foreign key, create parent record first
            parent_id = None
            if use_foreign_key and ParentModel:
                parent = ParentModel(id=1, name="parent")
                session.add(parent)
                session.commit()
                parent_id = 1
            
            # Insert a record
            record_data = {'id': 1}
            for i in range(num_columns):
                record_data[f'col_{i}'] = f'value_{i}'
            if use_foreign_key and parent_id:
                record_data['parent_id'] = parent_id
            
            record = DynamicModel(**record_data)
            session.add(record)
            session.commit()
            
            # Query it back (READ)
            result = session.query(DynamicModel).filter_by(id=1).first()
            assert result is not None, "Failed to query inserted record"
            for i in range(num_columns):
                assert getattr(result, f'col_{i}') == f'value_{i}', f"Column col_{i} value mismatch"
            
            # Update the record (UPDATE)
            result.col_0 = 'updated_value' if num_columns > 0 else None
            session.commit()
            
            # Verify update
            updated = session.query(DynamicModel).filter_by(id=1).first()
            if num_columns > 0:
                assert updated.col_0 == 'updated_value', "Update operation failed"
            
            # Delete the record (DELETE)
            session.delete(updated)
            session.commit()
            
            # Verify deletion
            deleted = session.query(DynamicModel).filter_by(id=1).first()
            assert deleted is None, "Delete operation failed"
            
        finally:
            session.close()
    finally:
        db_config.close()
        # Clean up the dynamic models from Base metadata
        if safe_table_name in Base.metadata.tables:
            Base.metadata.remove(Base.metadata.tables[safe_table_name])
        if parent_table_name and parent_table_name in Base.metadata.tables:
            Base.metadata.remove(Base.metadata.tables[parent_table_name])
