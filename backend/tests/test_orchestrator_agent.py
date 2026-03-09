"""
Unit tests for OrchestratorAgent

Tests the orchestration workflow, parallel execution, error recovery,
and result aggregation functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.agents.orchestrator_agent import OrchestratorAgent
from app.models.domain import (
    Application, ApplicationStatus, CreditRecommendation,
    RiskAssessment, RiskFactorScore
)


@pytest.fixture
def mock_repositories():
    """Create mock repositories for testing."""
    document_repo = MagicMock()
    application_repo = MagicMock()
    document_processor = MagicMock()
    
    return document_repo, application_repo, document_processor


@pytest.fixture
def orchestrator_agent(mock_repositories):
    """Create an OrchestratorAgent instance for testing."""
    document_repo, application_repo, document_processor = mock_repositories
    return OrchestratorAgent(document_repo, application_repo, document_processor)


@pytest.fixture
def sample_application():
    """Create a sample application for testing."""
    return Application(
        id="test-app-123",
        company_name="Test Company Inc",
        loan_amount=1000000.0,
        loan_purpose="Business expansion",
        applicant_email="test@example.com",
        status=ApplicationStatus.PROCESSING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_extracted_data():
    """Sample extracted data from document intelligence."""
    return {
        "financial_data": {
            "company_info": {
                "company_name": "Test Company Inc",
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
    }


@pytest.fixture
def sample_financial_analysis():
    """Sample financial analysis results."""
    return {
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
    }


@pytest.fixture
def sample_research_results():
    """Sample research results from all research agents."""
    return {
        "web": {
            "summary": "Positive market presence",
            "news_items": [],
            "red_flags": [],
            "positive_indicators": [{"description": "Strong growth"}],
            "sources": []
        },
        "promoter": {
            "summary": "Experienced management team",
            "promoter_profiles": [],
            "track_record_analysis": {"overall_rating": "good"},
            "red_flags": [],
            "positive_indicators": []
        },
        "industry": {
            "summary": "Favorable industry outlook",
            "industry": "Technology",
            "sector_trends": {"outlook": "positive"},
            "competitive_landscape": {},
            "industry_risks": []
        }
    }


@pytest.fixture
def sample_forecasts():
    """Sample forecast results."""
    return {
        "forecasts": {
            "revenue": {
                "projected_values": [1800000, 2100000, 2400000],
                "forecast_growth_rate": 20.0
            }
        },
        "assumptions": ["Historical trends continue"],
        "methodology": "Blended forecasting",
        "confidence_level": 75.0
    }


@pytest.fixture
def sample_risk_assessment():
    """Sample risk assessment."""
    return RiskAssessment(
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
    )


class TestOrchestratorAgent:
    """Test suite for OrchestratorAgent."""
    
    @pytest.mark.asyncio
    async def test_process_application_success(
        self,
        orchestrator_agent,
        sample_application,
        sample_extracted_data,
        sample_financial_analysis,
        sample_research_results,
        sample_forecasts,
        sample_risk_assessment
    ):
        """Test successful application processing workflow."""
        # Mock application repository
        orchestrator_agent.application_repository.get = AsyncMock(return_value=sample_application)
        
        # Mock all agent methods
        orchestrator_agent.document_intelligence.extract = AsyncMock(return_value=sample_extracted_data)
        orchestrator_agent.financial_analysis.analyze = AsyncMock(return_value=sample_financial_analysis)
        orchestrator_agent.web_research.research = AsyncMock(return_value=sample_research_results["web"])
        orchestrator_agent.promoter_intelligence.analyze = AsyncMock(return_value=sample_research_results["promoter"])
        orchestrator_agent.industry_intelligence.analyze = AsyncMock(return_value=sample_research_results["industry"])
        orchestrator_agent.forecasting.predict = AsyncMock(return_value=sample_forecasts)
        orchestrator_agent.risk_scoring.score = AsyncMock(return_value=sample_risk_assessment)
        orchestrator_agent.cam_generator.generate = AsyncMock(return_value={
            "content": "CAM content",
            "sections": {},
            "generated_at": datetime.utcnow().isoformat()
        })
        
        # Execute workflow
        result = await orchestrator_agent.process_application("test-app-123")
        
        # Verify result structure
        assert result["success"] is True
        assert result["application_id"] == "test-app-123"
        assert result["company_name"] == "Test Company Inc"
        assert "extracted_data" in result
        assert "financial_analysis" in result
        assert "research" in result
        assert "forecasts" in result
        assert "risk_assessment" in result
        assert "cam" in result
        assert len(result["errors"]) == 0
        assert "processing_time" in result
        assert "timestamp" in result
        
        # Verify all agents were called
        orchestrator_agent.document_intelligence.extract.assert_called_once()
        orchestrator_agent.financial_analysis.analyze.assert_called_once()
        orchestrator_agent.web_research.research.assert_called_once()
        orchestrator_agent.promoter_intelligence.analyze.assert_called_once()
        orchestrator_agent.industry_intelligence.analyze.assert_called_once()
        orchestrator_agent.forecasting.predict.assert_called_once()
        orchestrator_agent.risk_scoring.score.assert_called_once()
        orchestrator_agent.cam_generator.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_application_not_found(self, orchestrator_agent):
        """Test processing with non-existent application."""
        orchestrator_agent.application_repository.get = AsyncMock(return_value=None)
        
        result = await orchestrator_agent.process_application("nonexistent-app")
        
        assert result["success"] is False
        assert "not found" in result["errors"][0].lower()
    
    @pytest.mark.asyncio
    async def test_parallel_research_execution(
        self,
        orchestrator_agent,
        sample_extracted_data,
        sample_research_results
    ):
        """Test that research agents execute in parallel."""
        # Mock research agents
        orchestrator_agent.web_research.research = AsyncMock(return_value=sample_research_results["web"])
        orchestrator_agent.promoter_intelligence.analyze = AsyncMock(return_value=sample_research_results["promoter"])
        orchestrator_agent.industry_intelligence.analyze = AsyncMock(return_value=sample_research_results["industry"])
        
        # Execute parallel research
        result = await orchestrator_agent._execute_parallel_research(
            "Test Company Inc",
            sample_extracted_data
        )
        
        # Verify all research agents were called
        assert "web" in result
        assert "promoter" in result
        assert "industry" in result
        
        orchestrator_agent.web_research.research.assert_called_once()
        orchestrator_agent.promoter_intelligence.analyze.assert_called_once()
        orchestrator_agent.industry_intelligence.analyze.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_recovery_in_agent(self, orchestrator_agent):
        """Test error recovery when an agent fails."""
        # Mock agent that raises an exception
        async def failing_agent(*args, **kwargs):
            raise Exception("Agent failed")
        
        result = await orchestrator_agent._execute_with_recovery(
            failing_agent,
            "Test Agent"
        )
        
        # Should return None and log error
        assert result is None
        assert len(orchestrator_agent.errors) == 1
        assert "Test Agent failed" in orchestrator_agent.errors[0]
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_document_intelligence(
        self,
        orchestrator_agent,
        sample_application
    ):
        """Test graceful degradation when document intelligence fails."""
        orchestrator_agent.application_repository.get = AsyncMock(return_value=sample_application)
        
        # Mock document intelligence to fail
        orchestrator_agent.document_intelligence.extract = AsyncMock(side_effect=Exception("Extraction failed"))
        
        # Mock other agents to succeed
        orchestrator_agent.financial_analysis.analyze = AsyncMock(return_value={
            "ratios": {}, "trends": {}, "benchmarks": {}, "summary": "Limited analysis", "definitions": {}
        })
        orchestrator_agent.web_research.research = AsyncMock(return_value={
            "summary": "Research complete", "news_items": [], "red_flags": [], "positive_indicators": [], "sources": []
        })
        orchestrator_agent.promoter_intelligence.analyze = AsyncMock(return_value={
            "summary": "Promoter analysis", "promoter_profiles": [], "track_record_analysis": {},
            "conflicts_of_interest": [], "red_flags": [], "positive_indicators": [], "overall_assessment": {}
        })
        orchestrator_agent.industry_intelligence.analyze = AsyncMock(return_value={
            "summary": "Industry analysis", "industry": "Tech", "sector_trends": {},
            "competitive_landscape": {}, "industry_risks": [], "market_opportunities": [],
            "growth_outlook": {}, "overall_assessment": {}
        })
        orchestrator_agent.forecasting.predict = AsyncMock(return_value={
            "forecasts": {}, "assumptions": [], "methodology": "", "confidence_level": 0.0
        })
        orchestrator_agent.risk_scoring.score = AsyncMock(return_value=RiskAssessment(
            overall_score=50.0,
            recommendation=CreditRecommendation.APPROVE_WITH_CONDITIONS,
            financial_health=RiskFactorScore(
                factor_name="financial_health",
                score=50.0,
                weight=0.35,
                explanation="Default",
                key_findings=[]
            ),
            cash_flow=RiskFactorScore(
                factor_name="cash_flow",
                score=50.0,
                weight=0.25,
                explanation="Default",
                key_findings=[]
            ),
            industry=RiskFactorScore(
                factor_name="industry",
                score=50.0,
                weight=0.15,
                explanation="Default",
                key_findings=[]
            ),
            promoter=RiskFactorScore(
                factor_name="promoter",
                score=50.0,
                weight=0.15,
                explanation="Default",
                key_findings=[]
            ),
            external_intelligence=RiskFactorScore(
                factor_name="external_intelligence",
                score=50.0,
                weight=0.10,
                explanation="Default",
                key_findings=[]
            ),
            summary="Default assessment"
        ))
        orchestrator_agent.cam_generator.generate = AsyncMock(return_value={
            "content": "CAM", "sections": {}, "generated_at": datetime.utcnow().isoformat()
        })
        
        result = await orchestrator_agent.process_application("test-app-123")
        
        # Workflow should complete despite document intelligence failure
        assert result["success"] is False  # Has errors
        assert len(result["errors"]) > 0
        assert any("Document Intelligence failed" in error for error in result["errors"])
        assert len(result["warnings"]) > 0
    
    @pytest.mark.asyncio
    async def test_parallel_research_with_partial_failure(
        self,
        orchestrator_agent,
        sample_extracted_data
    ):
        """Test parallel research when one agent fails."""
        # Mock one agent to fail, others to succeed
        orchestrator_agent.web_research.research = AsyncMock(side_effect=Exception("Web research failed"))
        orchestrator_agent.promoter_intelligence.analyze = AsyncMock(return_value={
            "summary": "Promoter analysis", "promoter_profiles": []
        })
        orchestrator_agent.industry_intelligence.analyze = AsyncMock(return_value={
            "summary": "Industry analysis", "industry": "Tech"
        })
        
        result = await orchestrator_agent._execute_parallel_research(
            "Test Company",
            sample_extracted_data
        )
        
        # Should have results from successful agents and empty result for failed agent
        assert "web" in result
        assert "promoter" in result
        assert "industry" in result
        
        # Web research should have empty result (None is converted to empty dict)
        # The _execute_parallel_research method handles exceptions and returns empty results
        assert result["web"] is not None
        if isinstance(result["web"], dict):
            assert "summary" in result["web"]
        
        # Other agents should have real results
        assert result["promoter"]["summary"] == "Promoter analysis"
        assert result["industry"]["summary"] == "Industry analysis"
        
        # Should have logged error
        assert len(orchestrator_agent.errors) > 0
        assert any("Web Research failed" in error for error in orchestrator_agent.errors)
    
    @pytest.mark.asyncio
    async def test_serialize_risk_assessment(self, orchestrator_agent, sample_risk_assessment):
        """Test risk assessment serialization."""
        serialized = orchestrator_agent._serialize_risk_assessment(sample_risk_assessment)
        
        assert isinstance(serialized, dict)
        assert "overall_score" in serialized
        assert "recommendation" in serialized
        assert "financial_health" in serialized
        assert "cash_flow" in serialized
        assert "industry" in serialized
        assert "promoter" in serialized
        assert "external_intelligence" in serialized
        assert "summary" in serialized
        
        # Check that recommendation is serialized as string
        assert isinstance(serialized["recommendation"], str)
    
    def test_empty_result_generators(self, orchestrator_agent):
        """Test empty result generators for graceful degradation."""
        web_result = orchestrator_agent._empty_web_research_result()
        assert "summary" in web_result
        assert web_result["news_items"] == []
        
        promoter_result = orchestrator_agent._empty_promoter_result()
        assert "summary" in promoter_result
        assert promoter_result["promoter_profiles"] == []
        
        industry_result = orchestrator_agent._empty_industry_result()
        assert "summary" in industry_result
        assert industry_result["industry"] == "Unknown"
    
    @pytest.mark.asyncio
    async def test_error_result_generation(self, orchestrator_agent):
        """Test error result generation."""
        start_time = datetime.utcnow()
        result = orchestrator_agent._error_result(
            "test-app-123",
            "Test error message",
            start_time
        )
        
        assert result["success"] is False
        assert result["application_id"] == "test-app-123"
        assert "Test error message" in result["errors"]
        assert "processing_time" in result
        assert "timestamp" in result


class TestOrchestratorAgentIntegration:
    """Integration tests for OrchestratorAgent workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_with_all_stages(
        self,
        orchestrator_agent,
        sample_application,
        sample_extracted_data,
        sample_financial_analysis,
        sample_research_results,
        sample_forecasts,
        sample_risk_assessment
    ):
        """Test complete workflow through all stages."""
        # Setup mocks for complete workflow
        orchestrator_agent.application_repository.get = AsyncMock(return_value=sample_application)
        orchestrator_agent.document_intelligence.extract = AsyncMock(return_value=sample_extracted_data)
        orchestrator_agent.financial_analysis.analyze = AsyncMock(return_value=sample_financial_analysis)
        orchestrator_agent.web_research.research = AsyncMock(return_value=sample_research_results["web"])
        orchestrator_agent.promoter_intelligence.analyze = AsyncMock(return_value=sample_research_results["promoter"])
        orchestrator_agent.industry_intelligence.analyze = AsyncMock(return_value=sample_research_results["industry"])
        orchestrator_agent.forecasting.predict = AsyncMock(return_value=sample_forecasts)
        orchestrator_agent.risk_scoring.score = AsyncMock(return_value=sample_risk_assessment)
        orchestrator_agent.cam_generator.generate = AsyncMock(return_value={
            "content": "Complete CAM document",
            "sections": {
                "executive_summary": "Summary",
                "financial_analysis": "Analysis",
                "risk_assessment": "Assessment"
            },
            "generated_at": datetime.utcnow().isoformat()
        })
        
        result = await orchestrator_agent.process_application("test-app-123")
        
        # Verify complete workflow execution
        assert result["success"] is True
        assert len(result["errors"]) == 0
        
        # Verify data flows through stages
        assert result["extracted_data"]["documents_processed"] == 2
        assert result["financial_analysis"]["summary"] == "Strong financial performance"
        assert result["research"]["web"]["summary"] == "Positive market presence"
        assert result["forecasts"]["confidence_level"] == 75.0
        assert result["risk_assessment"]["overall_score"] == 75.0
        assert result["cam"]["content"] == "Complete CAM document"
        
        # Verify processing time is reasonable
        assert result["processing_time"] < 10.0  # Should complete quickly with mocks



