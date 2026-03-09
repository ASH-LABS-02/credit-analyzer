"""
Property-based tests for Pydantic data models.

These tests validate that data models correctly enforce validation rules
and structure data in standardized formats across a wide range of inputs.

**Validates: Requirements 2.2**
"""

import pytest
from datetime import datetime
from hypothesis import given, strategies as st, settings
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


# Custom strategies for domain-specific data
@st.composite
def valid_email_strategy(draw):
    """Generate valid email addresses."""
    username = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(
        whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='._-'
    )))
    domain = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(
        whitelist_categories=('Ll', 'Lu', 'Nd'), whitelist_characters='-'
    )))
    tld = draw(st.sampled_from(['com', 'org', 'net', 'edu', 'io']))
    return f"{username}@{domain}.{tld}"


@st.composite
def financial_metrics_strategy(draw):
    """Generate valid FinancialMetrics instances."""
    num_years = draw(st.integers(min_value=1, max_value=10))
    
    return FinancialMetrics(
        revenue=draw(st.lists(st.floats(min_value=0, max_value=1e12), min_size=num_years, max_size=num_years)),
        profit=draw(st.lists(st.floats(min_value=-1e12, max_value=1e12), min_size=num_years, max_size=num_years)),
        debt=draw(st.lists(st.floats(min_value=0, max_value=1e12), min_size=num_years, max_size=num_years)),
        cash_flow=draw(st.lists(st.floats(min_value=-1e12, max_value=1e12), min_size=num_years, max_size=num_years)),
        current_assets=draw(st.floats(min_value=0, max_value=1e12)),
        current_liabilities=draw(st.floats(min_value=0, max_value=1e12)),
        total_assets=draw(st.floats(min_value=0, max_value=1e12)),
        total_equity=draw(st.floats(min_value=-1e12, max_value=1e12)),
        total_debt=draw(st.floats(min_value=0, max_value=1e12)),
    )


@st.composite
def risk_factor_score_strategy(draw, factor_name=None):
    """Generate valid RiskFactorScore instances."""
    if factor_name is None:
        factor_name = draw(st.sampled_from([
            'financial_health', 'cash_flow', 'industry', 'promoter', 'external_intelligence'
        ]))
    
    # Map factor names to their expected weights
    weight_map = {
        'financial_health': 0.35,
        'cash_flow': 0.25,
        'industry': 0.15,
        'promoter': 0.15,
        'external_intelligence': 0.10
    }
    
    return RiskFactorScore(
        factor_name=factor_name,
        score=draw(st.floats(min_value=0, max_value=100)),
        weight=weight_map.get(factor_name, draw(st.floats(min_value=0, max_value=1))),
        explanation=draw(st.text(min_size=1, max_size=500)),
        key_findings=draw(st.lists(st.text(min_size=1, max_size=100), max_size=10))
    )


