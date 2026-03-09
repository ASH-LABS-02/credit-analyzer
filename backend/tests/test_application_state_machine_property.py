"""
Property-based tests for ApplicationStateMachine

Feature: intelli-credit-platform
Property 20: Application Status State Machine

**Validates: Requirements 9.1, 9.2, 9.3, 9.4**

Property 20: Application Status State Machine
For any application, status transitions should follow the valid state machine:
"Pending Document Upload" → "Processing" (on document upload) → "Analysis Complete" 
(on analysis completion) → {"Approved", "Approved with Conditions", "Rejected"} 
(on credit decision).
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from app.models.domain import ApplicationStatus
from app.services.application_state_machine import (
    ApplicationStateMachine,
    StateTransitionError
)


# Strategy for generating application statuses
application_status = st.sampled_from(list(ApplicationStatus))


class TestProperty20ApplicationStatusStateMachine:
    """
    Property 20: Application Status State Machine
    
    For any application, status transitions should follow the valid state machine:
    - PENDING → PROCESSING (on document upload)
    - PROCESSING → ANALYSIS_COMPLETE (on analysis completion)
    - ANALYSIS_COMPLETE → {APPROVED, APPROVED_WITH_CONDITIONS, REJECTED} (on credit decision)
    - Terminal states (APPROVED, APPROVED_WITH_CONDITIONS, REJECTED) have no valid transitions
    
    Validates: Requirements 9.1, 9.2, 9.3, 9.4
    """
    
    @pytest.mark.property
    @settings(max_examples=20)
    @given(
        current_state=application_status,
        new_state=application_status
    )
    def test_valid_transitions_are_allowed(self, current_state: ApplicationStatus, new_state: ApplicationStatus):
        """
        Property: All valid state transitions are allowed by the state machine
        
        For any valid state transition defined in the state machine specification,
        the can_transition method should return True and transition should succeed.
        """
        state_machine = ApplicationStateMachine()
        
        # Define the valid transitions according to the specification
        valid_transitions = {
            ApplicationStatus.PENDING: {ApplicationStatus.PROCESSING},
            ApplicationStatus.PROCESSING: {ApplicationStatus.ANALYSIS_COMPLETE},
            ApplicationStatus.ANALYSIS_COMPLETE: {
                ApplicationStatus.APPROVED,
                ApplicationStatus.APPROVED_WITH_CONDITIONS,
                ApplicationStatus.REJECTED
            },
            ApplicationStatus.APPROVED: set(),
            ApplicationStatus.APPROVED_WITH_CONDITIONS: set(),
            ApplicationStatus.REJECTED: set()
        }
        
        # Check if this is a valid transition (including same-state)
        is_valid = (current_state == new_state) or (new_state in valid_transitions.get(current_state, set()))
        
        if is_valid:
            # Valid transitions should be allowed
            assert state_machine.can_transition(current_state, new_state) is True, \
                f"Valid transition from {current_state.value} to {new_state.value} was rejected"
            
            # Transition should succeed without raising an exception
            result = state_machine.transition(current_state, new_state)
            assert result == new_state, \
                f"Transition returned {result.value} instead of {new_state.value}"
    
    @pytest.mark.property
    @settings(max_examples=20)
    @given(
        current_state=application_status,
        new_state=application_status
    )
    def test_invalid_transitions_are_rejected(self, current_state: ApplicationStatus, new_state: ApplicationStatus):
        """
        Property: All invalid state transitions are rejected by the state machine
        
        For any invalid state transition (not in the specification), the can_transition
        method should return False and transition should raise StateTransitionError.
        """
        state_machine = ApplicationStateMachine()
        
        # Define the valid transitions according to the specification
        valid_transitions = {
            ApplicationStatus.PENDING: {ApplicationStatus.PROCESSING},
            ApplicationStatus.PROCESSING: {ApplicationStatus.ANALYSIS_COMPLETE},
            ApplicationStatus.ANALYSIS_COMPLETE: {
                ApplicationStatus.APPROVED,
                ApplicationStatus.APPROVED_WITH_CONDITIONS,
                ApplicationStatus.REJECTED
            },
            ApplicationStatus.APPROVED: set(),
            ApplicationStatus.APPROVED_WITH_CONDITIONS: set(),
            ApplicationStatus.REJECTED: set()
        }
        
        # Check if this is an invalid transition (excluding same-state)
        is_invalid = (current_state != new_state) and (new_state not in valid_transitions.get(current_state, set()))
        
        if is_invalid:
            # Invalid transitions should be rejected
            assert state_machine.can_transition(current_state, new_state) is False, \
                f"Invalid transition from {current_state.value} to {new_state.value} was allowed"
            
            # Transition should raise StateTransitionError
            with pytest.raises(StateTransitionError) as exc_info:
                state_machine.transition(current_state, new_state)
            
            # Error message should mention both states
            error_msg = str(exc_info.value).lower()
            assert current_state.value in error_msg, \
                f"Error message should mention current state {current_state.value}"
    
    @pytest.mark.property
    @settings(max_examples=20)
    @given(state=application_status)
    def test_same_state_transition_always_allowed(self, state: ApplicationStatus):
        """
        Property: Staying in the same state is always allowed (no-op transition)
        
        For any application status, transitioning to the same status should always
        be allowed and should return the same status.
        """
        state_machine = ApplicationStateMachine()
        
        # Same-state transition should always be allowed
        assert state_machine.can_transition(state, state) is True, \
            f"Same-state transition for {state.value} was rejected"
        
        # Transition should succeed and return the same state
        result = state_machine.transition(state, state)
        assert result == state, \
            f"Same-state transition returned {result.value} instead of {state.value}"
    
    @pytest.mark.property
    @settings(max_examples=20)
    @given(terminal_state=st.sampled_from([
        ApplicationStatus.APPROVED,
        ApplicationStatus.APPROVED_WITH_CONDITIONS,
        ApplicationStatus.REJECTED
    ]))
    def test_terminal_states_have_no_outgoing_transitions(self, terminal_state: ApplicationStatus):
        """
        Property: Terminal states cannot transition to any other state
        
        For any terminal state (APPROVED, APPROVED_WITH_CONDITIONS, REJECTED),
        there should be no valid transitions to any other state (except same-state).
        """
        state_machine = ApplicationStateMachine()
        
        # Verify the state is identified as terminal
        assert state_machine.is_terminal_state(terminal_state) is True, \
            f"{terminal_state.value} should be identified as a terminal state"
        
        # Verify no outgoing transitions exist
        allowed_transitions = state_machine.get_allowed_transitions(terminal_state)
        assert len(allowed_transitions) == 0, \
            f"Terminal state {terminal_state.value} should have no outgoing transitions, found {allowed_transitions}"
        
        # Verify transitions to other states are rejected
        for other_state in ApplicationStatus:
            if other_state != terminal_state:
                assert state_machine.can_transition(terminal_state, other_state) is False, \
                    f"Terminal state {terminal_state.value} should not allow transition to {other_state.value}"
                
                with pytest.raises(StateTransitionError):
                    state_machine.transition(terminal_state, other_state)
    
    @pytest.mark.property
    @settings(max_examples=20)
    @given(non_terminal_state=st.sampled_from([
        ApplicationStatus.PENDING,
        ApplicationStatus.PROCESSING,
        ApplicationStatus.ANALYSIS_COMPLETE
    ]))
    def test_non_terminal_states_have_outgoing_transitions(self, non_terminal_state: ApplicationStatus):
        """
        Property: Non-terminal states have at least one valid outgoing transition
        
        For any non-terminal state (PENDING, PROCESSING, ANALYSIS_COMPLETE),
        there should be at least one valid transition to another state.
        """
        state_machine = ApplicationStateMachine()
        
        # Verify the state is not identified as terminal
        assert state_machine.is_terminal_state(non_terminal_state) is False, \
            f"{non_terminal_state.value} should not be identified as a terminal state"
        
        # Verify at least one outgoing transition exists
        allowed_transitions = state_machine.get_allowed_transitions(non_terminal_state)
        assert len(allowed_transitions) > 0, \
            f"Non-terminal state {non_terminal_state.value} should have at least one outgoing transition"
    
    @pytest.mark.property
    @settings(max_examples=20)
    @given(state=application_status)
    def test_get_allowed_transitions_matches_can_transition(self, state: ApplicationStatus):
        """
        Property: get_allowed_transitions should match can_transition results
        
        For any state, the set returned by get_allowed_transitions should exactly
        match the states for which can_transition returns True (excluding same-state).
        """
        state_machine = ApplicationStateMachine()
        
        # Get the allowed transitions
        allowed = state_machine.get_allowed_transitions(state)
        
        # Verify each allowed transition is accepted by can_transition
        for next_state in allowed:
            assert state_machine.can_transition(state, next_state) is True, \
                f"State {next_state.value} is in allowed_transitions but can_transition returns False"
        
        # Verify states not in allowed are rejected by can_transition (excluding same-state)
        for next_state in ApplicationStatus:
            if next_state != state and next_state not in allowed:
                assert state_machine.can_transition(state, next_state) is False, \
                    f"State {next_state.value} is not in allowed_transitions but can_transition returns True"
    
    @pytest.mark.property
    @settings(max_examples=10)
    @given(
        transition_sequence=st.lists(
            st.sampled_from([
                ApplicationStatus.PROCESSING,
                ApplicationStatus.ANALYSIS_COMPLETE,
                ApplicationStatus.APPROVED
            ]),
            min_size=0,
            max_size=3
        )
    )
    def test_valid_workflow_sequence(self, transition_sequence: list):
        """
        Property: Valid workflow sequences complete successfully
        
        For any valid sequence of state transitions starting from PENDING,
        the state machine should allow the complete sequence.
        """
        state_machine = ApplicationStateMachine()
        
        # Start from PENDING
        current = ApplicationStatus.PENDING
        
        # Define valid next states for each state
        valid_next = {
            ApplicationStatus.PENDING: ApplicationStatus.PROCESSING,
            ApplicationStatus.PROCESSING: ApplicationStatus.ANALYSIS_COMPLETE,
            ApplicationStatus.ANALYSIS_COMPLETE: ApplicationStatus.APPROVED
        }
        
        # Try to follow the sequence
        for next_state in transition_sequence:
            # Only attempt transition if it's valid from current state
            if next_state == valid_next.get(current):
                # This should succeed
                current = state_machine.transition(current, next_state)
                assert current == next_state
            else:
                # Skip invalid transitions in the sequence
                break
    
    @pytest.mark.property
    @settings(max_examples=20)
    @given(state=application_status)
    def test_validate_transition_consistency_with_can_transition(self, state: ApplicationStatus):
        """
        Property: validate_transition should be consistent with can_transition
        
        For any state transition, validate_transition should raise an exception
        if and only if can_transition returns False (excluding same-state).
        """
        state_machine = ApplicationStateMachine()
        
        for next_state in ApplicationStatus:
            can_transition = state_machine.can_transition(state, next_state)
            
            if can_transition:
                # Should not raise an exception
                try:
                    state_machine.validate_transition(state, next_state)
                except StateTransitionError:
                    pytest.fail(
                        f"validate_transition raised exception for valid transition "
                        f"{state.value} -> {next_state.value}"
                    )
            else:
                # Should raise an exception
                with pytest.raises(StateTransitionError):
                    state_machine.validate_transition(state, next_state)
    
    @pytest.mark.property
    def test_initial_state_is_pending(self):
        """
        Property: New applications always start in PENDING state
        
        The initial state returned by get_initial_state should always be PENDING.
        """
        state_machine = ApplicationStateMachine()
        
        initial = state_machine.get_initial_state()
        assert initial == ApplicationStatus.PENDING, \
            f"Initial state should be PENDING, got {initial.value}"
    
    @pytest.mark.property
    @settings(max_examples=20)
    @given(state=application_status)
    def test_state_description_exists(self, state: ApplicationStatus):
        """
        Property: Every state has a human-readable description
        
        For any application status, get_state_description should return
        a non-empty string describing the state.
        """
        state_machine = ApplicationStateMachine()
        
        description = state_machine.get_state_description(state)
        
        assert isinstance(description, str), \
            f"Description for {state.value} should be a string"
        assert len(description) > 0, \
            f"Description for {state.value} should not be empty"
    
    @pytest.mark.property
    def test_complete_workflow_pending_to_approved(self):
        """
        Property: Complete workflow from PENDING to APPROVED follows valid path
        
        The complete workflow PENDING → PROCESSING → ANALYSIS_COMPLETE → APPROVED
        should succeed without any errors.
        """
        state_machine = ApplicationStateMachine()
        
        # Start from PENDING
        current = state_machine.get_initial_state()
        assert current == ApplicationStatus.PENDING
        
        # PENDING → PROCESSING
        current = state_machine.transition(current, ApplicationStatus.PROCESSING)
        assert current == ApplicationStatus.PROCESSING
        
        # PROCESSING → ANALYSIS_COMPLETE
        current = state_machine.transition(current, ApplicationStatus.ANALYSIS_COMPLETE)
        assert current == ApplicationStatus.ANALYSIS_COMPLETE
        
        # ANALYSIS_COMPLETE → APPROVED
        current = state_machine.transition(current, ApplicationStatus.APPROVED)
        assert current == ApplicationStatus.APPROVED
        
        # Verify terminal state
        assert state_machine.is_terminal_state(current) is True
    
    @pytest.mark.property
    def test_complete_workflow_pending_to_rejected(self):
        """
        Property: Complete workflow from PENDING to REJECTED follows valid path
        
        The complete workflow PENDING → PROCESSING → ANALYSIS_COMPLETE → REJECTED
        should succeed without any errors.
        """
        state_machine = ApplicationStateMachine()
        
        # Start from PENDING
        current = state_machine.get_initial_state()
        assert current == ApplicationStatus.PENDING
        
        # PENDING → PROCESSING
        current = state_machine.transition(current, ApplicationStatus.PROCESSING)
        assert current == ApplicationStatus.PROCESSING
        
        # PROCESSING → ANALYSIS_COMPLETE
        current = state_machine.transition(current, ApplicationStatus.ANALYSIS_COMPLETE)
        assert current == ApplicationStatus.ANALYSIS_COMPLETE
        
        # ANALYSIS_COMPLETE → REJECTED
        current = state_machine.transition(current, ApplicationStatus.REJECTED)
        assert current == ApplicationStatus.REJECTED
        
        # Verify terminal state
        assert state_machine.is_terminal_state(current) is True
    
    @pytest.mark.property
    def test_complete_workflow_pending_to_approved_with_conditions(self):
        """
        Property: Complete workflow from PENDING to APPROVED_WITH_CONDITIONS follows valid path
        
        The complete workflow PENDING → PROCESSING → ANALYSIS_COMPLETE → APPROVED_WITH_CONDITIONS
        should succeed without any errors.
        """
        state_machine = ApplicationStateMachine()
        
        # Start from PENDING
        current = state_machine.get_initial_state()
        assert current == ApplicationStatus.PENDING
        
        # PENDING → PROCESSING
        current = state_machine.transition(current, ApplicationStatus.PROCESSING)
        assert current == ApplicationStatus.PROCESSING
        
        # PROCESSING → ANALYSIS_COMPLETE
        current = state_machine.transition(current, ApplicationStatus.ANALYSIS_COMPLETE)
        assert current == ApplicationStatus.ANALYSIS_COMPLETE
        
        # ANALYSIS_COMPLETE → APPROVED_WITH_CONDITIONS
        current = state_machine.transition(current, ApplicationStatus.APPROVED_WITH_CONDITIONS)
        assert current == ApplicationStatus.APPROVED_WITH_CONDITIONS
        
        # Verify terminal state
        assert state_machine.is_terminal_state(current) is True
    
    @pytest.mark.property
    @settings(max_examples=20)
    @given(
        start_state=application_status,
        intermediate_state=application_status,
        end_state=application_status
    )
    def test_transition_transitivity(
        self,
        start_state: ApplicationStatus,
        intermediate_state: ApplicationStatus,
        end_state: ApplicationStatus
    ):
        """
        Property: If A→B and B→C are valid, then A→B→C sequence is valid
        
        For any three states where the first two transitions are individually valid,
        the complete sequence should be valid.
        """
        state_machine = ApplicationStateMachine()
        
        # Check if both individual transitions are valid
        first_valid = state_machine.can_transition(start_state, intermediate_state)
        second_valid = state_machine.can_transition(intermediate_state, end_state)
        
        if first_valid and second_valid:
            # First transition
            current = state_machine.transition(start_state, intermediate_state)
            assert current == intermediate_state
            
            # Second transition
            current = state_machine.transition(current, end_state)
            assert current == end_state
