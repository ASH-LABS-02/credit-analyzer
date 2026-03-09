"""
Unit tests for FileStorageService.

Tests local filesystem operations, path validation, and security checks.

Feature: firebase-to-sqlite-migration
Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from app.services.file_storage_service import FileStorageService


@pytest.fixture
def temp_storage_dir():
    """Create a temporary directory for file storage tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def file_storage_service(temp_storage_dir):
    """Create FileStorageService instance with temporary storage."""
    return FileStorageService(temp_storage_dir)


class TestFileStorageServiceSaveFile:
    """Test save_file method."""
    
    def test_save_file_creates_application_directory(self, file_storage_service, temp_storage_dir):
        """Test that save_file creates application-specific directory."""
        content = b"test content"
        app_id = "app123"
        filename = "test.txt"
        
        file_path = file_storage_service.save_file(content, app_id, filename)
        
        # Check that application directory was created
        app_dir = Path(temp_storage_dir) / app_id
        assert app_dir.exists()
        assert app_dir.is_dir()
    
    def test_save_file_stores_content_correctly(self, file_storage_service, temp_storage_dir):
        """Test that save_file stores file content correctly."""
        content = b"test content with special chars: \x00\xff"
        app_id = "app123"
        filename = "test.bin"
        
        file_path = file_storage_service.save_file(content, app_id, filename)
        
        # Read file directly and verify content
        full_path = Path(temp_storage_dir) / file_path
        with open(full_path, 'rb') as f:
            stored_content = f.read()
        
        assert stored_content == content
    
    def test_save_file_returns_relative_path(self, file_storage_service):
        """Test that save_file returns relative path from storage root."""
        content = b"test"
        app_id = "app123"
        filename = "test.txt"
        
        file_path = file_storage_service.save_file(content, app_id, filename)
        
        # Path should be relative (not absolute)
        assert not Path(file_path).is_absolute()
        # Path should start with application ID
        assert file_path.startswith(app_id)
    
    def test_save_file_generates_unique_filename_on_conflict(self, file_storage_service):
        """Test that save_file generates unique filenames when file exists."""
        content1 = b"first file"
        content2 = b"second file"
        app_id = "app123"
        filename = "duplicate.txt"
        
        # Save first file
        path1 = file_storage_service.save_file(content1, app_id, filename)
        # Save second file with same name
        path2 = file_storage_service.save_file(content2, app_id, filename)
        
        # Paths should be different
        assert path1 != path2
        # Both files should exist
        assert (file_storage_service.storage_root / path1).exists()
        assert (file_storage_service.storage_root / path2).exists()
        # Second file should have counter suffix
        assert "_1" in path2
    
    def test_save_file_sanitizes_filename(self, file_storage_service):
        """Test that save_file sanitizes filenames with path components."""
        content = b"test"
        app_id = "app123"
        # Filename with directory traversal attempt
        filename = "../../../etc/passwd"
        
        file_path = file_storage_service.save_file(content, app_id, filename)
        
        # File should be saved in the correct application directory
        assert file_path.startswith(app_id)
        # File should not escape the application directory
        assert ".." not in file_path
        # File should be named "passwd" (basename)
        assert "passwd" in file_path


