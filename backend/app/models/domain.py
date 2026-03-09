"""
Core domain models for the Intelli-Credit platform.

These models represent the business entities and are used throughout
the application for data validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ApplicationStatus(str, Enum):
    """Application workflow status states."""
    PENDING = "pending"
    PROCESSING = "processing"
    ANALYSIS_COMPLETE = "analysis_complete"
    APPROVED = "approved"
    APPROVED_WITH_CONDITIONS = "approved_with_conditions"
    REJECTED = "rejected"


class CreditRecommendation(str, Enum):
    """Credit decision recommendations."""
    APPROVE = "approve"
    APPROVE_WITH_CONDITIONS = "approve_with_conditions"
    REJECT = "reject"


class Application(BaseModel):
    """Corporate loan application."""
    model_config = ConfigDict(use_enum_values=True)
    
    id: str = Field(..., description="Unique application identifier")
    company_name: str = Field(..., min_length=1, description="Company name")
    loan_amount: float = Field(..., gt=0, description="Requested loan amount")
    loan_purpose: str = Field(..., min_length=1, description="Purpose of the loan")
    applicant_email: str = Field(..., description="Applicant email address")
    status: ApplicationStatus = Field(default=ApplicationStatus.PENDING, description="Application status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    credit_score: Optional[float] = Field(None, ge=0, le=100, description="Credit score (0-100)")
    recommendation: Optional[CreditRecommendation] = Field(None, description="Credit recommendation")
    
    @field_validator('applicant_email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation."""
        if '@' not in v or '.' not in v.split('@')[-1]:
            raise ValueError('Invalid email format')
        return v.lower()


class Document(BaseModel):
    """Uploaded document metadata and content."""
    model_config = ConfigDict(use_enum_values=True)
    
    id: str = Field(..., description="Unique document identifier")
    application_id: str = Field(..., description="Associated application ID")
    filename: str = Field(..., min_length=1, description="Original filename")
    file_type: str = Field(..., description="File type/extension")
    content_base64: Optional[str] = Field(None, description="Base64-encoded file content (for small files)")
    total_chunks: Optional[int] = Field(None, description="Total number of chunks for large files")
    chunk_ids: Optional[List[str]] = Field(None, description="List of IDs for chunks stored in 'document_chunks' collection")
    file_size: int = Field(..., description="File size in bytes")
    upload_date: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    processing_status: str = Field(default="pending", description="Processing status")
    extracted_data: Optional[Dict] = Field(None, description="Extracted structured data")
    source_pages: Optional[Dict[str, int]] = Field(None, description="Mapping of data fields to source pages")


class FinancialMetrics(BaseModel):
    """Financial metrics and ratios."""
    model_config = ConfigDict(use_enum_values=True)
    
    # Multi-year historical data
    revenue: List[float] = Field(..., description="Revenue by year")
    profit: List[float] = Field(..., description="Profit by year")
    debt: List[float] = Field(..., description="Debt by year")
    cash_flow: List[float] = Field(..., description="Cash flow by year")
    
    # Balance sheet items
    current_assets: float = Field(..., ge=0, description="Current assets")
    current_liabilities: float = Field(..., ge=0, description="Current liabilities")
    total_assets: float = Field(..., ge=0, description="Total assets")
    total_equity: float = Field(..., description="Total equity")
    total_debt: float = Field(..., ge=0, description="Total debt")
    
    # Calculated ratios
    current_ratio: Optional[float] = Field(None, description="Current ratio")
    debt_to_equity: Optional[float] = Field(None, description="Debt-to-equity ratio")
    net_profit_margin: Optional[float] = Field(None, description="Net profit margin")
    roe: Optional[float] = Field(None, description="Return on equity")
    asset_turnover: Optional[float] = Field(None, description="Asset turnover ratio")
    
    # Growth rates
    revenue_growth: Optional[List[float]] = Field(None, description="Revenue growth rates")
    profit_growth: Optional[List[float]] = Field(None, description="Profit growth rates")
    
    @field_validator('revenue', 'profit', 'debt', 'cash_flow')
    @classmethod
    def validate_time_series(cls, v: List[float]) -> List[float]:
        """Ensure time series have at least one data point."""
        if len(v) == 0:
            raise ValueError('Time series must have at least one data point')
        return v


class Forecast(BaseModel):
    """Financial forecast for a specific metric."""
    model_config = ConfigDict(use_enum_values=True)
    
    metric_name: str = Field(..., description="Name of the forecasted metric")
    historical_values: List[float] = Field(..., description="Historical values")
    projected_values: List[float] = Field(..., min_length=3, max_length=3, description="3-year projections")
    confidence_level: float = Field(..., ge=0, le=1, description="Confidence level (0-1)")
    assumptions: List[str] = Field(default_factory=list, description="Forecasting assumptions")


