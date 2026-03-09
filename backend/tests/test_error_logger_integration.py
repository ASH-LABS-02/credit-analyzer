"""
Integration tests for ErrorLogger with error scenarios.

Tests the ErrorLogger in realistic error handling scenarios including:
- Agent failures with error logging
- Multiple errors for the same application
- Error retrieval and analysis
"""

import pytest
from unittest.mock import Mock, AsyncMock
from app.core.error_logger import ErrorLogger, ErrorSeverity


@pytest.fixture
def mock_firestore():
    """Create a mock Firestore client."""
    mock_db = Mock()
    mock_collection = Mock()
    mock_db.collection.return_value = mock_collection
    return mock_db


@pytest.fixture
def error_logger(mock_firestore):
    """Create an ErrorLogger instance with mocked Firestore."""
    return ErrorLogger(mock_firestore)


@pytest.mark.asyncio
async def test_agent_failure_logging_scenario(error_logger, mock_firestore):
    """
    Test a realistic scenario where an agent fails and logs the error.
    
    Simulates:
    1. DocumentIntelligenceAgent fails during extraction
    2. Error is logged with full context
    3. Orchestrator can retrieve the error for analysis
    """
    # Simulate agent failure
    application_id = 'app123'
    document_id = 'doc456'
    
    try:
        # Simulate document extraction failure
        raise ValueError("Failed to extract financial data from corrupted PDF")
    except Exception as e:
        # Log the error as an agent would
        error_id = await error_logger.log_error(
            error=e,
            context={
                'agent': 'DocumentIntelligenceAgent',
                'application_id': application_id,
                'document_id': document_id,
                'operation': 'extract_financial_data',
                'file_type': 'pdf'
            },
            severity=ErrorSeverity.ERROR,
            application_id=application_id
        )
    
    # Verify error was logged
    assert error_id is not None
    
    # Verify Firestore was called
    mock_firestore.collection.assert_called_with('error_logs')


@pytest.mark.asyncio
async def test_multiple_errors_same_application(error_logger, mock_firestore):
    """
    Test logging multiple errors for the same application.
    
    Simulates:
    1. Multiple agents fail for the same application
    2. Each error is logged with unique ID
    3. All errors can be retrieved by application ID
    """
    application_id = 'app789'
    error_ids = []
    
    # Simulate multiple agent failures
    agents_and_errors = [
        ('DocumentIntelligenceAgent', ValueError("Extraction failed")),
        ('WebResearchAgent', ConnectionError("API timeout")),
        ('ForecastingAgent', RuntimeError("Insufficient historical data"))
    ]
    
    for agent_name, error in agents_and_errors:
        error_id = await error_logger.log_error(
            error=error,
            context={
                'agent': agent_name,
                'application_id': application_id
            },
            severity=ErrorSeverity.ERROR,
            application_id=application_id
        )
        error_ids.append(error_id)
    
    # Verify all errors have unique IDs
    assert len(error_ids) == 3
    assert len(set(error_ids)) == 3  # All unique
    
    # Verify Firestore was called for each error
    assert mock_firestore.collection.call_count >= 3


@pytest.mark.asyncio
async def test_orchestrator_error_recovery_scenario(error_logger, mock_firestore):
    """
    Test orchestrator error recovery with logging.
    
    Simulates:
    1. Orchestrator attempts to run an agent
    2. Agent fails
    3. Error is logged
    4. Orchestrator continues with graceful degradation
    """
    application_id = 'app999'
    
    # Simulate orchestrator workflow
    workflow_errors = []
    
    # Stage 1: Document Intelligence (succeeds)
    # ... (no error)
    
    # Stage 2: Web Research (fails)
    try:
        raise ConnectionError("External API unavailable")
    except Exception as e:
        error_id = await error_logger.log_error(
            error=e,
            context={
                'orchestrator': 'OrchestratorAgent',
                'failed_agent': 'WebResearchAgent',
                'application_id': application_id,
                'stage': 'research',
                'recovery_action': 'continue_without_web_research'
            },
            severity=ErrorSeverity.WARNING,  # Warning because we can continue
            application_id=application_id
        )
        workflow_errors.append(error_id)
    
    # Stage 3: Financial Analysis (succeeds)
    # ... (no error)
    
    # Stage 4: Risk Scoring (fails critically)
    try:
        raise RuntimeError("Cannot calculate risk score without required data")
    except Exception as e:
        error_id = await error_logger.log_error(
            error=e,
            context={
                'orchestrator': 'OrchestratorAgent',
                'failed_agent': 'RiskScoringAgent',
                'application_id': application_id,
                'stage': 'risk_scoring',
                'recovery_action': 'abort_workflow'
            },
            severity=ErrorSeverity.CRITICAL,  # Critical because we must abort
            application_id=application_id
        )
        workflow_errors.append(error_id)
    
    # Verify both errors were logged
    assert len(workflow_errors) == 2
    assert all(error_id is not None for error_id in workflow_errors)


