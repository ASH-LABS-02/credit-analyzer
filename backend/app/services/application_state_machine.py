"""
Application State Machine for managing application lifecycle.

This module implements a state machine for managing the lifecycle of loan applications,
ensuring valid state transitions and preventing invalid state changes.

Requirements: 2.1, 2.2 (from requirements.md)
Property 20: Application Status State Machine
"""

from typing import Dict, Set, Optional
from enum import Enum
from datetime import datetime

from app.models.domain import ApplicationStatus


class StateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class ApplicationStateMachine:
    """
    State machine for managing application workflow states.
    
    Valid state transitions:
    - PENDING -> PROCESSING (when documents are uploaded)
    - PROCESSING -> ANALYSIS_COMPLETE (when analysis completes)
    - ANALYSIS_COMPLETE -> APPROVED (when credit decision is approve)
    - ANALYSIS_COMPLETE -> APPROVED_WITH_CONDITIONS (when credit decision is conditional)
    - ANALYSIS_COMPLETE -> REJECTED (when credit decision is reject)
    
    Terminal states: APPROVED, APPROVED_WITH_CONDITIONS, REJECTED
    
    The state machine integrates with AuditLogger to track all state transitions
    for compliance and audit trail purposes.
    """
    
    # Define valid state transitions as a mapping from current state to allowed next states
    VALID_TRANSITIONS: Dict[ApplicationStatus, Set[ApplicationStatus]] = {
        ApplicationStatus.PENDING: {
            ApplicationStatus.PROCESSING
        },
        ApplicationStatus.PROCESSING: {
            ApplicationStatus.ANALYSIS_COMPLETE
        },
        ApplicationStatus.ANALYSIS_COMPLETE: {
            ApplicationStatus.APPROVED,
            ApplicationStatus.APPROVED_WITH_CONDITIONS,
            ApplicationStatus.REJECTED
        },
        # Terminal states have no valid transitions
        ApplicationStatus.APPROVED: set(),
        ApplicationStatus.APPROVED_WITH_CONDITIONS: set(),
        ApplicationStatus.REJECTED: set()
    }
    
    # Terminal states that cannot transition to other states
    TERMINAL_STATES: Set[ApplicationStatus] = {
        ApplicationStatus.APPROVED,
        ApplicationStatus.APPROVED_WITH_CONDITIONS,
        ApplicationStatus.REJECTED
    }
    
    def __init__(self, audit_logger=None):
        """
        Initialize the state machine.
        
        Args:
            audit_logger: Optional AuditLogger instance for logging state transitions
        """
        self.audit_logger = audit_logger
    
    def can_transition(
        self,
        current_state: ApplicationStatus,
        new_state: ApplicationStatus
    ) -> bool:
        """
        Check if a state transition is valid.
        
        Args:
            current_state: The current application status
            new_state: The desired new application status
            
        Returns:
            True if the transition is valid, False otherwise
        """
        # Allow staying in the same state (no-op transition)
        if current_state == new_state:
            return True
        
        # Check if the new state is in the set of valid transitions
        allowed_states = self.VALID_TRANSITIONS.get(current_state, set())
        return new_state in allowed_states
    
    def validate_transition(
        self,
        current_state: ApplicationStatus,
        new_state: ApplicationStatus
    ) -> None:
        """
        Validate a state transition and raise an exception if invalid.
        
        Args:
            current_state: The current application status
            new_state: The desired new application status
            
        Raises:
            StateTransitionError: If the transition is not valid
        """
        if not self.can_transition(current_state, new_state):
            raise StateTransitionError(
                f"Invalid state transition from {current_state.value} to {new_state.value}. "
                f"Allowed transitions from {current_state.value}: "
                f"{[s.value for s in self.VALID_TRANSITIONS.get(current_state, set())]}"
            )
    
    def transition(
        self,
        current_state: ApplicationStatus,
        new_state: ApplicationStatus
    ) -> ApplicationStatus:
        """
        Perform a state transition with validation.
        
        Args:
            current_state: The current application status
            new_state: The desired new application status
            
        Returns:
            The new state after successful transition
            
        Raises:
            StateTransitionError: If the transition is not valid
        """
        self.validate_transition(current_state, new_state)
        return new_state
    
    async def transition_with_audit(
        self,
        application_id: str,
        current_state: ApplicationStatus,
        new_state: ApplicationStatus,
        user_id: Optional[str] = None,
        reason: Optional[str] = None,
        additional_context: Optional[Dict] = None
    ) -> ApplicationStatus:
        """
        Perform a state transition with validation and audit logging.
        
        This method validates the state transition, performs it, and logs
        the transition to the audit trail if an audit logger is configured.
        
        Args:
            application_id: The application identifier
            current_state: The current application status
            new_state: The desired new application status
            user_id: Optional user ID who initiated the transition
            reason: Optional reason for the transition
            additional_context: Optional additional context information
            
        Returns:
            The new state after successful transition
            
        Raises:
            StateTransitionError: If the transition is not valid
        
        Requirements: 9.5, 17.1
        Property 21: Audit Trail Completeness
        
        Example:
            >>> state_machine = ApplicationStateMachine(audit_logger)
            >>> new_state = await state_machine.transition_with_audit(
            ...     application_id='app123',
            ...     current_state=ApplicationStatus.PENDING,
            ...     new_state=ApplicationStatus.PROCESSING,
            ...     user_id='user456',
            ...     reason='Documents uploaded'
            ... )
        """
        # Validate the transition first
        self.validate_transition(current_state, new_state)
        
        # Log the transition if audit logger is configured
        if self.audit_logger:
            try:
                await self.audit_logger.log_state_transition(
                    application_id=application_id,
                    old_state=current_state,
                    new_state=new_state,
                    user_id=user_id,
                    reason=reason,
                    additional_context=additional_context
                )
            except Exception as e:
                # Log the error but don't fail the transition
                # This ensures audit logging failures don't block operations
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to log state transition to audit trail: {e}")
        
        return new_state
    
    def is_terminal_state(self, state: ApplicationStatus) -> bool:
        """
        Check if a state is a terminal state (no further transitions allowed).
        
        Args:
            state: The application status to check
            
        Returns:
            True if the state is terminal, False otherwise
        """
        return state in self.TERMINAL_STATES
    
    def get_allowed_transitions(
        self,
        current_state: ApplicationStatus
    ) -> Set[ApplicationStatus]:
        """
        Get the set of allowed transitions from the current state.
        
        Args:
            current_state: The current application status
            
        Returns:
            Set of allowed next states
        """
        return self.VALID_TRANSITIONS.get(current_state, set()).copy()
    
    def get_initial_state(self) -> ApplicationStatus:
        """
        Get the initial state for a new application.
        
        Returns:
            The initial application status (PENDING)
        """
        return ApplicationStatus.PENDING
    
    def get_state_description(self, state: ApplicationStatus) -> str:
        """
        Get a human-readable description of a state.
        
        Args:
            state: The application status
            
        Returns:
            A description of the state
        """
        descriptions = {
            ApplicationStatus.PENDING: "Pending document upload",
            ApplicationStatus.PROCESSING: "Processing documents and analyzing",
            ApplicationStatus.ANALYSIS_COMPLETE: "Analysis complete, awaiting credit decision",
            ApplicationStatus.APPROVED: "Application approved",
            ApplicationStatus.APPROVED_WITH_CONDITIONS: "Application approved with conditions",
            ApplicationStatus.REJECTED: "Application rejected"
        }
        return descriptions.get(state, f"Unknown state: {state.value}")
