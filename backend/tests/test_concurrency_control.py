"""
Unit tests for concurrency control service.

Tests optimistic concurrency control, locking mechanisms, and conflict resolution.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from google.cloud import firestore

from app.services.concurrency_control import (
    ConcurrencyControl,
    ConcurrencyConflictError,
    get_concurrency_control
)


@pytest.fixture
def mock_firestore():
    """Create a mock Firestore client."""
    mock_db = Mock()
    return mock_db


@pytest.fixture
def concurrency_control(mock_firestore):
    """Create a ConcurrencyControl instance with mocked Firestore."""
    with patch('app.services.concurrency_control.get_firestore_client', return_value=mock_firestore):
        cc = ConcurrencyControl()
        return cc


class TestConcurrencyControl:
    """Test suite for ConcurrencyControl class."""
    
    def test_initialization(self, concurrency_control):
        """Test that ConcurrencyControl initializes correctly."""
        assert concurrency_control.db is not None
        assert isinstance(concurrency_control._locks, dict)
        assert len(concurrency_control._locks) == 0
    
    @pytest.mark.asyncio
    async def test_get_lock_creates_new_lock(self, concurrency_control):
        """Test that _get_lock creates a new lock for a resource."""
        lock = await concurrency_control._get_lock("resource1")
        
        assert isinstance(lock, asyncio.Lock)
        assert "resource1" in concurrency_control._locks
        assert concurrency_control._locks["resource1"] is lock
    
    @pytest.mark.asyncio
    async def test_get_lock_returns_existing_lock(self, concurrency_control):
        """Test that _get_lock returns existing lock for same resource."""
        lock1 = await concurrency_control._get_lock("resource1")
        lock2 = await concurrency_control._get_lock("resource1")
        
        assert lock1 is lock2
    
    @pytest.mark.asyncio
    async def test_acquire_lock_success(self, concurrency_control):
        """Test successful lock acquisition."""
        async with concurrency_control.acquire_lock("resource1"):
            # Lock should be acquired
            lock = concurrency_control._locks["resource1"]
            assert lock.locked()
        
        # Lock should be released after context
        assert not lock.locked()
    
    @pytest.mark.asyncio
    async def test_acquire_lock_timeout(self, concurrency_control):
        """Test lock acquisition timeout."""
        # Acquire lock first
        lock = await concurrency_control._get_lock("resource1")
        await lock.acquire()
        
        try:
            # Try to acquire same lock with short timeout
            with pytest.raises(TimeoutError) as exc_info:
                async with concurrency_control.acquire_lock("resource1", timeout=0.1):
                    pass
            
            assert "Could not acquire lock" in str(exc_info.value)
        finally:
            if lock.locked():
                lock.release()
    
    @pytest.mark.asyncio
    async def test_get_with_version_document_exists(self, concurrency_control, mock_firestore):
        """Test getting document with version when it exists."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'id': 'app1',
            'status': 'pending',
            '_version': 5
        }
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        
        mock_collection = Mock()
        mock_collection.document.return_value = mock_doc_ref
        
        mock_firestore.collection.return_value = mock_collection
        
        # Test
        result = await concurrency_control.get_with_version('applications', 'app1')
        
        assert result is not None
        assert result['version'] == 5
        assert result['document_id'] == 'app1'
        assert result['data']['id'] == 'app1'
        assert result['data']['status'] == 'pending'
    
    @pytest.mark.asyncio
    async def test_get_with_version_document_not_exists(self, concurrency_control, mock_firestore):
        """Test getting document with version when it doesn't exist."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        
        mock_collection = Mock()
        mock_collection.document.return_value = mock_doc_ref
        
        mock_firestore.collection.return_value = mock_collection
        
        # Test
        result = await concurrency_control.get_with_version('applications', 'app1')
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_with_version_no_version_field(self, concurrency_control, mock_firestore):
        """Test getting document without version field defaults to version 1."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'id': 'app1',
            'status': 'pending'
        }
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        
        mock_collection = Mock()
        mock_collection.document.return_value = mock_doc_ref
        
        mock_firestore.collection.return_value = mock_collection
        
        # Test
        result = await concurrency_control.get_with_version('applications', 'app1')
        
        assert result is not None
        assert result['version'] == 1
    
    @pytest.mark.asyncio
    async def test_update_with_version_check_success(self, concurrency_control, mock_firestore):
        """Test successful update with version check."""
        # We need to test the logic without the decorator
        # Let's directly test the update logic
        
        # Setup mock
        mock_snapshot = Mock()
        mock_snapshot.exists = True
        mock_snapshot.to_dict.return_value = {
            'id': 'app1',
            'status': 'pending',
            '_version': 3
        }
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_snapshot
        
        mock_collection = Mock()
        mock_collection.document.return_value = mock_doc_ref
        
        mock_firestore.collection.return_value = mock_collection
        
        # Mock the transaction to execute the function immediately
        def mock_transaction_decorator(func):
            def wrapper(transaction):
                # Execute the function with a mock transaction
                mock_tx = Mock()
                mock_tx.update = Mock()
                return func(mock_tx)
            return wrapper
        
        with patch('app.services.concurrency_control.admin_firestore.transactional', mock_transaction_decorator):
            # Test
            updates = {'status': 'processing'}
            result = await concurrency_control.update_with_version_check(
                'applications',
                'app1',
                updates,
                expected_version=3
            )
            
            assert result['status'] == 'processing'
            assert result['_version'] == 4
            assert '_last_modified' in result
    
    @pytest.mark.asyncio
    async def test_update_with_version_check_conflict(self, concurrency_control, mock_firestore):
        """Test update with version mismatch raises conflict error."""
        # Setup mock
        mock_snapshot = Mock()
        mock_snapshot.exists = True
        mock_snapshot.to_dict.return_value = {
            'id': 'app1',
            'status': 'pending',
            '_version': 5  # Different from expected
        }
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_snapshot
        
        mock_collection = Mock()
        mock_collection.document.return_value = mock_doc_ref
        
        mock_firestore.collection.return_value = mock_collection
        
        # Mock the transaction to execute the function immediately
        def mock_transaction_decorator(func):
            def wrapper(transaction):
                mock_tx = Mock()
                return func(mock_tx)
            return wrapper
        
        with patch('app.services.concurrency_control.admin_firestore.transactional', mock_transaction_decorator):
            # Test
            updates = {'status': 'processing'}
            with pytest.raises(ConcurrencyConflictError) as exc_info:
                await concurrency_control.update_with_version_check(
                    'applications',
                    'app1',
                    updates,
                    expected_version=3
                )
            
            assert "Version mismatch" in str(exc_info.value)
            assert "expected 3" in str(exc_info.value)
            assert "current version is 5" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_update_with_version_check_document_not_exists(self, concurrency_control, mock_firestore):
        """Test update with version check when document doesn't exist."""
        # Setup mock
        mock_snapshot = Mock()
        mock_snapshot.exists = False
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_snapshot
        
        mock_collection = Mock()
        mock_collection.document.return_value = mock_doc_ref
        
        mock_firestore.collection.return_value = mock_collection
        
        # Mock the transaction to execute the function immediately
        def mock_transaction_decorator(func):
            def wrapper(transaction):
                mock_tx = Mock()
                return func(mock_tx)
            return wrapper
        
        with patch('app.services.concurrency_control.admin_firestore.transactional', mock_transaction_decorator):
            # Test
            updates = {'status': 'processing'}
            with pytest.raises(ValueError) as exc_info:
                await concurrency_control.update_with_version_check(
                    'applications',
                    'app1',
                    updates,
                    expected_version=3
                )
            
            assert "does not exist" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_with_version(self, concurrency_control, mock_firestore):
        """Test creating document with initial version."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_doc_ref.set = Mock()
        
        mock_collection = Mock()
        mock_collection.document.return_value = mock_doc_ref
        
        mock_firestore.collection.return_value = mock_collection
        
        # Test
        data = {'id': 'app1', 'status': 'pending'}
        result = await concurrency_control.create_with_version(
            'applications',
            'app1',
            data
        )
        
        assert result['_version'] == 1
        assert '_created_at' in result
        assert '_last_modified' in result
        assert result['id'] == 'app1'
        assert result['status'] == 'pending'
        
        mock_doc_ref.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_with_version_already_exists(self, concurrency_control, mock_firestore):
        """Test creating document that already exists raises error."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.exists = True
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        
        mock_collection = Mock()
        mock_collection.document.return_value = mock_doc_ref
        
        mock_firestore.collection.return_value = mock_collection
        
        # Test
        data = {'id': 'app1', 'status': 'pending'}
        with pytest.raises(ValueError) as exc_info:
            await concurrency_control.create_with_version(
                'applications',
                'app1',
                data
            )
        
        assert "already exists" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_retry_on_conflict_success_first_try(self, concurrency_control):
        """Test retry succeeds on first attempt."""
        call_count = 0
        
        async def operation():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await concurrency_control.retry_on_conflict(operation, max_retries=3)
        
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_on_conflict_success_after_retries(self, concurrency_control):
        """Test retry succeeds after conflicts."""
        call_count = 0
        
        async def operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConcurrencyConflictError("Conflict")
            return "success"
        
        result = await concurrency_control.retry_on_conflict(operation, max_retries=3)
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_on_conflict_exhausted(self, concurrency_control):
        """Test retry fails after max attempts."""
        call_count = 0
        
        async def operation():
            nonlocal call_count
            call_count += 1
            raise ConcurrencyConflictError("Conflict")
        
        with pytest.raises(ConcurrencyConflictError) as exc_info:
            await concurrency_control.retry_on_conflict(operation, max_retries=3)
        
        assert "failed after 3 attempts" in str(exc_info.value)
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_compare_and_swap_success(self, concurrency_control, mock_firestore):
        """Test successful compare and swap."""
        # Setup mock
        mock_snapshot = Mock()
        mock_snapshot.exists = True
        mock_snapshot.to_dict.return_value = {
            'id': 'app1',
            'status': 'pending',
            '_version': 2
        }
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_snapshot
        
        mock_collection = Mock()
        mock_collection.document.return_value = mock_doc_ref
        
        mock_firestore.collection.return_value = mock_collection
        
        # Mock the transaction to execute the function immediately
        def mock_transaction_decorator(func):
            def wrapper(transaction):
                mock_tx = Mock()
                mock_tx.update = Mock()
                return func(mock_tx)
            return wrapper
        
        with patch('app.services.concurrency_control.admin_firestore.transactional', mock_transaction_decorator):
            # Test
            result = await concurrency_control.compare_and_swap(
                'applications',
                'app1',
                'status',
                'pending',
                'processing'
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_compare_and_swap_value_mismatch(self, concurrency_control, mock_firestore):
        """Test compare and swap with value mismatch."""
        # Setup mock
        mock_snapshot = Mock()
        mock_snapshot.exists = True
        mock_snapshot.to_dict.return_value = {
            'id': 'app1',
            'status': 'processing',  # Different from expected
            '_version': 2
        }
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_snapshot
        
        mock_collection = Mock()
        mock_collection.document.return_value = mock_doc_ref
        
        mock_firestore.collection.return_value = mock_collection
        
        # Mock the transaction to execute the function immediately
        def mock_transaction_decorator(func):
            def wrapper(transaction):
                mock_tx = Mock()
                return func(mock_tx)
            return wrapper
        
        with patch('app.services.concurrency_control.admin_firestore.transactional', mock_transaction_decorator):
            # Test
            result = await concurrency_control.compare_and_swap(
                'applications',
                'app1',
                'status',
                'pending',
                'processing'
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_compare_and_swap_document_not_exists(self, concurrency_control, mock_firestore):
        """Test compare and swap when document doesn't exist."""
        # Setup mock
        mock_snapshot = Mock()
        mock_snapshot.exists = False
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_snapshot
        
        mock_collection = Mock()
        mock_collection.document.return_value = mock_doc_ref
        
        mock_firestore.collection.return_value = mock_collection
        
        # Mock the transaction to execute the function immediately
        def mock_transaction_decorator(func):
            def wrapper(transaction):
                mock_tx = Mock()
                return func(mock_tx)
            return wrapper
        
        with patch('app.services.concurrency_control.admin_firestore.transactional', mock_transaction_decorator):
            # Test
            with pytest.raises(ValueError) as exc_info:
                await concurrency_control.compare_and_swap(
                    'applications',
                    'app1',
                    'status',
                    'pending',
                    'processing'
                )
            
            assert "does not exist" in str(exc_info.value)


class TestGetConcurrencyControl:
    """Test suite for get_concurrency_control singleton function."""
    
    def test_returns_singleton_instance(self):
        """Test that get_concurrency_control returns the same instance."""
        with patch('app.services.concurrency_control.get_firestore_client'):
            instance1 = get_concurrency_control()
            instance2 = get_concurrency_control()
            
            assert instance1 is instance2
    
    def test_returns_concurrency_control_instance(self):
        """Test that get_concurrency_control returns ConcurrencyControl instance."""
        with patch('app.services.concurrency_control.get_firestore_client'):
            instance = get_concurrency_control()
            
            assert isinstance(instance, ConcurrencyControl)
