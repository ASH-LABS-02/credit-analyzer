"""
Property-based tests for Firebase Storage Service access control.

These tests validate that access control is properly enforced for all storage operations.

Feature: intelli-credit-platform
Requirements: 12.3
"""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, patch
import asyncio

from app.services.storage_service import StorageService


# Custom strategies for generating test data
@st.composite
def storage_path_strategy(draw):
    """Generate valid storage paths."""
    app_id = draw(st.text(
        min_size=1, max_size=50,
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')
    ))
    doc_id = draw(st.text(
        min_size=1, max_size=50,
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')
    ))
    filename = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))) + '.pdf'
    
    return {
        'path': f'documents/{app_id}/{doc_id}_{filename}',
        'app_id': app_id,
        'doc_id': doc_id,
        'filename': filename
    }


@st.composite
def file_data_strategy(draw):
    """Generate valid file data."""
    # Generate file data between 1 byte and 1MB for testing
    size = draw(st.integers(min_value=1, max_value=1024 * 1024))
    return b'x' * size


# Property 25: Document Access Control
# **Validates: Requirements 12.3**
@pytest.mark.property
@settings(max_examples=5)
@given(
    storage_info=storage_path_strategy(),
    authorized_app_id=st.text(
        min_size=1, max_size=50,
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')
    ),
    unauthorized_app_id=st.text(
        min_size=1, max_size=50,
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')
    )
)
def test_document_access_control_download(storage_info, authorized_app_id, unauthorized_app_id):
    """
    Property 25: Document Access Control
    
    For any document stored in Firebase Storage, unauthorized users should be unable
    to access the document, while authorized users with proper permissions should be
    able to retrieve it.
    
    This test validates download access control.
    
    **Validates: Requirements 12.3**
    """
    # Ensure authorized and unauthorized IDs are different
    if authorized_app_id == unauthorized_app_id:
        unauthorized_app_id = authorized_app_id + '_different'
    
    with patch('app.services.storage_service.get_storage_bucket') as mock_bucket_func:
        # Setup mock bucket
        mock_bucket = Mock()
        mock_bucket_func.return_value = mock_bucket
        
        # Setup mock blob with metadata
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.metadata = {'application_id': authorized_app_id}
        mock_blob.download_as_bytes.return_value = b'File content'
        mock_bucket.blob.return_value = mock_blob
        
        # Create storage service
        storage_service = StorageService()
        
        # Test 1: Authorized access should succeed
        try:
            file_data = asyncio.run(storage_service.download_file(
                storage_path=storage_info['path'],
                application_id=authorized_app_id
            ))
            
            assert file_data == b'File content', \
                "Authorized user should be able to download the file"
            
        except ValueError as e:
            pytest.fail(f"Authorized access should succeed but got error: {e}")
        
        # Test 2: Unauthorized access should fail
        with pytest.raises(ValueError) as exc_info:
            asyncio.run(storage_service.download_file(
                storage_path=storage_info['path'],
                application_id=unauthorized_app_id
            ))
        
        assert 'Access denied' in str(exc_info.value), \
            "Unauthorized access should be denied with appropriate error message"


@pytest.mark.property
@settings(max_examples=5)
@given(
    storage_info=storage_path_strategy(),
    authorized_app_id=st.text(
        min_size=1, max_size=50,
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')
    ),
    unauthorized_app_id=st.text(
        min_size=1, max_size=50,
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')
    )
)
def test_document_access_control_delete(storage_info, authorized_app_id, unauthorized_app_id):
    """
    Property 25: Document Access Control (Delete Operation)
    
    For any document stored in Firebase Storage, unauthorized users should be unable
    to delete the document, while authorized users with proper permissions should be
    able to delete it.
    
    **Validates: Requirements 12.3**
    """
    # Ensure authorized and unauthorized IDs are different
    if authorized_app_id == unauthorized_app_id:
        unauthorized_app_id = authorized_app_id + '_different'
    
    with patch('app.services.storage_service.get_storage_bucket') as mock_bucket_func:
        # Setup mock bucket
        mock_bucket = Mock()
        mock_bucket_func.return_value = mock_bucket
        
        # Setup mock blob with metadata
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.metadata = {'application_id': authorized_app_id}
        mock_bucket.blob.return_value = mock_blob
        
        # Create storage service
        storage_service = StorageService()
        
        # Test 1: Unauthorized deletion should fail
        with pytest.raises(ValueError) as exc_info:
            asyncio.run(storage_service.delete_file(
                storage_path=storage_info['path'],
                application_id=unauthorized_app_id
            ))
        
        assert 'Access denied' in str(exc_info.value), \
            "Unauthorized deletion should be denied with appropriate error message"
        
        # Verify delete was NOT called for unauthorized access
        mock_blob.delete.assert_not_called()
        
        # Test 2: Authorized deletion should succeed
        try:
            result = asyncio.run(storage_service.delete_file(
                storage_path=storage_info['path'],
                application_id=authorized_app_id
            ))
            
            assert result is True, \
                "Authorized user should be able to delete the file"
            
            # Verify delete was called for authorized access
            mock_blob.delete.assert_called_once()
            
        except ValueError as e:
            pytest.fail(f"Authorized deletion should succeed but got error: {e}")