# Feature: intelli-credit-platform, Property: Data Model Validation
class TestApplicationPropertyBased:
    """Property-based tests for Application model."""
    
    @settings(max_examples=5)
    @given(
        id=st.text(min_size=1, max_size=100),
        company_name=st.text(min_size=1, max_size=200),
        loan_amount=st.floats(min_value=0.01, max_value=1e12),
        loan_purpose=st.text(min_size=1, max_size=500),
        email=valid_email_strategy(),
        credit_score=st.one_of(st.none(), st.floats(min_value=0, max_value=100))
    )
    def test_application_accepts_valid_data(
        self, id, company_name, loan_amount, loan_purpose, email, credit_score
    ):
        """
        For any valid application data, the Application model should accept
        and structure the data correctly.
        
        **Validates: Requirements 2.2**
        """
        app = Application(
            id=id,
            company_name=company_name,
            loan_amount=loan_amount,
            loan_purpose=loan_purpose,
            applicant_email=email,
            credit_score=credit_score
        )
        
        # Verify data is structured correctly
        assert app.id == id
        assert app.company_name == company_name
        assert app.loan_amount == loan_amount
        assert app.loan_purpose == loan_purpose
        assert app.applicant_email == email.lower()  # Email normalized to lowercase
        assert app.credit_score == credit_score
        assert app.status == ApplicationStatus.PENDING
        assert isinstance(app.created_at, datetime)
        assert isinstance(app.updated_at, datetime)
    
    @settings(max_examples=5)
    @given(
        loan_amount=st.one_of(
            st.floats(max_value=0),  # Zero or negative
            st.just(float('nan'))
        )
    )
    def test_application_rejects_invalid_loan_amount(self, loan_amount):
        """
        For any invalid loan amount (negative, zero, or NaN),
        the Application model should reject the data.
        
        **Validates: Requirements 2.2**
        """
        # Skip if somehow we get a valid positive value
        if loan_amount > 0 and not (loan_amount != loan_amount):  # not NaN
            return
            
        with pytest.raises(ValidationError):
            Application(
                id="test-id",
                company_name="Test Corp",
                loan_amount=loan_amount,
                loan_purpose="Test purpose",
                applicant_email="test@example.com"
            )
    
    @settings(max_examples=5)
    @given(
        credit_score=st.floats() | st.floats(allow_nan=True, allow_infinity=True)
    )
    def test_application_credit_score_bounds(self, credit_score):
        """
        For any credit score outside the range [0, 100] or NaN/infinity,
        the Application model should reject the data.
        
        **Validates: Requirements 2.2**
        """
        # Skip valid scores
        if credit_score is not None and 0 <= credit_score <= 100:
            return
        
        with pytest.raises(ValidationError):
            Application(
                id="test-id",
                company_name="Test Corp",
                loan_amount=1000000.0,
                loan_purpose="Test purpose",
                applicant_email="test@example.com",
                credit_score=credit_score
            )


# Feature: intelli-credit-platform, Property: Data Model Validation
class TestFinancialMetricsPropertyBased:
    """Property-based tests for FinancialMetrics model."""
    
    @settings(max_examples=5)
    @given(metrics=financial_metrics_strategy())
    def test_financial_metrics_accepts_valid_data(self, metrics):
        """
        For any valid financial metrics data, the FinancialMetrics model
        should accept and structure the data correctly.
        
        **Validates: Requirements 2.2**
        """
        # Verify all required fields are present
        assert isinstance(metrics.revenue, list)
        assert isinstance(metrics.profit, list)
        assert isinstance(metrics.debt, list)
        assert isinstance(metrics.cash_flow, list)
        assert len(metrics.revenue) > 0
        assert len(metrics.profit) > 0
        assert len(metrics.debt) > 0
        assert len(metrics.cash_flow) > 0
        
        # Verify balance sheet items are non-negative where required
        assert metrics.current_assets >= 0
        assert metrics.current_liabilities >= 0
        assert metrics.total_assets >= 0
        assert metrics.total_debt >= 0
    
    @settings(max_examples=5)
    @given(
        current_assets=st.floats(max_value=-0.01)  # Strictly negative
    )
    def test_financial_metrics_rejects_negative_assets(self, current_assets):
        """
        For any negative current assets value, the FinancialMetrics model
        should reject the data.
        
        **Validates: Requirements 2.2**
        """
        with pytest.raises(ValidationError):
            FinancialMetrics(
                revenue=[1000000],
                profit=[100000],
                debt=[500000],
                cash_flow=[200000],
                current_assets=current_assets,
                current_liabilities=200000,
                total_assets=2000000,
                total_equity=1000000,
                total_debt=400000
            )
    
    @settings(max_examples=5)
    @given(
        time_series_length=st.integers(min_value=0, max_value=0)
    )
    def test_financial_metrics_rejects_empty_time_series(self, time_series_length):
        """
        For any empty time series, the FinancialMetrics model should
        reject the data.
        
        **Validates: Requirements 2.2**
        """
        with pytest.raises(ValidationError):
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


