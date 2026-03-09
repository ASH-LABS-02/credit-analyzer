"""
Centralized Error Logging

This module provides centralized error logging functionality with structured
error data storage in SQLite3. All errors across the platform are logged
with unique IDs for tracking and debugging.

Requirements: 15.5
"""

import logging
import traceback
import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """
    Error severity levels.
    
    - DEBUG: Debugging information
    - INFO: Informational messages
    - WARNING: Warning messages
    - ERROR: Error messages
    - CRITICAL: Critical errors requiring immediate attention
    """
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorLogger:
    """
    Centralized error logger with structured error logging to SQLite3.
    
    This class provides a unified interface for logging errors across the platform.
    All errors are logged with unique IDs for tracking, structured context data,
    and stored in SQLite3 for persistence and analysis.
    
    Requirements: 15.5
    
    Example:
        >>> from app.database.config import get_db_config
        >>> db_session = get_db_config().get_session()
        >>> error_logger = ErrorLogger(db_session)
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     error_id = error_logger.log_error_sync(
        ...         error=e,
        ...         context={'application_id': 'app123', 'agent': 'DocumentIntelligence'},
        ...         severity=ErrorSeverity.ERROR
        ...     )
        ...     print(f"Error logged with ID: {error_id}")
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize ErrorLogger.
        
        Args:
            db_session: SQLAlchemy database session for error persistence
        """
        self.db = db_session
    
    def log_error_sync(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        user_id: Optional[str] = None,
        application_id: Optional[str] = None
    ) -> str:
        """
        Log an error with structured data to SQLite3.
        
        This method creates a structured error log entry with a unique ID,
        stores it in the database, and logs it to stdout for real-time monitoring.
        
        Args:
            error: The exception that occurred
            context: Additional context information (e.g., application_id, agent_name)
            severity: Error severity level
            user_id: Optional user ID associated with the error
            application_id: Optional application ID associated with the error
        
        Returns:
            Unique error ID for tracking
        
        Requirements: 15.5
        
        Example:
            >>> error_id = error_logger.log_error_sync(
            ...     error=ValueError("Invalid input"),
            ...     context={'function': 'process_document', 'document_id': 'doc123'},
            ...     severity=ErrorSeverity.WARNING
            ... )
        """
        # Generate unique error ID
        error_id = self._generate_error_id()
        
        # Build structured log entry
        log_entry = self._build_log_entry(
            error_id=error_id,
            error=error,
            context=context or {},
            severity=severity,
            user_id=user_id,
            application_id=application_id
        )
        
        # Log to database for persistence
        try:
            self._persist_to_database(log_entry)
        except Exception as persist_error:
            logger.error(
                f"Failed to persist error log to database: {persist_error}. "
                f"Original error: {error}"
            )
        
        # Log to stdout for real-time monitoring
        self._log_to_stdout(log_entry)
        
        return error_id
    
    async def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        user_id: Optional[str] = None,
        application_id: Optional[str] = None
    ) -> str:
        """
        Async version of log_error for compatibility with async code.
        
        Args:
            error: The exception that occurred
            context: Additional context information
            severity: Error severity level
            user_id: Optional user ID associated with the error
            application_id: Optional application ID associated with the error
        
        Returns:
            Unique error ID for tracking
        """
        # Just call the sync version since SQLAlchemy operations are synchronous
        return self.log_error_sync(error, context, severity, user_id, application_id)
    
    def _generate_error_id(self) -> str:
        """
        Generate a unique error ID for tracking.
        
        Returns:
            UUID string for error identification
        """
        return str(uuid.uuid4())
    
    def _build_log_entry(
        self,
        error_id: str,
        error: Exception,
        context: Dict[str, Any],
        severity: ErrorSeverity,
        user_id: Optional[str],
        application_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Build a structured log entry with all error information.
        
        Args:
            error_id: Unique error identifier
            error: The exception that occurred
            context: Additional context information
            severity: Error severity level
            user_id: Optional user ID
            application_id: Optional application ID
        
        Returns:
            Structured log entry dictionary
        """
        log_entry = {
            'error_id': error_id,
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'stack_trace': traceback.format_exc(),
            'severity': severity.value,
            'context': context
        }
        
        # Add optional fields if provided
        if user_id:
            log_entry['user_id'] = user_id
        
        if application_id:
            log_entry['application_id'] = application_id
        
        return log_entry
    
    def _persist_to_database(self, log_entry: Dict[str, Any]):
        """
        Persist error log entry to SQLite3 database.
        
        Args:
            log_entry: Structured log entry to persist
        """
        from app.database.models import ErrorLog
        
        try:
            error_log = ErrorLog(
                id=log_entry['error_id'],
                error_type=log_entry['error_type'],
                error_message=log_entry['error_message'],
                stack_trace=log_entry['stack_trace'],
                severity=log_entry['severity'],
                context=json.dumps(log_entry['context']),
                user_id=log_entry.get('user_id'),
                application_id=log_entry.get('application_id'),
                timestamp=datetime.fromisoformat(log_entry['timestamp'])
            )
            
            self.db.add(error_log)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to persist error log: {str(e)}")
    
    def _log_to_stdout(self, log_entry: Dict[str, Any]):
        """
        Log error entry to stdout for real-time monitoring.
        
        Args:
            log_entry: Structured log entry to log
        """
        import json
        
        severity = log_entry['severity']
        error_id = log_entry['error_id']
        error_type = log_entry['error_type']
        error_message = log_entry['error_message']
        
        # Format log message
        log_message = (
            f"[{severity.upper()}] Error ID: {error_id} | "
            f"Type: {error_type} | Message: {error_message}"
        )
        
        # Log with appropriate level
        if severity == ErrorSeverity.DEBUG.value:
            logger.debug(log_message)
            logger.debug(f"Full error details: {json.dumps(log_entry, indent=2)}")
        elif severity == ErrorSeverity.INFO.value:
            logger.info(log_message)
        elif severity == ErrorSeverity.WARNING.value:
            logger.warning(log_message)
        elif severity == ErrorSeverity.ERROR.value:
            logger.error(log_message)
            logger.error(f"Stack trace: {log_entry['stack_trace']}")
        elif severity == ErrorSeverity.CRITICAL.value:
            logger.critical(log_message)
            logger.critical(f"Stack trace: {log_entry['stack_trace']}")
    
    def get_error_by_id(self, error_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an error log entry by its ID.
        
        Args:
            error_id: Unique error identifier
        
        Returns:
            Error log entry if found, None otherwise
        
        Example:
            >>> error_log = error_logger.get_error_by_id('abc-123-def')
            >>> if error_log:
            ...     print(f"Error: {error_log['error_message']}")
        """
        from app.database.models import ErrorLog
        
        try:
            error_log = self.db.query(ErrorLog).filter(ErrorLog.id == error_id).first()
            if error_log:
                return {
                    'error_id': error_log.id,
                    'timestamp': error_log.timestamp.isoformat(),
                    'error_type': error_log.error_type,
                    'error_message': error_log.error_message,
                    'stack_trace': error_log.stack_trace,
                    'severity': error_log.severity,
                    'context': json.loads(error_log.context) if error_log.context else {},
                    'user_id': error_log.user_id,
                    'application_id': error_log.application_id
                }
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve error log: {e}")
            return None
    
    def get_errors_by_application(
        self,
        application_id: str,
        limit: int = 50
    ) -> list[Dict[str, Any]]:
        """
        Retrieve error logs for a specific application.
        
        Args:
            application_id: Application identifier
            limit: Maximum number of errors to retrieve
        
        Returns:
            List of error log entries
        
        Example:
            >>> errors = error_logger.get_errors_by_application('app123')
            >>> print(f"Found {len(errors)} errors for application")
        """
        from app.database.models import ErrorLog
        
        try:
            error_logs = self.db.query(ErrorLog).filter(
                ErrorLog.application_id == application_id
            ).order_by(ErrorLog.timestamp.desc()).limit(limit).all()
            
            return [
                {
                    'error_id': log.id,
                    'timestamp': log.timestamp.isoformat(),
                    'error_type': log.error_type,
                    'error_message': log.error_message,
                    'severity': log.severity,
                    'context': json.loads(log.context) if log.context else {}
                }
                for log in error_logs
            ]
        except Exception as e:
            logger.error(f"Failed to retrieve error logs: {e}")
            return []
    
    def get_errors_by_severity(
        self,
        severity: ErrorSeverity,
        limit: int = 50
    ) -> list[Dict[str, Any]]:
        """
        Retrieve error logs by severity level.
        
        Args:
            severity: Error severity level to filter by
            limit: Maximum number of errors to retrieve
        
        Returns:
            List of error log entries
        
        Example:
            >>> critical_errors = error_logger.get_errors_by_severity(
            ...     ErrorSeverity.CRITICAL
            ... )
        """
        from app.database.models import ErrorLog
        
        try:
            error_logs = self.db.query(ErrorLog).filter(
                ErrorLog.severity == severity.value
            ).order_by(ErrorLog.timestamp.desc()).limit(limit).all()
            
            return [
                {
                    'error_id': log.id,
                    'timestamp': log.timestamp.isoformat(),
                    'error_type': log.error_type,
                    'error_message': log.error_message,
                    'severity': log.severity,
                    'context': json.loads(log.context) if log.context else {}
                }
                for log in error_logs
            ]
        except Exception as e:
            logger.error(f"Failed to retrieve error logs: {e}")
            return []
