"""
Unit tests for MonitoringService

Tests the continuous monitoring service functionality including:
- Monitoring activation on approval
- Periodic monitoring checks
- Material change detection
- Alert generation
- Monitoring activity logging
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from app.services.monitoring_service import MonitoringService, MonitoringStatus, ChangeType
from app.models.domain import ApplicationStatus, MonitoringAlert
from app.core.audit_logger import AuditLogger


@pytest.fixture
def mock_firestore():
    """Create a mock Firestore client."""
    mock_db = Mock()
    mock_collection = Mock()
    mock_document = Mock()
    
    mock_db.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document
    
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


class TestMonitoringActivation:
    """Test monitoring activation functionality."""
    
    @pytest.mark.asyncio
    async def test_activate_monitoring_creates_config(self, monitoring_service, mock_firestore):
        """Test that activating monitoring creates a proper configuration."""
        application_id = 'app123'
        company_name = 'Acme Corp'
        
        # Mock Firestore set operation
        mock_doc_ref = Mock()
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        mock_doc_ref.set = Mock()
        
        result = await monitoring_service.activate_monitoring(
            application_id=application_id,
            company_name=company_name
        )
        
        # Verify configuration structure
        assert result['application_id'] == application_id
        assert result['company_name'] == company_name
        assert result['status'] == MonitoringStatus.ACTIVE.value
        assert 'monitoring_id' in result
        assert 'activated_at' in result
        assert 'next_check' in result
        assert result['check_interval_days'] == 7
        assert result['total_checks'] == 0
        assert result['total_alerts'] == 0
        
        # Verify Firestore was called
        mock_firestore.collection.assert_called_with('monitoring')
        mock_firestore.collection.return_value.document.assert_called_with(application_id)
    
    @pytest.mark.asyncio
    async def test_activate_monitoring_with_context(self, monitoring_service, mock_firestore):
        """Test activating monitoring with additional context."""
        application_id = 'app123'
        company_name = 'Acme Corp'
        additional_context = {
            'industry': 'Manufacturing',
            'location': 'California'
        }
        
        mock_doc_ref = Mock()
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        mock_doc_ref.set = Mock()
        
        result = await monitoring_service.activate_monitoring(
            application_id=application_id,
            company_name=company_name,
            additional_context=additional_context
        )
        
        assert result['additional_context'] == additional_context
    
    @pytest.mark.asyncio
    async def test_activate_monitoring_logs_action(self, monitoring_service, mock_firestore, mock_audit_logger):
        """Test that monitoring activation is logged to audit trail."""
        application_id = 'app123'
        company_name = 'Acme Corp'
        
        mock_doc_ref = Mock()
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        mock_doc_ref.set = Mock()
        
        await monitoring_service.activate_monitoring(
            application_id=application_id,
            company_name=company_name
        )
        
        # Verify audit logging was called
        mock_audit_logger.log_user_action.assert_called_once()
        call_args = mock_audit_logger.log_user_action.call_args
        assert call_args[1]['action'] == 'activate_monitoring'
        assert call_args[1]['resource_type'] == 'monitoring'
        assert call_args[1]['resource_id'] == application_id
        assert call_args[1]['user_id'] == 'system'
    
    @pytest.mark.asyncio
    async def test_deactivate_monitoring(self, monitoring_service, mock_firestore):
        """Test deactivating monitoring."""
        application_id = 'app123'
        reason = 'Loan fully repaid'
        
        # Mock Firestore get and update operations
        mock_doc_ref = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc_ref.get.return_value = mock_doc
        mock_doc_ref.update = Mock()
        
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        result = await monitoring_service.deactivate_monitoring(
            application_id=application_id,
            reason=reason
        )
        
        assert result is True
        mock_doc_ref.update.assert_called_once()
        update_args = mock_doc_ref.update.call_args[0][0]
        assert update_args['status'] == MonitoringStatus.STOPPED.value
        assert update_args['stop_reason'] == reason


class TestMonitoringChecks:
    """Test monitoring check functionality."""
    
    @pytest.mark.asyncio
    async def test_perform_monitoring_check_success(self, monitoring_service, mock_firestore, mock_web_research_agent):
        """Test successful monitoring check."""
        application_id = 'app123'
        company_name = 'Acme Corp'
        
        # Mock monitoring configuration
        monitoring_config = {
            'monitoring_id': 'mon123',
            'application_id': application_id,
            'company_name': company_name,
            'status': MonitoringStatus.ACTIVE.value,
            'check_interval_days': 7,
            'alert_threshold': 0.7,
            'additional_context': {}
        }
        
        # Mock Firestore get operation
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = monitoring_config
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Mock web research results
        research_results = {
            'summary': 'Company is performing well',
            'news_items': [
                {'title': 'Acme Corp announces growth', 'summary': 'Strong quarter', 'source': 'News', 'date': '2024-01-01'}
            ],
            'red_flags': [],
            'positive_indicators': [
                {'description': 'Revenue growth', 'details': '20% increase'}
            ],
            'sources': []
        }
        mock_web_research_agent.research.return_value = research_results
        
        # Mock Firestore update operation
        mock_firestore.collection.return_value.document.return_value.update = Mock()
        
        result = await monitoring_service.perform_monitoring_check(application_id)
        
        assert result['success'] is True
        assert result['application_id'] == application_id
        assert result['company_name'] == company_name
        assert 'check_timestamp' in result
        assert result['alerts_generated'] is False
        assert len(result['alerts']) == 0
        
        # Verify web research was called
        mock_web_research_agent.research.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_perform_monitoring_check_with_red_flags(self, monitoring_service, mock_firestore, mock_web_research_agent):
        """Test monitoring check that detects red flags."""
        application_id = 'app123'
        company_name = 'Acme Corp'
        
        monitoring_config = {
            'monitoring_id': 'mon123',
            'application_id': application_id,
            'company_name': company_name,
            'status': MonitoringStatus.ACTIVE.value,
            'check_interval_days': 7,
            'alert_threshold': 0.7,
            'additional_context': {}
        }
        
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = monitoring_config
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc
        
        # Mock web research with critical red flag
        research_results = {
            'summary': 'Company facing financial difficulties',
            'news_items': [],
            'red_flags': [
                {
                    'description': 'Company files for bankruptcy protection',
                    'details': 'Chapter 11 filing announced',
                    'severity': 'critical',
                    'source': 'Financial Times',
                    'date': '2024-01-15'
                }
            ],
            'positive_indicators': [],
            'sources': []
        }
        mock_web_research_agent.research.return_value = research_results
        
        # Mock Firestore operations for alert creation
        mock_alert_doc = Mock()
        mock_alert_doc.set = Mock()
        
        def mock_collection_side_effect(collection_name):
            if collection_name == 'monitoring':
                return mock_firestore.collection.return_value
            elif collection_name == 'monitoring_alerts':
                mock_alerts_collection = Mock()
                mock_alerts_collection.document.return_value = mock_alert_doc
                return mock_alerts_collection
            return Mock()
        
        mock_firestore.collection.side_effect = mock_collection_side_effect
        mock_firestore.collection.return_value.document.return_value.update = Mock()
        
        result = await monitoring_service.perform_monitoring_check(application_id)
        
        assert result['success'] is True
        assert result['alerts_generated'] is True
        assert len(result['alerts']) == 1
        assert result['alerts'][0].severity == 'critical'
        assert 'bankruptcy' in result['alerts'][0].message.lower()
    
    @pytest.mark.asyncio
    async def test_perform_monitoring_check_inactive_monitoring(self, monitoring_service, mock_firestore):
        """Test monitoring check when monitoring is not active."""
        application_id = 'app123'
        
        monitoring_config = {
            'application_id': application_id,
            'status': MonitoringStatus.STOPPED.value
        }
        
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = monitoring_config
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc
        
        result = await monitoring_service.perform_monitoring_check(application_id)
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_perform_monitoring_check_not_configured(self, monitoring_service, mock_firestore):
        """Test monitoring check when monitoring is not configured."""
        application_id = 'app123'
        
        mock_doc = Mock()
        mock_doc.exists = False
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc
        
        result = await monitoring_service.perform_monitoring_check(application_id)
        
        assert result['success'] is False
        assert 'not configured' in result['error'].lower()


class TestMaterialChangeDetection:
    """Test material change detection logic."""
    
    @pytest.mark.asyncio
    async def test_detect_critical_red_flags(self, monitoring_service):
        """Test detection of critical red flags as material changes."""
        research_results = {
            'red_flags': [
                {
                    'description': 'Company defaults on loan',
                    'details': 'Failed to make payment',
                    'severity': 'critical',
                    'source': 'Bloomberg',
                    'date': '2024-01-15'
                }
            ],
            'news_items': []
        }
        
        monitoring_config = {'alert_threshold': 0.7}
        
        changes = await monitoring_service._detect_material_changes(
            application_id='app123',
            research_results=research_results,
            monitoring_config=monitoring_config
        )
        
        assert len(changes) == 1
        assert changes[0]['severity'] == 'critical'
        assert changes[0]['confidence'] == 0.9
    
    @pytest.mark.asyncio
    async def test_detect_multiple_negative_news(self, monitoring_service):
        """Test detection of pattern of negative news."""
        research_results = {
            'red_flags': [],
            'news_items': [
                {'title': 'Company reports loss', 'summary': 'Quarterly loss announced'},
                {'title': 'Revenue decline continues', 'summary': 'Third quarter of decline'},
                {'title': 'Warning issued by analysts', 'summary': 'Concerns about future'},
                {'title': 'Stock price drops', 'summary': 'Significant fall in value'}
            ]
        }
        
        monitoring_config = {'alert_threshold': 0.7}
        
        changes = await monitoring_service._detect_material_changes(
            application_id='app123',
            research_results=research_results,
            monitoring_config=monitoring_config
        )
        
        # Should detect pattern of negative news
        assert len(changes) >= 1
        negative_news_changes = [c for c in changes if c['change_type'] == ChangeType.NEGATIVE_NEWS.value]
        assert len(negative_news_changes) > 0
    
    @pytest.mark.asyncio
    async def test_no_material_changes_detected(self, monitoring_service):
        """Test when no material changes are detected."""
        research_results = {
            'red_flags': [],
            'news_items': [
                {'title': 'Company announces new product', 'summary': 'Innovation continues'}
            ]
        }
        
        monitoring_config = {'alert_threshold': 0.7}
        
        changes = await monitoring_service._detect_material_changes(
            application_id='app123',
            research_results=research_results,
            monitoring_config=monitoring_config
        )
        
        assert len(changes) == 0


class TestAlertGeneration:
    """Test alert generation functionality."""
    
    @pytest.mark.asyncio
    async def test_generate_alerts_for_changes(self, monitoring_service, mock_firestore, mock_audit_logger):
        """Test alert generation for material changes."""
        application_id = 'app123'
        company_name = 'Acme Corp'
        
        material_changes = [
            {
                'change_type': ChangeType.FINANCIAL_DETERIORATION.value,
                'severity': 'high',
                'description': 'Significant revenue decline',
                'details': 'Revenue down 30% year-over-year',
                'source': 'Financial Report',
                'date': '2024-01-15',
                'confidence': 0.85
            }
        ]
        
        research_results = {
            'summary': 'Company facing challenges'
        }
        
        # Mock Firestore alert creation
        mock_alert_doc = Mock()
        mock_alert_doc.set = Mock()
        mock_firestore.collection.return_value.document.return_value = mock_alert_doc
        
        alerts = await monitoring_service._generate_alerts(
            application_id=application_id,
            company_name=company_name,
            material_changes=material_changes,
            research_results=research_results
        )
        
        assert len(alerts) == 1
        assert alerts[0].application_id == application_id
        assert alerts[0].alert_type == ChangeType.FINANCIAL_DETERIORATION.value
        assert alerts[0].severity == 'high'
        assert company_name in alerts[0].message
        assert alerts[0].acknowledged is False
        
        # Verify audit logging
        mock_audit_logger.log_monitoring_alert.assert_called_once()


class TestMonitoringQueries:
    """Test monitoring query functionality."""
    
    @pytest.mark.asyncio
    async def test_get_monitoring_status(self, monitoring_service, mock_firestore):
        """Test retrieving monitoring status."""
        application_id = 'app123'
        
        monitoring_config = {
            'application_id': application_id,
            'status': MonitoringStatus.ACTIVE.value,
            'last_check': '2024-01-15T10:00:00',
            'next_check': '2024-01-22T10:00:00'
        }
        
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = monitoring_config
        mock_firestore.collection.return_value.document.return_value.get.return_value = mock_doc
        
        status = await monitoring_service.get_monitoring_status(application_id)
        
        assert status is not None
        assert status['application_id'] == application_id
        assert status['status'] == MonitoringStatus.ACTIVE.value
    
    @pytest.mark.asyncio
    async def test_get_alerts_for_application(self, monitoring_service, mock_firestore):
        """Test retrieving alerts for an application."""
        application_id = 'app123'
        
        mock_alerts = [
            {
                'id': 'alert1',
                'application_id': application_id,
                'severity': 'high',
                'message': 'Alert 1'
            },
            {
                'id': 'alert2',
                'application_id': application_id,
                'severity': 'medium',
                'message': 'Alert 2'
            }
        ]
        
        # Mock Firestore query
        mock_docs = [Mock(to_dict=Mock(return_value=alert)) for alert in mock_alerts]
        mock_query = Mock()
        mock_query.stream.return_value = mock_docs
        
        mock_collection = Mock()
        mock_collection.where.return_value.order_by.return_value.limit.return_value = mock_query
        mock_firestore.collection.return_value = mock_collection
        
        alerts = await monitoring_service.get_alerts_for_application(application_id)
        
        assert len(alerts) == 2
        assert all(alert['application_id'] == application_id for alert in alerts)
    
    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, monitoring_service, mock_firestore, mock_audit_logger):
        """Test acknowledging an alert."""
        alert_id = 'alert123'
        user_id = 'user456'
        
        # Mock Firestore get and update
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'id': alert_id,
            'application_id': 'app123',
            'alert_type': 'financial_deterioration',
            'severity': 'high'
        }
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        mock_doc_ref.update = Mock()
        
        mock_firestore.collection.return_value.document.return_value = mock_doc_ref
        
        result = await monitoring_service.acknowledge_alert(alert_id, user_id)
        
        assert result is True
        mock_doc_ref.update.assert_called_once()
        update_args = mock_doc_ref.update.call_args[0][0]
        assert update_args['acknowledged'] is True
        assert update_args['acknowledged_by'] == user_id
    
    @pytest.mark.asyncio
    async def test_get_applications_due_for_check(self, monitoring_service, mock_firestore):
        """Test retrieving applications due for monitoring check."""
        current_time = datetime.utcnow()
        
        mock_apps = [
            {'application_id': 'app1', 'next_check': (current_time - timedelta(days=1)).isoformat()},
            {'application_id': 'app2', 'next_check': (current_time - timedelta(hours=1)).isoformat()}
        ]
        
        mock_docs = [Mock(to_dict=Mock(return_value=app)) for app in mock_apps]
        mock_query = Mock()
        mock_query.stream.return_value = mock_docs
        
        mock_collection = Mock()
        mock_collection.where.return_value.where.return_value = mock_query
        mock_firestore.collection.return_value = mock_collection
        
        due_apps = await monitoring_service.get_applications_due_for_check(current_time)
        
        assert len(due_apps) == 2
        assert 'app1' in due_apps
        assert 'app2' in due_apps


class TestChangeClassification:
    """Test change type classification."""
    
    def test_classify_financial_deterioration(self, monitoring_service):
        """Test classification of financial deterioration."""
        red_flag = {
            'description': 'Company files for bankruptcy',
            'details': 'Chapter 11 bankruptcy protection'
        }
        
        change_type = monitoring_service._classify_red_flag(red_flag)
        assert change_type == ChangeType.FINANCIAL_DETERIORATION.value
    
    def test_classify_regulatory_action(self, monitoring_service):
        """Test classification of regulatory action."""
        red_flag = {
            'description': 'SEC investigation launched',
            'details': 'Regulatory violation suspected'
        }
        
        change_type = monitoring_service._classify_red_flag(red_flag)
        assert change_type == ChangeType.REGULATORY_ACTION.value
    
    def test_classify_management_change(self, monitoring_service):
        """Test classification of management change."""
        red_flag = {
            'description': 'CEO resigns amid controversy',
            'details': 'Management shake-up'
        }
        
        change_type = monitoring_service._classify_red_flag(red_flag)
        assert change_type == ChangeType.MANAGEMENT_CHANGE.value
    
    def test_classify_generic_negative_news(self, monitoring_service):
        """Test classification of generic negative news."""
        red_flag = {
            'description': 'Company faces challenges',
            'details': 'Various operational issues'
        }
        
        change_type = monitoring_service._classify_red_flag(red_flag)
        assert change_type == ChangeType.NEGATIVE_NEWS.value
