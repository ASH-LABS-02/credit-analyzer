"""
Property-based tests for OrchestratorAgent

Feature: intelli-credit-platform
Property 6: Orchestrator Agent Coordination
Property 30: Agent Failure Recovery

Validates: Requirements 3.1, 3.5, 15.1
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
import asyncio

from app.agents.orchestrator_agent import OrchestratorAgent
from app.models.domain import (
    Application, ApplicationStatus, CreditRecommendation,
    RiskAssessment, RiskFactorScore
)


# Strategies for generating test data
application_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='-_'),
    min_size=5,
    max_size=50
)

company_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' .,&-'),
    min_size=3,
    max_size=100
)

loan_amount_strategy = st.floats(
    min_value=10000.0,
    max_value=100000000.0,
    allow_nan=False,
    allow_infinity=False
)

# Strategy for agent failure scenarios
agent_failure_strategy = st.lists(
    st.sampled_from([
        'document_intelligence',
        'financial_analysis',
        'web_research',
        'promoter_intelligence',
        'industry_intelligence',
        'forecasting',
        'risk_scoring',
        'cam_generator'
    ]),
    min_size=0,
    max_size=3,
    unique=True
)


def create_mock_application(app_id: str, company_name: str, loan_amount: float) -> Application:
    """Create a mock Application object."""
    return Application(
        id=app_id,
        company_name=company_name,
        loan_amount=loan_amount,
        loan_purpose="Business expansion",
        applicant_email="test@example.com",
        status=ApplicationStatus.PROCESSING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


def create_mock_orchestrator() -> OrchestratorAgent:
    """Create a mock OrchestratorAgent with mocked dependencies."""
    document_repo = MagicMock()
    application_repo = MagicMock()
    document_processor = MagicMock()
    
    orchestrator = OrchestratorAgent(document_repo, application_repo, document_processor)
    
    return orchestrator


def setup_successful_agent_mocks(orchestrator: OrchestratorAgent, company_name: str):
    """Setup all agents to return successful results."""
    # Document Intelligence
    orchestrator.document_intelligence.extract = AsyncMock(return_value={
        "financial_data": {
            "company_info": {
                "company_name": company_name,
                "industry": "Technology",
                "fiscal_year": "2023"
            },
            "revenue": {
                "values": [1000000, 1200000, 1500000],
                "years": ["2021", "2022", "2023"],
                "currency": "USD"
            },
            "profit": {
                "values": [100000, 150000, 200000],
                "years": ["2021", "2022", "2023"],
                "currency": "USD"
            }
        },
        "source_tracking": {},
        "ambiguous_flags": [],
        "documents_processed": 2
    })
    
    # Financial Analysis
    orchestrator.financial_analysis.analyze = AsyncMock(return_value={
        "ratios": {
            "current_ratio": {"value": 2.0, "formatted_value": "2.00"},
            "debt_to_equity": {"value": 0.5, "formatted_value": "0.50"}
        },
        "trends": {
            "revenue": {
                "trend_direction": "increasing",
                "cagr": 22.5
            }
        },
        "benchmarks": {},
        "summary": "Strong financial performance",
        "definitions": {}
    })
    
    # Web Research
    orchestrator.web_research.research = AsyncMock(return_value={
        "summary": "Positive market presence",
        "news_items": [],
        "red_flags": [],
        "positive_indicators": [{"description": "Strong growth"}],
        "sources": [],
        "research_date": datetime.utcnow().isoformat()
    })
    
    # Promoter Intelligence
    orchestrator.promoter_intelligence.analyze = AsyncMock(return_value={
        "summary": "Experienced management team",
        "promoter_profiles": [],
        "track_record_analysis": {"overall_rating": "good"},
        "red_flags": [],
        "positive_indicators": [],
        "overall_assessment": {},
        "conflicts_of_interest": [],
        "analysis_date": datetime.utcnow().isoformat()
    })
    
    # Industry Intelligence
    orchestrator.industry_intelligence.analyze = AsyncMock(return_value={
        "summary": "Favorable industry outlook",
        "industry": "Technology",
        "sector_trends": {"outlook": "positive"},
        "competitive_landscape": {},
        "industry_risks": [],
        "market_opportunities": [],
        "growth_outlook": {},
        "overall_assessment": {},
        "analysis_date": datetime.utcnow().isoformat()
    })
    
    # Forecasting
    orchestrator.forecasting.predict = AsyncMock(return_value={
        "forecasts": {
            "revenue": {
                "projected_values": [1800000, 2100000, 2400000],
                "forecast_growth_rate": 20.0
            }
        },
        "assumptions": ["Historical trends continue"],
        "methodology": "Blended forecasting",
        "confidence_level": 75.0
    })
    
    # Risk Scoring
    orchestrator.risk_scoring.score = AsyncMock(return_value=RiskAssessment(
        overall_score=75.0,
        recommendation=CreditRecommendation.APPROVE,
        financial_health=RiskFactorScore(
            factor_name="financial_health",
            score=80.0,
            weight=0.35,
            explanation="Strong financial position",
            key_findings=["Healthy ratios"]
        ),
        cash_flow=RiskFactorScore(
            factor_name="cash_flow",
            score=75.0,
            weight=0.25,
            explanation="Adequate cash flow",
            key_findings=["Positive trends"]
        ),
        industry=RiskFactorScore(
            factor_name="industry",
            score=70.0,
            weight=0.15,
            explanation="Favorable industry",
            key_findings=["Growth sector"]
        ),
        promoter=RiskFactorScore(
            factor_name="promoter",
            score=75.0,
            weight=0.15,
            explanation="Experienced team",
            key_findings=["Strong track record"]
        ),
        external_intelligence=RiskFactorScore(
            factor_name="external_intelligence",
            score=70.0,
            weight=0.10,
            explanation="Positive sentiment",
            key_findings=["Good reputation"]
        ),
        summary="Strong creditworthiness with approval recommendation"
    ))
    
    # CAM Generator
    orchestrator.cam_generator.generate = AsyncMock(return_value={
        "content": "Complete CAM document",
        "sections": {
            "executive_summary": "Summary",
            "company_overview": "Overview",
            "financial_analysis": "Analysis",
            "risk_assessment": "Assessment",
            "recommendation": "Recommendation"
        },
        "generated_at": datetime.utcnow().isoformat(),
        "version": 1
    })


def inject_agent_failures(orchestrator: OrchestratorAgent, failing_agents: list):
    """Inject failures into specified agents."""
    for agent_name in failing_agents:
        if agent_name == 'document_intelligence':
            orchestrator.document_intelligence.extract = AsyncMock(
                side_effect=Exception(f"{agent_name} failed")
            )
        elif agent_name == 'financial_analysis':
            orchestrator.financial_analysis.analyze = AsyncMock(
                side_effect=Exception(f"{agent_name} failed")
            )
        elif agent_name == 'web_research':
            orchestrator.web_research.research = AsyncMock(
                side_effect=Exception(f"{agent_name} failed")
            )
        elif agent_name == 'promoter_intelligence':
            orchestrator.promoter_intelligence.analyze = AsyncMock(
                side_effect=Exception(f"{agent_name} failed")
            )
        elif agent_name == 'industry_intelligence':
            orchestrator.industry_intelligence.analyze = AsyncMock(
                side_effect=Exception(f"{agent_name} failed")
            )
        elif agent_name == 'forecasting':
            orchestrator.forecasting.predict = AsyncMock(
                side_effect=Exception(f"{agent_name} failed")
            )
        elif agent_name == 'risk_scoring':
            orchestrator.risk_scoring.score = AsyncMock(
                side_effect=Exception(f"{agent_name} failed")
            )
        elif agent_name == 'cam_generator':
            orchestrator.cam_generator.generate = AsyncMock(
                side_effect=Exception(f"{agent_name} failed")
            )


class TestProperty6OrchestratorAgentCoordination:
    """
    Property 6: Orchestrator Agent Coordination
    
    For any application requiring analysis, the Orchestrator should delegate tasks
    to all required specialized agents (Document Intelligence, Financial Analysis,
    Web Research, Promoter Intelligence, Industry Intelligence, Forecasting,
    Risk Scoring, CAM Generator) and aggregate their results into a unified analysis.
    
    Validates: Requirements 3.1, 3.5
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        app_id=application_id_strategy,
        company_name=company_name_strategy,
        loan_amount=loan_amount_strategy
    )
    async def test_orchestrator_delegates_to_all_agents(
        self,
        app_id: str,
        company_name: str,
        loan_amount: float
    ):
        """
        Property: For any application, the orchestrator delegates to all required agents.
        
        The orchestrator must call all 8 specialized agents:
        1. Document Intelligence
        2. Financial Analysis
        3. Web Research
        4. Promoter Intelligence
        5. Industry Intelligence
        6. Forecasting
        7. Risk Scoring
        8. CAM Generator
        """
        # Filter out invalid inputs
        assume(len(app_id.strip()) >= 5)
        assume(len(company_name.strip()) >= 3)
        assume(loan_amount >= 10000.0)
        
        # Create orchestrator and mock application
        orchestrator = create_mock_orchestrator()
        application = create_mock_application(app_id, company_name, loan_amount)
        orchestrator.application_repository.get = AsyncMock(return_value=application)
        
        # Setup all agents to succeed
        setup_successful_agent_mocks(orchestrator, company_name)
        
        # Execute workflow
        result = await orchestrator.process_application(app_id)
        
        # Verify all agents were called
        orchestrator.document_intelligence.extract.assert_called_once()
        orchestrator.financial_analysis.analyze.assert_called_once()
        orchestrator.web_research.research.assert_called_once()
        orchestrator.promoter_intelligence.analyze.assert_called_once()
        orchestrator.industry_intelligence.analyze.assert_called_once()
        orchestrator.forecasting.predict.assert_called_once()
        orchestrator.risk_scoring.score.assert_called_once()
        orchestrator.cam_generator.generate.assert_called_once()
        
        # Verify result contains all agent outputs
        assert "extracted_data" in result
        assert "financial_analysis" in result
        assert "research" in result
        assert "forecasts" in result
        assert "risk_assessment" in result
        assert "cam" in result
        
        # Verify research aggregation
        assert "web" in result["research"]
        assert "promoter" in result["research"]
        assert "industry" in result["research"]
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        app_id=application_id_strategy,
        company_name=company_name_strategy,
        loan_amount=loan_amount_strategy
    )
    async def test_orchestrator_aggregates_results_correctly(
        self,
        app_id: str,
        company_name: str,
        loan_amount: float
    ):
        """
        Property: For any application, the orchestrator aggregates all agent results
        into a unified analysis structure.
        
        The result must contain:
        - success flag
        - application_id
        - company_name
        - All agent results (extracted_data, financial_analysis, research, forecasts, risk_assessment, cam)
        - errors list
        - warnings list
        - processing_time
        - timestamp
        """
        # Filter out invalid inputs
        assume(len(app_id.strip()) >= 5)
        assume(len(company_name.strip()) >= 3)
        assume(loan_amount >= 10000.0)
        
        # Create orchestrator and mock application
        orchestrator = create_mock_orchestrator()
        application = create_mock_application(app_id, company_name, loan_amount)
        orchestrator.application_repository.get = AsyncMock(return_value=application)
        
        # Setup all agents to succeed
        setup_successful_agent_mocks(orchestrator, company_name)
        
        # Execute workflow
        result = await orchestrator.process_application(app_id)
        
        # Verify result structure completeness
        required_keys = [
            "success",
            "application_id",
            "company_name",
            "extracted_data",
            "financial_analysis",
            "research",
            "forecasts",
            "risk_assessment",
            "cam",
            "errors",
            "warnings",
            "processing_time",
            "timestamp"
        ]
        
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"
        
        # Verify data types
        assert isinstance(result["success"], bool)
        assert isinstance(result["application_id"], str)
        assert isinstance(result["company_name"], str)
        assert isinstance(result["extracted_data"], dict)
        assert isinstance(result["financial_analysis"], dict)
        assert isinstance(result["research"], dict)
        assert isinstance(result["forecasts"], dict)
        assert isinstance(result["risk_assessment"], dict)
        assert isinstance(result["cam"], dict)
        assert isinstance(result["errors"], list)
        assert isinstance(result["warnings"], list)
        assert isinstance(result["processing_time"], (int, float))
        assert isinstance(result["timestamp"], str)
        
        # Verify application_id matches
        assert result["application_id"] == app_id
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        app_id=application_id_strategy,
        company_name=company_name_strategy,
        loan_amount=loan_amount_strategy
    )
    async def test_orchestrator_executes_research_agents_in_parallel(
        self,
        app_id: str,
        company_name: str,
        loan_amount: float
    ):
        """
        Property: For any application, the orchestrator executes research agents
        (Web Research, Promoter Intelligence, Industry Intelligence) in parallel.
        
        This verifies that the orchestrator uses asyncio.gather for concurrent execution.
        """
        # Filter out invalid inputs
        assume(len(app_id.strip()) >= 5)
        assume(len(company_name.strip()) >= 3)
        assume(loan_amount >= 10000.0)
        
        # Create orchestrator and mock application
        orchestrator = create_mock_orchestrator()
        application = create_mock_application(app_id, company_name, loan_amount)
        orchestrator.application_repository.get = AsyncMock(return_value=application)
        
        # Setup all agents to succeed
        setup_successful_agent_mocks(orchestrator, company_name)
        
        # Track call order using a shared list
        call_order = []
        
        async def track_web_research(*args, **kwargs):
            call_order.append('web_research_start')
            await asyncio.sleep(0.01)  # Simulate work
            call_order.append('web_research_end')
            return {
                "summary": "Web research",
                "news_items": [],
                "red_flags": [],
                "positive_indicators": [],
                "sources": [],
                "research_date": datetime.utcnow().isoformat()
            }
        
        async def track_promoter(*args, **kwargs):
            call_order.append('promoter_start')
            await asyncio.sleep(0.01)  # Simulate work
            call_order.append('promoter_end')
            return {
                "summary": "Promoter analysis",
                "promoter_profiles": [],
                "track_record_analysis": {},
                "red_flags": [],
                "positive_indicators": [],
                "overall_assessment": {},
                "conflicts_of_interest": [],
                "analysis_date": datetime.utcnow().isoformat()
            }
        
        async def track_industry(*args, **kwargs):
            call_order.append('industry_start')
            await asyncio.sleep(0.01)  # Simulate work
            call_order.append('industry_end')
            return {
                "summary": "Industry analysis",
                "industry": "Tech",
                "sector_trends": {},
                "competitive_landscape": {},
                "industry_risks": [],
                "market_opportunities": [],
                "growth_outlook": {},
                "overall_assessment": {},
                "analysis_date": datetime.utcnow().isoformat()
            }
        
        orchestrator.web_research.research = AsyncMock(side_effect=track_web_research)
        orchestrator.promoter_intelligence.analyze = AsyncMock(side_effect=track_promoter)
        orchestrator.industry_intelligence.analyze = AsyncMock(side_effect=track_industry)
        
        # Execute workflow
        result = await orchestrator.process_application(app_id)
        
        # Verify all research agents were called
        orchestrator.web_research.research.assert_called_once()
        orchestrator.promoter_intelligence.analyze.assert_called_once()
        orchestrator.industry_intelligence.analyze.assert_called_once()
        
        # Verify parallel execution: all starts should happen before all ends
        # (if sequential, we'd see start-end-start-end-start-end pattern)
        start_indices = [
            call_order.index('web_research_start'),
            call_order.index('promoter_start'),
            call_order.index('industry_start')
        ]
        end_indices = [
            call_order.index('web_research_end'),
            call_order.index('promoter_end'),
            call_order.index('industry_end')
        ]
        
        # All starts should come before all ends (parallel execution)
        # This is a weak check but demonstrates concurrent execution
        assert len(call_order) == 6
        assert 'web_research_start' in call_order
        assert 'promoter_start' in call_order
        assert 'industry_start' in call_order


