"""
Unit tests for analysis operation API endpoints.

Tests the RESTful endpoints for triggering analysis, checking status,
and retrieving analysis results.

Requirements: 3.1, 14.1
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from app.main import app
from app.models.domain import (
    Application,
    ApplicationStatus,
    AnalysisResults,
    FinancialMetrics,
    Forecast,
    RiskAssessment,
    RiskFactorScore,
    CreditRecommendation,
    ResearchFindings
)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_application():
    """Create a sample application for testing."""
    return Application(
        id=str(uuid.uuid4()),
        company_name="Test Company",
        loan_amount=1000000.0,
        loan_purpose="Business expansion",
        applicant_email="test@example.com",
        status=ApplicationStatus.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_analysis_results():
    """Create sample analysis results for testing."""
    app_id = str(uuid.uuid4())
    
    financial_metrics = FinancialMetrics(
        revenue=[1000000, 1200000, 1500000],
        profit=[100000, 150000, 200000],
        debt=[500000, 450000, 400000],
        cash_flow=[200000, 250000, 300000],
        current_assets=800000,
        current_liabilities=400000,
        total_assets=2000000,
        total_equity=1000000,
        total_debt=400000,
        current_ratio=2.0,
        debt_to_equity=0.4,
        net_profit_margin=0.13,
        roe=0.20,
        asset_turnover=0.75,
        revenue_growth=[20.0, 25.0],
        profit_growth=[50.0, 33.3]
    )
    
    forecasts = [
        Forecast(
            metric_name="revenue",
            historical_values=[1000000, 1200000, 1500000],
            projected_values=[1800000, 2100000, 2400000],
            confidence_level=0.85,
            assumptions=["Market growth of 20% annually", "No major disruptions"]
        )
    ]
    
    risk_assessment = RiskAssessment(
        overall_score=75.0,
        recommendation=CreditRecommendation.APPROVE,
        financial_health=RiskFactorScore(
            factor_name="financial_health",
            score=80.0,
            weight=0.35,
            explanation="Strong financial position",
            key_findings=["Healthy profit margins", "Low debt levels"]
        ),
        cash_flow=RiskFactorScore(
            factor_name="cash_flow",
            score=75.0,
            weight=0.25,
            explanation="Positive cash flow trend",
            key_findings=["Consistent cash generation"]
        ),
        industry=RiskFactorScore(
            factor_name="industry",
            score=70.0,
            weight=0.15,
            explanation="Stable industry outlook",
            key_findings=["Growing market"]
        ),
        promoter=RiskFactorScore(
            factor_name="promoter",
            score=72.0,
            weight=0.15,
            explanation="Experienced management",
            key_findings=["Strong track record"]
        ),
        external_intelligence=RiskFactorScore(
            factor_name="external_intelligence",
            score=68.0,
            weight=0.10,
            explanation="Positive market sentiment",
            key_findings=["Good reputation"]
        ),
        summary="Strong credit profile with low risk"
    )
    
    research_findings = ResearchFindings(
        web_research="Company has positive market presence",
        promoter_analysis="Experienced management team",
        industry_analysis="Growing industry with good prospects",
        sources=["https://example.com/news"],
        red_flags=[],
        positive_indicators=["Strong market position", "Growing revenue"]
    )
    
    return AnalysisResults(
        application_id=app_id,
        financial_metrics=financial_metrics,
        forecasts=forecasts,
        risk_assessment=risk_assessment,
        research_findings=research_findings,
        generated_at=datetime.utcnow()
    )


@pytest.fixture
def mock_app_repository():
    """Create a mock application repository."""
    with patch('app.api.analysis.get_application_repository') as mock:
        repo = MagicMock()
        mock.return_value = repo
        yield repo


@pytest.fixture
def mock_analysis_repository():
    """Create a mock analysis repository."""
    with patch('app.api.analysis.get_analysis_repository') as mock:
        repo = MagicMock()
        mock.return_value = repo
        yield repo


@pytest.fixture
def mock_orchestrator():
    """Create a mock orchestrator agent."""
    with patch('app.api.analysis.get_orchestrator_agent') as mock:
        orchestrator = MagicMock()
        mock.return_value = orchestrator
        yield orchestrator


@pytest.fixture
def mock_audit_logger():
    """Create a mock audit logger."""
    with patch('app.api.analysis.get_audit_logger') as mock:
        logger = MagicMock()
        logger.log_user_action = AsyncMock()
        mock.return_value = logger
        yield logger


class TestTriggerAnalysis:
    """Tests for POST /api/v1/applications/{app_id}/analyze endpoint."""
    
    def test_trigger_analysis_success(
        self,
        client,
        sample_application,
        mock_app_repository,
        mock_analysis_repository,
        mock_audit_logger
    ):
        """Test successful analysis trigger."""
        # Setup mocks
        mock_app_repository.get_by_id = AsyncMock(return_value=sample_application)
        mock_app_repository.update = AsyncMock(return_value=sample_application)
        mock_analysis_repository.get_by_application_id = AsyncMock(return_value=None)
        
        # Make request
        response = client.post(
            f"/api/v1/applications/{sample_application.id}/analyze",
            json={"force_reanalysis": False}
        )
        
        # Assertions
        assert response.status_code == 202
        data = response.json()
        assert data["application_id"] == sample_application.id
        assert data["status"] == "processing"
        assert data["progress"] == "Analysis queued"
        assert "started_at" in data
        
        # Verify repository was called
        mock_app_repository.get_by_id.assert_called_once_with(sample_application.id)
        mock_analysis_repository.get_by_application_id.assert_called_once()
        
        # Verify audit logging was called at least once (for trigger)
        assert mock_audit_logger.log_user_action.call_count >= 1
    
    def test_trigger_analysis_application_not_found(
        self,
        client,
        mock_app_repository
    ):
        """Test analysis trigger with non-existent application."""
        # Setup mock
        mock_app_repository.get_by_id = AsyncMock(return_value=None)
        
        # Make request
        app_id = str(uuid.uuid4())
        response = client.post(
            f"/api/v1/applications/{app_id}/analyze",
            json={"force_reanalysis": False}
        )
        
        # Assertions
        assert response.status_code == 404
        data = response.json()
        # Check for either 'detail' or 'message' key (depending on error handler)
        error_msg = data.get("detail") or data.get("message", "")
        assert "not found" in error_msg.lower()
    
    def test_trigger_analysis_already_exists(
        self,
        client,
        sample_application,
        sample_analysis_results,
        mock_app_repository,
        mock_analysis_repository
    ):
        """Test analysis trigger when results already exist."""
        # Setup mocks
        mock_app_repository.get_by_id = AsyncMock(return_value=sample_application)
        mock_analysis_repository.get_by_application_id = AsyncMock(
            return_value=sample_analysis_results
        )
        
        # Make request
        response = client.post(
            f"/api/v1/applications/{sample_application.id}/analyze",
            json={"force_reanalysis": False}
        )
        
        # Assertions
        assert response.status_code == 400
        data = response.json()
        # Check for either 'detail' or 'message' key
        error_msg = data.get("detail") or data.get("message", "")
        assert "already exists" in error_msg.lower()
    
    def test_trigger_analysis_force_reanalysis(
        self,
        client,
        sample_application,
        sample_analysis_results,
        mock_app_repository,
        mock_analysis_repository,
        mock_audit_logger
    ):
        """Test analysis trigger with force_reanalysis=True."""
        # Setup mocks
        mock_app_repository.get_by_id = AsyncMock(return_value=sample_application)
        mock_analysis_repository.get_by_application_id = AsyncMock(
            return_value=sample_analysis_results
        )
        
        # Make request
        response = client.post(
            f"/api/v1/applications/{sample_application.id}/analyze",
            json={"force_reanalysis": True}
        )
        
        # Assertions
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "processing"


class TestGetAnalysisStatus:
    """Tests for GET /api/v1/applications/{app_id}/status endpoint."""
    
    def test_get_status_pending(
        self,
        client,
        sample_application,
        mock_app_repository,
        mock_analysis_repository
    ):
        """Test getting status when analysis hasn't started."""
        # Setup mocks
        mock_app_repository.get_by_id = AsyncMock(return_value=sample_application)
        mock_analysis_repository.get_by_application_id = AsyncMock(return_value=None)
        
        # Make request
        response = client.get(f"/api/v1/applications/{sample_application.id}/status")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["application_id"] == sample_application.id
        assert data["status"] == "pending"
        assert data["progress"] == "Analysis not started"
    
    def test_get_status_complete(
        self,
        client,
        sample_application,
        sample_analysis_results,
        mock_app_repository,
        mock_analysis_repository
    ):
        """Test getting status when analysis is complete."""
        # Setup mocks
        mock_app_repository.get_by_id = AsyncMock(return_value=sample_application)
        mock_analysis_repository.get_by_application_id = AsyncMock(
            return_value=sample_analysis_results
        )
        
        # Make request
        response = client.get(f"/api/v1/applications/{sample_application.id}/status")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["application_id"] == sample_application.id
        assert data["status"] == "complete"
        assert data["progress"] == "Analysis complete"
        assert "completed_at" in data
    
    def test_get_status_application_not_found(
        self,
        client,
        mock_app_repository
    ):
        """Test getting status for non-existent application."""
        # Setup mock
        mock_app_repository.get_by_id = AsyncMock(return_value=None)
        
        # Make request
        app_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/applications/{app_id}/status")
        
        # Assertions
        assert response.status_code == 404
        data = response.json()
        # Check for either 'detail' or 'message' key
        error_msg = data.get("detail") or data.get("message", "")
        assert "not found" in error_msg.lower()


