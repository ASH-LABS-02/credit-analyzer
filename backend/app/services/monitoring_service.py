"""
Continuous Monitoring Service

This service implements continuous post-approval monitoring for approved loan applications.
It periodically checks for material changes in financial condition, news, or industry trends
and generates alerts when significant changes are detected.

Requirements: 10.1, 10.2
Property 22: Monitoring Activation on Approval
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

from app.models.domain import ApplicationStatus, MonitoringAlert
from app.agents.web_research_agent import WebResearchAgent
from app.core.audit_logger import AuditLogger
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class MonitoringStatus(str, Enum):
    """Monitoring status for an application."""
    INACTIVE = "inactive"
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"


class ChangeType(str, Enum):
    """Types of material changes that can be detected."""
    FINANCIAL_DETERIORATION = "financial_deterioration"
    NEGATIVE_NEWS = "negative_news"
    INDUSTRY_DOWNTURN = "industry_downturn"
    REGULATORY_ACTION = "regulatory_action"
    MANAGEMENT_CHANGE = "management_change"
    CREDIT_EVENT = "credit_event"


class MonitoringService:
    """
    Service for continuous post-approval monitoring of loan applications.
    
    This service:
    - Activates monitoring when applications are approved
    - Schedules periodic checks for material changes
    - Detects changes in financial condition, news, and industry trends
    - Generates alerts when material adverse changes are detected
    - Logs all monitoring activities for audit trail
    
    Requirements: 10.1, 10.2
    Property 22: Monitoring Activation on Approval
    
    Example:
        >>> monitoring_service = MonitoringService(firestore_client, audit_logger)
        >>> await monitoring_service.activate_monitoring('app123', 'Acme Corp')
        >>> await monitoring_service.perform_monitoring_check('app123')
    """
    
    # Default monitoring configuration
    DEFAULT_CHECK_INTERVAL_DAYS = 7  # Weekly checks
    DEFAULT_ALERT_THRESHOLD = 0.7  # 70% confidence for alert generation
    
    def __init__(
        self,
        firestore_client,
        audit_logger: Optional[AuditLogger] = None,
        web_research_agent: Optional[WebResearchAgent] = None,
        notification_service: Optional[NotificationService] = None
    ):
        """
        Initialize the Monitoring Service.
        
        Args:
            firestore_client: Firestore client for data persistence
            audit_logger: Optional audit logger for logging monitoring activities
            web_research_agent: Optional web research agent for gathering intelligence
            notification_service: Optional notification service for sending alerts
        """
        self.db = firestore_client
        self.audit_logger = audit_logger
        self.web_research_agent = web_research_agent or WebResearchAgent(audit_logger)
        self.notification_service = notification_service
        self.monitoring_collection = 'monitoring'
        self.alerts_collection = 'monitoring_alerts'
    
    async def activate_monitoring(
        self,
        application_id: str,
        company_name: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Activate continuous monitoring for an approved application.
        
        This method is called when an application receives "Approved" or
        "Approved with Conditions" status. It creates a monitoring record
        and schedules the first monitoring check.
        
        Args:
            application_id: The application identifier
            company_name: Name of the company to monitor
            additional_context: Optional additional context (industry, location, etc.)
        
        Returns:
            Dictionary containing monitoring configuration
        
        Requirements: 10.1
        Property 22: Monitoring Activation on Approval
        
        Example:
            >>> config = await monitoring_service.activate_monitoring(
            ...     application_id='app123',
            ...     company_name='Acme Corp',
            ...     additional_context={'industry': 'Manufacturing'}
            ... )
        """
        monitoring_id = str(uuid.uuid4())
        now = datetime.utcnow()
        next_check = now + timedelta(days=self.DEFAULT_CHECK_INTERVAL_DAYS)
        
        monitoring_config = {
            'monitoring_id': monitoring_id,
            'application_id': application_id,
            'company_name': company_name,
            'status': MonitoringStatus.ACTIVE.value,
            'activated_at': now.isoformat(),
            'last_check': None,
            'next_check': next_check.isoformat(),
            'check_interval_days': self.DEFAULT_CHECK_INTERVAL_DAYS,
            'alert_threshold': self.DEFAULT_ALERT_THRESHOLD,
            'total_checks': 0,
            'total_alerts': 0,
            'additional_context': additional_context or {},
            'created_at': now.isoformat()
        }
        
        # Persist monitoring configuration to Firestore
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.db.collection(self.monitoring_collection).document(application_id).set(monitoring_config)
        )
        
        # Log monitoring activation
        if self.audit_logger:
            try:
                await self.audit_logger.log_user_action(
                    action='activate_monitoring',
                    resource_type='monitoring',
                    resource_id=application_id,
                    user_id='system',
                    details={
                        'company_name': company_name,
                        'monitoring_id': monitoring_id,
                        'next_check': next_check.isoformat(),
                        'check_interval_days': self.DEFAULT_CHECK_INTERVAL_DAYS
                    }
                )
            except Exception as e:
                logger.error(f"Failed to log monitoring activation: {e}")
        
        logger.info(
            f"Monitoring activated for application {application_id} ({company_name}). "
            f"Next check scheduled for {next_check.isoformat()}"
        )
        
        return monitoring_config
    
    async def deactivate_monitoring(
        self,
        application_id: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Deactivate monitoring for an application.
        
        Args:
            application_id: The application identifier
            reason: Optional reason for deactivation
        
        Returns:
            True if monitoring was deactivated, False if not found
        
        Example:
            >>> success = await monitoring_service.deactivate_monitoring(
            ...     application_id='app123',
            ...     reason='Loan fully repaid'
            ... )
        """
        import asyncio
        loop = asyncio.get_event_loop()
        
        def update_firestore():
            doc_ref = self.db.collection(self.monitoring_collection).document(application_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            doc_ref.update({
                'status': MonitoringStatus.STOPPED.value,
                'stopped_at': datetime.utcnow().isoformat(),
                'stop_reason': reason
            })
            return True
        
        success = await loop.run_in_executor(None, update_firestore)
        
        if success and self.audit_logger:
            try:
                await self.audit_logger.log_user_action(
                    action='deactivate_monitoring',
                    resource_type='monitoring',
                    resource_id=application_id,
                    user_id='system',
                    details={'reason': reason}
                )
            except Exception as e:
                logger.error(f"Failed to log monitoring deactivation: {e}")
        
        return success
    
    async def perform_monitoring_check(
        self,
        application_id: str
    ) -> Dict[str, Any]:
        """
        Perform a monitoring check for an application.
        
        This method:
        1. Retrieves the monitoring configuration
        2. Gathers current intelligence about the company
        3. Detects material changes compared to baseline
        4. Generates alerts if significant changes are detected
        5. Updates monitoring status and schedules next check
        6. Logs the monitoring activity
        
        Args:
            application_id: The application identifier
        
        Returns:
            Dictionary containing check results and any generated alerts
        
        Requirements: 10.2, 10.5
        Property 24: Monitoring Activity Logging
        
        Example:
            >>> results = await monitoring_service.perform_monitoring_check('app123')
            >>> if results['alerts_generated']:
            ...     print(f"Generated {len(results['alerts'])} alerts")
        """
        # Retrieve monitoring configuration
        monitoring_config = await self._get_monitoring_config(application_id)
        
        if not monitoring_config:
            logger.warning(f"No monitoring configuration found for application {application_id}")
            return {
                'success': False,
                'error': 'Monitoring not configured for this application'
            }
        
        if monitoring_config['status'] != MonitoringStatus.ACTIVE.value:
            logger.info(f"Monitoring is not active for application {application_id}")
            return {
                'success': False,
                'error': f"Monitoring status is {monitoring_config['status']}"
            }
        
        company_name = monitoring_config['company_name']
        additional_context = monitoring_config.get('additional_context', {})
        additional_context['application_id'] = application_id
        
        check_timestamp = datetime.utcnow()
        
        logger.info(f"Performing monitoring check for {company_name} (app: {application_id})")
        
        # Gather current intelligence using web research agent
        try:
            research_results = await self.web_research_agent.research(
                company_name=company_name,
                additional_context=additional_context
            )
        except Exception as e:
            logger.error(f"Error during web research for monitoring check: {e}")
            research_results = {
                'summary': f'Error gathering intelligence: {str(e)}',
                'news_items': [],
                'red_flags': [],
                'positive_indicators': [],
                'sources': []
            }
        
        # Detect material changes
        material_changes = await self._detect_material_changes(
            application_id=application_id,
            research_results=research_results,
            monitoring_config=monitoring_config
        )
        
        # Generate alerts for significant changes
        alerts = []
        if material_changes:
            alerts = await self._generate_alerts(
                application_id=application_id,
                company_name=company_name,
                material_changes=material_changes,
                research_results=research_results
            )
        
        # Update monitoring status
        await self._update_monitoring_status(
            application_id=application_id,
            check_timestamp=check_timestamp,
            alerts_generated=len(alerts)
        )
        
        # Log monitoring activity
        if self.audit_logger:
            try:
                await self.audit_logger.log_user_action(
                    action='monitoring_check',
                    resource_type='monitoring',
                    resource_id=application_id,
                    user_id='system',
                    details={
                        'company_name': company_name,
                        'check_timestamp': check_timestamp.isoformat(),
                        'news_items_found': len(research_results.get('news_items', [])),
                        'red_flags_found': len(research_results.get('red_flags', [])),
                        'material_changes_detected': len(material_changes),
                        'alerts_generated': len(alerts),
                        'findings': research_results.get('summary', '')[:500]
                    }
                )
            except Exception as e:
                logger.error(f"Failed to log monitoring check: {e}")
        
        return {
            'success': True,
            'application_id': application_id,
            'company_name': company_name,
            'check_timestamp': check_timestamp.isoformat(),
            'research_results': research_results,
            'material_changes': material_changes,
            'alerts_generated': len(alerts) > 0,
            'alerts': alerts
        }
    
    async def _get_monitoring_config(
        self,
        application_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve monitoring configuration for an application.
        
        Args:
            application_id: The application identifier
        
        Returns:
            Monitoring configuration dictionary or None if not found
        """
        import asyncio
        loop = asyncio.get_event_loop()
        
        def query_firestore():
            doc = self.db.collection(self.monitoring_collection).document(application_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        
        return await loop.run_in_executor(None, query_firestore)
    
    async def _detect_material_changes(
        self,
        application_id: str,
        research_results: Dict[str, Any],
        monitoring_config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect material changes from research results.
        
        Material changes include:
        - Critical or high-severity red flags
        - Significant negative news
        - Regulatory actions or legal issues
        - Financial distress indicators
        
        Args:
            application_id: The application identifier
            research_results: Results from web research
            monitoring_config: Monitoring configuration
        
        Returns:
            List of detected material changes
        """
        material_changes = []
        alert_threshold = monitoring_config.get('alert_threshold', self.DEFAULT_ALERT_THRESHOLD)
        
        # Check red flags
        red_flags = research_results.get('red_flags', [])
        for flag in red_flags:
            severity = flag.get('severity', 'low')
            
            # Critical and high severity flags are always material changes
            if severity in ['critical', 'high']:
                material_changes.append({
                    'change_type': self._classify_red_flag(flag),
                    'severity': severity,
                    'description': flag.get('description', ''),
                    'details': flag.get('details', ''),
                    'source': flag.get('source', ''),
                    'date': flag.get('date', ''),
                    'confidence': 0.9 if severity == 'critical' else 0.8
                })
        
        # Check for patterns in news items that indicate material changes
        news_items = research_results.get('news_items', [])
        negative_news_count = sum(
            1 for item in news_items
            if any(keyword in item.get('title', '').lower() + item.get('summary', '').lower()
                   for keyword in ['loss', 'decline', 'drop', 'fall', 'warning', 'concern'])
        )
        
        if negative_news_count >= 3:  # Multiple negative news items
            material_changes.append({
                'change_type': ChangeType.NEGATIVE_NEWS.value,
                'severity': 'medium',
                'description': f'Multiple negative news items detected ({negative_news_count} items)',
                'details': 'Pattern of negative news coverage may indicate deteriorating conditions',
                'source': 'News Analysis',
                'date': datetime.utcnow().isoformat(),
                'confidence': 0.7
            })
        
        return material_changes
    
    def _classify_red_flag(self, red_flag: Dict[str, Any]) -> str:
        """
        Classify a red flag into a change type.
        
        Args:
            red_flag: Red flag dictionary
        
        Returns:
            Change type classification
        """
        description = red_flag.get('description', '').lower()
        details = red_flag.get('details', '').lower()
        combined = f"{description} {details}"
        
        # Check for specific patterns
        if any(keyword in combined for keyword in ['bankruptcy', 'insolvency', 'default', 'financial distress']):
            return ChangeType.FINANCIAL_DETERIORATION.value
        elif any(keyword in combined for keyword in ['regulatory', 'violation', 'investigation', 'penalty']):
            return ChangeType.REGULATORY_ACTION.value
        elif any(keyword in combined for keyword in ['lawsuit', 'litigation', 'legal']):
            return ChangeType.CREDIT_EVENT.value
        elif any(keyword in combined for keyword in ['management', 'director', 'ceo', 'cfo']):
            return ChangeType.MANAGEMENT_CHANGE.value
        else:
            return ChangeType.NEGATIVE_NEWS.value
    
    async def _generate_alerts(
        self,
        application_id: str,
        company_name: str,
        material_changes: List[Dict[str, Any]],
        research_results: Dict[str, Any]
    ) -> List[MonitoringAlert]:
        """
        Generate monitoring alerts for material changes.
        
        Args:
            application_id: The application identifier
            company_name: Company name
            material_changes: List of detected material changes
            research_results: Full research results
        
        Returns:
            List of generated monitoring alerts
        
        Requirements: 10.3, 10.4
        Property 23: Alert Generation and Notification
        """
        alerts = []
        
        for change in material_changes:
            alert_id = str(uuid.uuid4())
            
            alert = MonitoringAlert(
                id=alert_id,
                application_id=application_id,
                alert_type=change['change_type'],
                severity=change['severity'],
                message=f"{company_name}: {change['description']}",
                details={
                    'company_name': company_name,
                    'change_details': change.get('details', ''),
                    'source': change.get('source', ''),
                    'date': change.get('date', ''),
                    'confidence': change.get('confidence', 0.0),
                    'research_summary': research_results.get('summary', '')[:500]
                },
                created_at=datetime.utcnow(),
                acknowledged=False
            )
            
            # Persist alert to Firestore
            import asyncio
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda a=alert: self.db.collection(self.alerts_collection).document(a.id).set(a.model_dump())
            )
            
            # Log alert generation
            if self.audit_logger:
                try:
                    await self.audit_logger.log_monitoring_alert(
                        application_id=application_id,
                        alert_type=alert.alert_type,
                        severity=alert.severity,
                        message=alert.message,
                        alert_details=alert.details
                    )
                except Exception as e:
                    logger.error(f"Failed to log monitoring alert: {e}")
            
            # Send notifications via dashboard and email
            if self.notification_service:
                try:
                    # Get recipients for this application (in production, this would query user preferences)
                    recipients = await self._get_alert_recipients(application_id)
                    
                    notification_result = await self.notification_service.send_alert_notification(
                        alert=alert,
                        recipients=recipients,
                        additional_context={
                            'company_name': company_name,
                            'application_id': application_id
                        }
                    )
                    
                    logger.info(
                        f"Notifications sent for alert {alert_id}: "
                        f"Dashboard={notification_result['dashboard_sent']}, "
                        f"Email={notification_result['email_sent']}"
                    )
                except Exception as e:
                    logger.error(f"Failed to send notifications for alert {alert_id}: {e}")
            
            alerts.append(alert)
            
            logger.warning(
                f"Monitoring alert generated for {company_name} (app: {application_id}): "
                f"[{alert.severity.upper()}] {alert.message}"
            )
        
        return alerts
    
    async def _update_monitoring_status(
        self,
        application_id: str,
        check_timestamp: datetime,
        alerts_generated: int
    ) -> None:
        """
        Update monitoring status after a check.
        
        Args:
            application_id: The application identifier
            check_timestamp: Timestamp of the check
            alerts_generated: Number of alerts generated
        """
        import asyncio
        loop = asyncio.get_event_loop()
        
        def update_firestore():
            doc_ref = self.db.collection(self.monitoring_collection).document(application_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return
            
            config = doc.to_dict()
            total_checks = config.get('total_checks', 0) + 1
            total_alerts = config.get('total_alerts', 0) + alerts_generated
            next_check = check_timestamp + timedelta(days=config.get('check_interval_days', self.DEFAULT_CHECK_INTERVAL_DAYS))
            
            doc_ref.update({
                'last_check': check_timestamp.isoformat(),
                'next_check': next_check.isoformat(),
                'total_checks': total_checks,
                'total_alerts': total_alerts,
                'updated_at': datetime.utcnow().isoformat()
            })
        
        await loop.run_in_executor(None, update_firestore)
    
    async def get_monitoring_status(
        self,
        application_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get current monitoring status for an application.
        
        Args:
            application_id: The application identifier
        
        Returns:
            Monitoring status dictionary or None if not found
        
        Example:
            >>> status = await monitoring_service.get_monitoring_status('app123')
            >>> if status:
            ...     print(f"Status: {status['status']}, Last check: {status['last_check']}")
        """
        return await self._get_monitoring_config(application_id)
    
    async def get_alerts_for_application(
        self,
        application_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all monitoring alerts for an application.
        
        Args:
            application_id: The application identifier
            limit: Maximum number of alerts to retrieve
        
        Returns:
            List of monitoring alerts ordered by creation time (newest first)
        
        Example:
            >>> alerts = await monitoring_service.get_alerts_for_application('app123')
            >>> for alert in alerts:
            ...     print(f"[{alert['severity']}] {alert['message']}")
        """
        import asyncio
        loop = asyncio.get_event_loop()
        
        def query_firestore():
            docs = self.db.collection(self.alerts_collection).where(
                'application_id', '==', application_id
            ).order_by('created_at', direction='DESCENDING').limit(limit).stream()
            
            return [doc.to_dict() for doc in docs]
        
        return await loop.run_in_executor(None, query_firestore)
    
    async def acknowledge_alert(
        self,
        alert_id: str,
        user_id: str
    ) -> bool:
        """
        Acknowledge a monitoring alert.
        
        Args:
            alert_id: The alert identifier
            user_id: User ID acknowledging the alert
        
        Returns:
            True if alert was acknowledged, False if not found
        
        Example:
            >>> success = await monitoring_service.acknowledge_alert('alert123', 'user456')
        """
        import asyncio
        loop = asyncio.get_event_loop()
        
        def update_firestore():
            doc_ref = self.db.collection(self.alerts_collection).document(alert_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            doc_ref.update({
                'acknowledged': True,
                'acknowledged_by': user_id,
                'acknowledged_at': datetime.utcnow().isoformat()
            })
            return True
        
        success = await loop.run_in_executor(None, update_firestore)
        
        if success and self.audit_logger:
            try:
                alert_data = await loop.run_in_executor(
                    None,
                    lambda: self.db.collection(self.alerts_collection).document(alert_id).get().to_dict()
                )
                await self.audit_logger.log_user_action(
                    action='acknowledge_alert',
                    resource_type='monitoring_alert',
                    resource_id=alert_id,
                    user_id=user_id,
                    details={
                        'application_id': alert_data.get('application_id'),
                        'alert_type': alert_data.get('alert_type'),
                        'severity': alert_data.get('severity')
                    }
                )
            except Exception as e:
                logger.error(f"Failed to log alert acknowledgment: {e}")
        
        return success
    
    async def get_applications_due_for_check(
        self,
        current_time: Optional[datetime] = None
    ) -> List[str]:
        """
        Get list of application IDs that are due for monitoring check.
        
        This method is used by a scheduler to identify which applications
        need to be checked.
        
        Args:
            current_time: Current time (defaults to now)
        
        Returns:
            List of application IDs due for check
        
        Example:
            >>> due_apps = await monitoring_service.get_applications_due_for_check()
            >>> for app_id in due_apps:
            ...     await monitoring_service.perform_monitoring_check(app_id)
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        import asyncio
        loop = asyncio.get_event_loop()
        
        def query_firestore():
            docs = self.db.collection(self.monitoring_collection).where(
                'status', '==', MonitoringStatus.ACTIVE.value
            ).where(
                'next_check', '<=', current_time.isoformat()
            ).stream()
            
            return [doc.to_dict()['application_id'] for doc in docs]
        
        return await loop.run_in_executor(None, query_firestore)

    async def _get_alert_recipients(
        self,
        application_id: str
    ) -> List[str]:
        """
        Get list of email recipients for alert notifications.
        
        In production, this would query user preferences and application
        ownership to determine who should receive alerts.
        
        For now, returns an empty list (notifications will still be sent
        to dashboard, but email requires configuration).
        
        Args:
            application_id: The application identifier
        
        Returns:
            List of email addresses to notify
        """
        # TODO: Implement user preference querying
        # This would typically:
        # 1. Query the application to find the owner/analyst
        # 2. Query user preferences for notification settings
        # 3. Return list of email addresses
        
        # For now, return empty list (dashboard notifications will still work)
        return []