class TestFileStorageServiceReadFile:
    """Test read_file method."""
    
    def test_read_file_returns_correct_content(self, file_storage_service):
        """Test that read_file returns the correct file content."""
        content = b"test content for reading"
        app_id = "app123"
        filename = "read_test.txt"
        
        # Save file first
        file_path = file_storage_service.save_file(content, app_id, filename)
        
        # Read file back
        read_content = file_storage_service.read_file(file_path)
        
        assert read_content == content
    
    def test_read_file_raises_error_for_nonexistent_file(self, file_storage_service):
        """Test that read_file raises FileNotFoundError for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            file_storage_service.read_file("app123/nonexistent.txt")
    
    def test_read_file_prevents_directory_traversal(self, file_storage_service):
        """Test that read_file prevents directory traversal attacks."""
        # Attempt to read file outside storage root
        with pytest.raises(ValueError, match="directory traversal"):
            file_storage_service.read_file("../../../etc/passwd")
    
    def test_read_file_prevents_absolute_path(self, file_storage_service):
        """Test that read_file prevents absolute path access."""
        with pytest.raises(ValueError, match="directory traversal"):
            file_storage_service.read_file("/etc/passwd")


class TestFileStorageServiceDeleteFile:
    """Test delete_file method."""
    
    def test_delete_file_removes_existing_file(self, file_storage_service):
        """Test that delete_file removes an existing file."""
        content = b"file to delete"
        app_id = "app123"
        filename = "delete_me.txt"
        
        # Save file first
        file_path = file_storage_service.save_file(content, app_id, filename)
        full_path = file_storage_service.storage_root / file_path
        
        # Verify file exists
        assert full_path.exists()
        
        # Delete file
        result = file_storage_service.delete_file(file_path)
        
        # Verify deletion
        assert result is True
        assert not full_path.exists()
    
    def test_delete_file_returns_false_for_nonexistent_file(self, file_storage_service):
        """Test that delete_file returns False for nonexistent file."""
        result = file_storage_service.delete_file("app123/nonexistent.txt")
        assert result is False
    
    def test_delete_file_prevents_directory_traversal(self, file_storage_service):
        """Test that delete_file prevents directory traversal attacks."""
        with pytest.raises(ValueError, match="directory traversal"):
            file_storage_service.delete_file("../../../etc/passwd")
    
    def test_delete_file_prevents_absolute_path(self, file_storage_service):
        """Test that delete_file prevents absolute path access."""
        with pytest.raises(ValueError, match="directory traversal"):
            file_storage_service.delete_file("/tmp/somefile.txt")


class TestFileStorageServicePathSanitization:
    """Test path sanitization and security methods."""
    
    def test_sanitize_filename_removes_path_components(self, file_storage_service):
        """Test that _sanitize_filename removes path components."""
        assert file_storage_service._sanitize_filename("../file.txt") == "file.txt"
        assert file_storage_service._sanitize_filename("../../file.txt") == "file.txt"
        assert file_storage_service._sanitize_filename("/etc/passwd") == "passwd"
        assert file_storage_service._sanitize_filename("dir/subdir/file.txt") == "file.txt"
    
    def test_sanitize_filename_handles_empty_or_invalid(self, file_storage_service):
        """Test that _sanitize_filename handles empty or invalid filenames."""
        # Empty string should generate a unique name
        result = file_storage_service._sanitize_filename("")
        assert result.startswith("file_")
        
        # Dot and double-dot should generate unique names
        result = file_storage_service._sanitize_filename(".")
        assert result.startswith("file_")
        
        result = file_storage_service._sanitize_filename("..")
        assert result.startswith("file_")
    
    def test_is_safe_path_accepts_valid_paths(self, file_storage_service):
        """Test that _is_safe_path accepts valid paths within storage root."""
        # Path within storage root
        safe_path = file_storage_service.storage_root / "app123" / "file.txt"
        assert file_storage_service._is_safe_path(safe_path) is True
        
        # Nested path within storage root
        safe_path = file_storage_service.storage_root / "app123" / "subdir" / "file.txt"
        assert file_storage_service._is_safe_path(safe_path) is True
    
    def test_is_safe_path_rejects_traversal_attempts(self, file_storage_service):
        """Test that _is_safe_path rejects directory traversal attempts."""
        # Path outside storage root using ..
        unsafe_path = file_storage_service.storage_root / ".." / "etc" / "passwd"
        assert file_storage_service._is_safe_path(unsafe_path) is False
        
        # Absolute path outside storage root
        unsafe_path = Path("/etc/passwd")
        assert file_storage_service._is_safe_path(unsafe_path) is False


class TestFileStorageServiceEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_save_file_with_binary_content(self, file_storage_service):
        """Test saving and reading binary content."""
        # Binary content with all byte values
        content = bytes(range(256))
        app_id = "app123"
        filename = "binary.bin"
        
        file_path = file_storage_service.save_file(content, app_id, filename)
        read_content = file_storage_service.read_file(file_path)
        
        assert read_content == content
    
    def test_save_file_with_large_content(self, file_storage_service):
        """Test saving and reading large file content."""
        # 1 MB of data
        content = b"x" * (1024 * 1024)
        app_id = "app123"
        filename = "large.bin"
        
        file_path = file_storage_service.save_file(content, app_id, filename)
        read_content = file_storage_service.read_file(file_path)
        
        assert len(read_content) == len(content)
        assert read_content == content
    
    def test_save_file_with_special_characters_in_filename(self, file_storage_service):
        """Test saving files with special characters in filename."""
        content = b"test"
        app_id = "app123"
        # Filename with spaces and special chars
        filename = "my file (copy) [1].txt"
        
        file_path = file_storage_service.save_file(content, app_id, filename)
        
        # Should be able to read the file back
        read_content = file_storage_service.read_file(file_path)
        assert read_content == content
    
    def test_multiple_applications_isolated(self, file_storage_service):
        """Test that files from different applications are isolated."""
        content = b"test"
        filename = "same_name.txt"
        
        # Save file for app1
        path1 = file_storage_service.save_file(content, "app1", filename)
        # Save file for app2 with same filename
        path2 = file_storage_service.save_file(content, "app2", filename)
        
        # Paths should be different (different app directories)
        assert path1 != path2
        assert "app1" in path1
        assert "app2" in path2
        
        # Both files should exist
        assert (file_storage_service.storage_root / path1).exists()
        assert (file_storage_service.storage_root / path2).exists()
