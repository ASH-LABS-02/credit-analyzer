# ErrorLogger - Centralized Error Logging

## Overview

The `ErrorLogger` class provides centralized error logging functionality for the Intelli-Credit platform. All errors across the system are logged with unique IDs for tracking, structured context data, and persisted to Firestore for analysis and debugging.

## Features

- **Unique Error IDs**: Every error is assigned a UUID for easy tracking and reference
- **Structured Logging**: Errors are logged with structured data including error type, message, stack trace, timestamp, and custom context
- **Firestore Persistence**: All errors are stored in Firestore for long-term analysis
- **Severity Levels**: Support for DEBUG, INFO, WARNING, ERROR, and CRITICAL severity levels
- **Context Data**: Attach custom context information (application ID, agent name, user ID, etc.)
- **Query Capabilities**: Retrieve errors by ID, application, or severity level
- **Graceful Degradation**: If Firestore logging fails, errors are still logged to stdout

## Requirements

Validates: Requirements 15.5

## Usage

### Basic Error Logging

```python
from app.core import ErrorLogger, ErrorSeverity
from app.core.firebase import get_firestore_client

# Initialize ErrorLogger
db = get_firestore_client()
error_logger = ErrorLogger(db)

# Log an error
try:
    risky_operation()
except Exception as e:
    error_id = await error_logger.log_error(
        error=e,
        context={'function': 'risky_operation'},
        severity=ErrorSeverity.ERROR
    )
    print(f"Error logged with ID: {error_id}")
```

### Logging with Application Context

```python
# Log error with application and user context
try:
    process_application(app_id)
except Exception as e:
    error_id = await error_logger.log_error(
        error=e,
        context={
            'agent': 'DocumentIntelligence',
            'document_id': 'doc123',
            'processing_stage': 'extraction'
        },
        severity=ErrorSeverity.ERROR,
        user_id='user456',
        application_id='app789'
    )
```

### Synchronous Error Logging

For non-async contexts, use `log_error_sync`:

```python
try:
    synchronous_operation()
except Exception as e:
    error_id = error_logger.log_error_sync(
        error=e,
        context={'operation': 'sync_task'},
        severity=ErrorSeverity.WARNING
    )
```

### Retrieving Errors

```python
# Get error by ID
error_log = await error_logger.get_error_by_id('error-uuid-here')
if error_log:
    print(f"Error: {error_log['error_message']}")
    print(f"Stack trace: {error_log['stack_trace']}")

# Get all errors for an application
app_errors = await error_logger.get_errors_by_application('app123', limit=50)
print(f"Found {len(app_errors)} errors for application")

# Get critical errors
critical_errors = await error_logger.get_errors_by_severity(
    ErrorSeverity.CRITICAL,
    limit=100
)
```

## Error Severity Levels

- **DEBUG**: Debugging information (not typically used for errors)
- **INFO**: Informational messages
- **WARNING**: Warning messages for non-critical issues
- **ERROR**: Error messages for failures that don't crash the system
- **CRITICAL**: Critical errors requiring immediate attention

## Log Entry Structure

Each error log entry contains:

```python
{
    'error_id': 'uuid-string',           # Unique identifier
    'timestamp': '2024-01-15T10:30:00',  # ISO format timestamp
    'error_type': 'ValueError',          # Exception class name
    'error_message': 'Invalid input',    # Error message
    'stack_trace': '...',                # Full stack trace
    'severity': 'error',                 # Severity level
    'context': {                         # Custom context data
        'application_id': 'app123',
        'agent': 'DocumentIntelligence',
        'document_id': 'doc456'
    },
    'user_id': 'user789',               # Optional
    'application_id': 'app123'          # Optional
}
```

## Integration with AI Agents

Example integration in an AI agent:

```python
from app.core import ErrorLogger, ErrorSeverity

class DocumentIntelligenceAgent:
    def __init__(self, openai_client, firestore_client):
        self.openai = openai_client
        self.db = firestore_client
        self.error_logger = ErrorLogger(firestore_client)
    
    async def extract(self, application_id: str) -> Dict:
        try:
            # Perform extraction
            documents = await self._get_documents(application_id)
            return await self._extract_data(documents)
        except Exception as e:
            # Log error with context
            error_id = await self.error_logger.log_error(
                error=e,
                context={
                    'agent': 'DocumentIntelligence',
                    'application_id': application_id,
                    'operation': 'extract'
                },
                severity=ErrorSeverity.ERROR,
                application_id=application_id
            )
            
            # Re-raise or handle gracefully
            raise RuntimeError(f"Extraction failed. Error ID: {error_id}") from e
```

## Integration with Orchestrator

Example integration in the orchestrator for agent failure recovery:

```python
from app.core import ErrorLogger, ErrorSeverity

class OrchestratorAgent:
    def __init__(self, openai_client, firestore_client):
        self.openai = openai_client
        self.db = firestore_client
        self.error_logger = ErrorLogger(firestore_client)
        self.agents = self._initialize_agents()
    
    async def process_application(self, application_id: str) -> Dict:
        try:
            # Attempt document intelligence
            extracted_data = await self.agents['document'].extract(application_id)
        except Exception as e:
            # Log agent failure
            error_id = await self.error_logger.log_error(
                error=e,
                context={
                    'orchestrator': 'OrchestratorAgent',
                    'failed_agent': 'DocumentIntelligence',
                    'application_id': application_id
                },
                severity=ErrorSeverity.ERROR,
                application_id=application_id
            )
            
            # Attempt graceful degradation
            logger.warning(f"Document extraction failed (Error ID: {error_id}). "
                          f"Attempting recovery...")
            
            # Continue with available data or fail gracefully
            extracted_data = await self._fallback_extraction(application_id)
        
        # Continue with workflow...
```

## Best Practices

1. **Always include context**: Provide relevant context data (application ID, agent name, operation) to make debugging easier

2. **Use appropriate severity levels**: 
   - Use ERROR for failures that need attention
   - Use CRITICAL for system-wide failures
   - Use WARNING for recoverable issues

3. **Include application_id when available**: This makes it easy to track all errors for a specific application

4. **Don't log sensitive data**: Avoid logging passwords, API keys, or PII in context data

5. **Log at the right level**: Log errors at the point where they're handled, not at every level of the call stack

6. **Use error IDs in user-facing messages**: Return error IDs to users so they can reference specific errors when reporting issues

## Firestore Collection Structure

Errors are stored in the `error_logs` collection with the following structure:

```
error_logs/
  {auto_generated_doc_id}/
    - error_id: string (UUID)
    - timestamp: string (ISO format)
    - error_type: string
    - error_message: string
    - stack_trace: string
    - severity: string
    - context: map
    - user_id: string (optional)
    - application_id: string (optional)
```

## Testing

The ErrorLogger includes comprehensive unit tests covering:
- Error ID generation and uniqueness
- Structured log entry creation
- Firestore persistence
- Error retrieval by ID, application, and severity
- Graceful handling of Firestore failures
- Stack trace capture

Run tests with:
```bash
pytest backend/tests/test_error_logger.py -v
```