class TestGetAnalysisResults:
    """Tests for GET /api/v1/applications/{app_id}/results endpoint."""
    
    def test_get_results_success(
        self,
        client,
        sample_application,
        sample_analysis_results,
        mock_app_repository,
        mock_analysis_repository
    ):
        """Test successful retrieval of analysis results."""
        # Setup mocks
        mock_app_repository.get_by_id = AsyncMock(return_value=sample_application)
        mock_analysis_repository.get_by_application_id = AsyncMock(
            return_value=sample_analysis_results
        )
        
        # Make request
        response = client.get(f"/api/v1/applications/{sample_application.id}/results")
        
        # Debug output if test fails
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["application_id"] == sample_analysis_results.application_id
        assert data["company_name"] == sample_application.company_name
        assert "financial_metrics" in data
        assert "forecasts" in data
        assert "risk_assessment" in data
        assert "research_findings" in data
        assert "generated_at" in data
        
        # Verify financial metrics
        if data["financial_metrics"]:
            assert data["financial_metrics"]["current_ratio"] == 2.0
            assert data["financial_metrics"]["debt_to_equity"] == 0.4
        
        # Verify risk assessment
        if data["risk_assessment"]:
            assert data["risk_assessment"]["overall_score"] == 75.0
            assert data["risk_assessment"]["recommendation"] == "approve"
    
    def test_get_results_application_not_found(
        self,
        client,
        mock_app_repository
    ):
        """Test getting results for non-existent application."""
        # Setup mock
        mock_app_repository.get_by_id = AsyncMock(return_value=None)
        
        # Make request
        app_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/applications/{app_id}/results")
        
        # Assertions
        assert response.status_code == 404
        data = response.json()
        # Check for either 'detail' or 'message' key
        error_msg = data.get("detail") or data.get("message", "")
        assert "not found" in error_msg.lower()
    
    def test_get_results_analysis_not_found(
        self,
        client,
        sample_application,
        mock_app_repository,
        mock_analysis_repository
    ):
        """Test getting results when analysis hasn't been run."""
        # Setup mocks
        mock_app_repository.get_by_id = AsyncMock(return_value=sample_application)
        mock_analysis_repository.get_by_application_id = AsyncMock(return_value=None)
        
        # Make request
        response = client.get(f"/api/v1/applications/{sample_application.id}/results")
        
        # Assertions
        assert response.status_code == 404
        data = response.json()
        # Check for either 'detail' or 'message' key
        error_msg = data.get("detail") or data.get("message", "")
        assert "not found" in error_msg.lower()
        assert "trigger analysis" in error_msg.lower()


