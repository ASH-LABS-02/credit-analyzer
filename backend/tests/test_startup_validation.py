"""
Unit tests for application startup and configuration validation.

Tests configuration validation, database initialization, and file storage setup.

Requirements: 6.5, 1.4, 3.1
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.core.startup import (
    validate_configuration,
    initialize_database,
    initialize_file_storage,
    startup,
    ConfigurationError
)


# Mark all tests in this module to not use the firebase mock
pytestmark = pytest.mark.usefixtures()


class TestConfigurationValidation:
    """Unit tests for configuration validation."""
    
    def test_validate_configuration_with_valid_config(self):
        """Test that validation passes with valid configuration."""
        with patch('app.core.startup.settings') as mock_settings:
            mock_settings.DATABASE_URL = "sqlite:///./test.db"
            mock_settings.FILE_STORAGE_ROOT = "./storage"
            mock_settings.JWT_SECRET_KEY = "a" * 32  # 32 character key
            mock_settings.OPENAI_API_KEY = "sk-test-key"
            mock_settings.JWT_ALGORITHM = "HS256"
            mock_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
            
            # Should not raise any exception
            validate_configuration()
    
    def test_validate_configuration_missing_database_url(self):
        """Test that validation fails when DATABASE_URL is missing."""
        with patch('app.core.startup.settings') as mock_settings:
            mock_settings.DATABASE_URL = ""
            mock_settings.FILE_STORAGE_ROOT = "./storage"
            mock_settings.JWT_SECRET_KEY = "a" * 32
            mock_settings.OPENAI_API_KEY = "sk-test-key"
            mock_settings.JWT_ALGORITHM = "HS256"
            mock_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
            
            with pytest.raises(ConfigurationError) as exc_info:
                validate_configuration()
            
            assert "DATABASE_URL is not configured" in str(exc_info.value)
    
    def test_validate_configuration_invalid_database_url(self):
        """Test that validation fails when DATABASE_URL is not a SQLite URL."""
        with patch('app.core.startup.settings') as mock_settings:
            mock_settings.DATABASE_URL = "postgresql://localhost/test"
            mock_settings.FILE_STORAGE_ROOT = "./storage"
            mock_settings.JWT_SECRET_KEY = "a" * 32
            mock_settings.OPENAI_API_KEY = "sk-test-key"
            mock_settings.JWT_ALGORITHM = "HS256"
            mock_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
            
            with pytest.raises(ConfigurationError) as exc_info:
                validate_configuration()
            
            assert "DATABASE_URL must be a SQLite URL" in str(exc_info.value)
    
    def test_validate_configuration_missing_file_storage_root(self):
        """Test that validation fails when FILE_STORAGE_ROOT is missing."""
        with patch('app.core.startup.settings') as mock_settings:
            mock_settings.DATABASE_URL = "sqlite:///./test.db"
            mock_settings.FILE_STORAGE_ROOT = ""
            mock_settings.JWT_SECRET_KEY = "a" * 32
            mock_settings.OPENAI_API_KEY = "sk-test-key"
            mock_settings.JWT_ALGORITHM = "HS256"
            mock_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
            
            with pytest.raises(ConfigurationError) as exc_info:
                validate_configuration()
            
            assert "FILE_STORAGE_ROOT is not configured" in str(exc_info.value)
    
    def test_validate_configuration_missing_jwt_secret_key(self):
        """Test that validation fails when JWT_SECRET_KEY is missing."""
        with patch('app.core.startup.settings') as mock_settings:
            mock_settings.DATABASE_URL = "sqlite:///./test.db"
            mock_settings.FILE_STORAGE_ROOT = "./storage"
            mock_settings.JWT_SECRET_KEY = ""
            mock_settings.OPENAI_API_KEY = "sk-test-key"
            mock_settings.JWT_ALGORITHM = "HS256"
            mock_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
            
            with pytest.raises(ConfigurationError) as exc_info:
                validate_configuration()
            
            assert "JWT_SECRET_KEY is not configured" in str(exc_info.value)
    
    def test_validate_configuration_missing_openai_api_key(self):
        """Test that validation fails when OPENAI_API_KEY is missing."""
        with patch('app.core.startup.settings') as mock_settings:
            mock_settings.DATABASE_URL = "sqlite:///./test.db"
            mock_settings.FILE_STORAGE_ROOT = "./storage"
            mock_settings.JWT_SECRET_KEY = "a" * 32
            mock_settings.OPENAI_API_KEY = ""
            mock_settings.JWT_ALGORITHM = "HS256"
            mock_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
            
            with pytest.raises(ConfigurationError) as exc_info:
                validate_configuration()
            
            assert "OPENAI_API_KEY is not configured" in str(exc_info.value)
    
    def test_validate_configuration_invalid_jwt_algorithm(self):
        """Test that validation fails with invalid JWT algorithm."""
        with patch('app.core.startup.settings') as mock_settings:
            mock_settings.DATABASE_URL = "sqlite:///./test.db"
            mock_settings.FILE_STORAGE_ROOT = "./storage"
            mock_settings.JWT_SECRET_KEY = "a" * 32
            mock_settings.OPENAI_API_KEY = "sk-test-key"
            mock_settings.JWT_ALGORITHM = "RS256"  # Invalid for our use case
            mock_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
            
            with pytest.raises(ConfigurationError) as exc_info:
                validate_configuration()
            
            assert "JWT_ALGORITHM must be one of HS256, HS384, HS512" in str(exc_info.value)
    
    def test_validate_configuration_invalid_token_expiration(self):
        """Test that validation fails with invalid token expiration."""
        with patch('app.core.startup.settings') as mock_settings:
            mock_settings.DATABASE_URL = "sqlite:///./test.db"
            mock_settings.FILE_STORAGE_ROOT = "./storage"
            mock_settings.JWT_SECRET_KEY = "a" * 32
            mock_settings.OPENAI_API_KEY = "sk-test-key"
            mock_settings.JWT_ALGORITHM = "HS256"
            mock_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 0
            
            with pytest.raises(ConfigurationError) as exc_info:
                validate_configuration()
            
            assert "JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be positive" in str(exc_info.value)
    
    def test_validate_configuration_warns_on_default_jwt_secret(self, caplog):
        """Test that validation warns when using default JWT secret."""
        with patch('app.core.startup.settings') as mock_settings:
            mock_settings.DATABASE_URL = "sqlite:///./test.db"
            mock_settings.FILE_STORAGE_ROOT = "./storage"
            mock_settings.JWT_SECRET_KEY = "change-this-to-a-secure-random-key-in-production"
            mock_settings.OPENAI_API_KEY = "sk-test-key"
            mock_settings.JWT_ALGORITHM = "HS256"
            mock_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
            
            validate_configuration()
            
            # Check that warning was logged
            assert any("default value" in record.message for record in caplog.records)
    
    def test_validate_configuration_warns_on_short_jwt_secret(self, caplog):
        """Test that validation warns when JWT secret is too short."""
        with patch('app.core.startup.settings') as mock_settings:
            mock_settings.DATABASE_URL = "sqlite:///./test.db"
            mock_settings.FILE_STORAGE_ROOT = "./storage"
            mock_settings.JWT_SECRET_KEY = "short"  # Only 5 characters
            mock_settings.OPENAI_API_KEY = "sk-test-key"
            mock_settings.JWT_ALGORITHM = "HS256"
            mock_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
            
            validate_configuration()
            
            # Check that warning was logged
            assert any("too short" in record.message for record in caplog.records)
    
    def test_validate_configuration_multiple_errors(self):
        """Test that validation reports multiple errors at once."""
        with patch('app.core.startup.settings') as mock_settings:
            mock_settings.DATABASE_URL = ""
            mock_settings.FILE_STORAGE_ROOT = ""
            mock_settings.JWT_SECRET_KEY = ""
            mock_settings.OPENAI_API_KEY = ""
            mock_settings.JWT_ALGORITHM = "HS256"
            mock_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
            
            with pytest.raises(ConfigurationError) as exc_info:
                validate_configuration()
            
            error_message = str(exc_info.value)
            assert "DATABASE_URL is not configured" in error_message
            assert "FILE_STORAGE_ROOT is not configured" in error_message
            assert "JWT_SECRET_KEY is not configured" in error_message
            assert "OPENAI_API_KEY is not configured" in error_message


class TestDatabaseInitialization:
    """Unit tests for database initialization."""
    
    def test_initialize_database_success(self):
        """Test successful database initialization."""
        with patch('app.core.startup.init_database') as mock_init_db, \
             patch('app.core.startup.settings') as mock_settings:
            mock_settings.DATABASE_URL = "sqlite:///:memory:"
            
            initialize_database()
            
            mock_init_db.assert_called_once_with("sqlite:///:memory:")
    
    def test_initialize_database_failure(self):
        """Test that database initialization failure is propagated."""
        with patch('app.core.startup.init_database') as mock_init_db, \
             patch('app.core.startup.settings') as mock_settings:
            mock_settings.DATABASE_URL = "sqlite:///:memory:"
            mock_init_db.side_effect = Exception("Database error")
            
            with pytest.raises(Exception) as exc_info:
                initialize_database()
            
            assert "Database error" in str(exc_info.value)


class TestFileStorageInitialization:
    """Unit tests for file storage initialization."""
    
    def test_initialize_file_storage_creates_directory(self):
        """Test that file storage initialization creates directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test_storage"
            
            with patch('app.core.startup.settings') as mock_settings:
                mock_settings.FILE_STORAGE_ROOT = str(storage_path)
                
                initialize_file_storage()
                
                assert storage_path.exists()
                assert storage_path.is_dir()
    
    def test_initialize_file_storage_verifies_write_permissions(self):
        """Test that file storage initialization verifies write permissions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "test_storage"
            
            with patch('app.core.startup.settings') as mock_settings:
                mock_settings.FILE_STORAGE_ROOT = str(storage_path)
                
                # Should not raise exception
                initialize_file_storage()
    
    def test_initialize_file_storage_fails_on_readonly_directory(self):
        """Test that initialization fails if directory is not writable."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "readonly_storage"
            storage_path.mkdir()
            
            with patch('app.core.startup.settings') as mock_settings:
                mock_settings.FILE_STORAGE_ROOT = str(storage_path)
                
                # Mock the write test to fail
                with patch.object(Path, 'write_text', side_effect=PermissionError("No write permission")):
                    with pytest.raises(ConfigurationError) as exc_info:
                        initialize_file_storage()
                    
                    assert "not writable" in str(exc_info.value)


