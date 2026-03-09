# Concurrency Control Implementation

## Overview

The concurrency control system implements optimistic concurrency control (OCC) with version tracking to prevent data corruption and race conditions when multiple operations attempt to modify the same resource simultaneously.

## Key Components

### 1. ConcurrencyControl Service (`app/services/concurrency_control.py`)

The main service that provides concurrency control mechanisms:

- **Optimistic Concurrency Control**: Uses version numbers to detect conflicts
- **Pessimistic Locking**: Provides exclusive locks for critical sections
- **Automatic Retry**: Handles conflicts with exponential backoff
- **Compare-and-Swap**: Atomic field updates with value checking

### 2. Version Tracking

Every document managed by the concurrency control system includes:
- `_version`: Integer version number (starts at 1, increments on each update)
- `_created_at`: Timestamp when document was created
- `_last_modified`: Timestamp of last modification

### 3. Repository Integration

Both `ApplicationRepository` and `AnalysisRepository` have been enhanced with concurrency control methods:

#### New Methods:
- `get_with_version()`: Retrieve document with current version
- `update_with_version_check()`: Update with version conflict detection
- `update_with_retry()`: Automatic retry on conflicts
- `compare_and_swap_status()`: Atomic status transitions
- `acquire_lock()`: Exclusive lock for critical sections

## Usage Examples

### Basic Optimistic Concurrency Control

```python
from app.repositories.application_repository import ApplicationRepository
from app.services.concurrency_control import ConcurrencyConflictError

repo = ApplicationRepository()

# Get application with version
versioned_data = await repo.get_with_version("app123")
current_version = versioned_data['version']

# Update with version check
try:
    updated_app = await repo.update_with_version_check(
        "app123",
        {"status": "processing"},
        expected_version=current_version
    )
except ConcurrencyConflictError:
    # Another operation modified the application
    # Handle conflict (e.g., retry, notify user)
    pass
```

### Automatic Retry on Conflicts

```python
# Define update logic
def update_logic(current_app):
    # Calculate updates based on current state
    return {
        "credit_score": calculate_score(current_app),
        "status": "analysis_complete"
    }

# Automatically retries on conflicts
updated_app = await repo.update_with_retry(
    "app123",
    update_logic,
    max_retries=3
)
```

### Compare-and-Swap for State Transitions

```python
# Only update status if it's currently "pending"
success = await repo.compare_and_swap_status(
    "app123",
    expected_status=ApplicationStatus.PENDING,
    new_status=ApplicationStatus.PROCESSING
)

if success:
    # Status was updated
    pass
else:
    # Status was not "pending", another operation changed it
    pass
```

### Pessimistic Locking for Critical Sections

```python
# Acquire exclusive lock for complex operations
async with repo.acquire_lock("app123", timeout=30.0):
    # Perform operations that require exclusive access
    app = await repo.get_by_id("app123")
    # ... complex logic ...
    await repo.update("app123", updates)
# Lock is automatically released
```

## Conflict Resolution Strategies

### 1. Retry with Exponential Backoff
Best for: Operations that can be safely retried
```python
result = await concurrency_control.retry_on_conflict(
    operation,
    max_retries=3,
    base_delay=0.1  # 0.1s, 0.2s, 0.4s delays
)
```

### 2. Fail Fast
Best for: User-initiated operations where immediate feedback is needed
```python
try:
    await repo.update_with_version_check(app_id, updates, version)
except ConcurrencyConflictError:
    return {"error": "Application was modified by another user"}
```

### 3. Last-Write-Wins
Best for: Non-critical updates where conflicts are rare
```python
# Use regular update (no version check)
await repo.update(app_id, updates)
```

## Performance Considerations

### Optimistic vs Pessimistic Locking

**Optimistic Locking (Version Checking)**
- ✅ Better performance under low contention
- ✅ No lock waiting time
- ✅ Scales well with many concurrent readers
- ❌ Requires retry logic for conflicts
- ❌ May waste work if conflicts are frequent

**Pessimistic Locking (Exclusive Locks)**
- ✅ Guarantees exclusive access
- ✅ No wasted work from conflicts
- ❌ Serializes operations (lower throughput)
- ❌ Risk of deadlocks if not careful
- ❌ Lock waiting time

### When to Use Each

**Use Optimistic Locking when:**
- Conflicts are rare
- Read operations are frequent
- Operations are fast
- Multiple concurrent readers are common

**Use Pessimistic Locking when:**
- Conflicts are frequent
- Operations are complex and expensive
- Absolute consistency is required
- Critical sections must not be interrupted

## Testing

Comprehensive unit tests are provided in `tests/test_concurrency_control.py`:
- Version tracking and conflict detection
- Lock acquisition and timeout handling
- Retry logic with exponential backoff
- Compare-and-swap operations
- Error handling and edge cases

Run tests:
```bash
pytest tests/test_concurrency_control.py -v
```

## Requirements Satisfied

This implementation satisfies **Requirement 18.5**:
> For any set of concurrent operations on the same application, the system should maintain data consistency and isolation, ensuring no data corruption or race conditions occur.

The implementation provides:
1. ✅ Database locking for concurrent operations (pessimistic locks)
2. ✅ Optimistic concurrency control (version checking)
3. ✅ Conflict resolution logic (retry with backoff, compare-and-swap)
4. ✅ Data consistency guarantees (Firestore transactions)
5. ✅ Isolation between concurrent operations

## Future Enhancements

Potential improvements for future iterations:
1. Distributed locking using Redis for multi-instance deployments
2. Conflict resolution policies configurable per resource type
3. Metrics and monitoring for conflict rates
4. Automatic conflict resolution for specific field types
5. Optimistic locking for batch operations
