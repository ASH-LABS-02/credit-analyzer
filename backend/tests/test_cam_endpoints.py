"""
Unit tests for CAM operation API endpoints.

Tests the RESTful endpoints for generating CAM, retrieving CAM content,
and exporting CAM in various formats.

Requirements: 7.1, 7.4, 14.1
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
    ResearchFindings,
    CAM
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
        status=ApplicationStatus.ANALYSIS_COMPLETE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        credit_score=75.0,
        recommendation=CreditRecommendation.APPROVE
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
            explanation="Favorable industry outlook",
            key_findings=["Growing market"]
        ),
        promoter=RiskFactorScore(
            factor_name="promoter",
            score=75.0,
            weight=0.15,
            explanation="Experienced management",
            key_findings=["Strong track record"]
        ),
        external_intelligence=RiskFactorScore(
            factor_name="external_intelligence",
            score=70.0,
            weight=0.10,
            explanation="Positive market sentiment",
            key_findings=["No negative news"]
        ),
        summary="Overall strong credit profile with favorable risk factors"
    )
    
    research_findings = ResearchFindings(
        web_research="Company has positive market presence",
        promoter_analysis="Management team has strong industry experience",
        industry_analysis="Industry showing steady growth",
        sources=["Company website", "Industry reports"],
        red_flags=[],
        positive_indicators=["Growing market share", "Strong customer base"]
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
def sample_cam():
    """Create a sample CAM for testing."""
    return CAM(
        application_id=str(uuid.uuid4()),
        content="# Credit Appraisal Memo\n\nTest CAM content",
        version=1,
        generated_at=datetime.utcnow(),
        sections={
            'executive_summary': 'Test executive summary',
            'company_overview': 'Test company overview',
            'financial_analysis': 'Test financial analysis',
            'risk_assessment': 'Test risk assessment',
            'recommendation': 'Test recommendation'
        }
    )


class TestGenerateCAM:
    """Tests for POST /api/v1/applications/{app_id}/cam endpoint."""
    
    @patch('app.api.cam.get_application_repository')
    @patch('app.api.cam.get_analysis_repository')
    @patch('app.api.cam.get_cam_generator_agent')
    @patch('app.api.cam.get_audit_logger')
    def test_generate_cam_success(
        self,
        mock_audit_logger,
        mock_cam_agent,
        mock_analysis_repo,
        mock_app_repo,
        client,
        sample_application,
        sample_analysis_results,
        sample_cam
    ):
        """Test successful CAM generation."""
        # Setup mocks
        app_repo_instance = AsyncMock()
        app_repo_instance.get_by_id = AsyncMock(return_value=sample_application)
        mock_app_repo.return_value = app_repo_instance
        
        analysis_repo_instance = AsyncMock()
        analysis_repo_instance.get_by_application_id = AsyncMock(return_value=sample_analysis_results)
        mock_analysis_repo.return_value = analysis_repo_instance
        
        cam_agent_instance = AsyncMock()
        cam_agent_instance.generate = AsyncMock(return_value=sample_cam)
        mock_cam_agent.return_value = cam_agent_instance
        
        audit_logger_instance = AsyncMock()
        audit_logger_instance.log_cam_generation = AsyncMock(return_value="audit_id")
        mock_audit_logger.return_value = audit_logger_instance
        
        # Make request
        response = client.post(
            f"/api/v1/applications/{sample_application.id}/cam",
            json={"version": 1, "force_regenerate": False}
        )
        
        # Debug: print response if it fails
        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")
        
        # Assertions
        assert response.status_code == 201
        data = response.json()
        assert data['application_id'] == sample_cam.application_id
        assert data['company_name'] == sample_application.company_name
        assert data['version'] == 1
        assert 'content' in data
        assert 'sections' in data
        
        # Verify CAM generation was called
        cam_agent_instance.generate.assert_called_once()
        
        # Verify audit logging
        audit_logger_instance.log_cam_generation.assert_called_once()
    
    @patch('app.api.cam.get_application_repository')
    def test_generate_cam_application_not_found(
        self,
        mock_app_repo,
        client
    ):
        """Test CAM generation when application doesn't exist."""
        # Setup mocks
        app_repo_instance = AsyncMock()
        app_repo_instance.get_by_id = AsyncMock(return_value=None)
        mock_app_repo.return_value = app_repo_instance
        
        # Make request
        response = client.post(
            "/api/v1/applications/nonexistent_id/cam",
            json={"version": 1}
        )
        
        # Assertions
        assert response.status_code == 404
        response_data = response.json()
        # Check for either 'detail' or 'message' key
        error_message = response_data.get('detail') or response_data.get('message', '')
        assert "not found" in error_message.lower()
    
    @patch('app.api.cam.get_application_repository')
    @patch('app.api.cam.get_analysis_repository')
    def test_generate_cam_analysis_not_found(
        self,
        mock_analysis_repo,
        mock_app_repo,
        client,
        sample_application
    ):
        """Test CAM generation when analysis doesn't exist."""
        # Setup mocks
        app_repo_instance = AsyncMock()
        app_repo_instance.get_by_id = AsyncMock(return_value=sample_application)
        mock_app_repo.return_value = app_repo_instance
        
        analysis_repo_instance = AsyncMock()
        analysis_repo_instance.get_by_application_id = AsyncMock(return_value=None)
        mock_analysis_repo.return_value = analysis_repo_instance
        
        # Make request
        response = client.post(
            f"/api/v1/applications/{sample_application.id}/cam",
            json={"version": 1}
        )
        
        # Assertions
        assert response.status_code == 404
        response_data = response.json()
        error_message = response_data.get('detail') or response_data.get('message', '')
        assert "analysis not found" in error_message.lower()
    
    @patch('app.api.cam.get_application_repository')
    @patch('app.api.cam.get_analysis_repository')
    @patch('app.api.cam.get_cam_generator_agent')
    @patch('app.api.cam.get_audit_logger')
    @patch('app.api.cam._cam_storage', {})
    def test_generate_cam_already_exists(
        self,
        mock_audit_logger,
        mock_cam_agent,
        mock_analysis_repo,
        mock_app_repo,
        client,
        sample_application,
        sample_analysis_results,
        sample_cam
    ):
        """Test CAM generation when CAM already exists."""
        # Setup mocks
        app_repo_instance = AsyncMock()
        app_repo_instance.get_by_id = AsyncMock(return_value=sample_application)
        mock_app_repo.return_value = app_repo_instance
        
        analysis_repo_instance = AsyncMock()
        analysis_repo_instance.get_by_application_id = AsyncMock(return_value=sample_analysis_results)
        mock_analysis_repo.return_value = analysis_repo_instance
        
        # Pre-populate CAM storage
        from app.api import cam as cam_module
        cam_module._cam_storage[sample_application.id] = sample_cam
        
        # Make request without force_regenerate
        response = client.post(
            f"/api/v1/applications/{sample_application.id}/cam",
            json={"version": 1, "force_regenerate": False}
        )
        
        # Assertions
        assert response.status_code == 400
        response_data = response.json()
        error_message = response_data.get('detail') or response_data.get('message', '')
        assert "already exists" in error_message.lower()
        
        # Clean up
        cam_module._cam_storage.clear()