@pytest.mark.asyncio
async def test_error_context_richness(error_logger, mock_firestore):
    """
    Test that error context includes rich debugging information.
    
    Verifies that logged errors contain sufficient context for debugging.
    """
    captured_entry = None
    
    def capture_add(entry):
        nonlocal captured_entry
        captured_entry = entry
        return (None, None)
    
    mock_firestore.collection.return_value.add.side_effect = capture_add
    
    # Simulate a complex error scenario
    try:
        # Create a nested call stack
        def level_3():
            raise ValueError("Invalid financial ratio: division by zero")
        
        def level_2():
            level_3()
        
        def level_1():
            level_2()
        
        level_1()
    except Exception as e:
        error_id = await error_logger.log_error(
            error=e,
            context={
                'agent': 'FinancialAnalysisAgent',
                'application_id': 'app555',
                'operation': 'calculate_ratios',
                'metric': 'debt_to_equity',
                'input_data': {
                    'total_debt': 1000000,
                    'total_equity': 0  # This caused the error
                },
                'calculation_step': 'ratio_calculation'
            },
            severity=ErrorSeverity.ERROR,
            application_id='app555',
            user_id='analyst123'
        )
    
    # Verify rich context was captured
    assert captured_entry is not None
    assert captured_entry['context']['agent'] == 'FinancialAnalysisAgent'
    assert captured_entry['context']['metric'] == 'debt_to_equity'
    assert captured_entry['context']['input_data']['total_equity'] == 0
    assert 'stack_trace' in captured_entry
    assert 'level_1' in captured_entry['stack_trace']
    assert 'level_2' in captured_entry['stack_trace']
    assert 'level_3' in captured_entry['stack_trace']


@pytest.mark.asyncio
async def test_error_severity_escalation(error_logger, mock_firestore):
    """
    Test logging errors with escalating severity levels.
    
    Simulates a scenario where errors escalate from WARNING to CRITICAL.
    """
    application_id = 'app111'
    
    # First attempt: Warning (retryable)
    try:
        raise ConnectionError("API timeout")
    except Exception as e:
        error_id_1 = await error_logger.log_error(
            error=e,
            context={
                'agent': 'WebResearchAgent',
                'application_id': application_id,
                'attempt': 1,
                'max_attempts': 3
            },
            severity=ErrorSeverity.WARNING,
            application_id=application_id
        )
    
    # Second attempt: Error (concerning)
    try:
        raise ConnectionError("API timeout")
    except Exception as e:
        error_id_2 = await error_logger.log_error(
            error=e,
            context={
                'agent': 'WebResearchAgent',
                'application_id': application_id,
                'attempt': 2,
                'max_attempts': 3
            },
            severity=ErrorSeverity.ERROR,
            application_id=application_id
        )
    
    # Third attempt: Critical (service down)
    try:
        raise ConnectionError("API timeout")
    except Exception as e:
        error_id_3 = await error_logger.log_error(
            error=e,
            context={
                'agent': 'WebResearchAgent',
                'application_id': application_id,
                'attempt': 3,
                'max_attempts': 3,
                'action': 'service_marked_unavailable'
            },
            severity=ErrorSeverity.CRITICAL,
            application_id=application_id
        )
    
    # Verify all three errors were logged with different IDs
    assert error_id_1 != error_id_2 != error_id_3
    assert all(eid is not None for eid in [error_id_1, error_id_2, error_id_3])


def test_synchronous_error_logging_in_sync_context(error_logger, mock_firestore):
    """
    Test that synchronous error logging works in non-async contexts.
    
    Some parts of the codebase may not be async, so we need sync logging.
    """
    # Simulate a synchronous operation that fails
    try:
        # Synchronous file operation
        raise IOError("Failed to read configuration file")
    except Exception as e:
        error_id = error_logger.log_error_sync(
            error=e,
            context={
                'component': 'ConfigLoader',
                'file_path': '/etc/config.yaml',
                'operation': 'read'
            },
            severity=ErrorSeverity.ERROR
        )
    
    assert error_id is not None
    mock_firestore.collection.assert_called_with('error_logs')