# Feature: intelli-credit-platform, Property: Data Model Validation
class TestForecastPropertyBased:
    """Property-based tests for Forecast model."""
    
    @settings(max_examples=5)
    @given(
        metric_name=st.text(min_size=1, max_size=100),
        historical_values=st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1, max_size=20),
        projected_values=st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=3, max_size=3),
        confidence_level=st.floats(min_value=0, max_value=1),
        assumptions=st.lists(st.text(min_size=1, max_size=200), max_size=10)
    )
    def test_forecast_accepts_valid_data(
        self, metric_name, historical_values, projected_values, confidence_level, assumptions
    ):
        """
        For any valid forecast data with exactly 3 projected values,
        the Forecast model should accept and structure the data correctly.
        
        **Validates: Requirements 2.2**
        """
        forecast = Forecast(
            metric_name=metric_name,
            historical_values=historical_values,
            projected_values=projected_values,
            confidence_level=confidence_level,
            assumptions=assumptions
        )
        
        # Verify data is structured correctly
        assert forecast.metric_name == metric_name
        assert len(forecast.projected_values) == 3
        assert 0 <= forecast.confidence_level <= 1
        assert isinstance(forecast.assumptions, list)
    
    @settings(max_examples=5)
    @given(
        projected_values=st.lists(st.floats(), min_size=0, max_size=10).filter(lambda x: len(x) != 3)
    )
    def test_forecast_rejects_invalid_projection_length(self, projected_values):
        """
        For any projected values list that doesn't have exactly 3 elements,
        the Forecast model should reject the data.
        
        **Validates: Requirements 2.2**
        """
        with pytest.raises(ValidationError):
            Forecast(
                metric_name="revenue",
                historical_values=[1000000],
                projected_values=projected_values,
                confidence_level=0.85
            )


# Feature: intelli-credit-platform, Property: Data Model Validation
class TestRiskFactorScorePropertyBased:
    """Property-based tests for RiskFactorScore model."""
    
    @settings(max_examples=5)
    @given(
        factor_name=st.text(min_size=1, max_size=100),
        score=st.floats(min_value=0, max_value=100),
        weight=st.floats(min_value=0, max_value=1),
        explanation=st.text(min_size=1, max_size=1000),
        key_findings=st.lists(st.text(min_size=1, max_size=200), max_size=20)
    )
    def test_risk_factor_score_accepts_valid_data(
        self, factor_name, score, weight, explanation, key_findings
    ):
        """
        For any valid risk factor score data, the RiskFactorScore model
        should accept and structure the data correctly.
        
        **Validates: Requirements 2.2**
        """
        risk_score = RiskFactorScore(
            factor_name=factor_name,
            score=score,
            weight=weight,
            explanation=explanation,
            key_findings=key_findings
        )
        
        # Verify data is structured correctly
        assert risk_score.factor_name == factor_name
        assert 0 <= risk_score.score <= 100
        assert 0 <= risk_score.weight <= 1
        assert risk_score.explanation == explanation
        assert isinstance(risk_score.key_findings, list)
    
    @settings(max_examples=5)
    @given(
        score=st.floats().filter(lambda x: x < 0 or x > 100 or x != x)  # Outside bounds or NaN
    )
    def test_risk_factor_score_rejects_invalid_score(self, score):
        """
        For any score outside the range [0, 100] or NaN,
        the RiskFactorScore model should reject the data.
        
        **Validates: Requirements 2.2**
        """
        with pytest.raises(ValidationError):
            RiskFactorScore(
                factor_name="test_factor",
                score=score,
                weight=0.5,
                explanation="Test explanation"
            )