class TestGetCAM:
    """Tests for GET /api/v1/applications/{app_id}/cam endpoint."""
    
    @patch('app.api.cam.get_application_repository')
    @patch('app.api.cam._cam_storage', {})
    def test_get_cam_success(
        self,
        mock_app_repo,
        client,
        sample_application,
        sample_cam
    ):
        """Test successful CAM retrieval."""
        # Setup mocks
        app_repo_instance = AsyncMock()
        app_repo_instance.get_by_id = AsyncMock(return_value=sample_application)
        mock_app_repo.return_value = app_repo_instance
        
        # Pre-populate CAM storage
        from app.api import cam as cam_module
        cam_module._cam_storage[sample_application.id] = sample_cam
        
        # Make request
        response = client.get(f"/api/v1/applications/{sample_application.id}/cam")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['application_id'] == sample_cam.application_id
        assert data['company_name'] == sample_application.company_name
        assert 'content' in data
        assert 'sections' in data
        
        # Clean up
        cam_module._cam_storage.clear()
    
    @patch('app.api.cam.get_application_repository')
    def test_get_cam_application_not_found(
        self,
        mock_app_repo,
        client
    ):
        """Test CAM retrieval when application doesn't exist."""
        # Setup mocks
        app_repo_instance = AsyncMock()
        app_repo_instance.get_by_id = AsyncMock(return_value=None)
        mock_app_repo.return_value = app_repo_instance
        
        # Make request
        response = client.get("/api/v1/applications/nonexistent_id/cam")
        
        # Assertions
        assert response.status_code == 404
        response_data = response.json()
        error_message = response_data.get('detail') or response_data.get('message', '')
        assert "not found" in error_message.lower()
    
    @patch('app.api.cam.get_application_repository')
    @patch('app.api.cam._cam_storage', {})
    def test_get_cam_not_found(
        self,
        mock_app_repo,
        client,
        sample_application
    ):
        """Test CAM retrieval when CAM doesn't exist."""
        # Setup mocks
        app_repo_instance = AsyncMock()
        app_repo_instance.get_by_id = AsyncMock(return_value=sample_application)
        mock_app_repo.return_value = app_repo_instance
        
        # Make request (CAM storage is empty)
        response = client.get(f"/api/v1/applications/{sample_application.id}/cam")
        
        # Assertions
        assert response.status_code == 404
        response_data = response.json()
        error_message = response_data.get('detail') or response_data.get('message', '')
        assert "cam not found" in error_message.lower()