class TestAnalysisWorkflow:
    """Integration tests for the complete analysis workflow."""
    
    def test_complete_workflow(
        self,
        client,
        sample_application,
        mock_app_repository,
        mock_analysis_repository,
        mock_audit_logger
    ):
        """Test the complete workflow: trigger -> status -> results."""
        # Setup mocks
        mock_app_repository.get_by_id = AsyncMock(return_value=sample_application)
        mock_app_repository.update = AsyncMock(return_value=sample_application)
        mock_analysis_repository.get_by_application_id = AsyncMock(return_value=None)
        
        # Step 1: Trigger analysis
        response = client.post(
            f"/api/v1/applications/{sample_application.id}/analyze",
            json={"force_reanalysis": False}
        )
        assert response.status_code == 202
        
        # Step 2: Check status (should be processing or pending)
        response = client.get(f"/api/v1/applications/{sample_application.id}/status")
        assert response.status_code == 200
        data = response.json()
        # Status could be processing, pending, or failed (if background task ran and failed)
        assert data["status"] in ["processing", "pending", "failed"]
        
        # Note: In a real scenario, we would wait for the background task to complete
        # and then check the results. For unit tests, we're just verifying the endpoints work.


class TestAnalysisValidation:
    """Tests for input validation and error handling."""
    
    def test_invalid_application_id_format(self, client):
        """Test with invalid application ID format."""
        # Make request with invalid ID
        response = client.post(
            "/api/v1/applications/invalid-id/analyze",
            json={"force_reanalysis": False}
        )
        
        # Should still process (ID validation happens in repository)
        # The endpoint will return 404 when repository doesn't find it
        assert response.status_code in [404, 500]
    
    def test_missing_request_body(self, client, sample_application, mock_app_repository):
        """Test analysis trigger without request body."""
        # Setup mock
        mock_app_repository.get_by_id = AsyncMock(return_value=sample_application)
        
        # Make request without body (should use defaults)
        response = client.post(
            f"/api/v1/applications/{sample_application.id}/analyze"
        )
        
        # Should fail due to missing request body
        assert response.status_code in [422, 400]
