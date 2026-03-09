"""
Property-based tests for AuditLogger

Feature: intelli-credit-platform
Property 21: Audit Trail Completeness
Property 37: Audit Record Immutability

Validates: Requirements 9.5, 17.1, 17.3
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, AsyncMock
from datetime import datetime
import uuid

from app.core.audit_logger import AuditLogger, AuditActionType
from app.models.domain import ApplicationStatus


# Strategies for generating test data
application_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
    min_size=5,
    max_size=50
)

user_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
    min_size=3,
    max_size=50
)

reason_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'), whitelist_characters='.,!?-'),
    min_size=0,
    max_size=200
)

application_status_strategy = st.sampled_from([
    ApplicationStatus.PENDING,
    ApplicationStatus.PROCESSING,
    ApplicationStatus.ANALYSIS_COMPLETE,
    ApplicationStatus.APPROVED,
    ApplicationStatus.APPROVED_WITH_CONDITIONS,
    ApplicationStatus.REJECTED
])

action_strategy = st.sampled_from(['create', 'update', 'delete', 'view'])

resource_type_strategy = st.sampled_from(['application', 'document', 'cam', 'monitoring_alert'])

agent_name_strategy = st.sampled_from([
    'DocumentIntelligenceAgent',
    'FinancialAnalysisAgent',
    'WebResearchAgent',
    'PromoterIntelligenceAgent',
    'IndustryIntelligenceAgent',
    'ForecastingAgent',
    'RiskScoringAgent',
    'CAMGeneratorAgent'
])

decision_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_'),
    min_size=3,
    max_size=50
)

data_sources_strategy = st.lists(
    st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_'),
        min_size=3,
        max_size=30
    ),
    min_size=1,
    max_size=10
)


def create_mock_firestore():
    """Create a mock Firestore client that stores audit records in memory."""
    mock_db = Mock()
    mock_collection = Mock()
    
    # In-memory storage for audit records
    audit_records = {}
    
    def mock_set(record):
        """Store audit record in memory."""
        audit_id = record['audit_id']
        audit_records[audit_id] = record.copy()
    
    def mock_get(audit_id):
        """Retrieve audit record from memory."""
        mock_doc = Mock()
        if audit_id in audit_records:
            mock_doc.exists = True
            mock_doc.to_dict.return_value = audit_records[audit_id]
        else:
            mock_doc.exists = False
        return mock_doc
    
    def mock_where(where_field, op, where_value):
        """Mock Firestore where query."""
        mock_query = Mock()
        
        def mock_order_by(order_field, direction='ASCENDING'):
            mock_ordered = Mock()
            
            def mock_limit(limit_value):
                mock_limited = Mock()
                
                def mock_stream():
                    # Filter records based on where clause
                    filtered = [
                        record for record in audit_records.values()
                        if record.get(where_field) == where_value
                    ]
                    # Return mock documents
                    return [Mock(to_dict=lambda r=record: r) for record in filtered]
                
                mock_limited.stream = mock_stream
                return mock_limited
            
            mock_ordered.limit = mock_limit
            return mock_ordered
        
        mock_query.order_by = mock_order_by
        return mock_query
    
    # Set up mock chain
    mock_db.collection.return_value = mock_collection
    mock_collection.document = lambda doc_id: Mock(
        set=mock_set,
        get=lambda: mock_get(doc_id)
    )
    mock_collection.where = mock_where
    
    # Store reference to audit_records for testing
    mock_db._audit_records = audit_records
    
    return mock_db


# Note: We don't use fixtures with Hypothesis property tests
# because function-scoped fixtures are not reset between examples.
# Instead, we create fresh instances inside each test.


class TestProperty21AuditTrailCompleteness:
    """
    Property 21: Audit Trail Completeness
    
    For any status transition or user action, the system should create an audit log
    entry with timestamp, user identifier, and action details.
    
    Validates: Requirements 9.5, 17.1
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        app_id=application_id_strategy,
        old_state=application_status_strategy,
        new_state=application_status_strategy,
        user_id=user_id_strategy,
        reason=reason_strategy
    )
    async def test_state_transition_creates_complete_audit_record(
        self,
        app_id: str,
        old_state: ApplicationStatus,
        new_state: ApplicationStatus,
        user_id: str,
        reason: str
    ):
        """
        Property: For any state transition, an audit record is created with all required fields.
        
        **Validates: Requirements 9.5, 17.1**
        
        For any application state transition, the audit log should contain:
        - audit_id (unique identifier)
        - timestamp (when the action occurred)
        - user_id (who performed the action)
        - action_type (state_transition)
        - resource_type (application)
        - resource_id (application_id)
        - details (old_state, new_state, reason)
        - immutable flag (set to True)
        """
        # Filter out invalid inputs
        assume(len(app_id.strip()) >= 5)
        assume(len(user_id.strip()) >= 3)
        assume(old_state != new_state)  # State must actually change
        
        # Create fresh mock firestore for this test
        mock_firestore = create_mock_firestore()
        
        # Create fresh mock firestore for this test
        mock_firestore = create_mock_firestore()
        
        # Create audit logger
        audit_logger = AuditLogger(mock_firestore)
        
        # Log state transition
        audit_id = await audit_logger.log_state_transition(
            application_id=app_id,
            old_state=old_state,
            new_state=new_state,
            user_id=user_id,
            reason=reason
        )
        
        # Verify audit ID was generated
        assert audit_id is not None
        assert isinstance(audit_id, str)
        assert len(audit_id) > 0
        
        # Retrieve the audit record from mock storage
        audit_record = mock_firestore._audit_records.get(audit_id)
        assert audit_record is not None, "Audit record should be stored"
        
        # Verify all required fields are present
        required_fields = [
            'audit_id',
            'timestamp',
            'timestamp_obj',
            'action_type',
            'resource_type',
            'resource_id',
            'user_id',
            'details',
            'immutable'
        ]
        
        for field in required_fields:
            assert field in audit_record, f"Missing required field: {field}"
        
        # Verify field values
        assert audit_record['audit_id'] == audit_id
        assert audit_record['action_type'] == AuditActionType.STATE_TRANSITION.value
        assert audit_record['resource_type'] == 'application'
        assert audit_record['resource_id'] == app_id
        assert audit_record['user_id'] == user_id
        assert audit_record['immutable'] is True
        
        # Verify timestamp is valid ISO format
        assert isinstance(audit_record['timestamp'], str)
        datetime.fromisoformat(audit_record['timestamp'])  # Should not raise
        
        # Verify details contain state transition information
        assert 'old_state' in audit_record['details']
        assert 'new_state' in audit_record['details']
        assert audit_record['details']['old_state'] == old_state.value
        assert audit_record['details']['new_state'] == new_state.value
        
        if reason:
            assert 'reason' in audit_record['details']
            assert audit_record['details']['reason'] == reason
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        action=action_strategy,
        resource_type=resource_type_strategy,
        resource_id=application_id_strategy,
        user_id=user_id_strategy
    )
    async def test_user_action_creates_complete_audit_record(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: str
    ):
        """
        Property: For any user action, an audit record is created with all required fields.
        
        **Validates: Requirements 9.5, 17.1**
        
        For any user action (create, update, delete, view), the audit log should contain:
        - audit_id
        - timestamp
        - user_id
        - action_type (user_action)
        - resource_type
        - resource_id
        - details (action)
        - immutable flag
        """
        # Filter out invalid inputs
        assume(len(resource_id.strip()) >= 5)
        assume(len(user_id.strip()) >= 3)
        
        # Create fresh mock firestore for this test
        mock_firestore = create_mock_firestore()
        
        # Create fresh mock firestore for this test
        mock_firestore = create_mock_firestore()
        
        # Create audit logger
        audit_logger = AuditLogger(mock_firestore)
        
        # Log user action
        audit_id = await audit_logger.log_user_action(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            details={'test_field': 'test_value'}
        )
        
        # Verify audit ID was generated
        assert audit_id is not None
        assert isinstance(audit_id, str)
        
        # Retrieve the audit record
        audit_record = mock_firestore._audit_records.get(audit_id)
        assert audit_record is not None
        
        # Verify all required fields
        assert audit_record['audit_id'] == audit_id
        assert audit_record['action_type'] == AuditActionType.USER_ACTION.value
        assert audit_record['resource_type'] == resource_type
        assert audit_record['resource_id'] == resource_id
        assert audit_record['user_id'] == user_id
        assert audit_record['immutable'] is True
        
        # Verify timestamp
        assert isinstance(audit_record['timestamp'], str)
        datetime.fromisoformat(audit_record['timestamp'])
        
        # Verify details contain action
        assert 'action' in audit_record['details']
        assert audit_record['details']['action'] == action
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        agent_name=agent_name_strategy,
        app_id=application_id_strategy,
        decision=decision_strategy,
        reasoning=reason_strategy,
        data_sources=data_sources_strategy
    )
    async def test_ai_decision_creates_complete_audit_record(
        self,
        agent_name: str,
        app_id: str,
        decision: str,
        reasoning: str,
        data_sources: list
    ):
        """
        Property: For any AI decision, an audit record is created with all required fields.
        
        **Validates: Requirements 17.2**
        
        For any AI agent decision, the audit log should contain:
        - audit_id
        - timestamp
        - user_id (system)
        - action_type (ai_decision)
        - resource_type (application)
        - resource_id (application_id)
        - details (agent_name, decision, reasoning, data_sources)
        - immutable flag
        """
        # Filter out invalid inputs
        assume(len(app_id.strip()) >= 5)
        assume(len(decision.strip()) >= 3)
        assume(len(data_sources) > 0)
        
        # Create fresh mock firestore for this test
        mock_firestore = create_mock_firestore()
        
        # Create audit logger
        audit_logger = AuditLogger(mock_firestore)
        
        # Log AI decision
        audit_id = await audit_logger.log_ai_decision(
            agent_name=agent_name,
            application_id=app_id,
            decision=decision,
            reasoning=reasoning,
            data_sources=data_sources
        )
        
        # Verify audit ID was generated
        assert audit_id is not None
        
        # Retrieve the audit record
        audit_record = mock_firestore._audit_records.get(audit_id)
        assert audit_record is not None
        
        # Verify all required fields
        assert audit_record['audit_id'] == audit_id
        assert audit_record['action_type'] == AuditActionType.AI_DECISION.value
        assert audit_record['resource_type'] == 'application'
        assert audit_record['resource_id'] == app_id
        assert audit_record['user_id'] == 'system'  # AI decisions use 'system' user
        assert audit_record['immutable'] is True
        
        # Verify timestamp
        assert isinstance(audit_record['timestamp'], str)
        datetime.fromisoformat(audit_record['timestamp'])
        
        # Verify details contain AI decision information
        assert 'agent_name' in audit_record['details']
        assert 'decision' in audit_record['details']
        assert 'reasoning' in audit_record['details']
        assert 'data_sources' in audit_record['details']
        
        assert audit_record['details']['agent_name'] == agent_name
        assert audit_record['details']['decision'] == decision
        assert audit_record['details']['reasoning'] == reasoning
        assert audit_record['details']['data_sources'] == data_sources
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        app_id=application_id_strategy,
        user_id=user_id_strategy
    )
    async def test_audit_trail_retrieval_returns_all_records(
        self,
        app_id: str,
        user_id: str
    ):
        """
        Property: For any application, all audit records can be retrieved.
        
        **Validates: Requirements 17.4**
        
        For any application with multiple audit records, the get_audit_trail_for_application
        method should return all records associated with that application.
        """
        # Filter out invalid inputs
        assume(len(app_id.strip()) >= 5)
        assume(len(user_id.strip()) >= 3)
        
        # Create fresh mock firestore for this test
        mock_firestore = create_mock_firestore()
        
        # Create audit logger
        audit_logger = AuditLogger(mock_firestore)
        
        # Create multiple audit records for the same application
        audit_ids = []
        
        # Log state transition
        audit_id1 = await audit_logger.log_state_transition(
            application_id=app_id,
            old_state=ApplicationStatus.PENDING,
            new_state=ApplicationStatus.PROCESSING,
            user_id=user_id
        )
        audit_ids.append(audit_id1)
        
        # Log user action
        audit_id2 = await audit_logger.log_user_action(
            action='update',
            resource_type='application',
            resource_id=app_id,
            user_id=user_id
        )
        audit_ids.append(audit_id2)
        
        # Log AI decision
        audit_id3 = await audit_logger.log_ai_decision(
            agent_name='RiskScoringAgent',
            application_id=app_id,
            decision='approve',
            reasoning='Strong financials',
            data_sources=['financial_analysis']
        )
        audit_ids.append(audit_id3)
        
        # Retrieve audit trail
        audit_trail = await audit_logger.get_audit_trail_for_application(app_id)
        
        # Verify all records are returned
        assert len(audit_trail) >= 3, "Should return at least 3 audit records"
        
        # Verify all audit IDs are present
        returned_ids = [record['audit_id'] for record in audit_trail]
        for audit_id in audit_ids:
            assert audit_id in returned_ids, f"Audit ID {audit_id} should be in trail"
        
        # Verify all records are for the correct application
        for record in audit_trail:
            assert record['resource_id'] == app_id, \
                "All records should be for the same application"


