# Application State Machine

## Overview

The `ApplicationStateMachine` class manages the lifecycle of loan applications in the Intelli-Credit platform. It enforces valid state transitions and prevents invalid state changes, ensuring data integrity and workflow consistency.

## State Diagram

```
┌─────────┐
│ PENDING │ (Initial State)
└────┬────┘
     │ Documents uploaded
     ▼
┌────────────┐
│ PROCESSING │
└─────┬──────┘
      │ Analysis complete
      ▼
┌──────────────────┐
│ANALYSIS_COMPLETE │
└────────┬─────────┘
         │
         ├─────────────────┬─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
    ┌─────────┐   ┌──────────────────┐  ┌──────────┐
    │APPROVED │   │APPROVED_WITH_     │  │REJECTED  │
    │         │   │CONDITIONS         │  │          │
    └─────────┘   └──────────────────┘  └──────────┘
    (Terminal)         (Terminal)         (Terminal)
```

## Valid State Transitions

| From State | To State(s) | Trigger |
|-----------|-------------|---------|
| PENDING | PROCESSING | Documents uploaded |
| PROCESSING | ANALYSIS_COMPLETE | AI analysis completes |
| ANALYSIS_COMPLETE | APPROVED | Credit score ≥ 70 |
| ANALYSIS_COMPLETE | APPROVED_WITH_CONDITIONS | 40 ≤ Credit score < 70 |
| ANALYSIS_COMPLETE | REJECTED | Credit score < 40 |

**Terminal States**: APPROVED, APPROVED_WITH_CONDITIONS, REJECTED
- Once an application reaches a terminal state, no further transitions are allowed.

## Usage

### Basic Usage

```python
from app.services import ApplicationStateMachine, StateTransitionError
from app.models.domain import ApplicationStatus

# Create state machine instance
state_machine = ApplicationStateMachine()

# Get initial state for new application
current_state = state_machine.get_initial_state()  # Returns PENDING

# Check if transition is valid
can_transition = state_machine.can_transition(
    current_state=ApplicationStatus.PENDING,
    new_state=ApplicationStatus.PROCESSING
)  # Returns True

# Perform state transition with validation
try:
    new_state = state_machine.transition(
        current_state=ApplicationStatus.PENDING,
        new_state=ApplicationStatus.PROCESSING
    )
    print(f"Transitioned to: {new_state}")
except StateTransitionError as e:
    print(f"Invalid transition: {e}")
```

### Checking Allowed Transitions

```python
# Get all allowed transitions from current state
allowed = state_machine.get_allowed_transitions(ApplicationStatus.PENDING)
print(f"Allowed transitions: {[s.value for s in allowed]}")
# Output: ['processing']
```

### Checking Terminal States

```python
# Check if a state is terminal
is_terminal = state_machine.is_terminal_state(ApplicationStatus.APPROVED)
print(f"Is terminal: {is_terminal}")  # Output: True
```

### Getting State Descriptions

```python
# Get human-readable description
description = state_machine.get_state_description(ApplicationStatus.PENDING)
print(description)  # Output: "Pending document upload"
```

### Complete Workflow Example

```python
from app.services import ApplicationStateMachine
from app.models.domain import ApplicationStatus

state_machine = ApplicationStateMachine()

# Start with initial state
current = state_machine.get_initial_state()
print(f"Initial: {current.value}")  # PENDING

# User uploads documents
current = state_machine.transition(current, ApplicationStatus.PROCESSING)
print(f"After upload: {current.value}")  # PROCESSING

# AI analysis completes
current = state_machine.transition(current, ApplicationStatus.ANALYSIS_COMPLETE)
print(f"After analysis: {current.value}")  # ANALYSIS_COMPLETE

# Credit decision made (e.g., approved)
current = state_machine.transition(current, ApplicationStatus.APPROVED)
print(f"Final: {current.value}")  # APPROVED

# Verify terminal state
print(f"Is terminal: {state_machine.is_terminal_state(current)}")  # True
```

## Integration with Application Repository

The state machine should be used in the `ApplicationRepository` when updating application status:

```python
from app.services import ApplicationStateMachine, StateTransitionError
from app.models.domain import Application, ApplicationStatus

class ApplicationRepository:
    def __init__(self, db):
        self.db = db
        self.state_machine = ApplicationStateMachine()
    
    async def update_status(
        self,
        application_id: str,
        new_status: ApplicationStatus
    ) -> Application:
        """Update application status with state machine validation."""
        # Get current application
        app = await self.get_by_id(application_id)
        
        # Validate state transition
        try:
            self.state_machine.validate_transition(
                current_state=app.status,
                new_state=new_status
            )
        except StateTransitionError as e:
            raise ValueError(f"Invalid status transition: {e}")
        
        # Update status
        app.status = new_status
        app.updated_at = datetime.utcnow()
        
        # Save to database
        await self.update(application_id, app)
        
        return app
```

## Error Handling

The state machine raises `StateTransitionError` when an invalid transition is attempted:

```python
from app.services import StateTransitionError

try:
    # Try invalid transition (PENDING -> APPROVED)
    state_machine.transition(
        ApplicationStatus.PENDING,
        ApplicationStatus.APPROVED
    )
except StateTransitionError as e:
    print(f"Error: {e}")
    # Output: "Invalid state transition from pending to approved.
    #          Allowed transitions from pending: ['processing']"
```

## Requirements Validation

This implementation validates:

- **Requirement 9.1**: New applications initialize with status "Pending Document Upload" (PENDING)
- **Requirement 9.2**: Status updates to "Processing" when documents are uploaded
- **Requirement 9.3**: Status updates to "Analysis Complete" when AI analysis completes
- **Requirement 9.4**: Status updates to final decision state (Approved/Approved with Conditions/Rejected)

## Testing

The state machine includes comprehensive unit tests covering:

- Valid state transitions
- Invalid state transitions
- Terminal state behavior
- Complete workflow scenarios
- Edge cases (same-state transitions, etc.)

Run tests with:

```bash
pytest tests/test_application_state_machine.py -v
```

## Design Properties

**Property 20: Application Status State Machine**

*For any* application, status transitions should follow the valid state machine:
- "Pending Document Upload" → "Processing" (on document upload)
- "Processing" → "Analysis Complete" (on analysis completion)
- "Analysis Complete" → {"Approved", "Approved with Conditions", "Rejected"} (on credit decision)

This property is validated through property-based tests (to be implemented in task 17.2).