# Feature: intelli-credit-platform, Property: Data Model Validation
class TestRiskAssessmentPropertyBased:
    """Property-based tests for RiskAssessment model."""
    
    @settings(max_examples=5)
    @given(
        overall_score=st.floats(min_value=0, max_value=100),
        recommendation=st.sampled_from(list(CreditRecommendation)),
        summary=st.text(min_size=1, max_size=1000)
    )
    def test_risk_assessment_accepts_valid_data_with_correct_weights(
        self, overall_score, recommendation, summary
    ):
        """
        For any valid risk assessment data with correctly weighted factors,
        the RiskAssessment model should accept and structure the data correctly.
        
        **Validates: Requirements 2.2**
        """
        assessment = RiskAssessment(
            overall_score=overall_score,
            recommendation=recommendation,
            financial_health=RiskFactorScore(
                factor_name="financial_health",
                score=75.0,
                weight=0.35,
                explanation="Test"
            ),
            cash_flow=RiskFactorScore(
                factor_name="cash_flow",
                score=70.0,
                weight=0.25,
                explanation="Test"
            ),
            industry=RiskFactorScore(
                factor_name="industry",
                score=65.0,
                weight=0.15,
                explanation="Test"
            ),
            promoter=RiskFactorScore(
                factor_name="promoter",
                score=80.0,
                weight=0.15,
                explanation="Test"
            ),
            external_intelligence=RiskFactorScore(
                factor_name="external_intelligence",
                score=75.0,
                weight=0.10,
                explanation="Test"
            ),
            summary=summary
        )
        
        # Verify data is structured correctly
        assert 0 <= assessment.overall_score <= 100
        # The recommendation is stored as a string due to use_enum_values=True
        assert assessment.recommendation in ['approve', 'approve_with_conditions', 'reject']
        assert assessment.financial_health.weight == 0.35
        assert assessment.cash_flow.weight == 0.25
        assert assessment.industry.weight == 0.15
        assert assessment.promoter.weight == 0.15
        assert assessment.external_intelligence.weight == 0.10


# Feature: intelli-credit-platform, Property: Data Model Validation
class TestCAMPropertyBased:
    """Property-based tests for CAM model."""
    
    @settings(max_examples=5)
    @given(
        application_id=st.text(min_size=1, max_size=100),
        content=st.text(min_size=1, max_size=10000),
        version=st.integers(min_value=1, max_value=1000)
    )
    def test_cam_accepts_valid_data_with_all_sections(
        self, application_id, content, version
    ):
        """
        For any valid CAM data with all required sections,
        the CAM model should accept and structure the data correctly.
        
        **Validates: Requirements 2.2**
        """
        cam = CAM(
            application_id=application_id,
            content=content,
            version=version,
            sections={
                "executive_summary": "Summary",
                "company_overview": "Overview",
                "financial_analysis": "Analysis",
                "risk_assessment": "Risk",
                "recommendation": "Recommendation"
            }
        )
        
        # Verify data is structured correctly
        assert cam.application_id == application_id
        assert cam.content == content
        assert cam.version >= 1
        assert len(cam.sections) >= 5
        assert "executive_summary" in cam.sections
        assert "company_overview" in cam.sections
        assert "financial_analysis" in cam.sections
        assert "risk_assessment" in cam.sections
        assert "recommendation" in cam.sections
    
    @settings(max_examples=5)
    @given(
        missing_section=st.sampled_from([
            "executive_summary",
            "company_overview",
            "financial_analysis",
            "risk_assessment",
            "recommendation"
        ])
    )
    def test_cam_rejects_missing_required_sections(self, missing_section):
        """
        For any CAM data missing a required section,
        the CAM model should reject the data.
        
        **Validates: Requirements 2.2**
        """
        all_sections = {
            "executive_summary": "Summary",
            "company_overview": "Overview",
            "financial_analysis": "Analysis",
            "risk_assessment": "Risk",
            "recommendation": "Recommendation"
        }
        
        # Remove one required section
        sections = {k: v for k, v in all_sections.items() if k != missing_section}
        
        with pytest.raises(ValidationError):
            CAM(
                application_id="test-id",
                content="Test content",
                sections=sections
            )


