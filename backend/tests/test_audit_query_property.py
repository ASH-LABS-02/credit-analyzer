"""
Property-Based Tests for Audit Query and Export

This module contains property-based tests for audit log querying and export
functionality, validating that filtering and export capabilities work correctly
across various input combinations.

Requirements: 17.4
Property 38: Audit Query and Export
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
import json
import csv
import io
from unittest.mock import Mock, AsyncMock, MagicMock

from app.core.audit_logger import AuditLogger, AuditActionType
from app.models.domain import ApplicationStatus


# Strategy for generating audit action types
audit_action_types = st.sampled_from([
    AuditActionType.STATE_TRANSITION,
    AuditActionType.USER_ACTION,
    AuditActionType.AI_DECISION,
    AuditActionType.DOCUMENT_UPLOAD,
    AuditActionType.DOCUMENT_DELETE,
    AuditActionType.CAM_GENERATION,
    AuditActionType.MONITORING_ALERT
])


# Strategy for generating resource types
resource_types = st.sampled_from([
    'application',
    'document',
    'cam',
    'monitoring_alert'
])


# Strategy for generating user IDs
user_ids = st.sampled_from(['user1', 'user2', 'user3', 'system'])


# Strategy for generating resource IDs
resource_ids = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789',
    min_size=5,
    max_size=20
)


# Strategy for generating timestamps
def generate_timestamp():
    """Generate a timestamp within the last 30 days."""
    base = datetime.utcnow()
    days_ago = st.integers(min_value=0, max_value=30)
    return st.builds(
        lambda d: base - timedelta(days=d),
        days_ago
    )


def create_mock_firestore():
    """Create a mock Firestore client."""
    mock_db = Mock()
    mock_collection = Mock()
    mock_db.collection.return_value = mock_collection
    return mock_db


def create_audit_logger():
    """Create an AuditLogger instance with mocked Firestore."""
    mock_firestore = create_mock_firestore()
    return AuditLogger(mock_firestore), mock_firestore


# Feature: intelli-credit-platform, Property 38: Audit Query and Export
@given(
    action_type=audit_action_types,
    resource_type=resource_types,
    user_id=user_ids,
    num_records=st.integers(min_value=1, max_value=20)
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_query_audit_logs_filtering(
    action_type,
    resource_type,
    user_id,
    num_records
):
    """
    **Validates: Requirements 17.4**
    
    Property 38: Audit Query and Export
    
    For any audit log query with filtering criteria, the system should return
    matching audit records.
    
    This test verifies that:
    1. Query filters are correctly applied
    2. Results match the specified criteria
    3. Pagination parameters are respected
    4. Total count is accurate
    """
    # Create audit logger with mock
    audit_logger, mock_firestore = create_audit_logger()
    
    # Generate mock audit records
    mock_records = []
    for i in range(num_records):
        record = {
            'audit_id': f'audit_{i}',
            'timestamp': (datetime.utcnow() - timedelta(days=i)).isoformat(),
            'timestamp_obj': datetime.utcnow() - timedelta(days=i),
            'action_type': action_type.value,
            'resource_type': resource_type,
            'resource_id': f'resource_{i}',
            'user_id': user_id,
            'details': {'test': f'detail_{i}'},
            'immutable': True
        }
        mock_records.append(record)
    
    # Mock Firestore query chain
    mock_query = Mock()
    mock_query.where.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    
    # Create mock documents
    mock_docs = [Mock(to_dict=Mock(return_value=record)) for record in mock_records]
    mock_query.stream.return_value = mock_docs
    
    mock_firestore.collection.return_value = mock_query
    
    # Query with filters
    filters = {
        'action_type': action_type.value,
        'resource_type': resource_type,
        'user_id': user_id
    }
    
    results = await audit_logger.query_audit_logs(
        filters=filters,
        limit=10,
        offset=0
    )
    
    # Verify results structure
    assert 'records' in results
    assert 'total_count' in results
    assert 'limit' in results
    assert 'offset' in results
    assert 'has_more' in results
    
    # Verify pagination parameters
    assert results['limit'] == 10
    assert results['offset'] == 0
    
    # Verify total count
    assert results['total_count'] == num_records
    
    # Verify has_more flag
    if num_records > 10:
        assert results['has_more'] is True
    else:
        assert results['has_more'] is False
    
    # Verify records match filters
    for record in results['records']:
        assert record['action_type'] == action_type.value
        assert record['resource_type'] == resource_type
        assert record['user_id'] == user_id


# Feature: intelli-credit-platform, Property 38: Audit Query and Export
@given(
    num_records=st.integers(min_value=1, max_value=50),
    limit=st.integers(min_value=5, max_value=20),
    offset=st.integers(min_value=0, max_value=10)
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_query_audit_logs_pagination(
    num_records,
    limit,
    offset
):
    """
    **Validates: Requirements 17.4**
    
    Property 38: Audit Query and Export
    
    For any audit log query with pagination parameters, the system should
    correctly apply limit and offset to return the appropriate subset of records.
    
    This test verifies that:
    1. Pagination limit is respected
    2. Offset correctly skips records
    3. has_more flag is accurate
    """
    # Create audit logger with mock
    audit_logger, mock_firestore = create_audit_logger()
    
    # Generate mock audit records
    mock_records = []
    for i in range(num_records):
        record = {
            'audit_id': f'audit_{i}',
            'timestamp': (datetime.utcnow() - timedelta(hours=i)).isoformat(),
            'timestamp_obj': datetime.utcnow() - timedelta(hours=i),
            'action_type': 'user_action',
            'resource_type': 'application',
            'resource_id': f'app_{i}',
            'user_id': 'user1',
            'details': {},
            'immutable': True
        }
        mock_records.append(record)
    
    # Mock Firestore query
    mock_query = Mock()
    mock_query.where.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    
    mock_docs = [Mock(to_dict=Mock(return_value=record)) for record in mock_records]
    mock_query.stream.return_value = mock_docs
    
    mock_firestore.collection.return_value = mock_query
    
    # Query with pagination
    results = await audit_logger.query_audit_logs(
        limit=limit,
        offset=offset
    )
    
    # Verify pagination
    assert results['limit'] == limit
    assert results['offset'] == offset
    assert results['total_count'] == num_records
    
    # Verify returned records count
    expected_count = min(limit, max(0, num_records - offset))
    assert len(results['records']) == expected_count
    
    # Verify has_more flag
    expected_has_more = (offset + limit) < num_records
    assert results['has_more'] == expected_has_more


# Feature: intelli-credit-platform, Property 38: Audit Query and Export
@given(
    num_records=st.integers(min_value=1, max_value=30),
    export_format=st.sampled_from(['json', 'csv'])
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_export_audit_logs_format(
    num_records,
    export_format
):
    """
    **Validates: Requirements 17.4**
    
    Property 38: Audit Query and Export
    
    For any audit log export request, the system should support export
    functionality in the specified format (JSON or CSV).
    
    This test verifies that:
    1. Export produces valid output in the requested format
    2. All records are included in the export
    3. JSON exports are valid JSON
    4. CSV exports are valid CSV with proper headers
    """
    # Create audit logger with mock
    audit_logger, mock_firestore = create_audit_logger()
    
    # Generate mock audit records
    mock_records = []
    for i in range(num_records):
        record = {
            'audit_id': f'audit_{i}',
            'timestamp': (datetime.utcnow() - timedelta(minutes=i)).isoformat(),
            'timestamp_obj': datetime.utcnow() - timedelta(minutes=i),
            'action_type': 'state_transition',
            'resource_type': 'application',
            'resource_id': f'app_{i}',
            'user_id': 'user1',
            'details': {'old_state': 'pending', 'new_state': 'processing'},
            'immutable': True
        }
        mock_records.append(record)
    
    # Mock Firestore query
    mock_query = Mock()
    mock_query.where.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    
    mock_docs = [Mock(to_dict=Mock(return_value=record)) for record in mock_records]
    mock_query.stream.return_value = mock_docs
    
    mock_firestore.collection.return_value = mock_query
    
    # Export audit logs
    export_data = await audit_logger.export_audit_logs(
        format=export_format,
        limit=num_records
    )
    
    # Verify export is not empty
    assert export_data is not None
    assert len(export_data) > 0
    
    if export_format == 'json':
        # Verify valid JSON
        parsed = json.loads(export_data)
        assert isinstance(parsed, list)
        assert len(parsed) == num_records
        
        # Verify each record has required fields
        for record in parsed:
            assert 'audit_id' in record
            assert 'timestamp' in record
            assert 'action_type' in record
            assert 'resource_type' in record
            assert 'resource_id' in record
            assert 'user_id' in record
            assert 'details' in record
    
    elif export_format == 'csv':
        # Verify valid CSV
        csv_reader = csv.DictReader(io.StringIO(export_data))
        rows = list(csv_reader)
        
        assert len(rows) == num_records
        
        # Verify CSV headers
        expected_headers = [
            'audit_id',
            'timestamp',
            'action_type',
            'resource_type',
            'resource_id',
            'user_id',
            'details'
        ]
        assert csv_reader.fieldnames == expected_headers
        
        # Verify each row has all fields
        for row in rows:
            for header in expected_headers:
                assert header in row


# Feature: intelli-credit-platform, Property 38: Audit Query and Export
@given(
    days_range=st.integers(min_value=1, max_value=30)
)
@settings(max_examples=100, deadline=None)
@pytest.mark.asyncio
async def test_query_audit_logs_date_range(
    days_range
):
    """
    **Validates: Requirements 17.4**
    
    Property 38: Audit Query and Export
    
    For any audit log query with date range filters, the system should return
    only records within the specified date range.
    
    This test verifies that:
    1. Start date filter is correctly applied
    2. End date filter is correctly applied
    3. Records outside the date range are excluded
    """
    # Create audit logger with mock
    audit_logger, mock_firestore = create_audit_logger()
    
    # Generate mock audit records spanning a date range
    base_date = datetime.utcnow()
    mock_records = []
    
    for i in range(days_range * 2):
        record = {
            'audit_id': f'audit_{i}',
            'timestamp': (base_date - timedelta(days=i)).isoformat(),
            'timestamp_obj': base_date - timedelta(days=i),
            'action_type': 'user_action',
            'resource_type': 'application',
            'resource_id': f'app_{i}',
            'user_id': 'user1',
            'details': {},
            'immutable': True
        }
        mock_records.append(record)
    
    # Mock Firestore query
    mock_query = Mock()
    mock_query.where.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    
    # Filter records based on date range (simulate Firestore behavior)
    start_date = base_date - timedelta(days=days_range)
    end_date = base_date
    
    filtered_records = [
        r for r in mock_records
        if start_date <= r['timestamp_obj'] <= end_date
    ]
    
    mock_docs = [Mock(to_dict=Mock(return_value=record)) for record in filtered_records]
    mock_query.stream.return_value = mock_docs
    
    mock_firestore.collection.return_value = mock_query
    
    # Query with date range
    results = await audit_logger.query_audit_logs(
        start_date=start_date,
        end_date=end_date,
        limit=100
    )
    
    # Verify all returned records are within date range
    for record in results['records']:
        record_date = datetime.fromisoformat(record['timestamp'])
        assert start_date <= record_date <= end_date
    
    # Verify count matches filtered records
    assert results['total_count'] == len(filtered_records)


# Feature: intelli-credit-platform, Property 38: Audit Query and Export
@pytest.mark.asyncio
async def test_export_unsupported_format():
    """
    **Validates: Requirements 17.4**
    
    Property 38: Audit Query and Export
    
    For any audit log export request with an unsupported format, the system
    should raise a ValueError with a descriptive error message.
    
    This test verifies that:
    1. Unsupported formats are rejected
    2. Appropriate error message is provided
    """
    # Create audit logger with mock
    audit_logger, mock_firestore = create_audit_logger()
    
    # Mock Firestore query
    mock_query = Mock()
    mock_query.where.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.stream.return_value = []
    
    mock_firestore.collection.return_value = mock_query
    
    # Attempt to export with unsupported format
    with pytest.raises(ValueError) as exc_info:
        await audit_logger.export_audit_logs(format='xml')
    
    # Verify error message
    assert 'Unsupported export format' in str(exc_info.value)
    assert 'xml' in str(exc_info.value)


# Feature: intelli-credit-platform, Property 38: Audit Query and Export
@given(
    num_records=st.integers(min_value=0, max_value=5)
)
@settings(max_examples=50, deadline=None)
@pytest.mark.asyncio
async def test_query_empty_results(
    num_records
):
    """
    **Validates: Requirements 17.4**
    
    Property 38: Audit Query and Export
    
    For any audit log query that matches no records, the system should return
    an empty result set with correct metadata.
    
    This test verifies that:
    1. Empty queries return valid structure
    2. Total count is zero
    3. has_more is False
    4. Records list is empty
    """
    # Create audit logger with mock
    audit_logger, mock_firestore = create_audit_logger()
    
    # Mock Firestore query with no results
    mock_query = Mock()
    mock_query.where.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.stream.return_value = []
    
    mock_firestore.collection.return_value = mock_query
    
    # Query with filters that match nothing
    results = await audit_logger.query_audit_logs(
        filters={'resource_id': 'nonexistent'},
        limit=10
    )
    
    # Verify empty results structure
    assert results['records'] == []
    assert results['total_count'] == 0
    assert results['has_more'] is False
    assert results['limit'] == 10
    assert results['offset'] == 0