# ============================================================================
# Property-Based Tests for Orchestrator Agent
# ============================================================================

from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis import assume


class TestOrchestratorAgentProperties:
    """
    Property-based tests for OrchestratorAgent.
    
    These tests validate universal properties that should hold across all
    valid executions of the orchestrator workflow.
    """
    
    # Feature: intelli-credit-platform, Property 6: Orchestrator Agent Coordination
    @pytest.mark.asyncio
    @settings(
        max_examples=5,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        company_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        loan_amount=st.floats(min_value=1000, max_value=100000000),
        loan_purpose=st.text(min_size=1, max_size=200).filter(lambda x: x.strip())
    )
    async def test_property_orchestrator_coordination(
        self,
        orchestrator_agent,
        company_name,
        loan_amount,
        loan_purpose
    ):
        """
        **Validates: Requirements 3.1, 3.5**
        
        Property 6: Orchestrator Agent Coordination
        
        For any application requiring analysis, the Orchestrator should delegate
        tasks to all required specialized agents (Document Intelligence, Financial
        Analysis, Web Research, Promoter Intelligence, Industry Intelligence,
        Forecasting, Risk Scoring, CAM Generator) and aggregate their results
        into a unified analysis.
        
        This property verifies that:
        1. All specialized agents are invoked during the workflow
        2. Results from all agents are aggregated into the final output
        3. The workflow completes with a structured result containing all components
        """
        # Create a test application
        from app.models.domain import Application, ApplicationStatus
        test_app = Application(
            id="prop-test-app",
            company_name=company_name,
            loan_amount=loan_amount,
            loan_purpose=loan_purpose,
            applicant_email="test@example.com",
            status=ApplicationStatus.PROCESSING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock application repository
        orchestrator_agent.application_repository.get = AsyncMock(return_value=test_app)
        
        # Mock all specialized agents with minimal valid responses
        orchestrator_agent.document_intelligence.extract = AsyncMock(return_value={
            "financial_data": {
                "company_info": {"company_name": company_name, "industry": "Technology"},
                "revenue": {"values": [1000000], "years": ["2023"], "currency": "USD"}
            },
            "source_tracking": {},
            "ambiguous_flags": [],
            "documents_processed": 1
        })
        
        orchestrator_agent.financial_analysis.analyze = AsyncMock(return_value={
            "ratios": {"current_ratio": {"value": 2.0, "formatted_value": "2.00"}},
            "trends": {},
            "benchmarks": {},
            "summary": "Analysis complete",
            "definitions": {}
        })
        
        orchestrator_agent.web_research.research = AsyncMock(return_value={
            "summary": "Research complete",
            "news_items": [],
            "red_flags": [],
            "positive_indicators": [],
            "sources": []
        })
        
        orchestrator_agent.promoter_intelligence.analyze = AsyncMock(return_value={
            "summary": "Promoter analysis complete",
            "promoter_profiles": [],
            "track_record_analysis": {},
            "conflicts_of_interest": [],
            "red_flags": [],
            "positive_indicators": [],
            "overall_assessment": {}
        })
        
        orchestrator_agent.industry_intelligence.analyze = AsyncMock(return_value={
            "summary": "Industry analysis complete",
            "industry": "Technology",
            "sector_trends": {},
            "competitive_landscape": {},
            "industry_risks": [],
            "market_opportunities": [],
            "growth_outlook": {},
            "overall_assessment": {}
        })
        
        orchestrator_agent.forecasting.predict = AsyncMock(return_value={
            "forecasts": {"revenue": {"projected_values": [1200000, 1400000, 1600000]}},
            "assumptions": ["Historical trends"],
            "methodology": "Trend analysis",
            "confidence_level": 70.0
        })
        
        from app.models.domain import RiskAssessment, CreditRecommendation, RiskFactorScore
        orchestrator_agent.risk_scoring.score = AsyncMock(return_value=RiskAssessment(
            overall_score=70.0,
            recommendation=CreditRecommendation.APPROVE,
            financial_health=RiskFactorScore(
                factor_name="financial_health",
                score=70.0,
                weight=0.35,
                explanation="Good",
                key_findings=[]
            ),
            cash_flow=RiskFactorScore(
                factor_name="cash_flow",
                score=70.0,
                weight=0.25,
                explanation="Good",
                key_findings=[]
            ),
            industry=RiskFactorScore(
                factor_name="industry",
                score=70.0,
                weight=0.15,
                explanation="Good",
                key_findings=[]
            ),
            promoter=RiskFactorScore(
                factor_name="promoter",
                score=70.0,
                weight=0.15,
                explanation="Good",
                key_findings=[]
            ),
            external_intelligence=RiskFactorScore(
                factor_name="external_intelligence",
                score=70.0,
                weight=0.10,
                explanation="Good",
                key_findings=[]
            ),
            summary="Approved"
        ))
        
        orchestrator_agent.cam_generator.generate = AsyncMock(return_value={
            "content": "CAM document",
            "sections": {"executive_summary": "Summary"},
            "generated_at": datetime.utcnow().isoformat()
        })
        
        # Execute the workflow
        result = await orchestrator_agent.process_application("prop-test-app")
        
        # Property verification: All agents should be invoked
        orchestrator_agent.document_intelligence.extract.assert_called_once()
        orchestrator_agent.financial_analysis.analyze.assert_called_once()
        orchestrator_agent.web_research.research.assert_called_once()
        orchestrator_agent.promoter_intelligence.analyze.assert_called_once()
        orchestrator_agent.industry_intelligence.analyze.assert_called_once()
        orchestrator_agent.forecasting.predict.assert_called_once()
        orchestrator_agent.risk_scoring.score.assert_called_once()
        orchestrator_agent.cam_generator.generate.assert_called_once()
        
        # Property verification: Results should be aggregated
        assert "application_id" in result
        assert "extracted_data" in result
        assert "financial_analysis" in result
        assert "research" in result
        assert "forecasts" in result
        assert "risk_assessment" in result
        assert "cam" in result
        
        # Property verification: Research results should contain all three research types
        assert "web" in result["research"]
        assert "promoter" in result["research"]
        assert "industry" in result["research"]
        
        # Property verification: Result should have metadata
        assert "processing_time" in result
        assert "timestamp" in result
        assert "errors" in result
        assert "warnings" in result
    
    # Feature: intelli-credit-platform, Property 30: Agent Failure Recovery
    @pytest.mark.asyncio
    @settings(
        max_examples=5,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @given(
        failing_agent=st.sampled_from([
            "document_intelligence",
            "financial_analysis",
            "web_research",
            "promoter_intelligence",
            "industry_intelligence",
            "forecasting",
            "risk_scoring"
        ]),
        error_message=st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
    )
    async def test_property_agent_failure_recovery(
        self,
        orchestrator_agent,
        failing_agent,
        error_message
    ):
        """
        **Validates: Requirements 15.1, 15.5**
        
        Property 30: Agent Failure Recovery
        
        For any agent failure during processing, the Orchestrator should log
        the error with detailed information and either attempt recovery or
        gracefully degrade functionality without crashing the entire workflow.
        
        This property verifies that:
        1. When an agent fails, the error is logged
        2. The workflow continues and completes (graceful degradation)
        3. The result indicates the failure but still contains partial results
        4. The workflow does not crash or raise unhandled exceptions
        """
        # Create a test application
        from app.models.domain import Application, ApplicationStatus
        test_app = Application(
            id="failure-test-app",
            company_name="Test Company",
            loan_amount=1000000.0,
            loan_purpose="Testing",
            applicant_email="test@example.com",
            status=ApplicationStatus.PROCESSING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock application repository
        orchestrator_agent.application_repository.get = AsyncMock(return_value=test_app)
        
        # Create a failing mock that raises an exception
        async def failing_mock(*args, **kwargs):
            raise Exception(error_message)
        
        # Create successful mocks for all agents
        success_mocks = {
            "document_intelligence": {
                "financial_data": {
                    "company_info": {"company_name": "Test", "industry": "Tech"},
                    "revenue": {"values": [1000000], "years": ["2023"], "currency": "USD"}
                },
                "source_tracking": {},
                "ambiguous_flags": [],
                "documents_processed": 1
            },
            "financial_analysis": {
                "ratios": {"current_ratio": {"value": 2.0, "formatted_value": "2.00"}},
                "trends": {},
                "benchmarks": {},
                "summary": "Analysis",
                "definitions": {}
            },
            "web_research": {
                "summary": "Research",
                "news_items": [],
                "red_flags": [],
                "positive_indicators": [],
                "sources": []
            },
            "promoter_intelligence": {
                "summary": "Promoter",
                "promoter_profiles": [],
                "track_record_analysis": {},
                "conflicts_of_interest": [],
                "red_flags": [],
                "positive_indicators": [],
                "overall_assessment": {}
            },
            "industry_intelligence": {
                "summary": "Industry",
                "industry": "Tech",
                "sector_trends": {},
                "competitive_landscape": {},
                "industry_risks": [],
                "market_opportunities": [],
                "growth_outlook": {},
                "overall_assessment": {}
            },
            "forecasting": {
                "forecasts": {"revenue": {"projected_values": [1200000]}},
                "assumptions": [],
                "methodology": "Trend",
                "confidence_level": 70.0
            }
        }
        
        # Set up mocks - failing agent gets the failing mock, others get success mocks
        if failing_agent == "document_intelligence":
            orchestrator_agent.document_intelligence.extract = AsyncMock(side_effect=failing_mock)
        else:
            orchestrator_agent.document_intelligence.extract = AsyncMock(
                return_value=success_mocks["document_intelligence"]
            )
        
        if failing_agent == "financial_analysis":
            orchestrator_agent.financial_analysis.analyze = AsyncMock(side_effect=failing_mock)
        else:
            orchestrator_agent.financial_analysis.analyze = AsyncMock(
                return_value=success_mocks["financial_analysis"]
            )
        
        if failing_agent == "web_research":
            orchestrator_agent.web_research.research = AsyncMock(side_effect=failing_mock)
        else:
            orchestrator_agent.web_research.research = AsyncMock(
                return_value=success_mocks["web_research"]
            )
        
        if failing_agent == "promoter_intelligence":
            orchestrator_agent.promoter_intelligence.analyze = AsyncMock(side_effect=failing_mock)
        else:
            orchestrator_agent.promoter_intelligence.analyze = AsyncMock(
                return_value=success_mocks["promoter_intelligence"]
            )
        
        if failing_agent == "industry_intelligence":
            orchestrator_agent.industry_intelligence.analyze = AsyncMock(side_effect=failing_mock)
        else:
            orchestrator_agent.industry_intelligence.analyze = AsyncMock(
                return_value=success_mocks["industry_intelligence"]
            )
        
        if failing_agent == "forecasting":
            orchestrator_agent.forecasting.predict = AsyncMock(side_effect=failing_mock)
        else:
            orchestrator_agent.forecasting.predict = AsyncMock(
                return_value=success_mocks["forecasting"]
            )
        
        # Risk scoring and CAM always succeed for this test
        from app.models.domain import RiskAssessment, CreditRecommendation, RiskFactorScore
        if failing_agent == "risk_scoring":
            orchestrator_agent.risk_scoring.score = AsyncMock(side_effect=failing_mock)
        else:
            orchestrator_agent.risk_scoring.score = AsyncMock(return_value=RiskAssessment(
                overall_score=50.0,
                recommendation=CreditRecommendation.APPROVE_WITH_CONDITIONS,
                financial_health=RiskFactorScore(
                    factor_name="financial_health",
                    score=50.0,
                    weight=0.35,
                    explanation="Default",
                    key_findings=[]
                ),
                cash_flow=RiskFactorScore(
                    factor_name="cash_flow",
                    score=50.0,
                    weight=0.25,
                    explanation="Default",
                    key_findings=[]
                ),
                industry=RiskFactorScore(
                    factor_name="industry",
                    score=50.0,
                    weight=0.15,
                    explanation="Default",
                    key_findings=[]
                ),
                promoter=RiskFactorScore(
                    factor_name="promoter",
                    score=50.0,
                    weight=0.15,
                    explanation="Default",
                    key_findings=[]
                ),
                external_intelligence=RiskFactorScore(
                    factor_name="external_intelligence",
                    score=50.0,
                    weight=0.10,
                    explanation="Default",
                    key_findings=[]
                ),
                summary="Default"
            ))
        
        orchestrator_agent.cam_generator.generate = AsyncMock(return_value={
            "content": "CAM",
            "sections": {},
            "generated_at": datetime.utcnow().isoformat()
        })
        
        # Execute the workflow - should not raise an exception
        result = await orchestrator_agent.process_application("failure-test-app")
        
        # Property verification: Workflow should complete without crashing
        assert result is not None
        assert isinstance(result, dict)
        
        # Property verification: Error should be logged
        assert "errors" in result
        assert len(result["errors"]) > 0
        
        # Property verification: Error message should reference the failing agent
        error_found = False
        for error in result["errors"]:
            # Convert agent name to display name format
            agent_display_names = {
                "document_intelligence": "Document Intelligence",
                "financial_analysis": "Financial Analysis",
                "web_research": "Web Research",
                "promoter_intelligence": "Promoter Intelligence",
                "industry_intelligence": "Industry Intelligence",
                "forecasting": "Forecasting",
                "risk_scoring": "Risk Scoring"
            }
            if agent_display_names[failing_agent] in error:
                error_found = True
                break
        
        assert error_found, f"Expected error for {failing_agent} not found in errors: {result['errors']}"
        
        # Property verification: Result should still have structure (graceful degradation)
        assert "application_id" in result
        assert "extracted_data" in result
        assert "financial_analysis" in result
        assert "research" in result
        assert "forecasts" in result
        assert "risk_assessment" in result
        assert "cam" in result
        assert "processing_time" in result
        assert "timestamp" in result
        
        # Property verification: Success flag should be False when errors occur
        assert result["success"] is False