class RiskFactorScore(BaseModel):
    """Individual risk factor score and explanation."""
    model_config = ConfigDict(use_enum_values=True)
    
    factor_name: str = Field(..., description="Risk factor name")
    score: float = Field(..., ge=0, le=100, description="Factor score (0-100)")
    weight: float = Field(..., ge=0, le=1, description="Factor weight in overall score")
    explanation: str = Field(..., description="Explanation of the score")
    key_findings: List[str] = Field(default_factory=list, description="Key findings for this factor")


class RiskAssessment(BaseModel):
    """Complete risk assessment with all factors."""
    model_config = ConfigDict(use_enum_values=True)
    
    overall_score: float = Field(..., ge=0, le=100, description="Overall credit score (0-100)")
    recommendation: CreditRecommendation = Field(..., description="Credit recommendation")
    financial_health: RiskFactorScore = Field(..., description="Financial health factor")
    cash_flow: RiskFactorScore = Field(..., description="Cash flow factor")
    industry: RiskFactorScore = Field(..., description="Industry factor")
    promoter: RiskFactorScore = Field(..., description="Promoter factor")
    external_intelligence: RiskFactorScore = Field(..., description="External intelligence factor")
    summary: str = Field(..., description="Overall assessment summary")
    
    @field_validator('financial_health', 'cash_flow', 'industry', 'promoter', 'external_intelligence')
    @classmethod
    def validate_weights(cls, v: RiskFactorScore) -> RiskFactorScore:
        """Validate that weights are within expected ranges."""
        expected_weights = {
            'financial_health': 0.35,
            'cash_flow': 0.25,
            'industry': 0.15,
            'promoter': 0.15,
            'external_intelligence': 0.10
        }
        expected = expected_weights.get(v.factor_name)
        if expected and abs(v.weight - expected) > 0.01:
            raise ValueError(f'Weight for {v.factor_name} should be {expected}, got {v.weight}')
        return v


class ResearchFindings(BaseModel):
    """Multi-source research findings."""
    model_config = ConfigDict(use_enum_values=True)
    
    web_research: str = Field(..., description="Web research summary")
    promoter_analysis: str = Field(..., description="Promoter intelligence summary")
    industry_analysis: str = Field(..., description="Industry intelligence summary")
    sources: List[str] = Field(default_factory=list, description="Source citations")
    red_flags: List[str] = Field(default_factory=list, description="Identified red flags")
    positive_indicators: List[str] = Field(default_factory=list, description="Positive indicators")


class AnalysisResults(BaseModel):
    """Complete analysis results for an application."""
    model_config = ConfigDict(use_enum_values=True)
    
    application_id: str = Field(..., description="Associated application ID")
    financial_metrics: FinancialMetrics = Field(..., description="Financial metrics and ratios")
    forecasts: List[Forecast] = Field(..., description="Financial forecasts")
    risk_assessment: RiskAssessment = Field(..., description="Risk assessment")
    research_findings: ResearchFindings = Field(..., description="Research findings")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")


class CAM(BaseModel):
    """Credit Appraisal Memo."""
    model_config = ConfigDict(use_enum_values=True)
    
    application_id: str = Field(..., description="Associated application ID")
    content: str = Field(..., description="CAM content (Markdown/HTML)")
    version: int = Field(default=1, ge=1, description="CAM version number")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")
    sections: Dict[str, str] = Field(default_factory=dict, description="Section name to content mapping")
    
    @field_validator('sections')
    @classmethod
    def validate_required_sections(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Ensure all required sections are present."""
        required_sections = {
            'executive_summary',
            'company_overview',
            'financial_analysis',
            'risk_assessment',
            'recommendation'
        }
        missing = required_sections - set(v.keys())
        if missing:
            raise ValueError(f'Missing required sections: {missing}')
        return v


class MonitoringAlert(BaseModel):
    """Post-approval monitoring alert."""
    model_config = ConfigDict(use_enum_values=True)
    
    id: str = Field(..., description="Unique alert identifier")
    application_id: str = Field(..., description="Associated application ID")
    alert_type: str = Field(..., description="Type of alert")
    severity: str = Field(..., description="Alert severity level")
    message: str = Field(..., description="Alert message")
    details: Dict = Field(default_factory=dict, description="Additional alert details")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Alert creation timestamp")
    acknowledged: bool = Field(default=False, description="Whether alert has been acknowledged")
    
    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Validate severity level."""
        valid_severities = {'low', 'medium', 'high', 'critical'}
        if v.lower() not in valid_severities:
            raise ValueError(f'Severity must be one of {valid_severities}')
        return v.lower()