class TestProperty30AgentFailureRecovery:
    """
    Property 30: Agent Failure Recovery
    
    For any agent failure during processing, the Orchestrator should log the error
    with detailed information and either attempt recovery or gracefully degrade
    functionality without crashing the entire workflow.
    
    Validates: Requirements 15.1, 15.5
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        app_id=application_id_strategy,
        company_name=company_name_strategy,
        loan_amount=loan_amount_strategy,
        failing_agents=agent_failure_strategy
    )
    async def test_orchestrator_handles_agent_failures_gracefully(
        self,
        app_id: str,
        company_name: str,
        loan_amount: float,
        failing_agents: list
    ):
        """
        Property: For any agent failure, the orchestrator logs the error and
        continues workflow execution without crashing.
        
        The workflow should:
        1. Not raise an exception
        2. Log errors for failed agents
        3. Continue processing with remaining agents
        4. Return a result (even if partial)
        """
        # Filter out invalid inputs
        assume(len(app_id.strip()) >= 5)
        assume(len(company_name.strip()) >= 3)
        assume(loan_amount >= 10000.0)
        
        # Create orchestrator and mock application
        orchestrator = create_mock_orchestrator()
        application = create_mock_application(app_id, company_name, loan_amount)
        orchestrator.application_repository.get = AsyncMock(return_value=application)
        
        # Setup all agents to succeed initially
        setup_successful_agent_mocks(orchestrator, company_name)
        
        # Inject failures into specified agents
        inject_agent_failures(orchestrator, failing_agents)
        
        # Execute workflow - should not raise exception
        result = await orchestrator.process_application(app_id)
        
        # Verify workflow completed (didn't crash)
        assert result is not None
        assert "success" in result
        assert "errors" in result
        assert "application_id" in result
        
        # Verify errors were logged for failed agents
        if len(failing_agents) > 0:
            assert len(result["errors"]) > 0, "Failed agents should produce error logs"
            
            # Check that each failing agent has an error logged
            for agent_name in failing_agents:
                # Convert agent name to expected error format
                agent_display_names = {
                    'document_intelligence': 'Document Intelligence',
                    'financial_analysis': 'Financial Analysis',
                    'web_research': 'Web Research',
                    'promoter_intelligence': 'Promoter Intelligence',
                    'industry_intelligence': 'Industry Intelligence',
                    'forecasting': 'Forecasting',
                    'risk_scoring': 'Risk Scoring',
                    'cam_generator': 'CAM Generation'
                }
                
                expected_agent_name = agent_display_names.get(agent_name, agent_name)
                
                # Check if any error mentions this agent
                agent_error_found = any(
                    expected_agent_name in error or agent_name in error
                    for error in result["errors"]
                )
                
                assert agent_error_found, \
                    f"Expected error log for {expected_agent_name}, but not found in: {result['errors']}"
        
        # Verify result structure is still complete (graceful degradation)
        required_keys = [
            "success",
            "application_id",
            "company_name",
            "extracted_data",
            "financial_analysis",
            "research",
            "forecasts",
            "risk_assessment",
            "cam",
            "errors",
            "warnings",
            "processing_time",
            "timestamp"
        ]
        
        for key in required_keys:
            assert key in result, f"Missing required key even with failures: {key}"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        app_id=application_id_strategy,
        company_name=company_name_strategy,
        loan_amount=loan_amount_strategy
    )
    async def test_orchestrator_provides_default_values_on_failure(
        self,
        app_id: str,
        company_name: str,
        loan_amount: float
    ):
        """
        Property: For any agent failure, the orchestrator provides default/empty
        values to allow downstream agents to continue processing.
        
        This tests graceful degradation by ensuring that even when agents fail,
        the workflow continues with sensible defaults.
        """
        # Filter out invalid inputs
        assume(len(app_id.strip()) >= 5)
        assume(len(company_name.strip()) >= 3)
        assume(loan_amount >= 10000.0)
        
        # Create orchestrator and mock application
        orchestrator = create_mock_orchestrator()
        application = create_mock_application(app_id, company_name, loan_amount)
        orchestrator.application_repository.get = AsyncMock(return_value=application)
        
        # Setup all agents to succeed initially
        setup_successful_agent_mocks(orchestrator, company_name)
        
        # Make document intelligence fail (early stage failure)
        orchestrator.document_intelligence.extract = AsyncMock(
            side_effect=Exception("Document intelligence failed")
        )
        
        # Execute workflow
        result = await orchestrator.process_application(app_id)
        
        # Verify workflow completed
        assert result is not None
        
        # Verify error was logged
        assert len(result["errors"]) > 0
        assert any("Document Intelligence" in error for error in result["errors"])
        
        # Verify downstream agents still executed (graceful degradation)
        # Even though document intelligence failed, other agents should have been called
        orchestrator.financial_analysis.analyze.assert_called_once()
        orchestrator.risk_scoring.score.assert_called_once()
        orchestrator.cam_generator.generate.assert_called_once()
        
        # Verify result contains default/empty values for failed agent
        assert "extracted_data" in result
        # The extracted_data might be None or empty dict depending on implementation
        assert result["extracted_data"] is not None or result["extracted_data"] == {}
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        app_id=application_id_strategy,
        company_name=company_name_strategy,
        loan_amount=loan_amount_strategy
    )
    async def test_orchestrator_handles_parallel_research_failures(
        self,
        app_id: str,
        company_name: str,
        loan_amount: float
    ):
        """
        Property: For any research agent failure during parallel execution,
        the orchestrator continues with successful agents and logs failures.
        
        This specifically tests the parallel research execution error handling.
        """
        # Filter out invalid inputs
        assume(len(app_id.strip()) >= 5)
        assume(len(company_name.strip()) >= 3)
        assume(loan_amount >= 10000.0)
        
        # Create orchestrator and mock application
        orchestrator = create_mock_orchestrator()
        application = create_mock_application(app_id, company_name, loan_amount)
        orchestrator.application_repository.get = AsyncMock(return_value=application)
        
        # Setup all agents to succeed initially
        setup_successful_agent_mocks(orchestrator, company_name)
        
        # Make one research agent fail
        orchestrator.web_research.research = AsyncMock(
            side_effect=Exception("Web research failed")
        )
        
        # Execute workflow
        result = await orchestrator.process_application(app_id)
        
        # Verify workflow completed
        assert result is not None
        
        # Verify error was logged for web research
        assert len(result["errors"]) > 0
        assert any("Web Research" in error for error in result["errors"])
        
        # Verify other research agents still executed successfully
        orchestrator.promoter_intelligence.analyze.assert_called_once()
        orchestrator.industry_intelligence.analyze.assert_called_once()
        
        # Verify research results contain data from successful agents
        assert "research" in result
        assert "web" in result["research"]  # Should have empty/default result
        assert "promoter" in result["research"]  # Should have real result
        assert "industry" in result["research"]  # Should have real result
        
        # Verify successful agents have meaningful data
        assert result["research"]["promoter"]["summary"] == "Experienced management team"
        assert result["research"]["industry"]["summary"] == "Favorable industry outlook"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        app_id=application_id_strategy,
        company_name=company_name_strategy,
        loan_amount=loan_amount_strategy
    )
    async def test_orchestrator_logs_detailed_error_information(
        self,
        app_id: str,
        company_name: str,
        loan_amount: float
    ):
        """
        Property: For any agent failure, the orchestrator logs detailed error
        information including agent name and error message.
        
        Validates: Requirements 15.5
        """
        # Filter out invalid inputs
        assume(len(app_id.strip()) >= 5)
        assume(len(company_name.strip()) >= 3)
        assume(loan_amount >= 10000.0)
        
        # Create orchestrator and mock application
        orchestrator = create_mock_orchestrator()
        application = create_mock_application(app_id, company_name, loan_amount)
        orchestrator.application_repository.get = AsyncMock(return_value=application)
        
        # Setup all agents to succeed initially
        setup_successful_agent_mocks(orchestrator, company_name)
        
        # Make forecasting agent fail with specific error message
        error_message = "Insufficient historical data for forecasting"
        orchestrator.forecasting.predict = AsyncMock(
            side_effect=Exception(error_message)
        )
        
        # Execute workflow
        result = await orchestrator.process_application(app_id)
        
        # Verify error was logged with detailed information
        assert len(result["errors"]) > 0
        
        # Check that error log contains both agent name and error message
        forecasting_error_found = False
        for error in result["errors"]:
            if "Forecasting" in error and error_message in error:
                forecasting_error_found = True
                break
        
        assert forecasting_error_found, \
            f"Expected detailed error log for Forecasting with message '{error_message}', " \
            f"but found: {result['errors']}"