class TestStartup:
    """Unit tests for complete startup process."""
    
    def test_startup_executes_all_steps(self):
        """Test that startup executes all initialization steps in order."""
        with patch('app.core.startup.validate_configuration') as mock_validate, \
             patch('app.core.startup.initialize_database') as mock_init_db, \
             patch('app.core.startup.initialize_file_storage') as mock_init_storage:
            
            startup()
            
            # Verify all steps were called
            mock_validate.assert_called_once()
            mock_init_db.assert_called_once()
            mock_init_storage.assert_called_once()
    
    def test_startup_fails_on_invalid_configuration(self):
        """Test that startup fails if configuration is invalid."""
        with patch('app.core.startup.validate_configuration') as mock_validate:
            mock_validate.side_effect = ConfigurationError("Invalid config")
            
            with pytest.raises(ConfigurationError):
                startup()
    
    def test_startup_fails_on_database_initialization_error(self):
        """Test that startup fails if database initialization fails."""
        with patch('app.core.startup.validate_configuration'), \
             patch('app.core.startup.initialize_database') as mock_init_db:
            mock_init_db.side_effect = Exception("Database error")
            
            with pytest.raises(Exception) as exc_info:
                startup()
            
            assert "Database error" in str(exc_info.value)
    
    def test_startup_fails_on_file_storage_initialization_error(self):
        """Test that startup fails if file storage initialization fails."""
        with patch('app.core.startup.validate_configuration'), \
             patch('app.core.startup.initialize_database'), \
             patch('app.core.startup.initialize_file_storage') as mock_init_storage:
            mock_init_storage.side_effect = ConfigurationError("Storage error")
            
            with pytest.raises(ConfigurationError) as exc_info:
                startup()
            
            assert "Storage error" in str(exc_info.value)