@pytest.mark.property
@settings(max_examples=5)
@given(
    storage_info=storage_path_strategy(),
    authorized_app_id=st.text(
        min_size=1, max_size=50,
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')
    ),
    unauthorized_app_id=st.text(
        min_size=1, max_size=50,
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')
    )
)
def test_document_access_control_metadata(storage_info, authorized_app_id, unauthorized_app_id):
    """
    Property 25: Document Access Control (Metadata Operations)
    
    For any document stored in Firebase Storage, unauthorized users should be unable
    to access or modify the document metadata, while authorized users with proper
    permissions should be able to access and modify it.
    
    **Validates: Requirements 12.3**
    """
    # Ensure authorized and unauthorized IDs are different
    if authorized_app_id == unauthorized_app_id:
        unauthorized_app_id = authorized_app_id + '_different'
    
    with patch('app.services.storage_service.get_storage_bucket') as mock_bucket_func:
        # Setup mock bucket
        mock_bucket = Mock()
        mock_bucket_func.return_value = mock_bucket
        
        # Setup mock blob with metadata
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.name = storage_info['path']
        mock_blob.size = 1024
        mock_blob.content_type = 'application/pdf'
        mock_blob.time_created = None
        mock_blob.updated = None
        mock_blob.metadata = {'application_id': authorized_app_id, 'status': 'pending'}
        mock_blob.md5_hash = 'abc123'
        mock_bucket.blob.return_value = mock_blob
        
        # Create storage service
        storage_service = StorageService()
        
        # Test 1: Unauthorized metadata access should fail
        with pytest.raises(ValueError) as exc_info:
            asyncio.run(storage_service.get_file_metadata(
                storage_path=storage_info['path'],
                application_id=unauthorized_app_id
            ))
        
        assert 'Access denied' in str(exc_info.value), \
            "Unauthorized metadata access should be denied"
        
        # Test 2: Authorized metadata access should succeed
        try:
            metadata = asyncio.run(storage_service.get_file_metadata(
                storage_path=storage_info['path'],
                application_id=authorized_app_id
            ))
            
            assert metadata is not None, \
                "Authorized user should be able to access metadata"
            assert metadata['metadata']['application_id'] == authorized_app_id, \
                "Metadata should contain correct application ID"
            
        except ValueError as e:
            pytest.fail(f"Authorized metadata access should succeed but got error: {e}")
        
        # Test 3: Unauthorized metadata update should fail
        with pytest.raises(ValueError) as exc_info:
            asyncio.run(storage_service.update_file_metadata(
                storage_path=storage_info['path'],
                metadata={'status': 'processed'},
                application_id=unauthorized_app_id
            ))
        
        assert 'Access denied' in str(exc_info.value), \
            "Unauthorized metadata update should be denied"
        
        # Verify patch was NOT called for unauthorized access
        mock_blob.patch.assert_not_called()
        
        # Test 4: Authorized metadata update should succeed
        try:
            result = asyncio.run(storage_service.update_file_metadata(
                storage_path=storage_info['path'],
                metadata={'status': 'processed'},
                application_id=authorized_app_id
            ))
            
            assert result is not None, \
                "Authorized user should be able to update metadata"
            
            # Verify patch was called for authorized access
            mock_blob.patch.assert_called_once()
            
        except ValueError as e:
            pytest.fail(f"Authorized metadata update should succeed but got error: {e}")


