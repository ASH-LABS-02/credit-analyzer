"""
Unit tests for ApplicationStateMachine.

Tests the state machine logic for managing application lifecycle,
including valid transitions, invalid transitions, and terminal states.
"""

import pytest
from app.models.domain import ApplicationStatus
from app.services.application_state_machine import (
    ApplicationStateMachine,
    StateTransitionError
)


class TestApplicationStateMachine:
    """Test suite for ApplicationStateMachine."""
    
    @pytest.fixture
    def state_machine(self):
        """Create a state machine instance for testing."""
        return ApplicationStateMachine()
    
    def test_initial_state(self, state_machine):
        """Test that the initial state is PENDING."""
        assert state_machine.get_initial_state() == ApplicationStatus.PENDING
    
    def test_valid_transition_pending_to_processing(self, state_machine):
        """Test valid transition from PENDING to PROCESSING."""
        current = ApplicationStatus.PENDING
        new = ApplicationStatus.PROCESSING
        
        assert state_machine.can_transition(current, new) is True
        result = state_machine.transition(current, new)
        assert result == ApplicationStatus.PROCESSING
    
    def test_valid_transition_processing_to_analysis_complete(self, state_machine):
        """Test valid transition from PROCESSING to ANALYSIS_COMPLETE."""
        current = ApplicationStatus.PROCESSING
        new = ApplicationStatus.ANALYSIS_COMPLETE
        
        assert state_machine.can_transition(current, new) is True
        result = state_machine.transition(current, new)
        assert result == ApplicationStatus.ANALYSIS_COMPLETE
    
    def test_valid_transition_analysis_to_approved(self, state_machine):
        """Test valid transition from ANALYSIS_COMPLETE to APPROVED."""
        current = ApplicationStatus.ANALYSIS_COMPLETE
        new = ApplicationStatus.APPROVED
        
        assert state_machine.can_transition(current, new) is True
        result = state_machine.transition(current, new)
        assert result == ApplicationStatus.APPROVED
    
    def test_valid_transition_analysis_to_approved_with_conditions(self, state_machine):
        """Test valid transition from ANALYSIS_COMPLETE to APPROVED_WITH_CONDITIONS."""
        current = ApplicationStatus.ANALYSIS_COMPLETE
        new = ApplicationStatus.APPROVED_WITH_CONDITIONS
        
        assert state_machine.can_transition(current, new) is True
        result = state_machine.transition(current, new)
        assert result == ApplicationStatus.APPROVED_WITH_CONDITIONS
    
    def test_valid_transition_analysis_to_rejected(self, state_machine):
        """Test valid transition from ANALYSIS_COMPLETE to REJECTED."""
        current = ApplicationStatus.ANALYSIS_COMPLETE
        new = ApplicationStatus.REJECTED
        
        assert state_machine.can_transition(current, new) is True
        result = state_machine.transition(current, new)
        assert result == ApplicationStatus.REJECTED
    
    def test_same_state_transition_allowed(self, state_machine):
        """Test that staying in the same state is allowed (no-op)."""
        for status in ApplicationStatus:
            assert state_machine.can_transition(status, status) is True
            result = state_machine.transition(status, status)
            assert result == status
    
    def test_invalid_transition_pending_to_approved(self, state_machine):
        """Test invalid transition from PENDING to APPROVED."""
        current = ApplicationStatus.PENDING
        new = ApplicationStatus.APPROVED
        
        assert state_machine.can_transition(current, new) is False
        
        with pytest.raises(StateTransitionError) as exc_info:
            state_machine.transition(current, new)
        
        assert "Invalid state transition" in str(exc_info.value)
        assert "pending" in str(exc_info.value).lower()
        assert "approved" in str(exc_info.value).lower()
    
    def test_invalid_transition_pending_to_analysis_complete(self, state_machine):
        """Test invalid transition from PENDING to ANALYSIS_COMPLETE."""
        current = ApplicationStatus.PENDING
        new = ApplicationStatus.ANALYSIS_COMPLETE
        
        assert state_machine.can_transition(current, new) is False
        
        with pytest.raises(StateTransitionError):
            state_machine.transition(current, new)
    
    def test_invalid_transition_processing_to_approved(self, state_machine):
        """Test invalid transition from PROCESSING to APPROVED."""
        current = ApplicationStatus.PROCESSING
        new = ApplicationStatus.APPROVED
        
        assert state_machine.can_transition(current, new) is False
        
        with pytest.raises(StateTransitionError):
            state_machine.transition(current, new)
    
    def test_invalid_transition_from_terminal_state_approved(self, state_machine):
        """Test that APPROVED is a terminal state with no valid transitions."""
        current = ApplicationStatus.APPROVED
        
        # Try transitioning to all other states
        for new_state in ApplicationStatus:
            if new_state != current:
                assert state_machine.can_transition(current, new_state) is False
                
                with pytest.raises(StateTransitionError):
                    state_machine.transition(current, new_state)
    
    def test_invalid_transition_from_terminal_state_rejected(self, state_machine):
        """Test that REJECTED is a terminal state with no valid transitions."""
        current = ApplicationStatus.REJECTED
        
        # Try transitioning to all other states
        for new_state in ApplicationStatus:
            if new_state != current:
                assert state_machine.can_transition(current, new_state) is False
                
                with pytest.raises(StateTransitionError):
                    state_machine.transition(current, new_state)
    
    def test_invalid_transition_from_terminal_state_approved_with_conditions(self, state_machine):
        """Test that APPROVED_WITH_CONDITIONS is a terminal state."""
        current = ApplicationStatus.APPROVED_WITH_CONDITIONS
        
        # Try transitioning to all other states
        for new_state in ApplicationStatus:
            if new_state != current:
                assert state_machine.can_transition(current, new_state) is False
                
                with pytest.raises(StateTransitionError):
                    state_machine.transition(current, new_state)
    
    def test_is_terminal_state(self, state_machine):
        """Test terminal state identification."""
        # Terminal states
        assert state_machine.is_terminal_state(ApplicationStatus.APPROVED) is True
        assert state_machine.is_terminal_state(ApplicationStatus.APPROVED_WITH_CONDITIONS) is True
        assert state_machine.is_terminal_state(ApplicationStatus.REJECTED) is True
        
        # Non-terminal states
        assert state_machine.is_terminal_state(ApplicationStatus.PENDING) is False
        assert state_machine.is_terminal_state(ApplicationStatus.PROCESSING) is False
        assert state_machine.is_terminal_state(ApplicationStatus.ANALYSIS_COMPLETE) is False
    
    def test_get_allowed_transitions_pending(self, state_machine):
        """Test getting allowed transitions from PENDING state."""
        allowed = state_machine.get_allowed_transitions(ApplicationStatus.PENDING)
        assert allowed == {ApplicationStatus.PROCESSING}
    
    def test_get_allowed_transitions_processing(self, state_machine):
        """Test getting allowed transitions from PROCESSING state."""
        allowed = state_machine.get_allowed_transitions(ApplicationStatus.PROCESSING)
        assert allowed == {ApplicationStatus.ANALYSIS_COMPLETE}
    
    def test_get_allowed_transitions_analysis_complete(self, state_machine):
        """Test getting allowed transitions from ANALYSIS_COMPLETE state."""
        allowed = state_machine.get_allowed_transitions(ApplicationStatus.ANALYSIS_COMPLETE)
        assert allowed == {
            ApplicationStatus.APPROVED,
            ApplicationStatus.APPROVED_WITH_CONDITIONS,
            ApplicationStatus.REJECTED
        }
    
    def test_get_allowed_transitions_terminal_states(self, state_machine):
        """Test that terminal states have no allowed transitions."""
        terminal_states = [
            ApplicationStatus.APPROVED,
            ApplicationStatus.APPROVED_WITH_CONDITIONS,
            ApplicationStatus.REJECTED
        ]
        
        for state in terminal_states:
            allowed = state_machine.get_allowed_transitions(state)
            assert allowed == set()
    
    def test_validate_transition_success(self, state_machine):
        """Test that validate_transition doesn't raise for valid transitions."""
        # Should not raise
        state_machine.validate_transition(
            ApplicationStatus.PENDING,
            ApplicationStatus.PROCESSING
        )
        
        state_machine.validate_transition(
            ApplicationStatus.PROCESSING,
            ApplicationStatus.ANALYSIS_COMPLETE
        )
        
        state_machine.validate_transition(
            ApplicationStatus.ANALYSIS_COMPLETE,
            ApplicationStatus.APPROVED
        )
    
    def test_validate_transition_failure(self, state_machine):
        """Test that validate_transition raises for invalid transitions."""
        with pytest.raises(StateTransitionError):
            state_machine.validate_transition(
                ApplicationStatus.PENDING,
                ApplicationStatus.APPROVED
            )
        
        with pytest.raises(StateTransitionError):
            state_machine.validate_transition(
                ApplicationStatus.APPROVED,
                ApplicationStatus.PENDING
            )
    
    def test_get_state_description(self, state_machine):
        """Test getting human-readable state descriptions."""
        descriptions = {
            ApplicationStatus.PENDING: "Pending document upload",
            ApplicationStatus.PROCESSING: "Processing documents and analyzing",
            ApplicationStatus.ANALYSIS_COMPLETE: "Analysis complete, awaiting credit decision",
            ApplicationStatus.APPROVED: "Application approved",
            ApplicationStatus.APPROVED_WITH_CONDITIONS: "Application approved with conditions",
            ApplicationStatus.REJECTED: "Application rejected"
        }
        
        for status, expected_desc in descriptions.items():
            desc = state_machine.get_state_description(status)
            assert desc == expected_desc
    
    def test_complete_workflow_happy_path_approved(self, state_machine):
        """Test complete workflow from PENDING to APPROVED."""
        current = ApplicationStatus.PENDING
        
        # PENDING -> PROCESSING
        current = state_machine.transition(current, ApplicationStatus.PROCESSING)
        assert current == ApplicationStatus.PROCESSING
        
        # PROCESSING -> ANALYSIS_COMPLETE
        current = state_machine.transition(current, ApplicationStatus.ANALYSIS_COMPLETE)
        assert current == ApplicationStatus.ANALYSIS_COMPLETE
        
        # ANALYSIS_COMPLETE -> APPROVED
        current = state_machine.transition(current, ApplicationStatus.APPROVED)
        assert current == ApplicationStatus.APPROVED
        
        # Verify terminal state
        assert state_machine.is_terminal_state(current) is True
    
    def test_complete_workflow_happy_path_rejected(self, state_machine):
        """Test complete workflow from PENDING to REJECTED."""
        current = ApplicationStatus.PENDING
        
        # PENDING -> PROCESSING
        current = state_machine.transition(current, ApplicationStatus.PROCESSING)
        assert current == ApplicationStatus.PROCESSING
        
        # PROCESSING -> ANALYSIS_COMPLETE
        current = state_machine.transition(current, ApplicationStatus.ANALYSIS_COMPLETE)
        assert current == ApplicationStatus.ANALYSIS_COMPLETE
        
        # ANALYSIS_COMPLETE -> REJECTED
        current = state_machine.transition(current, ApplicationStatus.REJECTED)
        assert current == ApplicationStatus.REJECTED
        
        # Verify terminal state
        assert state_machine.is_terminal_state(current) is True
    
    def test_complete_workflow_happy_path_approved_with_conditions(self, state_machine):
        """Test complete workflow from PENDING to APPROVED_WITH_CONDITIONS."""
        current = ApplicationStatus.PENDING
        
        # PENDING -> PROCESSING
        current = state_machine.transition(current, ApplicationStatus.PROCESSING)
        assert current == ApplicationStatus.PROCESSING
        
        # PROCESSING -> ANALYSIS_COMPLETE
        current = state_machine.transition(current, ApplicationStatus.ANALYSIS_COMPLETE)
        assert current == ApplicationStatus.ANALYSIS_COMPLETE
        
        # ANALYSIS_COMPLETE -> APPROVED_WITH_CONDITIONS
        current = state_machine.transition(current, ApplicationStatus.APPROVED_WITH_CONDITIONS)
        assert current == ApplicationStatus.APPROVED_WITH_CONDITIONS
        
        # Verify terminal state
        assert state_machine.is_terminal_state(current) is True
