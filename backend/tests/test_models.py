"""
Unit tests for Pydantic data models.

Tests validation rules, field constraints, and edge cases for all domain models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.domain import (
    ApplicationStatus,
    CreditRecommendation,
    Application,
    Document,
    FinancialMetrics,
    Forecast,
    RiskFactorScore,
    RiskAssessment,
    ResearchFindings,
    AnalysisResults,
    CAM,
    MonitoringAlert,
)


class TestApplicationStatus:
    """Test ApplicationStatus enum."""
    
    def test_all_status_values(self):
        """Test all valid status values."""
        assert ApplicationStatus.PENDING == "pending"
        assert ApplicationStatus.PROCESSING == "processing"
        assert ApplicationStatus.ANALYSIS_COMPLETE == "analysis_complete"
        assert ApplicationStatus.APPROVED == "approved"
        assert ApplicationStatus.APPROVED_WITH_CONDITIONS == "approved_with_conditions"
        assert ApplicationStatus.REJECTED == "rejected"


class TestCreditRecommendation:
    """Test CreditRecommendation enum."""
    
    def test_all_recommendation_values(self):
        """Test all valid recommendation values."""
        assert CreditRecommendation.APPROVE == "approve"
        assert CreditRecommendation.APPROVE_WITH_CONDITIONS == "approve_with_conditions"
        assert CreditRecommendation.REJECT == "reject"


class TestApplication:
    """Test Application model."""
    
    def test_valid_application(self):
        """Test creating a valid application."""
        app = Application(
            id="app-123",
            company_name="Test Corp",
            loan_amount=1000000.0,
            loan_purpose="Business expansion",
            applicant_email="test@example.com"
        )
        assert app.id == "app-123"
        assert app.company_name == "Test Corp"
        assert app.loan_amount == 1000000.0
        assert app.status == ApplicationStatus.PENDING
        assert app.credit_score is None
        assert app.recommendation is None
    
    def test_application_with_credit_score(self):
        """Test application with credit score."""
        app = Application(
            id="app-123",
            company_name="Test Corp",
            loan_amount=1000000.0,
            loan_purpose="Business expansion",
            applicant_email="test@example.com",
            credit_score=75.5,
            recommendation=CreditRecommendation.APPROVE
        )
        assert app.credit_score == 75.5
        assert app.recommendation == CreditRecommendation.APPROVE
    
    def test_invalid_email(self):
        """Test that invalid email raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Application(
                id="app-123",
                company_name="Test Corp",
                loan_amount=1000000.0,
                loan_purpose="Business expansion",
                applicant_email="invalid-email"
            )
        assert "Invalid email format" in str(exc_info.value)
    
    def test_email_normalization(self):
        """Test that email is normalized to lowercase."""
        app = Application(
            id="app-123",
            company_name="Test Corp",
            loan_amount=1000000.0,
            loan_purpose="Business expansion",
            applicant_email="Test@Example.COM"
        )
        assert app.applicant_email == "test@example.com"
    
    def test_negative_loan_amount(self):
        """Test that negative loan amount raises validation error."""
        with pytest.raises(ValidationError):
            Application(
                id="app-123",
                company_name="Test Corp",
                loan_amount=-1000.0,
                loan_purpose="Business expansion",
                applicant_email="test@example.com"
            )
    
    def test_zero_loan_amount(self):
        """Test that zero loan amount raises validation error."""
        with pytest.raises(ValidationError):
            Application(
                id="app-123",
                company_name="Test Corp",
                loan_amount=0.0,
                loan_purpose="Business expansion",
                applicant_email="test@example.com"
            )
    
    def test_credit_score_bounds(self):
        """Test credit score must be between 0 and 100."""
        # Valid scores
        app1 = Application(
            id="app-123",
            company_name="Test Corp",
            loan_amount=1000000.0,
            loan_purpose="Business expansion",
            applicant_email="test@example.com",
            credit_score=0.0
        )
        assert app1.credit_score == 0.0
        
        app2 = Application(
            id="app-123",
            company_name="Test Corp",
            loan_amount=1000000.0,
            loan_purpose="Business expansion",
            applicant_email="test@example.com",
            credit_score=100.0
        )
        assert app2.credit_score == 100.0
        
        # Invalid scores
        with pytest.raises(ValidationError):
            Application(
                id="app-123",
                company_name="Test Corp",
                loan_amount=1000000.0,
                loan_purpose="Business expansion",
                applicant_email="test@example.com",
                credit_score=-1.0
            )
        
        with pytest.raises(ValidationError):
            Application(
                id="app-123",
                company_name="Test Corp",
                loan_amount=1000000.0,
                loan_purpose="Business expansion",
                applicant_email="test@example.com",
                credit_score=101.0
            )
    
    def test_empty_company_name(self):
        """Test that empty company name raises validation error."""
        with pytest.raises(ValidationError):
            Application(
                id="app-123",
                company_name="",
                loan_amount=1000000.0,
                loan_purpose="Business expansion",
                applicant_email="test@example.com"
            )