# Feature: intelli-credit-platform, Property: Data Model Validation
class TestMonitoringAlertPropertyBased:
    """Property-based tests for MonitoringAlert model."""
    
    @settings(max_examples=5)
    @given(
        id=st.text(min_size=1, max_size=100),
        application_id=st.text(min_size=1, max_size=100),
        alert_type=st.text(min_size=1, max_size=100),
        severity=st.sampled_from(['low', 'medium', 'high', 'critical', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
        message=st.text(min_size=1, max_size=1000),
        details=st.dictionaries(st.text(min_size=1, max_size=50), st.text(max_size=200), max_size=10),
        acknowledged=st.booleans()
    )
    def test_monitoring_alert_accepts_valid_data(
        self, id, application_id, alert_type, severity, message, details, acknowledged
    ):
        """
        For any valid monitoring alert data with valid severity,
        the MonitoringAlert model should accept and structure the data correctly.
        
        **Validates: Requirements 2.2**
        """
        alert = MonitoringAlert(
            id=id,
            application_id=application_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            details=details,
            acknowledged=acknowledged
        )
        
        # Verify data is structured correctly
        assert alert.id == id
        assert alert.application_id == application_id
        assert alert.alert_type == alert_type
        assert alert.severity in ['low', 'medium', 'high', 'critical']  # Normalized to lowercase
        assert alert.message == message
        assert isinstance(alert.details, dict)
        assert alert.acknowledged == acknowledged
        assert isinstance(alert.created_at, datetime)
    
    @settings(max_examples=5)
    @given(
        severity=st.text(min_size=1, max_size=50).filter(
            lambda x: x.lower() not in ['low', 'medium', 'high', 'critical']
        )
    )
    def test_monitoring_alert_rejects_invalid_severity(self, severity):
        """
        For any invalid severity value,
        the MonitoringAlert model should reject the data.
        
        **Validates: Requirements 2.2**
        """
        with pytest.raises(ValidationError):
            MonitoringAlert(
                id="test-id",
                application_id="app-123",
                alert_type="test",
                severity=severity,
                message="Test message"
            )


# Feature: intelli-credit-platform, Property: Data Model Validation
class TestDocumentPropertyBased:
    """Property-based tests for Document model."""
    
    @settings(max_examples=5)
    @given(
        id=st.text(min_size=1, max_size=100),
        application_id=st.text(min_size=1, max_size=100),
        filename=st.text(min_size=1, max_size=255),
        file_type=st.sampled_from(['pdf', 'docx', 'xlsx', 'csv', 'jpg', 'png']),
        storage_path=st.text(min_size=1, max_size=500),
        processing_status=st.sampled_from(['pending', 'processing', 'complete', 'failed']),
        extracted_data=st.one_of(
            st.none(),
            st.dictionaries(st.text(min_size=1, max_size=50), st.floats(allow_nan=False), max_size=20)
        )
    )
    def test_document_accepts_valid_data(
        self, id, application_id, filename, file_type, storage_path, processing_status, extracted_data
    ):
        """
        For any valid document data,
        the Document model should accept and structure the data correctly.
        
        **Validates: Requirements 2.2**
        """
        doc = Document(
            id=id,
            application_id=application_id,
            filename=filename,
            file_type=file_type,
            storage_path=storage_path,
            processing_status=processing_status,
            extracted_data=extracted_data
        )
        
        # Verify data is structured correctly
        assert doc.id == id
        assert doc.application_id == application_id
        assert doc.filename == filename
        assert doc.file_type == file_type
        assert doc.storage_path == storage_path
        assert doc.processing_status == processing_status
        assert isinstance(doc.upload_date, datetime)
        
        if extracted_data is not None:
            assert isinstance(doc.extracted_data, dict)