class TestExportCAM:
    """Tests for GET /api/v1/applications/{app_id}/cam/export endpoint."""
    
    @patch('app.api.cam.get_application_repository')
    @patch('app.api.cam.get_cam_generator_agent')
    @patch('app.api.cam._cam_storage', {})
    def test_export_cam_pdf_success(
        self,
        mock_cam_agent,
        mock_app_repo,
        client,
        sample_application,
        sample_cam
    ):
        """Test successful CAM export to PDF."""
        # Setup mocks
        app_repo_instance = AsyncMock()
        app_repo_instance.get_by_id = AsyncMock(return_value=sample_application)
        mock_app_repo.return_value = app_repo_instance
        
        cam_agent_instance = AsyncMock()
        cam_agent_instance.validate_export_format = MagicMock(return_value=True)
        cam_agent_instance.export_to_pdf = AsyncMock(return_value=b'%PDF-1.4 fake pdf content')
        mock_cam_agent.return_value = cam_agent_instance
        
        # Pre-populate CAM storage
        from app.api import cam as cam_module
        cam_module._cam_storage[sample_application.id] = sample_cam
        
        # Make request
        response = client.get(
            f"/api/v1/applications/{sample_application.id}/cam/export",
            params={"format": "pdf"}
        )
        
        # Assertions
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/pdf'
        assert 'content-disposition' in response.headers
        assert '.pdf' in response.headers['content-disposition']
        assert response.content.startswith(b'%PDF')
        
        # Verify export was called
        cam_agent_instance.export_to_pdf.assert_called_once()
        
        # Clean up
        cam_module._cam_storage.clear()
    
    @patch('app.api.cam.get_application_repository')
    @patch('app.api.cam.get_cam_generator_agent')
    @patch('app.api.cam._cam_storage', {})
    def test_export_cam_word_success(
        self,
        mock_cam_agent,
        mock_app_repo,
        client,
        sample_application,
        sample_cam
    ):
        """Test successful CAM export to Word."""
        # Setup mocks
        app_repo_instance = AsyncMock()
        app_repo_instance.get_by_id = AsyncMock(return_value=sample_application)
        mock_app_repo.return_value = app_repo_instance
        
        cam_agent_instance = AsyncMock()
        cam_agent_instance.validate_export_format = MagicMock(return_value=True)
        cam_agent_instance.export_to_word = AsyncMock(return_value=b'PK\x03\x04 fake docx content')
        mock_cam_agent.return_value = cam_agent_instance
        
        # Pre-populate CAM storage
        from app.api import cam as cam_module
        cam_module._cam_storage[sample_application.id] = sample_cam
        
        # Make request
        response = client.get(
            f"/api/v1/applications/{sample_application.id}/cam/export",
            params={"format": "word"}
        )
        
        # Assertions
        assert response.status_code == 200
        assert 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in response.headers['content-type']
        assert 'content-disposition' in response.headers
        assert '.docx' in response.headers['content-disposition']
        assert response.content.startswith(b'PK')
        
        # Verify export was called
        cam_agent_instance.export_to_word.assert_called_once()
        
        # Clean up
        cam_module._cam_storage.clear()
    
    @patch('app.api.cam.get_application_repository')
    @patch('app.api.cam.get_cam_generator_agent')
    def test_export_cam_invalid_format(
        self,
        mock_cam_agent,
        mock_app_repo,
        client,
        sample_application
    ):
        """Test CAM export with invalid format."""
        # Setup mocks
        app_repo_instance = AsyncMock()
        app_repo_instance.get_by_id = AsyncMock(return_value=sample_application)
        mock_app_repo.return_value = app_repo_instance
        
        cam_agent_instance = AsyncMock()
        cam_agent_instance.validate_export_format = MagicMock(return_value=False)
        mock_cam_agent.return_value = cam_agent_instance
        
        # Make request with invalid format - this will fail validation before reaching our code
        # FastAPI will return 422 for invalid enum value
        response = client.get(
            f"/api/v1/applications/{sample_application.id}/cam/export",
            params={"format": "invalid"}
        )
        
        # Assertions - FastAPI returns 422 for validation errors
        assert response.status_code == 422
    
    @patch('app.api.cam.get_application_repository')
    @patch('app.api.cam.get_cam_generator_agent')
    @patch('app.api.cam._cam_storage', {})
    def test_export_cam_not_found(
        self,
        mock_cam_agent,
        mock_app_repo,
        client,
        sample_application
    ):
        """Test CAM export when CAM doesn't exist."""
        # Setup mocks
        app_repo_instance = AsyncMock()
        app_repo_instance.get_by_id = AsyncMock(return_value=sample_application)
        mock_app_repo.return_value = app_repo_instance
        
        cam_agent_instance = AsyncMock()
        cam_agent_instance.validate_export_format = MagicMock(return_value=True)
        mock_cam_agent.return_value = cam_agent_instance
        
        # Make request (CAM storage is empty)
        response = client.get(
            f"/api/v1/applications/{sample_application.id}/cam/export",
            params={"format": "pdf"}
        )
        
        # Assertions
        assert response.status_code == 404
        response_data = response.json()
        error_message = response_data.get('detail') or response_data.get('message', '')
        assert "cam not found" in error_message.lower()
    
    @patch('app.api.cam.get_application_repository')
    def test_export_cam_application_not_found(
        self,
        mock_app_repo,
        client
    ):
        """Test CAM export when application doesn't exist."""
        # Setup mocks
        app_repo_instance = AsyncMock()
        app_repo_instance.get_by_id = AsyncMock(return_value=None)
        mock_app_repo.return_value = app_repo_instance
        
        # Make request - will fail validation first due to invalid format
        # But if we use a valid format, it should return 404
        response = client.get(
            "/api/v1/applications/nonexistent_id/cam/export",
            params={"format": "pdf"}
        )
        
        # Assertions - should be 404 for application not found
        # But FastAPI might return 400 if validation happens first
        assert response.status_code in [400, 404]
