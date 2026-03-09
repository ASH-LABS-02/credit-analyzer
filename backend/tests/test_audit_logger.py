"""
Unit tests for AuditLogger

Tests the audit logging functionality including state transition logging,
user action tracking, AI decision logging, and audit record immutability.

Requirements: 9.5, 17.1, 17.3
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from app.core.audit_logger import AuditLogger, AuditActionType
from app.models.domain import ApplicationStatus


@pytest.fixture
def mock_firestore():
    """Create a mock Firestore client."""
    mock_db = Mock()
    mock_collection = Mock()
    mock_document = Mock()
    
    # Set up the mock chain
    mock_db.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document
    mock_document.set = Mock()
    mock_document.get = Mock()
    
    # Mock query methods
    mock_collection.where.return_value = mock_collection
    mock_collection.order_by.return_value = mock_collection
    mock_collection.limit.return_value = mock_collection
    mock_collection.stream.return_value = []
    
    return mock_db


@pytest.fixture
def audit_logger(mock_firestore):
    """Create an AuditLogger instance with mocked Firestore."""
    return AuditLogger(mock_firestore)


class TestAuditLoggerStateTransitions:
    """Test audit logging for state transitions."""
    
    @pytest.mark.asyncio
    async def test_log_state_transition_creates_audit_record(self, audit_logger, mock_firestore):
        """Test that state transitions are logged with all required fields."""
        audit_id = await audit_logger.log_state_transition(
            application_id='app123',
            old_state=ApplicationStatus.PENDING,
            new_state=ApplicationStatus.PROCESSING,
            user_id='user456',
            reason='Documents uploaded'
        )
        
        # Verify audit ID was generated
        assert audit_id is not None
        assert isinstance(audit_id, str)
        
        # Verify Firestore was called
        mock_firestore.collection.assert_called_with('audit_logs')
    
    @pytest.mark.asyncio
    async def test_log_state_transition_with_system_user(self, audit_logger):
        """Test that state transitions without user_id default to 'system'."""
        audit_id = await audit_logger.log_state_transition(
            application_id='app123',
            old_state=ApplicationStatus.PROCESSING,
            new_state=ApplicationStatus.ANALYSIS_COMPLETE,
            reason='Analysis completed'
        )
        
        assert audit_id is not None
    
    @pytest.mark.asyncio
    async def test_log_state_transition_with_additional_context(self, audit_logger):
        """Test that additional context is included in audit record."""
        audit_id = await audit_logger.log_state_transition(
            application_id='app123',
            old_state=ApplicationStatus.ANALYSIS_COMPLETE,
            new_state=ApplicationStatus.APPROVED,
            user_id='user456',
            reason='Credit score above threshold',
            additional_context={'credit_score': 85, 'recommendation': 'approve'}
        )
        
        assert audit_id is not None


class TestAuditLoggerUserActions:
    """Test audit logging for user actions."""
    
    @pytest.mark.asyncio
    async def test_log_user_action_create(self, audit_logger):
        """Test logging user action for creating a resource."""
        audit_id = await audit_logger.log_user_action(
            action='create',
            resource_type='application',
            resource_id='app123',
            user_id='user456',
            details={'company_name': 'Acme Corp', 'loan_amount': 1000000}
        )
        
        assert audit_id is not None
    
    @pytest.mark.asyncio
    async def test_log_user_action_update(self, audit_logger):
        """Test logging user action for updating a resource."""
        audit_id = await audit_logger.log_user_action(
            action='update',
            resource_type='application',
            resource_id='app123',
            user_id='user456',
            details={'field': 'loan_amount', 'old_value': 1000000, 'new_value': 1500000}
        )
        
        assert audit_id is not None
    
    @pytest.mark.asyncio
    async def test_log_user_action_delete(self, audit_logger):
        """Test logging user action for deleting a resource."""
        audit_id = await audit_logger.log_user_action(
            action='delete',
            resource_type='document',
            resource_id='doc789',
            user_id='user456'
        )
        
        assert audit_id is not None


class TestAuditLoggerAIDecisions:
    """Test audit logging for AI decisions."""
    
    @pytest.mark.asyncio
    async def test_log_ai_decision(self, audit_logger):
        """Test logging AI agent decisions with reasoning and data sources."""
        audit_id = await audit_logger.log_ai_decision(
            agent_name='RiskScoringAgent',
            application_id='app123',
            decision='approve_with_conditions',
            reasoning='Strong financials but high industry risk',
            data_sources=['financial_analysis', 'industry_report', 'promoter_analysis']
        )
        
        assert audit_id is not None
    
    @pytest.mark.asyncio
    async def test_log_ai_decision_with_additional_details(self, audit_logger):
        """Test logging AI decision with additional details."""
        audit_id = await audit_logger.log_ai_decision(
            agent_name='ForecastingAgent',
            application_id='app123',
            decision='forecast_generated',
            reasoning='Based on 3-year historical trends',
            data_sources=['financial_statements'],
            additional_details={
                'forecast_period': '3_years',
                'confidence_level': 0.85,
                'methodology': 'time_series_analysis'
            }
        )
        
        assert audit_id is not None


class TestAuditLoggerDocumentActions:
    """Test audit logging for document actions."""
    
    @pytest.mark.asyncio
    async def test_log_document_upload(self, audit_logger):
        """Test logging document upload action."""
        audit_id = await audit_logger.log_document_action(
            action='upload',
            application_id='app123',
            document_id='doc456',
            user_id='user789',
            document_details={'filename': 'financials.pdf', 'file_type': 'pdf', 'size': 1024000}
        )
        
        assert audit_id is not None
    
    @pytest.mark.asyncio
    async def test_log_document_delete(self, audit_logger):
        """Test logging document deletion action."""
        audit_id = await audit_logger.log_document_action(
            action='delete',
            application_id='app123',
            document_id='doc456',
            user_id='user789',
            document_details={'filename': 'old_financials.pdf'}
        )
        
        assert audit_id is not None


class TestAuditLoggerCAMGeneration:
    """Test audit logging for CAM generation."""
    
    @pytest.mark.asyncio
    async def test_log_cam_generation(self, audit_logger):
        """Test logging CAM report generation."""
        audit_id = await audit_logger.log_cam_generation(
            application_id='app123',
            cam_version=1,
            user_id='user456',
            generation_details={'format': 'pdf', 'sections': 5}
        )
        
        assert audit_id is not None
    
    @pytest.mark.asyncio
    async def test_log_cam_generation_system_user(self, audit_logger):
        """Test logging CAM generation without user_id defaults to 'system'."""
        audit_id = await audit_logger.log_cam_generation(
            application_id='app123',
            cam_version=2
        )
        
        assert audit_id is not None


class TestAuditLoggerMonitoringAlerts:
    """Test audit logging for monitoring alerts."""
    
    @pytest.mark.asyncio
    async def test_log_monitoring_alert(self, audit_logger):
        """Test logging monitoring alert generation."""
        audit_id = await audit_logger.log_monitoring_alert(
            application_id='app123',
            alert_type='financial_deterioration',
            severity='high',
            message='Significant revenue decline detected',
            alert_details={'revenue_change': -25, 'period': 'Q1_2024'}
        )
        
        assert audit_id is not None


class TestAuditRecordImmutability:
    """Test that audit records are immutable."""
    
    @pytest.mark.asyncio
    async def test_attempt_modify_audit_record_raises_error(self, audit_logger, mock_firestore):
        """Test that attempting to modify an audit record raises an error."""
        # Create a mock audit record
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'audit_id': 'audit123',
            'timestamp': datetime.utcnow().isoformat(),
            'action_type': 'state_transition',
            'immutable': True
        }
        
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Attempt to modify the record
        with pytest.raises(ValueError) as exc_info:
            await audit_logger.attempt_modify_audit_record(
                audit_id='audit123',
                updates={'user_id': 'hacker'}
            )
        
        assert 'immutable' in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_attempt_modify_nonexistent_record_raises_error(self, audit_logger, mock_firestore):
        """Test that attempting to modify a non-existent record raises an error."""
        # Mock non-existent record
        mock_doc = Mock()
        mock_doc.exists = False
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc
        
        with pytest.raises(ValueError) as exc_info:
            await audit_logger.attempt_modify_audit_record(
                audit_id='nonexistent',
                updates={'user_id': 'hacker'}
            )
        
        assert 'not found' in str(exc_info.value).lower()


class TestAuditRecordRetrieval:
    """Test audit record retrieval and querying."""
    
    @pytest.mark.asyncio
    async def test_get_audit_record(self, audit_logger, mock_firestore):
        """Test retrieving a single audit record by ID."""
        # Mock audit record
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'audit_id': 'audit123',
            'timestamp': datetime.utcnow().isoformat(),
            'action_type': 'state_transition'
        }
        
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc
        
        record = await audit_logger.get_audit_record('audit123')
        
        assert record is not None
        assert record['audit_id'] == 'audit123'
    
    @pytest.mark.asyncio
    async def test_get_audit_record_not_found(self, audit_logger, mock_firestore):
        """Test retrieving a non-existent audit record returns None."""
        mock_doc = Mock()
        mock_doc.exists = False
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc
        
        record = await audit_logger.get_audit_record('nonexistent')
        
        assert record is None
    
    @pytest.mark.asyncio
    async def test_get_audit_trail_for_application(self, audit_logger, mock_firestore):
        """Test retrieving audit trail for an application."""
        # Mock audit records
        mock_docs = [
            Mock(to_dict=lambda: {'audit_id': 'audit1', 'action_type': 'state_transition'}),
            Mock(to_dict=lambda: {'audit_id': 'audit2', 'action_type': 'user_action'})
        ]
        
        mock_firestore.collection.return_value.where.return_value.order_by.return_value.limit.return_value.stream.return_value = mock_docs
        
        trail = await audit_logger.get_audit_trail_for_application('app123')
        
        assert len(trail) == 2
        assert trail[0]['audit_id'] == 'audit1'
        assert trail[1]['audit_id'] == 'audit2'
    
    @pytest.mark.asyncio
    async def test_get_audit_trail_by_user(self, audit_logger, mock_firestore):
        """Test retrieving audit trail for a specific user."""
        mock_docs = [
            Mock(to_dict=lambda: {'audit_id': 'audit1', 'user_id': 'user456'})
        ]
        
        mock_firestore.collection.return_value.where.return_value.order_by.return_value.limit.return_value.stream.return_value = mock_docs
        
        trail = await audit_logger.get_audit_trail_by_user('user456')
        
        assert len(trail) == 1
        assert trail[0]['user_id'] == 'user456'
    
    @pytest.mark.asyncio
    async def test_get_audit_trail_by_action_type(self, audit_logger, mock_firestore):
        """Test retrieving audit trail by action type."""
        mock_docs = [
            Mock(to_dict=lambda: {'audit_id': 'audit1', 'action_type': 'state_transition'}),
            Mock(to_dict=lambda: {'audit_id': 'audit2', 'action_type': 'state_transition'})
        ]
        
        mock_firestore.collection.return_value.where.return_value.order_by.return_value.limit.return_value.stream.return_value = mock_docs
        
        trail = await audit_logger.get_audit_trail_by_action_type(AuditActionType.STATE_TRANSITION)
        
        assert len(trail) == 2
        assert all(record['action_type'] == 'state_transition' for record in trail)


class TestAuditRecordStructure:
    """Test the structure of audit records."""
    
    def test_create_audit_record_structure(self, audit_logger):
        """Test that audit records have the correct structure."""
        record = audit_logger._create_audit_record(
            action_type=AuditActionType.STATE_TRANSITION,
            resource_type='application',
            resource_id='app123',
            user_id='user456',
            details={'old_state': 'pending', 'new_state': 'processing'}
        )
        
        # Verify required fields
        assert 'audit_id' in record
        assert 'timestamp' in record
        assert 'timestamp_obj' in record
        assert 'action_type' in record
        assert 'resource_type' in record
        assert 'resource_id' in record
        assert 'user_id' in record
        assert 'details' in record
        assert 'immutable' in record
        
        # Verify field values
        assert record['action_type'] == 'state_transition'
        assert record['resource_type'] == 'application'
        assert record['resource_id'] == 'app123'
        assert record['user_id'] == 'user456'
        assert record['immutable'] is True
        assert record['details']['old_state'] == 'pending'
        assert record['details']['new_state'] == 'processing'
    
    def test_generate_audit_id_is_unique(self, audit_logger):
        """Test that generated audit IDs are unique."""
        id1 = audit_logger._generate_audit_id()
        id2 = audit_logger._generate_audit_id()
        
        assert id1 != id2
        assert isinstance(id1, str)
        assert isinstance(id2, str)


class TestAuditLoggerEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.mark.asyncio
    async def test_log_state_transition_with_empty_reason(self, audit_logger):
        """Test logging state transition with empty reason."""
        audit_id = await audit_logger.log_state_transition(
            application_id='app123',
            old_state=ApplicationStatus.PENDING,
            new_state=ApplicationStatus.PROCESSING,
            user_id='user456',
            reason=''
        )
        
        assert audit_id is not None
    
    @pytest.mark.asyncio
    async def test_log_user_action_with_no_details(self, audit_logger):
        """Test logging user action without details."""
        audit_id = await audit_logger.log_user_action(
            action='view',
            resource_type='application',
            resource_id='app123',
            user_id='user456'
        )
        
        assert audit_id is not None
    
    @pytest.mark.asyncio
    async def test_log_ai_decision_with_empty_data_sources(self, audit_logger):
        """Test logging AI decision with empty data sources list."""
        audit_id = await audit_logger.log_ai_decision(
            agent_name='TestAgent',
            application_id='app123',
            decision='test_decision',
            reasoning='test reasoning',
            data_sources=[]
        )
        
        assert audit_id is not None
