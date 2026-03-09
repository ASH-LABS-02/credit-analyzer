"""
Unit tests for Firebase Storage Service.

Tests file upload/download operations, access control, and metadata management.

Feature: intelli-credit-platform
Requirements: 1.4, 12.3
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import asyncio

from app.services.storage_service import StorageService


@pytest.fixture
def mock_storage_bucket():
    """Mock Firebase Storage bucket."""
    with patch('app.services.storage_service.get_storage_bucket') as mock_bucket:
        bucket = Mock()
        mock_bucket.return_value = bucket
        yield bucket


@pytest.fixture
def storage_service(mock_storage_bucket):
    """Create StorageService instance with mocked bucket."""
    return StorageService()


class TestStorageServiceValidation:
    """Test file validation methods."""
    
    def test_validate_file_type_valid_extensions(self, storage_service):
        """Test that valid file extensions are accepted."""
        valid_files = [
            'document.pdf',
            'report.docx',
            'data.xlsx',
            'info.csv',
            'image.jpg',
            'photo.png'
        ]
        
        for filename in valid_files:
            assert storage_service._validate_file_type(filename), \
                f"File {filename} should be valid"
    
    def test_validate_file_type_invalid_extensions(self, storage_service):
        """Test that invalid file extensions are rejected."""
        invalid_files = [
            'script.exe',
            'code.py',
            'archive.zip',
            'video.mp4',
            'audio.mp3'
        ]
        
        for filename in invalid_files:
            assert not storage_service._validate_file_type(filename), \
                f"File {filename} should be invalid"
    
    def test_validate_file_type_case_insensitive(self, storage_service):
        """Test that file type validation is case-insensitive."""
        assert storage_service._validate_file_type('document.PDF')
        assert storage_service._validate_file_type('report.DOCX')
        assert storage_service._validate_file_type('Image.JPG')
    
    def test_validate_file_size_valid(self, storage_service):
        """Test that valid file sizes are accepted."""
        valid_sizes = [
            1,  # 1 byte
            1024,  # 1 KB
            1024 * 1024,  # 1 MB
            10 * 1024 * 1024,  # 10 MB
            50 * 1024 * 1024,  # 50 MB (max)
        ]
        
        for size in valid_sizes:
            assert storage_service._validate_file_size(size), \
                f"File size {size} should be valid"
    
    def test_validate_file_size_invalid(self, storage_service):
        """Test that invalid file sizes are rejected."""
        invalid_sizes = [
            0,  # Zero bytes
            -1,  # Negative
            51 * 1024 * 1024,  # Over 50 MB
            100 * 1024 * 1024,  # Way over limit
        ]
        
        for size in invalid_sizes:
            assert not storage_service._validate_file_size(size), \
                f"File size {size} should be invalid"
    
    def test_generate_storage_path(self, storage_service):
        """Test storage path generation."""
        path = storage_service._generate_storage_path(
            'app-123',
            'doc-456',
            'report.pdf'
        )
        
        assert path == 'documents/app-123/doc-456_report.pdf'
        assert 'app-123' in path
        assert 'doc-456' in path
        assert 'report.pdf' in path
    
    def test_generate_storage_path_sanitizes_filename(self, storage_service):
        """Test that storage path sanitizes filenames to prevent path traversal."""
        path = storage_service._generate_storage_path(
            'app-123',
            'doc-456',
            '../../../etc/passwd'
        )
        
        # Should only use the filename, not the path
        assert path == 'documents/app-123/doc-456_passwd'
        assert '../' not in path


class TestStorageServiceUpload:
    """Test file upload operations."""
    
    @pytest.mark.asyncio
    async def test_upload_file_success(self, storage_service, mock_storage_bucket):
        """Test successful file upload."""
        # Mock blob
        mock_blob = Mock()
        mock_blob.generate_signed_url.return_value = 'https://signed-url.com/file'
        mock_storage_bucket.blob.return_value = mock_blob
        
        # Test data
        file_data = b'Test file content'
        filename = 'test.pdf'
        app_id = 'app-123'
        doc_id = 'doc-456'
        
        # Upload file
        result = await storage_service.upload_file(
            file_data=file_data,
            filename=filename,
            application_id=app_id,
            document_id=doc_id
        )
        
        # Verify result
        assert result['storage_path'] == f'documents/{app_id}/{doc_id}_{filename}'
        assert result['signed_url'] == 'https://signed-url.com/file'
        assert result['file_size'] == len(file_data)
        assert 'metadata' in result
        assert result['metadata']['application_id'] == app_id
        assert result['metadata']['document_id'] == doc_id
        
        # Verify blob operations
        mock_blob.upload_from_string.assert_called_once()
        mock_blob.generate_signed_url.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_file_invalid_type(self, storage_service):
        """Test upload with invalid file type."""
        file_data = b'Test content'
        
        with pytest.raises(ValueError) as exc_info:
            await storage_service.upload_file(
                file_data=file_data,
                filename='script.exe',
                application_id='app-123',
                document_id='doc-456'
            )
        
        assert 'Invalid file type' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_upload_file_too_large(self, storage_service):
        """Test upload with file size exceeding limit."""
        # Create file data larger than 50MB
        file_data = b'x' * (51 * 1024 * 1024)
        
        with pytest.raises(ValueError) as exc_info:
            await storage_service.upload_file(
                file_data=file_data,
                filename='large.pdf',
                application_id='app-123',
                document_id='doc-456'
            )
        
        assert 'File size must be' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_upload_file_empty(self, storage_service):
        """Test upload with empty file."""
        file_data = b''
        
        with pytest.raises(ValueError) as exc_info:
            await storage_service.upload_file(
                file_data=file_data,
                filename='empty.pdf',
                application_id='app-123',
                document_id='doc-456'
            )
        
        assert 'File size must be' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_upload_file_with_custom_metadata(self, storage_service, mock_storage_bucket):
        """Test file upload with custom metadata."""
        mock_blob = Mock()
        mock_blob.generate_signed_url.return_value = 'https://signed-url.com/file'
        mock_storage_bucket.blob.return_value = mock_blob
        
        custom_metadata = {
            'document_type': 'financial_statement',
            'year': '2023'
        }
        
        result = await storage_service.upload_file(
            file_data=b'Test content',
            filename='test.pdf',
            application_id='app-123',
            document_id='doc-456',
            metadata=custom_metadata
        )
        
        # Verify custom metadata is included
        assert result['metadata']['document_type'] == 'financial_statement'
        assert result['metadata']['year'] == '2023'
        
        # Verify standard metadata is also present
        assert result['metadata']['application_id'] == 'app-123'
        assert result['metadata']['document_id'] == 'doc-456'


class TestStorageServiceDownload:
    """Test file download operations."""
    
    @pytest.mark.asyncio
    async def test_download_file_success(self, storage_service, mock_storage_bucket):
        """Test successful file download."""
        # Mock blob
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.download_as_bytes.return_value = b'File content'
        mock_blob.metadata = {'application_id': 'app-123'}
        mock_storage_bucket.blob.return_value = mock_blob
        
        # Download file
        file_data = await storage_service.download_file(
            storage_path='documents/app-123/doc-456_test.pdf'
        )
        
        assert file_data == b'File content'
        mock_blob.download_as_bytes.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_download_file_not_found(self, storage_service, mock_storage_bucket):
        """Test download of non-existent file."""
        mock_blob = Mock()
        mock_blob.exists.return_value = False
        mock_storage_bucket.blob.return_value = mock_blob
        
        with pytest.raises(ValueError) as exc_info:
            await storage_service.download_file(
                storage_path='documents/app-123/nonexistent.pdf'
            )
        
        assert 'File not found' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_download_file_with_access_control(self, storage_service, mock_storage_bucket):
        """Test download with access control check."""
        # Mock blob with metadata
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.metadata = {'application_id': 'app-123'}
        mock_blob.download_as_bytes.return_value = b'File content'
        mock_storage_bucket.blob.return_value = mock_blob
        
        # Download with matching application_id
        file_data = await storage_service.download_file(
            storage_path='documents/app-123/doc-456_test.pdf',
            application_id='app-123'
        )
        
        assert file_data == b'File content'
    
    @pytest.mark.asyncio
    async def test_download_file_access_denied(self, storage_service, mock_storage_bucket):
        """Test download with access control failure."""
        # Mock blob with different application_id
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.metadata = {'application_id': 'app-123'}
        mock_storage_bucket.blob.return_value = mock_blob
        
        # Try to download with different application_id
        with pytest.raises(ValueError) as exc_info:
            await storage_service.download_file(
                storage_path='documents/app-123/doc-456_test.pdf',
                application_id='app-999'  # Different app ID
            )
        
        assert 'Access denied' in str(exc_info.value)


class TestStorageServiceDelete:
    """Test file deletion operations."""
    
    @pytest.mark.asyncio
    async def test_delete_file_success(self, storage_service, mock_storage_bucket):
        """Test successful file deletion."""
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.metadata = {'application_id': 'app-123'}
        mock_storage_bucket.blob.return_value = mock_blob
        
        result = await storage_service.delete_file(
            storage_path='documents/app-123/doc-456_test.pdf',
            application_id='app-123'
        )
        
        assert result is True
        mock_blob.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, storage_service, mock_storage_bucket):
        """Test deletion of non-existent file."""
        mock_blob = Mock()
        mock_blob.exists.return_value = False
        mock_storage_bucket.blob.return_value = mock_blob
        
        with pytest.raises(ValueError) as exc_info:
            await storage_service.delete_file(
                storage_path='documents/app-123/nonexistent.pdf'
            )
        
        assert 'File not found' in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_delete_file_access_denied(self, storage_service, mock_storage_bucket):
        """Test deletion with access control failure."""
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.metadata = {'application_id': 'app-123'}
        mock_storage_bucket.blob.return_value = mock_blob
        
        with pytest.raises(ValueError) as exc_info:
            await storage_service.delete_file(
                storage_path='documents/app-123/doc-456_test.pdf',
                application_id='app-999'
            )
        
        assert 'Access denied' in str(exc_info.value)


class TestStorageServiceMetadata:
    """Test metadata management operations."""
    
    @pytest.mark.asyncio
    async def test_get_file_metadata_success(self, storage_service, mock_storage_bucket):
        """Test successful metadata retrieval."""
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.name = 'documents/app-123/doc-456_test.pdf'
        mock_blob.size = 1024
        mock_blob.content_type = 'application/pdf'
        mock_blob.time_created = datetime(2024, 1, 1, 12, 0, 0)
        mock_blob.updated = datetime(2024, 1, 2, 12, 0, 0)
        mock_blob.metadata = {'application_id': 'app-123', 'document_id': 'doc-456'}
        mock_blob.md5_hash = 'abc123'
        mock_storage_bucket.blob.return_value = mock_blob
        
        metadata = await storage_service.get_file_metadata(
            storage_path='documents/app-123/doc-456_test.pdf'
        )
        
        assert metadata['name'] == 'documents/app-123/doc-456_test.pdf'
        assert metadata['size'] == 1024
        assert metadata['content_type'] == 'application/pdf'
        assert metadata['metadata']['application_id'] == 'app-123'
        assert metadata['md5_hash'] == 'abc123'
    
    @pytest.mark.asyncio
    async def test_update_file_metadata_success(self, storage_service, mock_storage_bucket):
        """Test successful metadata update."""
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.metadata = {'application_id': 'app-123', 'old_key': 'old_value'}
        mock_storage_bucket.blob.return_value = mock_blob
        
        new_metadata = {'new_key': 'new_value', 'status': 'processed'}
        
        result = await storage_service.update_file_metadata(
            storage_path='documents/app-123/doc-456_test.pdf',
            metadata=new_metadata,
            application_id='app-123'
        )
        
        # Verify metadata was updated
        mock_blob.patch.assert_called_once()
        
        # Verify old metadata is preserved and new metadata is added
        assert mock_blob.metadata['application_id'] == 'app-123'
        assert mock_blob.metadata['new_key'] == 'new_value'
        assert mock_blob.metadata['status'] == 'processed'


class TestStorageServiceSignedURL:
    """Test signed URL generation."""
    
    @pytest.mark.asyncio
    async def test_generate_signed_url_success(self, storage_service, mock_storage_bucket):
        """Test successful signed URL generation."""
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.metadata = {'application_id': 'app-123'}
        mock_blob.generate_signed_url.return_value = 'https://signed-url.com/file'
        mock_storage_bucket.blob.return_value = mock_blob
        
        signed_url = await storage_service.generate_signed_url(
            storage_path='documents/app-123/doc-456_test.pdf',
            expiration_minutes=30,
            application_id='app-123'
        )
        
        assert signed_url == 'https://signed-url.com/file'
        mock_blob.generate_signed_url.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_signed_url_access_denied(self, storage_service, mock_storage_bucket):
        """Test signed URL generation with access control failure."""
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.metadata = {'application_id': 'app-123'}
        mock_storage_bucket.blob.return_value = mock_blob
        
        with pytest.raises(ValueError) as exc_info:
            await storage_service.generate_signed_url(
                storage_path='documents/app-123/doc-456_test.pdf',
                application_id='app-999'
            )
        
        assert 'Access denied' in str(exc_info.value)


class TestStorageServiceListFiles:
    """Test file listing operations."""
    
    @pytest.mark.asyncio
    async def test_list_files_by_application(self, storage_service, mock_storage_bucket):
        """Test listing files for an application."""
        # Mock blobs
        mock_blob1 = Mock()
        mock_blob1.name = 'documents/app-123/doc-1_file1.pdf'
        mock_blob1.size = 1024
        mock_blob1.content_type = 'application/pdf'
        mock_blob1.time_created = datetime(2024, 1, 1)
        mock_blob1.updated = datetime(2024, 1, 2)
        mock_blob1.metadata = {'document_id': 'doc-1'}
        
        mock_blob2 = Mock()
        mock_blob2.name = 'documents/app-123/doc-2_file2.xlsx'
        mock_blob2.size = 2048
        mock_blob2.content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        mock_blob2.time_created = datetime(2024, 1, 3)
        mock_blob2.updated = datetime(2024, 1, 4)
        mock_blob2.metadata = {'document_id': 'doc-2'}
        
        mock_storage_bucket.list_blobs.return_value = [mock_blob1, mock_blob2]
        
        files = await storage_service.list_files_by_application('app-123')
        
        assert len(files) == 2
        assert files[0]['name'] == 'documents/app-123/doc-1_file1.pdf'
        assert files[0]['size'] == 1024
        assert files[1]['name'] == 'documents/app-123/doc-2_file2.xlsx'
        assert files[1]['size'] == 2048
        
        # Verify correct prefix was used
        mock_storage_bucket.list_blobs.assert_called_once_with(prefix='documents/app-123/')
    
    @pytest.mark.asyncio
    async def test_list_files_empty_application(self, storage_service, mock_storage_bucket):
        """Test listing files for application with no files."""
        mock_storage_bucket.list_blobs.return_value = []
        
        files = await storage_service.list_files_by_application('app-999')
        
        assert len(files) == 0
        assert files == []
