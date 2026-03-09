"""
Notification Service for Alert Delivery

This service handles sending notifications via multiple channels (dashboard, email)
when monitoring alerts are generated.

Requirements: 10.4
Property 23: Alert Generation and Notification
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.domain import MonitoringAlert

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending notifications via multiple channels.
    
    This service:
    - Sends dashboard notifications (stored in Firestore)
    - Sends email notifications to relevant users
    - Tracks notification delivery status
    - Handles notification failures gracefully
    
    Requirements: 10.4
    Property 23: Alert Generation and Notification
    
    Example:
        >>> notification_service = NotificationService(
        ...     firestore_client=db,
        ...     smtp_host='smtp.gmail.com',
        ...     smtp_port=587,
        ...     smtp_user='alerts@example.com',
        ...     smtp_password='password'
        ... )
        >>> await notification_service.send_alert_notification(
        ...     alert=alert,
        ...     recipients=['user@example.com']
        ... )
    """
    
    def __init__(
        self,
        firestore_client,
        smtp_host: Optional[str] = None,
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        smtp_from_email: Optional[str] = None,
        enable_email: bool = True
    ):
        """
        Initialize the Notification Service.
        
        Args:
            firestore_client: Firestore client for dashboard notifications
            smtp_host: SMTP server hostname (e.g., 'smtp.gmail.com')
            smtp_port: SMTP server port (default: 587 for TLS)
            smtp_user: SMTP username for authentication
            smtp_password: SMTP password for authentication
            smtp_from_email: Email address to send from
            enable_email: Whether to enable email notifications
        """
        self.db = firestore_client
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_from_email = smtp_from_email or smtp_user
        self.enable_email = enable_email and all([smtp_host, smtp_user, smtp_password])
        
        self.notifications_collection = 'dashboard_notifications'
        
        if not self.enable_email:
            logger.warning(
                "Email notifications are disabled. "
                "Configure SMTP settings to enable email notifications."
            )
    
    async def send_alert_notification(
        self,
        alert: MonitoringAlert,
        recipients: List[str],
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send alert notification via dashboard and email.
        
        This method:
        1. Creates a dashboard notification (stored in Firestore)
        2. Sends email notifications to all recipients
        3. Tracks delivery status
        
        Args:
            alert: The monitoring alert to send
            recipients: List of email addresses to notify
            additional_context: Optional additional context for the notification
        
        Returns:
            Dictionary containing notification delivery status
        
        Requirements: 10.4
        Property 23: Alert Generation and Notification
        
        Example:
            >>> result = await notification_service.send_alert_notification(
            ...     alert=alert,
            ...     recipients=['analyst@bank.com', 'manager@bank.com']
            ... )
            >>> if result['dashboard_sent']:
            ...     print("Dashboard notification created")
            >>> if result['email_sent']:
            ...     print(f"Email sent to {len(result['email_recipients'])} recipients")
        """
        notification_id = alert.id
        results = {
            'notification_id': notification_id,
            'alert_id': alert.id,
            'dashboard_sent': False,
            'email_sent': False,
            'email_recipients': [],
            'email_failures': [],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # 1. Create dashboard notification
        try:
            await self._create_dashboard_notification(alert, additional_context)
            results['dashboard_sent'] = True
            logger.info(f"Dashboard notification created for alert {alert.id}")
        except Exception as e:
            logger.error(f"Failed to create dashboard notification for alert {alert.id}: {e}")
            results['dashboard_error'] = str(e)
        
        # 2. Send email notifications
        if self.enable_email and recipients:
            email_results = await self._send_email_notifications(
                alert=alert,
                recipients=recipients,
                additional_context=additional_context
            )
            results['email_sent'] = email_results['success']
            results['email_recipients'] = email_results['successful_recipients']
            results['email_failures'] = email_results['failed_recipients']
            
            if email_results['success']:
                logger.info(
                    f"Email notifications sent for alert {alert.id} "
                    f"to {len(email_results['successful_recipients'])} recipients"
                )
            else:
                logger.warning(
                    f"Email notification failed for alert {alert.id}: "
                    f"{email_results.get('error', 'Unknown error')}"
                )
        elif not self.enable_email:
            logger.debug(f"Email notifications disabled for alert {alert.id}")
        
        return results
    
    async def _create_dashboard_notification(
        self,
        alert: MonitoringAlert,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Create a dashboard notification in Firestore.
        
        Dashboard notifications are displayed in the user interface
        and can be acknowledged by users.
        
        Args:
            alert: The monitoring alert
            additional_context: Optional additional context
        """
        notification = {
            'notification_id': alert.id,
            'alert_id': alert.id,
            'application_id': alert.application_id,
            'type': 'monitoring_alert',
            'severity': alert.severity,
            'title': f"Monitoring Alert: {alert.alert_type.replace('_', ' ').title()}",
            'message': alert.message,
            'details': alert.details,
            'created_at': alert.created_at.isoformat(),
            'read': False,
            'acknowledged': alert.acknowledged,
            'additional_context': additional_context or {}
        }
        
        # Persist to Firestore
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.db.collection(self.notifications_collection).document(alert.id).set(notification)
        )
    
    async def _send_email_notifications(
        self,
        alert: MonitoringAlert,
        recipients: List[str],
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send email notifications to recipients.
        
        Args:
            alert: The monitoring alert
            recipients: List of email addresses
            additional_context: Optional additional context
        
        Returns:
            Dictionary with success status and recipient lists
        """
        if not self.enable_email:
            return {
                'success': False,
                'error': 'Email notifications not configured',
                'successful_recipients': [],
                'failed_recipients': recipients
            }
        
        successful_recipients = []
        failed_recipients = []
        
        # Compose email
        subject = f"[{alert.severity.upper()}] Monitoring Alert: {alert.alert_type.replace('_', ' ').title()}"
        body = self._compose_email_body(alert, additional_context)
        
        # Send to each recipient
        for recipient in recipients:
            try:
                await self._send_email(
                    to_email=recipient,
                    subject=subject,
                    body=body
                )
                successful_recipients.append(recipient)
            except Exception as e:
                logger.error(f"Failed to send email to {recipient}: {e}")
                failed_recipients.append({
                    'email': recipient,
                    'error': str(e)
                })
        
        return {
            'success': len(successful_recipients) > 0,
            'successful_recipients': successful_recipients,
            'failed_recipients': failed_recipients
        }
    
    def _compose_email_body(
        self,
        alert: MonitoringAlert,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Compose email body for alert notification.
        
        Args:
            alert: The monitoring alert
            additional_context: Optional additional context
        
        Returns:
            HTML email body
        """
        severity_colors = {
            'low': '#3498db',
            'medium': '#f39c12',
            'high': '#e74c3c',
            'critical': '#c0392b'
        }
        
        severity_color = severity_colors.get(alert.severity, '#95a5a6')
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {severity_color}; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-top: none; }}
                .footer {{ background-color: #f1f1f1; padding: 15px; text-align: center; font-size: 12px; color: #666; }}
                .detail-row {{ margin: 10px 0; }}
                .detail-label {{ font-weight: bold; color: #555; }}
                .severity-badge {{ 
                    display: inline-block; 
                    padding: 5px 10px; 
                    background-color: {severity_color}; 
                    color: white; 
                    border-radius: 3px; 
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Monitoring Alert</h2>
                    <p><span class="severity-badge">{alert.severity.upper()}</span></p>
                </div>
                <div class="content">
                    <div class="detail-row">
                        <span class="detail-label">Alert Type:</span> {alert.alert_type.replace('_', ' ').title()}
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Application ID:</span> {alert.application_id}
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Message:</span><br>
                        {alert.message}
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Time:</span> {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
                    </div>
        """
        
        # Add details if available
        if alert.details:
            html += """
                    <div class="detail-row">
                        <span class="detail-label">Details:</span><br>
            """
            for key, value in alert.details.items():
                if key not in ['research_summary']:  # Skip very long fields
                    html += f"                        <div style='margin-left: 20px;'><strong>{key.replace('_', ' ').title()}:</strong> {value}</div>\n"
            html += "                    </div>\n"
        
        html += """
                    <div class="detail-row" style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd;">
                        <p><strong>Action Required:</strong> Please review this alert in the Intelli-Credit dashboard and take appropriate action.</p>
                    </div>
                </div>
                <div class="footer">
                    <p>This is an automated notification from the Intelli-Credit Monitoring System.</p>
                    <p>Do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    async def _send_email(
        self,
        to_email: str,
        subject: str,
        body: str
    ) -> None:
        """
        Send an email using SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (HTML)
        
        Raises:
            Exception: If email sending fails
        """
        import asyncio
        loop = asyncio.get_event_loop()
        
        def send_smtp():
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_from_email
            msg['To'] = to_email
            
            # Attach HTML body
            html_part = MIMEText(body, 'html')
            msg.attach(html_part)
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
        
        await loop.run_in_executor(None, send_smtp)
    
    async def get_dashboard_notifications(
        self,
        application_id: Optional[str] = None,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get dashboard notifications.
        
        Args:
            application_id: Optional filter by application ID
            unread_only: If True, only return unread notifications
            limit: Maximum number of notifications to return
        
        Returns:
            List of dashboard notifications
        
        Example:
            >>> notifications = await notification_service.get_dashboard_notifications(
            ...     application_id='app123',
            ...     unread_only=True
            ... )
        """
        import asyncio
        loop = asyncio.get_event_loop()
        
        def query_firestore():
            query = self.db.collection(self.notifications_collection)
            
            if application_id:
                query = query.where('application_id', '==', application_id)
            
            if unread_only:
                query = query.where('read', '==', False)
            
            query = query.order_by('created_at', direction='DESCENDING').limit(limit)
            
            docs = query.stream()
            return [doc.to_dict() for doc in docs]
        
        return await loop.run_in_executor(None, query_firestore)
    
    async def mark_notification_as_read(
        self,
        notification_id: str,
        user_id: str
    ) -> bool:
        """
        Mark a dashboard notification as read.
        
        Args:
            notification_id: Notification identifier
            user_id: User ID marking the notification as read
        
        Returns:
            True if successful, False otherwise
        
        Example:
            >>> success = await notification_service.mark_notification_as_read(
            ...     notification_id='notif123',
            ...     user_id='user456'
            ... )
        """
        import asyncio
        loop = asyncio.get_event_loop()
        
        def update_firestore():
            doc_ref = self.db.collection(self.notifications_collection).document(notification_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            doc_ref.update({
                'read': True,
                'read_by': user_id,
                'read_at': datetime.utcnow().isoformat()
            })
            return True
        
        return await loop.run_in_executor(None, update_firestore)
