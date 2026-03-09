"""
Property-based tests for ErrorLogger class.

Feature: intelli-credit-platform
Property 30: Agent Failure Recovery (Error Logging Component)

Validates: Requirements 15.5
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import MagicMock
from datetime import datetime
import uuid

from app.core.error_logger import ErrorLogger, ErrorSeverity


# Test data strategies
error_message_strategy = st.text(min_size=1, max_size=200)
context_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=50),
    values=st.one_of(st.text(max_size=100), st.integers(), st.booleans()),
    min_size=0,
    max_size=10
)
severity_strategy = st.sampled_from(list(ErrorSeverity))


def create_mock_firestore():
    """Create a mock Firestore client."""
    mock_db = MagicMock()
    mock_collection = MagicMock()
    mock_db.collection.return_value = mock_collection
    return mock_db



class TestProperty30ErrorLoggingUniqueIDs:
    """
    Property: Unique Error ID Generation
    
    **Validates: Requirements 15.5**
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        error_message=error_message_strategy,
        context=context_strategy,
        severity=severity_strategy
    )
    async def test_error_logger_generates_unique_ids(
        self,
        error_message: str,
        context: dict,
        severity: ErrorSeverity
    ):
        """
        Property: For any error logged, a unique error ID is generated.
        """
        assume(len(error_message.strip()) > 0)
        
        mock_db = create_mock_firestore()
        error_logger = ErrorLogger(mock_db)
        
        error = ValueError(error_message)
        
        error_id_1 = await error_logger.log_error(
            error=error,
            context=context,
            severity=severity
        )
        
        error_id_2 = await error_logger.log_error(
            error=error,
            context=context,
            severity=severity
        )
        
        # Verify both IDs are valid UUIDs
        uuid.UUID(error_id_1)
        uuid.UUID(error_id_2)
        
        # Verify IDs are unique
        assert error_id_1 != error_id_2



class TestProperty30ErrorLoggingStructuredData:
    """
    Property: Structured Log Entry Completeness
    
    **Validates: Requirements 15.5**
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        error_message=error_message_strategy,
        context=context_strategy,
        severity=severity_strategy
    )
    async def test_error_logger_creates_complete_log_entry(
        self,
        error_message: str,
        context: dict,
        severity: ErrorSeverity
    ):
        """
        Property: For any error logged, the log entry contains all required fields.
        """
        assume(len(error_message.strip()) > 0)
        
        mock_db = create_mock_firestore()
        
        captured_entry = None
        
        def capture_add(entry):
            nonlocal captured_entry
            captured_entry = entry
            return ('doc_id', None)
        
        mock_db.collection.return_value.add = capture_add
        
        error_logger = ErrorLogger(mock_db)
        
        error = ValueError(error_message)
        error_id = await error_logger.log_error(
            error=error,
            context=context,
            severity=severity
        )
        
        assert captured_entry is not None
        
        # Verify all required fields
        required_fields = [
            'error_id',
            'timestamp',
            'error_type',
            'error_message',
            'stack_trace',
            'severity',
            'context'
        ]
        
        for field in required_fields:
            assert field in captured_entry, f"Missing required field: {field}"
        
        # Verify field values
        assert captured_entry['error_id'] == error_id
        assert captured_entry['error_type'] == 'ValueError'
        assert captured_entry['error_message'] == error_message
        assert captured_entry['severity'] == severity.value
        assert captured_entry['context'] == context
        
        # Verify timestamp is valid ISO format
        datetime.fromisoformat(captured_entry['timestamp'])
        
        # Verify stack trace is present
        assert isinstance(captured_entry['stack_trace'], str)
        assert len(captured_entry['stack_trace']) > 0



class TestProperty30ErrorLoggingContextPreservation:
    """
    Property: Context Data Preservation
    
    **Validates: Requirements 15.5**
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        error_message=error_message_strategy,
        context=context_strategy
    )
    async def test_error_logger_preserves_context_data(
        self,
        error_message: str,
        context: dict
    ):
        """
        Property: For any error logged with context, the context data is preserved exactly.
        """
        assume(len(error_message.strip()) > 0)
        
        mock_db = create_mock_firestore()
        
        captured_entry = None
        
        def capture_add(entry):
            nonlocal captured_entry
            captured_entry = entry
            return ('doc_id', None)
        
        mock_db.collection.return_value.add = capture_add
        
        error_logger = ErrorLogger(mock_db)
        
        error = ValueError(error_message)
        await error_logger.log_error(error=error, context=context)
        
        assert captured_entry is not None
        assert 'context' in captured_entry
        assert captured_entry['context'] == context



class TestProperty30ErrorLoggingRobustness:
    """
    Property: Error Logging Robustness
    
    **Validates: Requirements 15.5**
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        error_message=error_message_strategy,
        context=context_strategy
    )
    async def test_error_logger_handles_firestore_failures_gracefully(
        self,
        error_message: str,
        context: dict
    ):
        """
        Property: For any error logged, if Firestore persistence fails,
        the ErrorLogger still returns a valid error ID without raising an exception.
        """
        assume(len(error_message.strip()) > 0)
        
        mock_db = create_mock_firestore()
        mock_db.collection.return_value.add.side_effect = Exception("Firestore connection failed")
        
        error_logger = ErrorLogger(mock_db)
        
        error = ValueError(error_message)
        error_id = await error_logger.log_error(error=error, context=context)
        
        # Verify error ID is still returned
        assert error_id is not None
        assert isinstance(error_id, str)
        assert len(error_id) > 0
        
        # Verify it's a valid UUID
        uuid.UUID(error_id)
