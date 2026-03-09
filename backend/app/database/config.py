"""
Database configuration and session management for SQLite3.

This module provides the core database infrastructure including:
- SQLAlchemy engine configuration
- Session management
- Base model class for all ORM models
- Database initialization utilities
"""

from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool


# Create the declarative base class for all models
Base = declarative_base()


class DatabaseConfig:
    """
    SQLite database configuration and session management.
    
    This class handles:
    - Database engine creation with SQLite-specific settings
    - Session factory configuration
    - Table creation and initialization
    - Foreign key constraint enforcement
    """
    
    def __init__(self, database_url: str, echo: bool = False):
        """
        Initialize database configuration.
        
        Args:
            database_url: SQLite database URL (e.g., "sqlite:///./intellicredit.db")
            echo: If True, log all SQL statements (useful for debugging)
        """
        self.database_url = database_url
        
        # Configure engine with SQLite-specific settings
        connect_args = {"check_same_thread": False}  # Allow multi-threading
        
        # Use StaticPool for in-memory databases to maintain single connection
        if database_url == "sqlite:///:memory:":
            self.engine = create_engine(
                database_url,
                connect_args=connect_args,
                poolclass=StaticPool,
                echo=echo
            )
        else:
            self.engine = create_engine(
                database_url,
                connect_args=connect_args,
                pool_pre_ping=True,  # Verify connections before using
                echo=echo
            )
        
        # Enable foreign key constraints for SQLite
        self._enable_foreign_keys()
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def _enable_foreign_keys(self):
        """
        Enable foreign key constraint enforcement for SQLite.
        
        SQLite has foreign keys disabled by default. This method ensures
        they are enabled for every connection.
        """
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    
    def create_tables(self):
        """
        Create all tables defined in SQLAlchemy models.
        
        This method creates tables for all models that inherit from Base.
        It's idempotent - safe to call multiple times.
        """
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """
        Drop all tables defined in SQLAlchemy models.
        
        WARNING: This will delete all data. Use only for testing or migrations.
        """
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            A new SQLAlchemy Session instance
            
        Note:
            Caller is responsible for closing the session.
            Consider using get_db() dependency for FastAPI endpoints.
        """
        return self.SessionLocal()
    
    def close(self):
        """
        Close the database engine and all connections.
        
        Call this when shutting down the application.
        """
        self.engine.dispose()


# Global database configuration instance
# This will be initialized in main.py with actual configuration
_db_config: DatabaseConfig = None


def init_database(database_url: str, echo: bool = False) -> DatabaseConfig:
    """
    Initialize the global database configuration.
    
    Args:
        database_url: SQLite database URL
        echo: If True, log all SQL statements
        
    Returns:
        Initialized DatabaseConfig instance
    """
    global _db_config
    _db_config = DatabaseConfig(database_url, echo)
    _db_config.create_tables()
    return _db_config


def get_db_config() -> DatabaseConfig:
    """
    Get the global database configuration instance.
    
    Returns:
        The initialized DatabaseConfig instance
        
    Raises:
        RuntimeError: If database has not been initialized
    """
    if _db_config is None:
        raise RuntimeError(
            "Database not initialized. Call init_database() first."
        )
    return _db_config


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for getting database sessions.
    
    This is a generator function that yields a database session
    and ensures it's closed after use.
    
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    
    Yields:
        A database session
    """
    db_config = get_db_config()
    session = db_config.get_session()
    try:
        yield session
    finally:
        session.close()