@pytest.mark.property
@settings(max_examples=5)
@given(
    storage_info=storage_path_strategy(),
    authorized_app_id=st.text(
        min_size=1, max_size=50,
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')
    ),
    unauthorized_app_id=st.text(
        min_size=1, max_size=50,
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_')
    )
)
def test_document_access_control_signed_url(storage_info, authorized_app_id, unauthorized_app_id):
    """
    Property 25: Document Access Control (Signed URL Generation)
    
    For any document stored in Firebase Storage, unauthorized users should be unable
    to generate signed URLs for the document, while authorized users with proper
    permissions should be able to generate them.
    
    **Validates: Requirements 12.3**
    """
    # Ensure authorized and unauthorized IDs are different
    if authorized_app_id == unauthorized_app_id:
        unauthorized_app_id = authorized_app_id + '_different'
    
    with patch('app.services.storage_service.get_storage_bucket') as mock_bucket_func:
        # Setup mock bucket
        mock_bucket = Mock()
        mock_bucket_func.return_value = mock_bucket
        
        # Setup mock blob with metadata
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.metadata = {'application_id': authorized_app_id}
        mock_blob.generate_signed_url.return_value = 'https://signed-url.com/file'
        mock_bucket.blob.return_value = mock_blob
        
        # Create storage service
        storage_service = StorageService()
        
        # Test 1: Unauthorized signed URL generation should fail
        with pytest.raises(ValueError) as exc_info:
            asyncio.run(storage_service.generate_signed_url(
                storage_path=storage_info['path'],
                application_id=unauthorized_app_id
            ))
        
        assert 'Access denied' in str(exc_info.value), \
            "Unauthorized signed URL generation should be denied"
        
        # Verify generate_signed_url was NOT called for unauthorized access
        mock_blob.generate_signed_url.assert_not_called()
        
        # Test 2: Authorized signed URL generation should succeed
        try:
            signed_url = asyncio.run(storage_service.generate_signed_url(
                storage_path=storage_info['path'],
                application_id=authorized_app_id
            ))
            
            assert signed_url == 'https://signed-url.com/file', \
                "Authorized user should be able to generate signed URL"
            
            # Verify generate_signed_url was called for authorized access
            mock_blob.generate_signed_url.assert_called_once()
            
        except ValueError as e:
            pytest.fail(f"Authorized signed URL generation should succeed but got error: {e}")


@pytest.mark.property
@settings(max_examples=5)
@given(storage_info=storage_path_strategy())
def test_document_access_without_application_id(storage_info):
    """
    Property 25: Document Access Control (No Application ID)
    
    When no application_id is provided for access control, operations should succeed
    without access control checks (for administrative operations).
    
    **Validates: Requirements 12.3**
    """
    with patch('app.services.storage_service.get_storage_bucket') as mock_bucket_func:
        # Setup mock bucket
        mock_bucket = Mock()
        mock_bucket_func.return_value = mock_bucket
        
        # Setup mock blob
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.metadata = {'application_id': 'some-app-id'}
        mock_blob.download_as_bytes.return_value = b'File content'
        mock_blob.name = storage_info['path']
        mock_blob.size = 1024
        mock_blob.content_type = 'application/pdf'
        mock_blob.time_created = None
        mock_blob.updated = None
        mock_blob.md5_hash = 'abc123'
        mock_blob.generate_signed_url.return_value = 'https://signed-url.com/file'
        mock_bucket.blob.return_value = mock_blob
        
        # Create storage service
        storage_service = StorageService()
        
        # Test 1: Download without application_id should succeed
        try:
            file_data = asyncio.run(storage_service.download_file(
                storage_path=storage_info['path']
                # No application_id provided
            ))
            assert file_data == b'File content', \
                "Download without application_id should succeed"
        except ValueError as e:
            pytest.fail(f"Download without application_id should succeed but got error: {e}")
        
        # Test 2: Get metadata without application_id should succeed
        try:
            metadata = asyncio.run(storage_service.get_file_metadata(
                storage_path=storage_info['path']
                # No application_id provided
            ))
            assert metadata is not None, \
                "Get metadata without application_id should succeed"
        except ValueError as e:
            pytest.fail(f"Get metadata without application_id should succeed but got error: {e}")
        
        # Test 3: Delete without application_id should succeed
        try:
            result = asyncio.run(storage_service.delete_file(
                storage_path=storage_info['path']
                # No application_id provided
            ))
            assert result is True, \
                "Delete without application_id should succeed"
        except ValueError as e:
            pytest.fail(f"Delete without application_id should succeed but got error: {e}")
        
        # Test 4: Generate signed URL without application_id should succeed
        try:
            signed_url = asyncio.run(storage_service.generate_signed_url(
                storage_path=storage_info['path']
                # No application_id provided
            ))
            assert signed_url == 'https://signed-url.com/file', \
                "Generate signed URL without application_id should succeed"
        except ValueError as e:
            pytest.fail(f"Generate signed URL without application_id should succeed but got error: {e}")
