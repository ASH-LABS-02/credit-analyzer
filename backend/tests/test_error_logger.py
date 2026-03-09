"""
Unit tests for ErrorLogger class.

Tests the centralized error logging functionality including:
- Error ID generation
- Structured log entry creation
- Firestore persistence
- Error retrieval by ID, application, and severity
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from app.core.error_logger import ErrorLogger, ErrorSeverity


@pytest.fixture
def mock_firestore():
    """Create a mock Firestore client."""
    mock_db = Mock()
    mock_collection = Mock()
    mock_db.collection.return_value = mock_collection
    return mock_db


@pytest.fixture
def error_logger(mock_firestore):
    """Create an ErrorLogger instance with mocked Firestore."""
    return ErrorLogger(mock_firestore)


@pytest.mark.asyncio
async def test_log_error_generates_unique_id(error_logger, mock_firestore):
    """Test that log_error generates a unique error ID."""
    error = ValueError("Test error")
    
    error_id = await error_logger.log_error(error)
    
    assert error_id is not None
    assert isinstance(error_id, str)
    assert len(error_id) > 0


@pytest.mark.asyncio
async def test_log_error_persists_to_firestore(error_logger, mock_firestore):
    """Test that log_error persists error data to Firestore."""
    error = ValueError("Test error")
    context = {'application_id': 'app123', 'agent': 'TestAgent'}
    
    error_id = await error_logger.log_error(
        error=error,
        context=context,
        severity=ErrorSeverity.ERROR
    )
    
    # Verify Firestore collection was called
    mock_firestore.collection.assert_called_with('error_logs')
    
    # Verify add was called (we need to check the call happened)
    collection_mock = mock_firestore.collection.return_value
    assert collection_mock.add.called


@pytest.mark.asyncio
async def test_log_error_includes_all_fields(error_logger, mock_firestore):
    """Test that log entry includes all required fields."""
    error = ValueError("Test error")
    context = {'key': 'value'}
    user_id = 'user123'
    application_id = 'app456'
    
    # Capture the log entry that would be persisted
    captured_entry = None
    
    def capture_add(entry):
        nonlocal captured_entry
        captured_entry = entry
        return (None, None)  # Mock return value
    
    mock_firestore.collection.return_value.add.side_effect = capture_add
    
    error_id = await error_logger.log_error(
        error=error,
        context=context,
        severity=ErrorSeverity.WARNING,
        user_id=user_id,
        application_id=application_id
    )
    
    # Verify the captured entry has all required fields
    assert captured_entry is not None
    assert captured_entry['error_id'] == error_id
    assert captured_entry['error_type'] == 'ValueError'
    assert captured_entry['error_message'] == 'Test error'
    assert 'timestamp' in captured_entry
    assert 'stack_trace' in captured_entry
    assert captured_entry['severity'] == 'warning'
    assert captured_entry['context'] == context
    assert captured_entry['user_id'] == user_id
    assert captured_entry['application_id'] == application_id


@pytest.mark.asyncio
async def test_log_error_handles_firestore_failure(error_logger, mock_firestore):
    """Test that log_error handles Firestore persistence failures gracefully."""
    error = ValueError("Test error")
    
    # Make Firestore add raise an exception
    mock_firestore.collection.return_value.add.side_effect = Exception("Firestore error")
    
    # Should not raise, but return error ID
    error_id = await error_logger.log_error(error)
    
    assert error_id is not None
    assert isinstance(error_id, str)


def test_log_error_sync_generates_unique_id(error_logger, mock_firestore):
    """Test that log_error_sync generates a unique error ID."""
    error = ValueError("Test error")
    
    error_id = error_logger.log_error_sync(error)
    
    assert error_id is not None
    assert isinstance(error_id, str)
    assert len(error_id) > 0


def test_log_error_sync_persists_to_firestore(error_logger, mock_firestore):
    """Test that log_error_sync persists error data to Firestore."""
    error = ValueError("Test error")
    context = {'application_id': 'app123'}
    
    error_id = error_logger.log_error_sync(
        error=error,
        context=context,
        severity=ErrorSeverity.ERROR
    )
    
    # Verify Firestore collection was called
    mock_firestore.collection.assert_called_with('error_logs')
    
    # Verify add was called
    collection_mock = mock_firestore.collection.return_value
    assert collection_mock.add.called


def test_generate_error_id_uniqueness(error_logger):
    """Test that generated error IDs are unique."""
    error_ids = set()
    
    for _ in range(100):
        error_id = error_logger._generate_error_id()
        assert error_id not in error_ids
        error_ids.add(error_id)
    
    assert len(error_ids) == 100


def test_build_log_entry_structure(error_logger):
    """Test that log entry has correct structure."""
    error = ValueError("Test error")
    context = {'key': 'value'}
    error_id = 'test-error-id'
    
    log_entry = error_logger._build_log_entry(
        error_id=error_id,
        error=error,
        context=context,
        severity=ErrorSeverity.ERROR,
        user_id='user123',
        application_id='app456'
    )
    
    # Verify structure
    assert log_entry['error_id'] == error_id
    assert log_entry['error_type'] == 'ValueError'
    assert log_entry['error_message'] == 'Test error'
    assert 'timestamp' in log_entry
    assert 'stack_trace' in log_entry
    assert log_entry['severity'] == 'error'
    assert log_entry['context'] == context
    assert log_entry['user_id'] == 'user123'
    assert log_entry['application_id'] == 'app456'


def test_build_log_entry_without_optional_fields(error_logger):
    """Test that log entry works without optional fields."""
    error = ValueError("Test error")
    error_id = 'test-error-id'
    
    log_entry = error_logger._build_log_entry(
        error_id=error_id,
        error=error,
        context={},
        severity=ErrorSeverity.ERROR,
        user_id=None,
        application_id=None
    )
    
    # Verify optional fields are not present
    assert 'user_id' not in log_entry
    assert 'application_id' not in log_entry
    
    # Verify required fields are present
    assert log_entry['error_id'] == error_id
    assert log_entry['error_type'] == 'ValueError'
    assert log_entry['error_message'] == 'Test error'


def test_build_log_entry_with_different_severities(error_logger):
    """Test log entry creation with different severity levels."""
    error = ValueError("Test error")
    error_id = 'test-error-id'
    
    for severity in ErrorSeverity:
        log_entry = error_logger._build_log_entry(
            error_id=error_id,
            error=error,
            context={},
            severity=severity,
            user_id=None,
            application_id=None
        )
        
        assert log_entry['severity'] == severity.value


@pytest.mark.asyncio
async def test_get_error_by_id(error_logger, mock_firestore):
    """Test retrieving an error by its ID."""
    error_id = 'test-error-id'
    expected_error = {
        'error_id': error_id,
        'error_type': 'ValueError',
        'error_message': 'Test error'
    }
    
    # Mock Firestore query
    mock_doc = Mock()
    mock_doc.to_dict.return_value = expected_error
    
    mock_query = Mock()
    mock_query.stream.return_value = [mock_doc]
    
    mock_where = Mock()
    mock_where.limit.return_value = mock_query
    
    mock_collection = Mock()
    mock_collection.where.return_value = mock_where
    
    mock_firestore.collection.return_value = mock_collection
    
    # Retrieve error
    result = await error_logger.get_error_by_id(error_id)
    
    assert result == expected_error
    mock_collection.where.assert_called_with('error_id', '==', error_id)


@pytest.mark.asyncio
async def test_get_error_by_id_not_found(error_logger, mock_firestore):
    """Test retrieving a non-existent error by ID."""
    error_id = 'non-existent-id'
    
    # Mock Firestore query with no results
    mock_query = Mock()
    mock_query.stream.return_value = []
    
    mock_where = Mock()
    mock_where.limit.return_value = mock_query
    
    mock_collection = Mock()
    mock_collection.where.return_value = mock_where
    
    mock_firestore.collection.return_value = mock_collection
    
    # Retrieve error
    result = await error_logger.get_error_by_id(error_id)
    
    assert result is None


@pytest.mark.asyncio
async def test_get_errors_by_application(error_logger, mock_firestore):
    """Test retrieving errors for a specific application."""
    application_id = 'app123'
    expected_errors = [
        {'error_id': 'err1', 'application_id': application_id},
        {'error_id': 'err2', 'application_id': application_id}
    ]
    
    # Mock Firestore query
    mock_docs = [Mock(), Mock()]
    mock_docs[0].to_dict.return_value = expected_errors[0]
    mock_docs[1].to_dict.return_value = expected_errors[1]
    
    mock_query = Mock()
    mock_query.stream.return_value = mock_docs
    
    mock_limit = Mock()
    mock_limit.limit.return_value = mock_query
    
    mock_order = Mock()
    mock_order.order_by.return_value = mock_limit
    
    mock_collection = Mock()
    mock_collection.where.return_value = mock_order
    
    mock_firestore.collection.return_value = mock_collection
    
    # Retrieve errors
    result = await error_logger.get_errors_by_application(application_id)
    
    assert len(result) == 2
    assert result == expected_errors
    mock_collection.where.assert_called_with('application_id', '==', application_id)


@pytest.mark.asyncio
async def test_get_errors_by_severity(error_logger, mock_firestore):
    """Test retrieving errors by severity level."""
    severity = ErrorSeverity.CRITICAL
    expected_errors = [
        {'error_id': 'err1', 'severity': 'critical'},
        {'error_id': 'err2', 'severity': 'critical'}
    ]
    
    # Mock Firestore query
    mock_docs = [Mock(), Mock()]
    mock_docs[0].to_dict.return_value = expected_errors[0]
    mock_docs[1].to_dict.return_value = expected_errors[1]
    
    mock_query = Mock()
    mock_query.stream.return_value = mock_docs
    
    mock_limit = Mock()
    mock_limit.limit.return_value = mock_query
    
    mock_order = Mock()
    mock_order.order_by.return_value = mock_limit
    
    mock_collection = Mock()
    mock_collection.where.return_value = mock_order
    
    mock_firestore.collection.return_value = mock_collection
    
    # Retrieve errors
    result = await error_logger.get_errors_by_severity(severity)
    
    assert len(result) == 2
    assert result == expected_errors
    mock_collection.where.assert_called_with('severity', '==', 'critical')


def test_error_severity_enum_values():
    """Test that ErrorSeverity enum has correct values."""
    assert ErrorSeverity.DEBUG.value == "debug"
    assert ErrorSeverity.INFO.value == "info"
    assert ErrorSeverity.WARNING.value == "warning"
    assert ErrorSeverity.ERROR.value == "error"
    assert ErrorSeverity.CRITICAL.value == "critical"


@pytest.mark.asyncio
async def test_log_error_with_complex_context(error_logger, mock_firestore):
    """Test logging error with complex context data."""
    error = ValueError("Test error")
    context = {
        'application_id': 'app123',
        'agent': 'DocumentIntelligence',
        'document_id': 'doc456',
        'metadata': {
            'file_type': 'pdf',
            'page_count': 10
        },
        'processing_stage': 'extraction'
    }
    
    captured_entry = None
    
    def capture_add(entry):
        nonlocal captured_entry
        captured_entry = entry
        return (None, None)
    
    mock_firestore.collection.return_value.add.side_effect = capture_add
    
    error_id = await error_logger.log_error(error=error, context=context)
    
    assert captured_entry is not None
    assert captured_entry['context'] == context
    assert captured_entry['context']['metadata']['file_type'] == 'pdf'


@pytest.mark.asyncio
async def test_log_error_captures_stack_trace(error_logger, mock_firestore):
    """Test that log_error captures the stack trace."""
    captured_entry = None
    
    def capture_add(entry):
        nonlocal captured_entry
        captured_entry = entry
        return (None, None)
    
    mock_firestore.collection.return_value.add.side_effect = capture_add
    
    try:
        # Create a real exception with stack trace
        raise ValueError("Test error with stack trace")
    except ValueError as e:
        error_id = await error_logger.log_error(e)
    
    assert captured_entry is not None
    assert 'stack_trace' in captured_entry
    assert len(captured_entry['stack_trace']) > 0
    assert 'ValueError' in captured_entry['stack_trace']
    assert 'Test error with stack trace' in captured_entry['stack_trace']
