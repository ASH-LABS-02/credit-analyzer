# Transaction Manager

The Transaction Manager provides robust transaction support for Firestore operations with automatic rollback on errors and comprehensive transaction logging.

## Features

- **Automatic Rollback**: All changes are automatically rolled back if any operation fails
- **Transaction Logging**: All transactions are logged with start, completion, or rollback status
- **Error Tracking**: Failed transactions are logged with detailed error information
- **Context Manager Support**: Clean, Pythonic API using async context managers
- **Multi-Operation Support**: Execute multiple operations atomically

## Requirements

Validates: **Requirement 15.3** - Database transaction rollback

## Usage

### Basic Transaction with Context Manager

```python
from app.core.transaction_manager import get_transaction_manager

transaction_manager = get_transaction_manager()

# Use context manager for automatic rollback
async with transaction_manager.transaction(
    "update_application",
    {'application_id': app_id}
) as tx:
    # Perform operations using the transaction
    app_ref = db.collection('applications').document(app_id)
    tx.update(app_ref, {'status': 'processing'})
    
    log_ref = db.collection('audit_logs').document()
    tx.set(log_ref, {'message': 'Started processing'})
    
    # If any operation fails, all changes are automatically rolled back
```

### Repository Methods with Transactions

The repositories now include transactional methods:

#### ApplicationRepository

```python
from app.repositories.application_repository import ApplicationRepository

repo = ApplicationRepository()

# Create application with initial document atomically
application = await repo.create_with_initial_document(
    application=app,
    document_data={'id': doc_id, 'filename': 'report.pdf', ...}
)

# Update application and create audit log atomically
updated_app = await repo.update_with_status_log(
    application_id=app_id,
    updates={'status': 'approved'},
    log_entry={'id': log_id, 'action': 'approved', ...}
)

# Delete application with all associated documents atomically
deleted = await repo.delete_with_cascade(
    application_id=app_id,
    document_ids=[doc1_id, doc2_id, doc3_id]
)
```

#### DocumentRepository

```python
from app.repositories.document_repository import DocumentRepository

repo = DocumentRepository()

# Update status for multiple documents atomically
updated_count = await repo.batch_update_status(
    document_ids=[doc1_id, doc2_id, doc3_id],
    status='processing'
)
```

#### AnalysisRepository

```python
from app.repositories.analysis_repository import AnalysisRepository

repo = AnalysisRepository()

# Save analysis and update application status atomically
analysis = await repo.save_with_application_update(
    analysis=analysis_results,
    application_updates={
        'status': 'analysis_complete',
        'credit_score': 75.5
    }
)
```

### Execute Multiple Operations

```python
def update_app(tx):
    doc_ref = db.collection('applications').document(app_id)
    tx.update(doc_ref, {'status': 'processing'})

def create_log(tx):
    log_ref = db.collection('logs').document()
    tx.set(log_ref, {'message': 'Started processing'})

# Execute both operations atomically
await transaction_manager.execute_in_transaction(
    "start_processing",
    [update_app, create_log],
    {'application_id': app_id}
)
```

## Transaction Logging

All transactions are logged to the `transaction_logs` collection with the following information:

- `transaction_id`: Unique identifier
- `operation_name`: Name of the operation
- `status`: "started", "completed", or "rolled_back"
- `started_at`: Timestamp when transaction started
- `completed_at`: Timestamp when transaction completed (if successful)
- `rolled_back_at`: Timestamp when transaction was rolled back (if failed)
- `error_type`: Type of error that caused rollback
- `error_message`: Error message
- `stack_trace`: Full stack trace for debugging
- `context`: Additional context information

### Querying Transaction Logs

```python
# Get a specific transaction log
log = await transaction_manager.get_transaction_log(transaction_id)

# List recent failed transactions
failed = await transaction_manager.list_failed_transactions(
    limit=50,
    start_date=datetime(2024, 1, 1)
)
```

## Error Handling

When a transaction fails:

1. All changes are automatically rolled back by Firestore
2. The transaction is logged with "rolled_back" status
3. The error is logged to the error_logs collection
4. An exception is raised with transaction ID and error ID for tracking

Example error message:
```
Transaction failed and was rolled back. 
Transaction ID: 123e4567-e89b-12d3-a456-426614174000, 
Error ID: 789e4567-e89b-12d3-a456-426614174001, 
Original error: Document does not exist
```

## Best Practices

1. **Use transactions for multi-step operations**: Any operation that modifies multiple documents should use a transaction
2. **Keep transactions short**: Firestore transactions have a 10-second timeout
3. **Read before write**: Always read documents within the transaction before updating them
4. **Handle conflicts**: Firestore may retry transactions if there are conflicts
5. **Provide context**: Always include meaningful operation names and context for logging

## Limitations

- Firestore transactions have a maximum of 500 document operations
- Transactions timeout after 10 seconds
- Transactions are retried automatically by Firestore on conflicts
- Cannot perform queries within transactions (only direct document reads)

## Testing

The transaction manager is tested with property-based tests to ensure:

- All changes are rolled back on errors
- Transaction logs are created correctly
- Error information is captured accurately
- Multiple operations execute atomically

See `backend/tests/test_transaction_rollback_property.py` for property-based tests.