class TestDocument:
    """Test Document model."""
    
    def test_valid_document(self):
        """Test creating a valid document."""
        doc = Document(
            id="doc-123",
            application_id="app-123",
            filename="financial_statement.pdf",
            file_type="pdf",
            storage_path="documents/app-123/doc-123.pdf"
        )
        assert doc.id == "doc-123"
        assert doc.application_id == "app-123"
        assert doc.processing_status == "pending"
        assert doc.extracted_data is None
    
    def test_document_with_extracted_data(self):
        """Test document with extracted data."""
        doc = Document(
            id="doc-123",
            application_id="app-123",
            filename="financial_statement.pdf",
            file_type="pdf",
            storage_path="documents/app-123/doc-123.pdf",
            extracted_data={"revenue": 1000000, "profit": 100000},
            source_pages={"revenue": 1, "profit": 2}
        )
        assert doc.extracted_data == {"revenue": 1000000, "profit": 100000}
        assert doc.source_pages == {"revenue": 1, "profit": 2}


class TestFinancialMetrics:
    """Test FinancialMetrics model."""
    
    def test_valid_financial_metrics(self):
        """Test creating valid financial metrics."""
        metrics = FinancialMetrics(
            revenue=[1000000, 1200000, 1500000],
            profit=[100000, 120000, 150000],
            debt=[500000, 450000, 400000],
            cash_flow=[200000, 250000, 300000],
            current_assets=500000,
            current_liabilities=200000,
            total_assets=2000000,
            total_equity=1000000,
            total_debt=400000,
            current_ratio=2.5,
            debt_to_equity=0.4,
            net_profit_margin=0.1,
            roe=0.15,
            asset_turnover=0.75
        )
        assert len(metrics.revenue) == 3
        assert metrics.current_ratio == 2.5
    
    def test_empty_time_series(self):
        """Test that empty time series raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            FinancialMetrics(
                revenue=[],
                profit=[100000],
                debt=[500000],
                cash_flow=[200000],
                current_assets=500000,
                current_liabilities=200000,
                total_assets=2000000,
                total_equity=1000000,
                total_debt=400000
            )
        assert "Time series must have at least one data point" in str(exc_info.value)
    
    def test_negative_balance_sheet_items(self):
        """Test that negative balance sheet items raise validation error."""
        with pytest.raises(ValidationError):
            FinancialMetrics(
                revenue=[1000000],
                profit=[100000],
                debt=[500000],
                cash_flow=[200000],
                current_assets=-500000,  # Invalid
                current_liabilities=200000,
                total_assets=2000000,
                total_equity=1000000,
                total_debt=400000
            )


class TestForecast:
    """Test Forecast model."""
    
    def test_valid_forecast(self):
        """Test creating a valid forecast."""
        forecast = Forecast(
            metric_name="revenue",
            historical_values=[1000000, 1200000, 1500000],
            projected_values=[1800000, 2100000, 2400000],
            confidence_level=0.85,
            assumptions=["10% annual growth", "Stable market conditions"]
        )
        assert forecast.metric_name == "revenue"
        assert len(forecast.projected_values) == 3
        assert forecast.confidence_level == 0.85
    
    def test_invalid_projection_length(self):
        """Test that projections must be exactly 3 years."""
        with pytest.raises(ValidationError):
            Forecast(
                metric_name="revenue",
                historical_values=[1000000, 1200000],
                projected_values=[1800000, 2100000],  # Only 2 years
                confidence_level=0.85
            )
        
        with pytest.raises(ValidationError):
            Forecast(
                metric_name="revenue",
                historical_values=[1000000, 1200000],
                projected_values=[1800000, 2100000, 2400000, 2700000],  # 4 years
                confidence_level=0.85
            )
    
    def test_confidence_level_bounds(self):
        """Test confidence level must be between 0 and 1."""
        with pytest.raises(ValidationError):
            Forecast(
                metric_name="revenue",
                historical_values=[1000000],
                projected_values=[1800000, 2100000, 2400000],
                confidence_level=1.5  # Invalid
            )


class TestRiskFactorScore:
    """Test RiskFactorScore model."""
    
    def test_valid_risk_factor_score(self):
        """Test creating a valid risk factor score."""
        score = RiskFactorScore(
            factor_name="financial_health",
            score=75.0,
            weight=0.35,
            explanation="Strong financial position with healthy ratios",
            key_findings=["High current ratio", "Low debt-to-equity"]
        )
        assert score.factor_name == "financial_health"
        assert score.score == 75.0
        assert score.weight == 0.35
    
    def test_score_bounds(self):
        """Test score must be between 0 and 100."""
        with pytest.raises(ValidationError):
            RiskFactorScore(
                factor_name="financial_health",
                score=150.0,  # Invalid
                weight=0.35,
                explanation="Test"
            )


class TestRiskAssessment:
    """Test RiskAssessment model."""
    
    def test_valid_risk_assessment(self):
        """Test creating a valid risk assessment."""
        assessment = RiskAssessment(
            overall_score=72.5,
            recommendation=CreditRecommendation.APPROVE,
            financial_health=RiskFactorScore(
                factor_name="financial_health",
                score=75.0,
                weight=0.35,
                explanation="Strong financial position"
            ),
            cash_flow=RiskFactorScore(
                factor_name="cash_flow",
                score=70.0,
                weight=0.25,
                explanation="Stable cash flow"
            ),
            industry=RiskFactorScore(
                factor_name="industry",
                score=65.0,
                weight=0.15,
                explanation="Favorable industry trends"
            ),
            promoter=RiskFactorScore(
                factor_name="promoter",
                score=80.0,
                weight=0.15,
                explanation="Experienced management"
            ),
            external_intelligence=RiskFactorScore(
                factor_name="external_intelligence",
                score=75.0,
                weight=0.10,
                explanation="Positive market sentiment"
            ),
            summary="Overall positive assessment"
        )
        assert assessment.overall_score == 72.5
        assert assessment.recommendation == CreditRecommendation.APPROVE
    
    def test_invalid_weight(self):
        """Test that incorrect weights raise validation error."""
        with pytest.raises(ValidationError) as exc_info:
            RiskAssessment(
                overall_score=72.5,
                recommendation=CreditRecommendation.APPROVE,
                financial_health=RiskFactorScore(
                    factor_name="financial_health",
                    score=75.0,
                    weight=0.50,  # Should be 0.35
                    explanation="Strong financial position"
                ),
                cash_flow=RiskFactorScore(
                    factor_name="cash_flow",
                    score=70.0,
                    weight=0.25,
                    explanation="Stable cash flow"
                ),
                industry=RiskFactorScore(
                    factor_name="industry",
                    score=65.0,
                    weight=0.15,
                    explanation="Favorable industry trends"
                ),
                promoter=RiskFactorScore(
                    factor_name="promoter",
                    score=80.0,
                    weight=0.15,
                    explanation="Experienced management"
                ),
                external_intelligence=RiskFactorScore(
                    factor_name="external_intelligence",
                    score=75.0,
                    weight=0.10,
                    explanation="Positive market sentiment"
                ),
                summary="Overall positive assessment"
            )
        assert "Weight for financial_health should be 0.35" in str(exc_info.value)


class TestResearchFindings:
    """Test ResearchFindings model."""
    
    def test_valid_research_findings(self):
        """Test creating valid research findings."""
        findings = ResearchFindings(
            web_research="Company has strong online presence",
            promoter_analysis="Experienced leadership team",
            industry_analysis="Growing industry with positive outlook",
            sources=["source1.com", "source2.com"],
            red_flags=["Recent lawsuit pending"],
            positive_indicators=["Award-winning products", "Strong customer base"]
        )
        assert findings.web_research == "Company has strong online presence"
        assert len(findings.sources) == 2
        assert len(findings.red_flags) == 1


class TestAnalysisResults:
    """Test AnalysisResults model."""
    
    def test_valid_analysis_results(self):
        """Test creating valid analysis results."""
        results = AnalysisResults(
            application_id="app-123",
            financial_metrics=FinancialMetrics(
                revenue=[1000000],
                profit=[100000],
                debt=[500000],
                cash_flow=[200000],
                current_assets=500000,
                current_liabilities=200000,
                total_assets=2000000,
                total_equity=1000000,
                total_debt=400000
            ),
            forecasts=[
                Forecast(
                    metric_name="revenue",
                    historical_values=[1000000],
                    projected_values=[1200000, 1400000, 1600000],
                    confidence_level=0.85
                )
            ],
            risk_assessment=RiskAssessment(
                overall_score=72.5,
                recommendation=CreditRecommendation.APPROVE,
                financial_health=RiskFactorScore(
                    factor_name="financial_health",
                    score=75.0,
                    weight=0.35,
                    explanation="Strong"
                ),
                cash_flow=RiskFactorScore(
                    factor_name="cash_flow",
                    score=70.0,
                    weight=0.25,
                    explanation="Stable"
                ),
                industry=RiskFactorScore(
                    factor_name="industry",
                    score=65.0,
                    weight=0.15,
                    explanation="Favorable"
                ),
                promoter=RiskFactorScore(
                    factor_name="promoter",
                    score=80.0,
                    weight=0.15,
                    explanation="Experienced"
                ),
                external_intelligence=RiskFactorScore(
                    factor_name="external_intelligence",
                    score=75.0,
                    weight=0.10,
                    explanation="Positive"
                ),
                summary="Overall positive"
            ),
            research_findings=ResearchFindings(
                web_research="Positive",
                promoter_analysis="Strong",
                industry_analysis="Growing"
            )
        )
        assert results.application_id == "app-123"
        assert isinstance(results.generated_at, datetime)


class TestCAM:
    """Test CAM model."""
    
    def test_valid_cam(self):
        """Test creating a valid CAM."""
        cam = CAM(
            application_id="app-123",
            content="# Credit Appraisal Memo\n\nComplete analysis...",
            version=1,
            sections={
                "executive_summary": "Summary content",
                "company_overview": "Company details",
                "financial_analysis": "Financial analysis",
                "risk_assessment": "Risk details",
                "recommendation": "Approve"
            }
        )
        assert cam.application_id == "app-123"
        assert cam.version == 1
        assert len(cam.sections) == 5
    
    def test_missing_required_sections(self):
        """Test that missing required sections raise validation error."""
        with pytest.raises(ValidationError) as exc_info:
            CAM(
                application_id="app-123",
                content="# Credit Appraisal Memo",
                sections={
                    "executive_summary": "Summary content",
                    "company_overview": "Company details"
                    # Missing other required sections
                }
            )
        assert "Missing required sections" in str(exc_info.value)
    
    def test_invalid_version(self):
        """Test that version must be >= 1."""
        with pytest.raises(ValidationError):
            CAM(
                application_id="app-123",
                content="Content",
                version=0,  # Invalid
                sections={
                    "executive_summary": "Summary",
                    "company_overview": "Overview",
                    "financial_analysis": "Analysis",
                    "risk_assessment": "Risk",
                    "recommendation": "Approve"
                }
            )


class TestMonitoringAlert:
    """Test MonitoringAlert model."""
    
    def test_valid_monitoring_alert(self):
        """Test creating a valid monitoring alert."""
        alert = MonitoringAlert(
            id="alert-123",
            application_id="app-123",
            alert_type="financial_deterioration",
            severity="high",
            message="Significant drop in revenue detected",
            details={"revenue_drop": "25%"}
        )
        assert alert.id == "alert-123"
        assert alert.severity == "high"
        assert alert.acknowledged is False
    
    def test_severity_validation(self):
        """Test severity must be one of valid values."""
        # Valid severities
        for severity in ["low", "medium", "high", "critical"]:
            alert = MonitoringAlert(
                id="alert-123",
                application_id="app-123",
                alert_type="test",
                severity=severity,
                message="Test message"
            )
            assert alert.severity == severity
        
        # Invalid severity
        with pytest.raises(ValidationError) as exc_info:
            MonitoringAlert(
                id="alert-123",
                application_id="app-123",
                alert_type="test",
                severity="invalid",
                message="Test message"
            )
        assert "Severity must be one of" in str(exc_info.value)
    
    def test_severity_case_normalization(self):
        """Test that severity is normalized to lowercase."""
        alert = MonitoringAlert(
            id="alert-123",
            application_id="app-123",
            alert_type="test",
            severity="HIGH",
            message="Test message"
        )
        assert alert.severity == "high"
