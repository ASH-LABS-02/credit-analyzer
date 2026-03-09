"""
Property-Based Tests for MonitoringService

This module contains property-based tests for the MonitoringService using Hypothesis.
These tests validate universal properties that should hold across all valid inputs.

Properties tested:
- Property 22: Monitoring Activation on Approval
- Property 23: Alert Generation and Notification
- Property 24: Monitoring Activity Logging

Requirements: 10.1, 10.3, 10.4, 10.5
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from app.services.monitoring_service import MonitoringService, MonitoringStatus, ChangeType
from app.models.domain import ApplicationStatus, MonitoringAlert
from app.core.audit_logger import AuditLogger


# Hypothesis strategies for generating test data
@st.composite
def application_id_strategy(draw):
    """Generate valid application IDs."""
    prefix = draw(st.sampled_from(['app', 'application', 'loan']))
    number = draw(st.integers(min_value=1, max_value=999999))
    return f"{prefix}{number}"


@st.composite
def company_name_strategy(draw):
    """Generate valid company names."""
    first_part = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll')),
        min_size=3,
        max_size=20
    ))
    suffix = draw(st.sampled_from(['Corp', 'Inc', 'LLC', 'Ltd', 'Co']))
    return f"{first_part} {suffix}"


@st.composite
def monitoring_context_strategy(draw):
    """Generate additional context for monitoring."""
    industries = ['Manufacturing', 'Technology', 'Healthcare', 'Finance', 'Retail']
    locations = ['California', 'New York', 'Texas', 'Florida', 'Illinois']
    
    return {
        'industry': draw(st.sampled_from(industries)),
        'location': draw(st.sampled_from(locations)),
        'loan_amount': draw(st.floats(min_value=100000, max_value=10000000))
    }


@pytest.fixture
def mock_firestore():
    """Create a mock Firestore client."""
    mock_db = Mock()
    mock_collection = Mock()
    mock_document = Mock()
    
    mock_db.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document
    
    # Mock document set operation
    mock_document.set = Mock()
    
    # Mock document get operation
    mock_doc = Mock()
    mock_doc.exists = True
    mock_document.get.return_value = mock_doc
    
    return mock_db


@pytest.fixture
def mock_audit_logger():
    """Create a mock audit logger."""
    logger = Mock(spec=AuditLogger)
    logger.log_user_action = AsyncMock()
    logger.log_monitoring_alert = AsyncMock()
    return logger


@pytest.fixture
def mock_web_research_agent():
    """Create a mock web research agent."""
    agent = Mock()
    agent.research = AsyncMock()
    return agent


@pytest.fixture
def monitoring_service(mock_firestore, mock_audit_logger, mock_web_research_agent):
    """Create a MonitoringService instance with mocked dependencies."""
    return MonitoringService(
        firestore_client=mock_firestore,
        audit_logger=mock_audit_logger,
        web_research_agent=mock_web_research_agent
    )


# Feature: intelli-credit-platform, Property 22: Monitoring Activation on Approval
@settings(max_examples=100, deadline=None)
@given(
    application_id=application_id_strategy(),
    company_name=company_name_strategy(),
    additional_context=st.one_of(st.none(), monitoring_context_strategy())
)
@pytest.mark.asyncio
async def test_property_monitoring_activation_on_approval(
    application_id,
    company_name,
    additional_context
):
    """
    **Validates: Requirements 10.1**
    
    Property 22: Monitoring Activation on Approval
    
    For any application that receives an "Approved" or "Approved with Conditions" status,
    the system should initiate continuous monitoring for that company.
    
    This property verifies that:
    1. Monitoring configuration is created with ACTIVE status
    2. Configuration includes all required fields
    3. Next check is scheduled appropriately
    4. Monitoring activation is logged to audit trail
    """
    # Create fresh mocks for each test run
    mock_firestore = Mock()
    mock_collection = Mock()
    mock_document = Mock()
    
    mock_firestore.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document
    
    # Mock document set operation
    mock_document.set = Mock()
    
    # Mock document get operation
    mock_doc = Mock()
    mock_doc.exists = True
    mock_document.get.return_value = mock_doc
    
    mock_audit_logger = Mock(spec=AuditLogger)
    mock_audit_logger.log_user_action = AsyncMock()
    mock_audit_logger.log_monitoring_alert = AsyncMock()
    
    mock_web_research_agent = Mock()
    mock_web_research_agent.research = AsyncMock()
    
    # Create monitoring service
    monitoring_service = MonitoringService(
        firestore_client=mock_firestore,
        audit_logger=mock_audit_logger,
        web_research_agent=mock_web_research_agent
    )
    
    # Mock Firestore set operation
    mock_doc_ref = Mock()
    mock_firestore.collection.return_value.document.return_value = mock_doc_ref
    mock_doc_ref.set = Mock()
    
    # Activate monitoring
    result = await monitoring_service.activate_monitoring(
        application_id=application_id,
        company_name=company_name,
        additional_context=additional_context
    )
    
    # Property assertions
    
    # 1. Monitoring configuration is created with ACTIVE status
    assert result['status'] == MonitoringStatus.ACTIVE.value, \
        "Monitoring should be activated with ACTIVE status"
    
    # 2. Configuration includes all required fields
    required_fields = [
        'monitoring_id', 'application_id', 'company_name', 'status',
        'activated_at', 'last_check', 'next_check', 'check_interval_days',
        'alert_threshold', 'total_checks', 'total_alerts', 'created_at'
    ]
    for field in required_fields:
        assert field in result, f"Monitoring configuration must include '{field}' field"
    
    # 3. Application ID and company name match input
    assert result['application_id'] == application_id, \
        "Application ID in configuration must match input"
    assert result['company_name'] == company_name, \
        "Company name in configuration must match input"
    
    # 4. Monitoring ID is generated
    assert result['monitoring_id'] is not None and len(result['monitoring_id']) > 0, \
        "Monitoring ID must be generated"
    
    # 5. Timestamps are valid ISO format
    try:
        datetime.fromisoformat(result['activated_at'])
        datetime.fromisoformat(result['next_check'])
        datetime.fromisoformat(result['created_at'])
    except ValueError:
        pytest.fail("Timestamps must be in valid ISO format")
    
    # 6. Next check is scheduled in the future
    activated_at = datetime.fromisoformat(result['activated_at'])
    next_check = datetime.fromisoformat(result['next_check'])
    assert next_check > activated_at, \
        "Next check must be scheduled after activation time"
    
    # 7. Check interval is positive
    assert result['check_interval_days'] > 0, \
        "Check interval must be positive"
    
    # 8. Initial counters are zero
    assert result['total_checks'] == 0, \
        "Total checks should be zero at activation"
    assert result['total_alerts'] == 0, \
        "Total alerts should be zero at activation"
    
    # 9. Last check is None (no checks performed yet)
    assert result['last_check'] is None, \
        "Last check should be None at activation"
    
    # 10. Additional context is preserved if provided
    if additional_context is not None:
        assert result['additional_context'] == additional_context, \
            "Additional context must be preserved"
    
    # 11. Firestore persistence is called
    mock_firestore.collection.assert_called_with('monitoring')
    mock_firestore.collection.return_value.document.assert_called_with(application_id)
    
    # 12. Audit logging is called
    mock_audit_logger.log_user_action.assert_called_once()
    call_args = mock_audit_logger.log_user_action.call_args
    assert call_args[1]['action'] == 'activate_monitoring', \
        "Audit log should record 'activate_monitoring' action"
    assert call_args[1]['resource_type'] == 'monitoring', \
        "Audit log should record 'monitoring' resource type"
    assert call_args[1]['resource_id'] == application_id, \
        "Audit log should record correct application ID"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



# Strategies for alert generation testing
@st.composite
def material_change_strategy(draw):
    """Generate material changes for testing."""
    change_types = ['financial_deterioration', 'negative_news', 'industry_downturn', 
                    'regulatory_action', 'management_change', 'credit_event']
    severities = ['low', 'medium', 'high', 'critical']
    
    return {
        'change_type': draw(st.sampled_from(change_types)),
        'severity': draw(st.sampled_from(severities)),
        'description': draw(st.text(min_size=10, max_size=100)),
        'details': draw(st.text(min_size=20, max_size=200)),
        'source': draw(st.sampled_from(['Bloomberg', 'Reuters', 'Financial Times', 'WSJ'])),
        'date': draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2025, 12, 31))).isoformat(),
        'confidence': draw(st.floats(min_value=0.5, max_value=1.0))
    }


# Feature: intelli-credit-platform, Property 23: Alert Generation and Notification
@settings(max_examples=100, deadline=None)
@given(
    application_id=application_id_strategy(),
    company_name=company_name_strategy(),
    material_changes=st.lists(material_change_strategy(), min_size=1, max_size=5)
)
@pytest.mark.asyncio
async def test_property_alert_generation_and_notification(
    application_id,
    company_name,
    material_changes
):
    """
    **Validates: Requirements 10.3, 10.4**
    
    Property 23: Alert Generation and Notification
    
    For any detected material adverse change during monitoring, the system should
    generate a Monitoring_Alert and send notifications to relevant users via
    dashboard and email.
    
    This property verifies that:
    1. Alerts are generated for each material change
    2. Alerts contain all required information
    3. Alerts are persisted to Firestore
    4. Dashboard notifications are created
    5. Audit logging is performed
    """
    # Create fresh mocks for each test run
    mock_firestore = Mock()
    mock_collection = Mock()
    mock_document = Mock()
    
    mock_firestore.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document
    mock_document.set = Mock()
    
    mock_audit_logger = Mock(spec=AuditLogger)
    mock_audit_logger.log_user_action = AsyncMock()
    mock_audit_logger.log_monitoring_alert = AsyncMock()
    
    mock_web_research_agent = Mock()
    mock_web_research_agent.research = AsyncMock()
    
    # Create mock notification service
    mock_notification_service = Mock()
    mock_notification_service.send_alert_notification = AsyncMock(return_value={
        'notification_id': 'notif123',
        'alert_id': 'alert123',
        'dashboard_sent': True,
        'email_sent': False,
        'email_recipients': [],
        'email_failures': [],
        'timestamp': datetime.utcnow().isoformat()
    })
    
    # Create monitoring service
    monitoring_service = MonitoringService(
        firestore_client=mock_firestore,
        audit_logger=mock_audit_logger,
        web_research_agent=mock_web_research_agent,
        notification_service=mock_notification_service
    )
    
    # Mock research results
    research_results = {
        'summary': 'Test research summary',
        'news_items': [],
        'red_flags': [],
        'positive_indicators': [],
        'sources': []
    }
    
    # Generate alerts
    alerts = await monitoring_service._generate_alerts(
        application_id=application_id,
        company_name=company_name,
        material_changes=material_changes,
        research_results=research_results
    )
    
    # Property assertions
    
    # 1. Number of alerts matches number of material changes
    assert len(alerts) == len(material_changes), \
        f"Should generate one alert per material change (expected {len(material_changes)}, got {len(alerts)})"
    
    # 2. Each alert has required fields
    for i, alert in enumerate(alerts):
        assert isinstance(alert, MonitoringAlert), \
            "Generated alerts must be MonitoringAlert instances"
        
        assert alert.id is not None and len(alert.id) > 0, \
            "Alert must have a valid ID"
        
        assert alert.application_id == application_id, \
            "Alert application_id must match input"
        
        assert alert.alert_type == material_changes[i]['change_type'], \
            "Alert type must match material change type"
        
        assert alert.severity == material_changes[i]['severity'], \
            "Alert severity must match material change severity"
        
        assert company_name in alert.message, \
            "Alert message must include company name"
        
        assert material_changes[i]['description'] in alert.message, \
            "Alert message must include change description"
        
        assert alert.acknowledged is False, \
            "New alerts should not be acknowledged"
        
        assert isinstance(alert.created_at, datetime), \
            "Alert must have a valid creation timestamp"
        
        # Check alert details
        assert 'company_name' in alert.details, \
            "Alert details must include company_name"
        assert alert.details['company_name'] == company_name, \
            "Alert details company_name must match input"
        
        assert 'change_details' in alert.details, \
            "Alert details must include change_details"
        
        assert 'source' in alert.details, \
            "Alert details must include source"
        
        assert 'confidence' in alert.details, \
            "Alert details must include confidence"
    
    # 3. Firestore persistence is called for each alert
    # The collection method should be called for alerts collection
    assert mock_firestore.collection.called, \
        "Firestore collection should be called to persist alerts"
    
    # 4. Audit logging is called for each alert
    assert mock_audit_logger.log_monitoring_alert.call_count == len(material_changes), \
        f"Audit logger should be called once per alert (expected {len(material_changes)} calls)"
    
    # Verify audit log calls have correct structure
    for call in mock_audit_logger.log_monitoring_alert.call_args_list:
        call_kwargs = call[1]
        assert 'application_id' in call_kwargs, \
            "Audit log must include application_id"
        assert call_kwargs['application_id'] == application_id, \
            "Audit log application_id must match input"
        assert 'alert_type' in call_kwargs, \
            "Audit log must include alert_type"
        assert 'severity' in call_kwargs, \
            "Audit log must include severity"
        assert 'message' in call_kwargs, \
            "Audit log must include message"
    
    # 5. Notification service is called for each alert (if configured)
    if mock_notification_service:
        assert mock_notification_service.send_alert_notification.call_count == len(material_changes), \
            f"Notification service should be called once per alert (expected {len(material_changes)} calls)"
        
        # Verify notification calls have correct structure
        for call in mock_notification_service.send_alert_notification.call_args_list:
            call_kwargs = call[1]
            assert 'alert' in call_kwargs, \
                "Notification call must include alert"
            assert isinstance(call_kwargs['alert'], MonitoringAlert), \
                "Notification alert must be a MonitoringAlert instance"
            assert 'recipients' in call_kwargs, \
                "Notification call must include recipients list"
            assert isinstance(call_kwargs['recipients'], list), \
                "Recipients must be a list"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



# Feature: intelli-credit-platform, Property 24: Monitoring Activity Logging
@settings(max_examples=100, deadline=None)
@given(
    application_id=application_id_strategy(),
    company_name=company_name_strategy()
)
@pytest.mark.asyncio
async def test_property_monitoring_activity_logging(
    application_id,
    company_name
):
    """
    **Validates: Requirements 10.5**
    
    Property 24: Monitoring Activity Logging
    
    For any monitoring check performed, the system should log the check timestamp
    and findings.
    
    This property verifies that:
    1. Monitoring checks are logged to audit trail
    2. Log entries include check timestamp
    3. Log entries include findings (news items, red flags, alerts generated)
    4. Log entries are created for both successful and failed checks
    """
    # Create fresh mocks for each test run
    mock_firestore = Mock()
    
    # Setup mock for monitoring configuration retrieval
    monitoring_config = {
        'monitoring_id': 'mon123',
        'application_id': application_id,
        'company_name': company_name,
        'status': MonitoringStatus.ACTIVE.value,
        'check_interval_days': 7,
        'alert_threshold': 0.7,
        'additional_context': {},
        'total_checks': 0,
        'total_alerts': 0
    }
    
    mock_doc = Mock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = monitoring_config
    
    mock_doc_ref = Mock()
    mock_doc_ref.get.return_value = mock_doc
    mock_doc_ref.update = Mock()
    mock_doc_ref.set = Mock()
    
    mock_collection = Mock()
    mock_collection.document.return_value = mock_doc_ref
    mock_firestore.collection.return_value = mock_collection
    
    mock_audit_logger = Mock(spec=AuditLogger)
    mock_audit_logger.log_user_action = AsyncMock()
    mock_audit_logger.log_monitoring_alert = AsyncMock()
    
    # Mock web research agent with various findings
    mock_web_research_agent = Mock()
    research_results = {
        'summary': 'Company performance analysis',
        'news_items': [
            {'title': 'Company announces expansion', 'summary': 'Growth plans', 'source': 'News', 'date': '2024-01-01'},
            {'title': 'New product launch', 'summary': 'Innovation', 'source': 'Press', 'date': '2024-01-02'}
        ],
        'red_flags': [
            {
                'description': 'Minor compliance issue',
                'details': 'Resolved quickly',
                'severity': 'low',
                'source': 'Regulatory',
                'date': '2024-01-03'
            }
        ],
        'positive_indicators': [
            {'description': 'Strong revenue growth', 'details': '25% increase'}
        ],
        'sources': ['Bloomberg', 'Reuters']
    }
    mock_web_research_agent.research = AsyncMock(return_value=research_results)
    
    # Create monitoring service
    monitoring_service = MonitoringService(
        firestore_client=mock_firestore,
        audit_logger=mock_audit_logger,
        web_research_agent=mock_web_research_agent
    )
    
    # Perform monitoring check
    result = await monitoring_service.perform_monitoring_check(application_id)
    
    # Property assertions
    
    # 1. Monitoring check was successful
    assert result['success'] is True, \
        "Monitoring check should complete successfully"
    
    # 2. Audit logger was called to log the monitoring check
    assert mock_audit_logger.log_user_action.called, \
        "Audit logger should be called to log monitoring check"
    
    # Find the monitoring_check log entry
    monitoring_check_calls = [
        call for call in mock_audit_logger.log_user_action.call_args_list
        if call[1].get('action') == 'monitoring_check'
    ]
    
    assert len(monitoring_check_calls) > 0, \
        "At least one monitoring_check action should be logged"
    
    # 3. Log entry includes check timestamp
    for call in monitoring_check_calls:
        call_kwargs = call[1]
        
        assert 'details' in call_kwargs, \
            "Audit log must include details"
        
        details = call_kwargs['details']
        
        assert 'check_timestamp' in details, \
            "Audit log details must include check_timestamp"
        
        # Verify timestamp is valid ISO format
        try:
            datetime.fromisoformat(details['check_timestamp'])
        except ValueError:
            pytest.fail("check_timestamp must be in valid ISO format")
        
        # 4. Log entry includes company name
        assert 'company_name' in details, \
            "Audit log details must include company_name"
        assert details['company_name'] == company_name, \
            "Logged company_name must match input"
        
        # 5. Log entry includes findings
        assert 'news_items_found' in details, \
            "Audit log details must include news_items_found count"
        assert details['news_items_found'] == len(research_results['news_items']), \
            "Logged news_items_found must match actual count"
        
        assert 'red_flags_found' in details, \
            "Audit log details must include red_flags_found count"
        assert details['red_flags_found'] == len(research_results['red_flags']), \
            "Logged red_flags_found must match actual count"
        
        assert 'material_changes_detected' in details, \
            "Audit log details must include material_changes_detected count"
        assert isinstance(details['material_changes_detected'], int), \
            "material_changes_detected must be an integer"
        
        assert 'alerts_generated' in details, \
            "Audit log details must include alerts_generated count"
        assert isinstance(details['alerts_generated'], int), \
            "alerts_generated must be an integer"
        
        # 6. Log entry includes findings summary
        assert 'findings' in details, \
            "Audit log details must include findings summary"
        assert isinstance(details['findings'], str), \
            "findings must be a string"
        
        # 7. Resource type and ID are correct
        assert call_kwargs['action'] == 'monitoring_check', \
            "Action must be 'monitoring_check'"
        assert call_kwargs['resource_type'] == 'monitoring', \
            "Resource type must be 'monitoring'"
        assert call_kwargs['resource_id'] == application_id, \
            "Resource ID must match application_id"
        assert call_kwargs['user_id'] == 'system', \
            "User ID should be 'system' for automated checks"


# Test monitoring logging with failed web research
@settings(max_examples=50, deadline=None)
@given(
    application_id=application_id_strategy(),
    company_name=company_name_strategy()
)
@pytest.mark.asyncio
async def test_property_monitoring_logging_with_errors(
    application_id,
    company_name
):
    """
    **Validates: Requirements 10.5**
    
    Property 24: Monitoring Activity Logging (Error Cases)
    
    Verify that monitoring checks are logged even when errors occur during
    the check process (e.g., web research failures).
    """
    # Create fresh mocks
    mock_firestore = Mock()
    
    monitoring_config = {
        'monitoring_id': 'mon123',
        'application_id': application_id,
        'company_name': company_name,
        'status': MonitoringStatus.ACTIVE.value,
        'check_interval_days': 7,
        'alert_threshold': 0.7,
        'additional_context': {},
        'total_checks': 0,
        'total_alerts': 0
    }
    
    mock_doc = Mock()
    mock_doc.exists = True
    mock_doc.to_dict.return_value = monitoring_config
    
    mock_doc_ref = Mock()
    mock_doc_ref.get.return_value = mock_doc
    mock_doc_ref.update = Mock()
    mock_doc_ref.set = Mock()
    
    mock_collection = Mock()
    mock_collection.document.return_value = mock_doc_ref
    mock_firestore.collection.return_value = mock_collection
    
    mock_audit_logger = Mock(spec=AuditLogger)
    mock_audit_logger.log_user_action = AsyncMock()
    
    # Mock web research agent that raises an error
    mock_web_research_agent = Mock()
    mock_web_research_agent.research = AsyncMock(side_effect=Exception("API connection failed"))
    
    # Create monitoring service
    monitoring_service = MonitoringService(
        firestore_client=mock_firestore,
        audit_logger=mock_audit_logger,
        web_research_agent=mock_web_research_agent
    )
    
    # Perform monitoring check (should handle error gracefully)
    result = await monitoring_service.perform_monitoring_check(application_id)
    
    # Property assertions
    
    # 1. Check completes even with web research error
    assert result['success'] is True, \
        "Monitoring check should complete even when web research fails"
    
    # 2. Audit logger is still called
    assert mock_audit_logger.log_user_action.called, \
        "Audit logger should be called even when errors occur"
    
    # 3. Log entry includes error information
    monitoring_check_calls = [
        call for call in mock_audit_logger.log_user_action.call_args_list
        if call[1].get('action') == 'monitoring_check'
    ]
    
    assert len(monitoring_check_calls) > 0, \
        "Monitoring check should be logged even with errors"
    
    # Verify the log includes timestamp and basic information
    for call in monitoring_check_calls:
        call_kwargs = call[1]
        details = call_kwargs['details']
        
        assert 'check_timestamp' in details, \
            "Log must include timestamp even with errors"
        assert 'company_name' in details, \
            "Log must include company_name even with errors"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
