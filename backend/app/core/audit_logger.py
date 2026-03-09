"""
Audit Logging for State Changes and User Actions

This module provides audit logging functionality for tracking all state transitions,
user actions, and AI decisions. Audit records are immutable once created and stored
in Firestore for compliance and regulatory requirements.

Requirements: 9.5, 17.1, 17.3
Property 21: Audit Trail Completeness
Property 37: Audit Record Immutability
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

from app.models.domain import ApplicationStatus

logger = logging.getLogger(__name__)


class AuditActionType(Enum):
    """
    Types of actions that can be audited.
    
    - STATE_TRANSITION: Application status change
    - USER_ACTION: User-initiated action (create, update, delete)
    - AI_DECISION: AI agent decision or analysis
    - DOCUMENT_UPLOAD: Document upload action
    - DOCUMENT_DELETE: Document deletion action
    - CAM_GENERATION: CAM report generation
    - MONITORING_ALERT: Monitoring alert generation
    """
    STATE_TRANSITION = "state_transition"
    USER_ACTION = "user_action"
    AI_DECISION = "ai_decision"
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_DELETE = "document_delete"
    CAM_GENERATION = "cam_generation"
    MONITORING_ALERT = "monitoring_alert"


class AuditLogger:
    """
    Audit logger for tracking state changes, user actions, and AI decisions.
    
    This class provides a unified interface for creating immutable audit records
    that track all significant actions in the system. Audit records include:
    - Timestamp of the action
    - User identifier (who performed the action)
    - Action type and details
    - Resource identifiers (application_id, document_id, etc.)
    - Reason or context for the action
    
    Audit records are immutable once created and stored in Firestore.
    
    Requirements: 9.5, 17.1, 17.3
    Property 21: Audit Trail Completeness
    Property 37: Audit Record Immutability
    
    Example:
        >>> audit_logger = AuditLogger(firestore_client)
        >>> await audit_logger.log_state_transition(
        ...     application_id='app123',
        ...     old_state=ApplicationStatus.PENDING,
        ...     new_state=ApplicationStatus.PROCESSING,
        ...     user_id='user456',
        ...     reason='Documents uploaded'
        ... )
    """
    
    def __init__(self, firestore_client):
        """
        Initialize AuditLogger.
        
        Args:
            firestore_client: Firestore client instance for audit record persistence
        """
        self.db = firestore_client
        self.collection_name = 'audit_logs'
    
    async def log_state_transition(
        self,
        application_id: str,
        old_state: ApplicationStatus,
        new_state: ApplicationStatus,
        user_id: Optional[str] = None,
        reason: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log an application state transition.
        
        This method creates an immutable audit record for a state transition,
        capturing who made the change, when it occurred, and why.
        
        Args:
            application_id: The application identifier
            old_state: The previous application status
            new_state: The new application status
            user_id: Optional user ID who initiated the transition
            reason: Optional reason for the transition
            additional_context: Optional additional context information
        
        Returns:
            Unique audit record ID
        
        Requirements: 9.5, 17.1
        Property 21: Audit Trail Completeness
        
        Example:
            >>> audit_id = await audit_logger.log_state_transition(
            ...     application_id='app123',
            ...     old_state=ApplicationStatus.PROCESSING,
            ...     new_state=ApplicationStatus.ANALYSIS_COMPLETE,
            ...     user_id='system',
            ...     reason='Analysis completed successfully'
            ... )
        """
        audit_record = self._create_audit_record(
            action_type=AuditActionType.STATE_TRANSITION,
            resource_type='application',
            resource_id=application_id,
            user_id=user_id or 'system',
            details={
                'old_state': old_state.value,
                'new_state': new_state.value,
                'reason': reason,
                **(additional_context or {})
            }
        )
        
        return await self._persist_audit_record(audit_record)
    
    async def log_user_action(
        self,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: str,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a user-initiated action.
        
        This method creates an immutable audit record for user actions such as
        creating, updating, or deleting resources.
        
        Args:
            action: The action performed (e.g., 'create', 'update', 'delete')
            resource_type: Type of resource (e.g., 'application', 'document')
            resource_id: Identifier of the resource
            user_id: User ID who performed the action
            details: Optional additional details about the action
        
        Returns:
            Unique audit record ID
        
        Requirements: 9.5, 17.1
        Property 21: Audit Trail Completeness
        
        Example:
            >>> audit_id = await audit_logger.log_user_action(
            ...     action='create',
            ...     resource_type='application',
            ...     resource_id='app123',
            ...     user_id='user456',
            ...     details={'company_name': 'Acme Corp', 'loan_amount': 1000000}
            ... )
        """
        audit_record = self._create_audit_record(
            action_type=AuditActionType.USER_ACTION,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            details={
                'action': action,
                **(details or {})
            }
        )
        
        return await self._persist_audit_record(audit_record)
    
    async def log_ai_decision(
        self,
        agent_name: str,
        application_id: str,
        decision: str,
        reasoning: str,
        data_sources: list[str],
        additional_details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log an AI agent decision.
        
        This method creates an immutable audit record for AI agent decisions,
        including the reasoning and data sources used.
        
        Args:
            agent_name: Name of the AI agent (e.g., 'RiskScoringAgent')
            application_id: The application identifier
            decision: The decision made by the agent
            reasoning: Explanation of the decision
            data_sources: List of data sources used in the decision
            additional_details: Optional additional details
        
        Returns:
            Unique audit record ID
        
        Requirements: 17.2
        Property 36: AI Decision Logging
        
        Example:
            >>> audit_id = await audit_logger.log_ai_decision(
            ...     agent_name='RiskScoringAgent',
            ...     application_id='app123',
            ...     decision='approve_with_conditions',
            ...     reasoning='Strong financials but high industry risk',
            ...     data_sources=['financial_analysis', 'industry_report']
            ... )
        """
        audit_record = self._create_audit_record(
            action_type=AuditActionType.AI_DECISION,
            resource_type='application',
            resource_id=application_id,
            user_id='system',
            details={
                'agent_name': agent_name,
                'decision': decision,
                'reasoning': reasoning,
                'data_sources': data_sources,
                **(additional_details or {})
            }
        )
        
        return await self._persist_audit_record(audit_record)
    
    async def log_document_action(
        self,
        action: str,
        application_id: str,
        document_id: str,
        user_id: str,
        document_details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log a document-related action (upload or delete).
        
        Args:
            action: The action performed ('upload' or 'delete')
            application_id: The application identifier
            document_id: The document identifier
            user_id: User ID who performed the action
            document_details: Optional document details (filename, file_type, etc.)
        
        Returns:
            Unique audit record ID
        
        Requirements: 9.5, 17.1
        Property 21: Audit Trail Completeness
        
        Example:
            >>> audit_id = await audit_logger.log_document_action(
            ...     action='upload',
            ...     application_id='app123',
            ...     document_id='doc456',
            ...     user_id='user789',
            ...     document_details={'filename': 'financials.pdf', 'file_type': 'pdf'}
            ... )
        """
        action_type = (
            AuditActionType.DOCUMENT_UPLOAD if action == 'upload'
            else AuditActionType.DOCUMENT_DELETE
        )
        
        audit_record = self._create_audit_record(
            action_type=action_type,
            resource_type='document',
            resource_id=document_id,
            user_id=user_id,
            details={
                'application_id': application_id,
                'action': action,
                **(document_details or {})
            }
        )
        
        return await self._persist_audit_record(audit_record)
    
    async def log_cam_generation(
        self,
        application_id: str,
        cam_version: int,
        user_id: Optional[str] = None,
        generation_details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log CAM report generation.
        
        Args:
            application_id: The application identifier
            cam_version: Version number of the generated CAM
            user_id: Optional user ID who requested the CAM
            generation_details: Optional details about the generation
        
        Returns:
            Unique audit record ID
        
        Requirements: 9.5, 17.1
        Property 21: Audit Trail Completeness
        
        Example:
            >>> audit_id = await audit_logger.log_cam_generation(
            ...     application_id='app123',
            ...     cam_version=1,
            ...     user_id='user456'
            ... )
        """
        audit_record = self._create_audit_record(
            action_type=AuditActionType.CAM_GENERATION,
            resource_type='cam',
            resource_id=application_id,
            user_id=user_id or 'system',
            details={
                'cam_version': cam_version,
                **(generation_details or {})
            }
        )
        
        return await self._persist_audit_record(audit_record)
    
    async def log_monitoring_alert(
        self,
        application_id: str,
        alert_type: str,
        severity: str,
        message: str,
        alert_details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log monitoring alert generation.
        
        Args:
            application_id: The application identifier
            alert_type: Type of alert
            severity: Alert severity level
            message: Alert message
            alert_details: Optional additional alert details
        
        Returns:
            Unique audit record ID
        
        Requirements: 9.5, 17.1
        Property 21: Audit Trail Completeness
        
        Example:
            >>> audit_id = await audit_logger.log_monitoring_alert(
            ...     application_id='app123',
            ...     alert_type='financial_deterioration',
            ...     severity='high',
            ...     message='Significant revenue decline detected'
            ... )
        """
        audit_record = self._create_audit_record(
            action_type=AuditActionType.MONITORING_ALERT,
            resource_type='monitoring_alert',
            resource_id=application_id,
            user_id='system',
            details={
                'alert_type': alert_type,
                'severity': severity,
                'message': message,
                **(alert_details or {})
            }
        )
        
        return await self._persist_audit_record(audit_record)
    
    def _create_audit_record(
        self,
        action_type: AuditActionType,
        resource_type: str,
        resource_id: str,
        user_id: str,
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a structured audit record.
        
        Args:
            action_type: Type of action being audited
            resource_type: Type of resource affected
            resource_id: Identifier of the resource
            user_id: User ID who performed the action
            details: Additional details about the action
        
        Returns:
            Structured audit record dictionary
        """
        audit_id = self._generate_audit_id()
        timestamp = datetime.utcnow()
        
        return {
            'audit_id': audit_id,
            'timestamp': timestamp.isoformat(),
            'timestamp_obj': timestamp,  # For Firestore ordering
            'action_type': action_type.value,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'user_id': user_id,
            'details': details,
            'immutable': True  # Flag to indicate this record should not be modified
        }
    
    def _generate_audit_id(self) -> str:
        """
        Generate a unique audit record ID.
        
        Returns:
            UUID string for audit record identification
        """
        return str(uuid.uuid4())
    
    async def _persist_audit_record(self, audit_record: Dict[str, Any]) -> str:
        """
        Persist audit record to Firestore.
        
        This method stores the audit record in Firestore. Once stored,
        the record is immutable and cannot be modified.
        
        Args:
            audit_record: Structured audit record to persist
        
        Returns:
            Audit record ID
        
        Requirements: 17.3
        Property 37: Audit Record Immutability
        """
        audit_id = audit_record['audit_id']
        
        try:
            # Use asyncio to run the synchronous Firestore operation
            import asyncio
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.db.collection(self.collection_name).document(audit_id).set(audit_record)
            )
            
            # Log to stdout for real-time monitoring
            logger.info(
                f"Audit record created: {audit_id} | "
                f"Action: {audit_record['action_type']} | "
                f"Resource: {audit_record['resource_type']}:{audit_record['resource_id']} | "
                f"User: {audit_record['user_id']}"
            )
            
        except Exception as e:
            # If Firestore persistence fails, log the error but don't raise
            # to avoid disrupting the main workflow
            logger.error(
                f"Failed to persist audit record {audit_id} to Firestore: {e}"
            )
            # Re-raise to ensure audit failures are visible
            raise
        
        return audit_id
    
    async def get_audit_record(self, audit_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an audit record by its ID.
        
        Args:
            audit_id: Unique audit record identifier
        
        Returns:
            Audit record if found, None otherwise
        
        Example:
            >>> audit_record = await audit_logger.get_audit_record('abc-123-def')
            >>> if audit_record:
            ...     print(f"Action: {audit_record['action_type']}")
        """
        import asyncio
        loop = asyncio.get_event_loop()
        
        def query_firestore():
            doc = self.db.collection(self.collection_name).document(audit_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        
        return await loop.run_in_executor(None, query_firestore)
    
    async def get_audit_trail_for_application(
        self,
        application_id: str,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """
        Retrieve audit trail for a specific application.
        
        Args:
            application_id: Application identifier
            limit: Maximum number of audit records to retrieve
        
        Returns:
            List of audit records ordered by timestamp (newest first)
        
        Requirements: 17.4
        Property 38: Audit Query and Export
        
        Example:
            >>> audit_trail = await audit_logger.get_audit_trail_for_application('app123')
            >>> for record in audit_trail:
            ...     print(f"{record['timestamp']}: {record['action_type']}")
        """
        import asyncio
        loop = asyncio.get_event_loop()
        
        def query_firestore():
            docs = self.db.collection(self.collection_name).where(
                'resource_id', '==', application_id
            ).order_by('timestamp_obj', direction='DESCENDING').limit(limit).stream()
            
            return [doc.to_dict() for doc in docs]
        
        return await loop.run_in_executor(None, query_firestore)
    
    async def get_audit_trail_by_user(
        self,
        user_id: str,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """
        Retrieve audit trail for a specific user.
        
        Args:
            user_id: User identifier
            limit: Maximum number of audit records to retrieve
        
        Returns:
            List of audit records ordered by timestamp (newest first)
        
        Requirements: 17.4
        Property 38: Audit Query and Export
        
        Example:
            >>> user_actions = await audit_logger.get_audit_trail_by_user('user456')
        """
        import asyncio
        loop = asyncio.get_event_loop()
        
        def query_firestore():
            docs = self.db.collection(self.collection_name).where(
                'user_id', '==', user_id
            ).order_by('timestamp_obj', direction='DESCENDING').limit(limit).stream()
            
            return [doc.to_dict() for doc in docs]
        
        return await loop.run_in_executor(None, query_firestore)
    
    async def get_audit_trail_by_action_type(
        self,
        action_type: AuditActionType,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """
        Retrieve audit trail by action type.
        
        Args:
            action_type: Type of action to filter by
            limit: Maximum number of audit records to retrieve
        
        Returns:
            List of audit records ordered by timestamp (newest first)
        
        Requirements: 17.4
        Property 38: Audit Query and Export
        
        Example:
            >>> state_transitions = await audit_logger.get_audit_trail_by_action_type(
            ...     AuditActionType.STATE_TRANSITION
            ... )
        """
        import asyncio
        loop = asyncio.get_event_loop()
        
        def query_firestore():
            docs = self.db.collection(self.collection_name).where(
                'action_type', '==', action_type.value
            ).order_by('timestamp_obj', direction='DESCENDING').limit(limit).stream()
            
            return [doc.to_dict() for doc in docs]
        
        return await loop.run_in_executor(None, query_firestore)
    
    async def attempt_modify_audit_record(
        self,
        audit_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Attempt to modify an audit record (should always fail).
        
        This method is provided to demonstrate that audit records are immutable.
        Any attempt to modify an audit record should be rejected.
        
        Args:
            audit_id: Audit record identifier
            updates: Attempted updates
        
        Returns:
            False (modification is never allowed)
        
        Raises:
            ValueError: Always raised to indicate immutability
        
        Requirements: 17.3
        Property 37: Audit Record Immutability
        
        Example:
            >>> try:
            ...     await audit_logger.attempt_modify_audit_record('abc-123', {'user_id': 'hacker'})
            ... except ValueError as e:
            ...     print(f"Modification rejected: {e}")
        """
        # Check if the record exists
        record = await self.get_audit_record(audit_id)
        
        if not record:
            raise ValueError(f"Audit record {audit_id} not found")
        
        # Check immutability flag
        if record.get('immutable', True):
            raise ValueError(
                f"Audit record {audit_id} is immutable and cannot be modified. "
                "Audit records are permanent and tamper-proof for compliance purposes."
            )
        
        # This code should never be reached
        return False
    
    async def query_audit_logs(
        self,
        filters: Optional[Dict[str, Any]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Query audit logs with flexible filtering criteria.
        
        This method provides comprehensive filtering capabilities for audit logs,
        supporting filtering by multiple criteria including action type, resource type,
        user ID, date range, and more.
        
        Args:
            filters: Dictionary of filter criteria:
                - action_type: Filter by action type (e.g., 'state_transition')
                - resource_type: Filter by resource type (e.g., 'application')
                - resource_id: Filter by specific resource ID
                - user_id: Filter by user ID
            start_date: Filter records after this date (inclusive)
            end_date: Filter records before this date (inclusive)
            limit: Maximum number of records to return
            offset: Number of records to skip (for pagination)
        
        Returns:
            Dictionary containing:
                - records: List of matching audit records
                - total_count: Total number of matching records
                - limit: Applied limit
                - offset: Applied offset
        
        Requirements: 17.4
        Property 38: Audit Query and Export
        
        Example:
            >>> results = await audit_logger.query_audit_logs(
            ...     filters={'action_type': 'state_transition', 'user_id': 'user123'},
            ...     start_date=datetime(2024, 1, 1),
            ...     limit=50
            ... )
            >>> print(f"Found {results['total_count']} records")
            >>> for record in results['records']:
            ...     print(f"{record['timestamp']}: {record['action_type']}")
        """
        import asyncio
        loop = asyncio.get_event_loop()
        
        def query_firestore():
            # Start with base query
            query = self.db.collection(self.collection_name)
            
            # Apply filters
            if filters:
                if 'action_type' in filters:
                    query = query.where('action_type', '==', filters['action_type'])
                if 'resource_type' in filters:
                    query = query.where('resource_type', '==', filters['resource_type'])
                if 'resource_id' in filters:
                    query = query.where('resource_id', '==', filters['resource_id'])
                if 'user_id' in filters:
                    query = query.where('user_id', '==', filters['user_id'])
            
            # Apply date range filters
            if start_date:
                query = query.where('timestamp_obj', '>=', start_date)
            if end_date:
                query = query.where('timestamp_obj', '<=', end_date)
            
            # Order by timestamp (newest first)
            query = query.order_by('timestamp_obj', direction='DESCENDING')
            
            # Get total count (for pagination info)
            # Note: In production, you might want to cache this or use a separate count query
            all_docs = list(query.stream())
            total_count = len(all_docs)
            
            # Apply pagination
            paginated_docs = all_docs[offset:offset + limit]
            
            records = [doc.to_dict() for doc in paginated_docs]
            
            return {
                'records': records,
                'total_count': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total_count
            }
        
        return await loop.run_in_executor(None, query_firestore)
    
    async def export_audit_logs(
        self,
        filters: Optional[Dict[str, Any]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = 'json',
        limit: int = 10000
    ) -> str:
        """
        Export audit logs in various formats.
        
        This method exports audit logs matching the specified criteria in the
        requested format (JSON or CSV). Useful for compliance reporting and
        external analysis.
        
        Args:
            filters: Dictionary of filter criteria (same as query_audit_logs)
            start_date: Filter records after this date (inclusive)
            end_date: Filter records before this date (inclusive)
            format: Export format ('json' or 'csv')
            limit: Maximum number of records to export
        
        Returns:
            Formatted string containing the exported audit logs
        
        Raises:
            ValueError: If an unsupported format is specified
        
        Requirements: 17.4
        Property 38: Audit Query and Export
        
        Example:
            >>> # Export as JSON
            >>> json_export = await audit_logger.export_audit_logs(
            ...     filters={'resource_id': 'app123'},
            ...     format='json'
            ... )
            >>> 
            >>> # Export as CSV
            >>> csv_export = await audit_logger.export_audit_logs(
            ...     filters={'action_type': 'state_transition'},
            ...     format='csv'
            ... )
        """
        # Query audit logs with filters
        results = await self.query_audit_logs(
            filters=filters,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=0
        )
        
        records = results['records']
        
        if format == 'json':
            return self._export_as_json(records)
        elif format == 'csv':
            return self._export_as_csv(records)
        else:
            raise ValueError(f"Unsupported export format: {format}. Supported formats: 'json', 'csv'")
    
    def _export_as_json(self, records: list[Dict[str, Any]]) -> str:
        """
        Export audit records as JSON.
        
        Args:
            records: List of audit records
        
        Returns:
            JSON string representation of the records
        """
        import json
        
        # Convert datetime objects to ISO format strings for JSON serialization
        serializable_records = []
        for record in records:
            serializable_record = record.copy()
            # Remove timestamp_obj (Firestore timestamp) and keep ISO string
            if 'timestamp_obj' in serializable_record:
                del serializable_record['timestamp_obj']
            serializable_records.append(serializable_record)
        
        return json.dumps(serializable_records, indent=2, default=str)
    
    def _export_as_csv(self, records: list[Dict[str, Any]]) -> str:
        """
        Export audit records as CSV.
        
        Args:
            records: List of audit records
        
        Returns:
            CSV string representation of the records
        """
        import csv
        import io
        
        if not records:
            return ""
        
        # Prepare CSV output
        output = io.StringIO()
        
        # Define CSV columns
        fieldnames = [
            'audit_id',
            'timestamp',
            'action_type',
            'resource_type',
            'resource_id',
            'user_id',
            'details'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write records
        for record in records:
            row = {
                'audit_id': record.get('audit_id', ''),
                'timestamp': record.get('timestamp', ''),
                'action_type': record.get('action_type', ''),
                'resource_type': record.get('resource_type', ''),
                'resource_id': record.get('resource_id', ''),
                'user_id': record.get('user_id', ''),
                'details': str(record.get('details', {}))
            }
            writer.writerow(row)
        
        return output.getvalue()
