"""
Integration Tests for Audit Query and Export

This module contains integration tests that verify the audit query and export
functionality works correctly with the full AuditLogger implementation.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
import json
import csv
import io

from app.core.audit_logger import AuditLogger, AuditActionType
from app.models.domain import ApplicationStatus


@pytest.fixture
def mock_firestore():
    """Create a mock Firestore client for integration testing."""
    mock_db = Mock()
    return mock_db


@pytest.fixture
def audit_logger(mock_firestore):
    """Create an AuditLogger instance."""
    return AuditLogger(mock_firestore)


@pytest.mark.asyncio
async def test_query_and_export_workflow(audit_logger, mock_firestore):
    """
    Integration test for the complete query and export workflow.
    
    This test verifies that:
    1. Audit logs can be queried with various filters
    2. Results can be exported in JSON format
    3. Results can be exported in CSV format
    4. The workflow handles edge cases correctly
    """
    # Create sample audit records
    sample_records = [
        {
            'audit_id': 'audit_1',
            'timestamp': (datetime.utcnow() - timedelta(days=1)).isoformat(),
            'timestamp_obj': datetime.utcnow() - timedelta(days=1),
            'action_type': 'state_transition',
            'resource_type': 'application',
            'resource_id': 'app_123',
            'user_id': 'user_1',
            'details': {'old_state': 'pending', 'new_state': 'processing'},
            'immutable': True
        },
        {
            'audit_id': 'audit_2',
            'timestamp': (datetime.utcnow() - timedelta(hours=12)).isoformat(),
            'timestamp_obj': datetime.utcnow() - timedelta(hours=12),
            'action_type': 'ai_decision',
            'resource_type': 'application',
            'resource_id': 'app_123',
            'user_id': 'system',
            'details': {
                'agent_name': 'RiskScoringAgent',
                'decision': 'approve',
                'reasoning': 'Strong financials'
            },
            'immutable': True
        },
        {
            'audit_id': 'audit_3',
            'timestamp': (datetime.utcnow() - timedelta(hours=6)).isoformat(),
            'timestamp_obj': datetime.utcnow() - timedelta(hours=6),
            'action_type': 'document_upload',
            'resource_type': 'document',
            'resource_id': 'doc_456',
            'user_id': 'user_1',
            'details': {'filename': 'financials.pdf', 'file_type': 'pdf'},
            'immutable': True
        }
    ]
    
    # Mock Firestore query
    mock_query = Mock()
    mock_query.where.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    
    mock_docs = [Mock(to_dict=Mock(return_value=record)) for record in sample_records]
    mock_query.stream.return_value = mock_docs
    
    mock_firestore.collection.return_value = mock_query
    
    # Test 1: Query all records
    results = await audit_logger.query_audit_logs(limit=10)
    assert results['total_count'] == 3
    assert len(results['records']) == 3
    
    # Test 2: Query with filter
    results = await audit_logger.query_audit_logs(
        filters={'action_type': 'state_transition'},
        limit=10
    )
    assert 'records' in results
    
    # Test 3: Export as JSON
    json_export = await audit_logger.export_audit_logs(format='json', limit=10)
    parsed_json = json.loads(json_export)
    assert isinstance(parsed_json, list)
    assert len(parsed_json) == 3
    
    # Verify JSON structure
    for record in parsed_json:
        assert 'audit_id' in record
        assert 'timestamp' in record
        assert 'action_type' in record
        assert 'resource_type' in record
        assert 'user_id' in record
    
    # Test 4: Export as CSV
    csv_export = await audit_logger.export_audit_logs(format='csv', limit=10)
    csv_reader = csv.DictReader(io.StringIO(csv_export))
    csv_rows = list(csv_reader)
    
    assert len(csv_rows) == 3
    
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
    
    # Verify CSV content
    assert csv_rows[0]['audit_id'] == 'audit_1'
    assert csv_rows[0]['action_type'] == 'state_transition'
    assert csv_rows[1]['audit_id'] == 'audit_2'
    assert csv_rows[1]['action_type'] == 'ai_decision'


@pytest.mark.asyncio
async def test_pagination_workflow(audit_logger, mock_firestore):
    """
    Integration test for pagination workflow.
    
    This test verifies that pagination works correctly across multiple queries.
    """
    # Create 25 sample records
    sample_records = []
    for i in range(25):
        record = {
            'audit_id': f'audit_{i}',
            'timestamp': (datetime.utcnow() - timedelta(hours=i)).isoformat(),
            'timestamp_obj': datetime.utcnow() - timedelta(hours=i),
            'action_type': 'user_action',
            'resource_type': 'application',
            'resource_id': f'app_{i}',
            'user_id': 'user_1',
            'details': {},
            'immutable': True
        }
        sample_records.append(record)
    
    # Mock Firestore query
    mock_query = Mock()
    mock_query.where.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    
    mock_docs = [Mock(to_dict=Mock(return_value=record)) for record in sample_records]
    mock_query.stream.return_value = mock_docs
    
    mock_firestore.collection.return_value = mock_query
    
    # Query first page
    page1 = await audit_logger.query_audit_logs(limit=10, offset=0)
    assert page1['total_count'] == 25
    assert len(page1['records']) == 10
    assert page1['has_more'] is True
    
    # Query second page
    page2 = await audit_logger.query_audit_logs(limit=10, offset=10)
    assert page2['total_count'] == 25
    assert len(page2['records']) == 10
    assert page2['has_more'] is True
    
    # Query third page
    page3 = await audit_logger.query_audit_logs(limit=10, offset=20)
    assert page3['total_count'] == 25
    assert len(page3['records']) == 5
    assert page3['has_more'] is False


@pytest.mark.asyncio
async def test_date_range_filtering(audit_logger, mock_firestore):
    """
    Integration test for date range filtering.
    
    This test verifies that date range filters work correctly.
    """
    base_date = datetime.utcnow()
    
    # Create records spanning 10 days
    sample_records = []
    for i in range(10):
        record = {
            'audit_id': f'audit_{i}',
            'timestamp': (base_date - timedelta(days=i)).isoformat(),
            'timestamp_obj': base_date - timedelta(days=i),
            'action_type': 'user_action',
            'resource_type': 'application',
            'resource_id': f'app_{i}',
            'user_id': 'user_1',
            'details': {},
            'immutable': True
        }
        sample_records.append(record)
    
    # Filter to last 5 days
    start_date = base_date - timedelta(days=5)
    filtered_records = [
        r for r in sample_records
        if r['timestamp_obj'] >= start_date
    ]
    
    # Mock Firestore query
    mock_query = Mock()
    mock_query.where.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    
    mock_docs = [Mock(to_dict=Mock(return_value=record)) for record in filtered_records]
    mock_query.stream.return_value = mock_docs
    
    mock_firestore.collection.return_value = mock_query
    
    # Query with date range
    results = await audit_logger.query_audit_logs(
        start_date=start_date,
        limit=100
    )
    
    # Verify results
    assert results['total_count'] == len(filtered_records)
    
    # Verify all records are within date range
    for record in results['records']:
        record_date = datetime.fromisoformat(record['timestamp'])
        assert record_date >= start_date


@pytest.mark.asyncio
async def test_empty_export(audit_logger, mock_firestore):
    """
    Integration test for exporting empty results.
    
    This test verifies that exports handle empty result sets correctly.
    """
    # Mock Firestore query with no results
    mock_query = Mock()
    mock_query.where.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.stream.return_value = []
    
    mock_firestore.collection.return_value = mock_query
    
    # Export as JSON
    json_export = await audit_logger.export_audit_logs(format='json')
    parsed_json = json.loads(json_export)
    assert parsed_json == []
    
    # Export as CSV
    csv_export = await audit_logger.export_audit_logs(format='csv')
    assert csv_export == ""