class TestProperty37AuditRecordImmutability:
    """
    Property 37: Audit Record Immutability
    
    For any credit decision audit record, once created, the record should be immutable
    and any attempt to modify it should be rejected.
    
    Validates: Requirements 17.3
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        app_id=application_id_strategy,
        old_state=application_status_strategy,
        new_state=application_status_strategy,
        user_id=user_id_strategy
    )
    async def test_audit_record_cannot_be_modified(
        self,
        app_id: str,
        old_state: ApplicationStatus,
        new_state: ApplicationStatus,
        user_id: str
    ):
        """
        Property: For any audit record, attempts to modify it should be rejected.
        
        **Validates: Requirements 17.3**
        
        For any audit record created in the system, any attempt to modify the record
        should raise a ValueError indicating that the record is immutable.
        """
        # Filter out invalid inputs
        assume(len(app_id.strip()) >= 5)
        assume(len(user_id.strip()) >= 3)
        assume(old_state != new_state)
        
        # Create fresh mock firestore for this test
        mock_firestore = create_mock_firestore()
        
        # Create audit logger
        audit_logger = AuditLogger(mock_firestore)
        
        # Create an audit record
        audit_id = await audit_logger.log_state_transition(
            application_id=app_id,
            old_state=old_state,
            new_state=new_state,
            user_id=user_id,
            reason='Test transition'
        )
        
        # Verify the record exists
        audit_record = await audit_logger.get_audit_record(audit_id)
        assert audit_record is not None
        assert audit_record['immutable'] is True
        
        # Attempt to modify the record - should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            await audit_logger.attempt_modify_audit_record(
                audit_id=audit_id,
                updates={'user_id': 'hacker', 'details': {'tampered': True}}
            )
        
        # Verify error message indicates immutability
        error_message = str(exc_info.value).lower()
        assert 'immutable' in error_message, \
            "Error message should mention immutability"
        
        # Verify the record was not modified
        audit_record_after = await audit_logger.get_audit_record(audit_id)
        assert audit_record_after == audit_record, \
            "Audit record should remain unchanged after modification attempt"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        agent_name=agent_name_strategy,
        app_id=application_id_strategy,
        decision=decision_strategy,
        data_sources=data_sources_strategy
    )
    async def test_ai_decision_audit_record_is_immutable(
        self,
        agent_name: str,
        app_id: str,
        decision: str,
        data_sources: list
    ):
        """
        Property: For any AI decision audit record, the record is immutable.
        
        **Validates: Requirements 17.3**
        
        AI decision audit records are critical for compliance and should never be
        modified after creation. This test verifies that AI decision records have
        the immutable flag set and cannot be modified.
        """
        # Filter out invalid inputs
        assume(len(app_id.strip()) >= 5)
        assume(len(decision.strip()) >= 3)
        assume(len(data_sources) > 0)
        
        # Create fresh mock firestore for this test
        mock_firestore = create_mock_firestore()
        
        # Create fresh mock firestore for this test
        mock_firestore = create_mock_firestore()
        
        # Create audit logger
        audit_logger = AuditLogger(mock_firestore)
        
        # Create an AI decision audit record
        audit_id = await audit_logger.log_ai_decision(
            agent_name=agent_name,
            application_id=app_id,
            decision=decision,
            reasoning='Test reasoning',
            data_sources=data_sources
        )
        
        # Verify the record exists and is marked immutable
        audit_record = await audit_logger.get_audit_record(audit_id)
        assert audit_record is not None
        assert audit_record['immutable'] is True
        assert audit_record['action_type'] == AuditActionType.AI_DECISION.value
        
        # Attempt to modify the AI decision - should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            await audit_logger.attempt_modify_audit_record(
                audit_id=audit_id,
                updates={'details': {'decision': 'reject', 'tampered': True}}
            )
        
        # Verify error message
        assert 'immutable' in str(exc_info.value).lower()
        
        # Verify the record was not modified
        audit_record_after = await audit_logger.get_audit_record(audit_id)
        assert audit_record_after['details']['decision'] == decision, \
            "Decision should not be modified"
        assert 'tampered' not in audit_record_after['details'], \
            "Tampered field should not be added"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        action=action_strategy,
        resource_type=resource_type_strategy,
        resource_id=application_id_strategy,
        user_id=user_id_strategy
    )
    async def test_user_action_audit_record_is_immutable(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: str
    ):
        """
        Property: For any user action audit record, the record is immutable.
        
        **Validates: Requirements 17.3**
        
        User action audit records track who did what and when. These records must
        be immutable to maintain accountability and prevent tampering.
        """
        # Filter out invalid inputs
        assume(len(resource_id.strip()) >= 5)
        assume(len(user_id.strip()) >= 3)
        
        # Create fresh mock firestore for this test
        mock_firestore = create_mock_firestore()
        
        # Create audit logger
        audit_logger = AuditLogger(mock_firestore)
        
        # Create a user action audit record
        audit_id = await audit_logger.log_user_action(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            details={'original_field': 'original_value'}
        )
        
        # Verify the record exists and is marked immutable
        audit_record = await audit_logger.get_audit_record(audit_id)
        assert audit_record is not None
        assert audit_record['immutable'] is True
        
        # Attempt to modify the user_id (critical field) - should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            await audit_logger.attempt_modify_audit_record(
                audit_id=audit_id,
                updates={'user_id': 'different_user'}
            )
        
        # Verify error message
        assert 'immutable' in str(exc_info.value).lower()
        
        # Verify the user_id was not modified
        audit_record_after = await audit_logger.get_audit_record(audit_id)
        assert audit_record_after['user_id'] == user_id, \
            "User ID should not be modified"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        audit_id=application_id_strategy
    )
    async def test_nonexistent_audit_record_modification_raises_error(
        self,
        audit_id: str
    ):
        """
        Property: Attempting to modify a non-existent audit record raises an error.
        
        **Validates: Requirements 17.3**
        
        For any audit ID that doesn't exist, attempting to modify it should raise
        a ValueError indicating the record was not found.
        """
        # Filter out invalid inputs
        assume(len(audit_id.strip()) >= 5)
        
        # Create fresh mock firestore for this test
        mock_firestore = create_mock_firestore()
        
        # Create audit logger
        audit_logger = AuditLogger(mock_firestore)
        
        # Attempt to modify a non-existent record - should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            await audit_logger.attempt_modify_audit_record(
                audit_id=audit_id,
                updates={'user_id': 'hacker'}
            )
        
        # Verify error message indicates record not found
        error_message = str(exc_info.value).lower()
        assert 'not found' in error_message, \
            "Error message should indicate record not found"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        app_id=application_id_strategy,
        user_id=user_id_strategy
    )
    async def test_audit_record_immutability_flag_always_true(
        self,
        app_id: str,
        user_id: str
    ):
        """
        Property: For any audit record, the immutable flag is always set to True.
        
        **Validates: Requirements 17.3**
        
        All audit records should have the immutable flag set to True upon creation,
        regardless of the type of action being logged.
        """
        # Filter out invalid inputs
        assume(len(app_id.strip()) >= 5)
        assume(len(user_id.strip()) >= 3)
        
        # Create fresh mock firestore for this test
        mock_firestore = create_mock_firestore()
        
        # Create audit logger
        audit_logger = AuditLogger(mock_firestore)
        
        # Create various types of audit records
        audit_ids = []
        
        # State transition
        audit_id1 = await audit_logger.log_state_transition(
            application_id=app_id,
            old_state=ApplicationStatus.PENDING,
            new_state=ApplicationStatus.PROCESSING,
            user_id=user_id
        )
        audit_ids.append(audit_id1)
        
        # User action
        audit_id2 = await audit_logger.log_user_action(
            action='create',
            resource_type='application',
            resource_id=app_id,
            user_id=user_id
        )
        audit_ids.append(audit_id2)
        
        # AI decision
        audit_id3 = await audit_logger.log_ai_decision(
            agent_name='TestAgent',
            application_id=app_id,
            decision='test_decision',
            reasoning='test reasoning',
            data_sources=['test_source']
        )
        audit_ids.append(audit_id3)
        
        # Document action
        audit_id4 = await audit_logger.log_document_action(
            action='upload',
            application_id=app_id,
            document_id='doc123',
            user_id=user_id
        )
        audit_ids.append(audit_id4)
        
        # CAM generation
        audit_id5 = await audit_logger.log_cam_generation(
            application_id=app_id,
            cam_version=1,
            user_id=user_id
        )
        audit_ids.append(audit_id5)
        
        # Monitoring alert
        audit_id6 = await audit_logger.log_monitoring_alert(
            application_id=app_id,
            alert_type='test_alert',
            severity='high',
            message='Test alert'
        )
        audit_ids.append(audit_id6)
        
        # Verify all records have immutable flag set to True
        for audit_id in audit_ids:
            audit_record = await audit_logger.get_audit_record(audit_id)
            assert audit_record is not None, f"Audit record {audit_id} should exist"
            assert 'immutable' in audit_record, \
                f"Audit record {audit_id} should have immutable flag"
            assert audit_record['immutable'] is True, \
                f"Audit record {audit_id} should have immutable flag set to True"
