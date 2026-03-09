"""
Application Startup Configuration and Validation

This module handles application startup tasks including:
- Configuration validation
- Database initialization
- File storage setup

Requirements: 6.5
"""
import os
import logging
from pathlib import Path
from typing import List, Tuple

from app.core.config import settings
from app.database import init_database

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid"""
    pass


def validate_configuration() -> None:
    """
    Validate all required configuration parameters at startup.
    
    Validates:
    - DATABASE_URL: SQLite database file path
    - FILE_STORAGE_ROOT: Local file storage directory path
    - JWT_SECRET_KEY: JWT secret key for token signing
    - OPENAI_API_KEY: OpenAI API key for AI services
    
    Raises:
        ConfigurationError: If any required configuration is missing or invalid
    
    Requirements: 6.5
    """
    errors: List[str] = []
    warnings: List[str] = []
    
    # Validate DATABASE_URL
    if not settings.DATABASE_URL:
        errors.append("DATABASE_URL is not configured")
    elif not settings.DATABASE_URL.startswith("sqlite:///"):
        errors.append(f"DATABASE_URL must be a SQLite URL (sqlite:///path), got: {settings.DATABASE_URL}")
    
    # Validate FILE_STORAGE_ROOT
    if not settings.FILE_STORAGE_ROOT:
        errors.append("FILE_STORAGE_ROOT is not configured")
    
    # Validate JWT_SECRET_KEY
    if not settings.JWT_SECRET_KEY:
        errors.append("JWT_SECRET_KEY is not configured")
    elif settings.JWT_SECRET_KEY == "change-this-to-a-secure-random-key-in-production":
        warnings.append(
            "JWT_SECRET_KEY is using the default value. "
            "Please change this to a secure random key in production!"
        )
    elif len(settings.JWT_SECRET_KEY) < 32:
        warnings.append(
            f"JWT_SECRET_KEY is too short ({len(settings.JWT_SECRET_KEY)} characters). "
            "Recommended minimum is 32 characters for security."
        )
    
    # Validate OPENAI_API_KEY
    if not settings.OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is not configured")
    
    # Validate JWT_ALGORITHM
    if settings.JWT_ALGORITHM not in ["HS256", "HS384", "HS512"]:
        errors.append(
            f"JWT_ALGORITHM must be one of HS256, HS384, HS512, got: {settings.JWT_ALGORITHM}"
        )
    
    # Validate JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    if settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
        errors.append(
            f"JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be positive, got: {settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES}"
        )
    
    # Log warnings
    for warning in warnings:
        logger.warning(f"Configuration warning: {warning}")
    
    # Raise error if any critical configuration is missing
    if errors:
        error_message = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
        logger.error(error_message)
        raise ConfigurationError(error_message)
    
    logger.info("Configuration validation passed")


def initialize_database() -> None:
    """
    Initialize the SQLite database.
    
    Creates the database file and all tables if they don't exist.
    
    Raises:
        Exception: If database initialization fails
    
    Requirements: 1.4
    """
    try:
        logger.info(f"Initializing database: {settings.DATABASE_URL}")
        init_database(settings.DATABASE_URL)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def initialize_file_storage() -> None:
    """
    Initialize the file storage directory.
    
    Creates the storage directory if it doesn't exist and validates write permissions.
    
    Raises:
        ConfigurationError: If storage directory cannot be created or is not writable
    
    Requirements: 3.1
    """
    try:
        storage_path = Path(settings.FILE_STORAGE_ROOT)
        
        # Create directory if it doesn't exist
        storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"File storage directory initialized: {storage_path.absolute()}")
        
        # Verify write permissions by creating a test file
        test_file = storage_path / ".write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            raise ConfigurationError(
                f"File storage directory is not writable: {storage_path.absolute()}"
            ) from e
        
        logger.info("File storage directory is writable")
        
    except ConfigurationError:
        raise
    except Exception as e:
        logger.error(f"Failed to initialize file storage: {e}")
        raise ConfigurationError(f"Failed to initialize file storage: {e}") from e


def startup() -> None:
    """
    Execute all startup tasks.
    
    This function should be called when the application starts to:
    1. Validate configuration
    2. Initialize database
    3. Initialize file storage
    
    Raises:
        ConfigurationError: If configuration validation fails
        Exception: If any initialization step fails
    
    Requirements: 6.5, 1.4, 3.1
    """
    logger.info("Starting application initialization...")
    
    # Step 1: Validate configuration
    validate_configuration()
    
    # Step 2: Initialize database
    initialize_database()
    
    # Step 3: Initialize file storage
    initialize_file_storage()
    
    logger.info("Application initialization completed successfully")
