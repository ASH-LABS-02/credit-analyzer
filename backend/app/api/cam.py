"""
CAM Operation API Endpoints

This module implements RESTful endpoints for Credit Appraisal Memo (CAM) operations:
- POST /api/v1/applications/{app_id}/cam - Generate CAM
- GET /api/v1/applications/{app_id}/cam - Get CAM content
- GET /api/v1/applications/{app_id}/cam/export - Export CAM (PDF/Word)

Requirements: 7.1, 7.4, 14.1
"""

from typing import Optional, Literal
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Request, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.models.domain import CAM
from app.repositories.application_repository import ApplicationRepository
from app.repositories.analysis_repository import AnalysisRepository
from app.agents.cam_generator_agent import CAMGeneratorAgent
from app.core.audit_logger import AuditLogger


# Request/Response Models
class GenerateCAMRequest(BaseModel):
    """Request model for generating CAM."""
    version: int = Field(
        default=1,
        ge=1,
        description="CAM version number (defaults to 1)"
    )
    force_regenerate: bool = Field(
        default=False,
        description="Force regeneration even if CAM already exists"
    )


class CAMResponse(BaseModel):
    """Response model for CAM content."""
    application_id: str
    company_name: str
    content: str
    version: int
    generated_at: datetime
    sections: dict


# Initialize router
router = APIRouter(
    prefix="/api/v1/applications",
    tags=["cam"]
)

# Initialize repositories and services (lazy initialization)
_application_repository = None
_analysis_repository = None
_cam_generator_agent = None
_audit_logger = None

# In-memory CAM storage (keyed by application_id)
# In production, this should be stored in Firestore
_cam_storage: dict[str, CAM] = {}


def get_application_repository() -> ApplicationRepository:
    """Get or initialize application repository."""
    global _application_repository
    if _application_repository is None:
        from app.database.config import get_db_config
        db_config = get_db_config()
        db_session = db_config.get_session()
        _application_repository = ApplicationRepository(db_session)
    return _application_repository


def get_analysis_repository() -> AnalysisRepository:
    """Get or initialize analysis repository."""
    global _analysis_repository
    if _analysis_repository is None:
        from app.database.config import get_db_config
        db_config = get_db_config()
        db_session = db_config.get_session()
        _analysis_repository = AnalysisRepository(db_session)
    return _analysis_repository


def get_audit_logger() -> AuditLogger:
    """Get or initialize audit logger."""
    global _audit_logger
    if _audit_logger is None:
        from app.database.config import get_db_config
        db_config = get_db_config()
        db_session = db_config.get_session()
        _audit_logger = AuditLogger(db_session)
    return _audit_logger


def get_cam_generator_agent() -> CAMGeneratorAgent:
    """Get or initialize CAM generator agent."""
    global _cam_generator_agent
    if _cam_generator_agent is None:
        audit_logger = get_audit_logger()
        _cam_generator_agent = CAMGeneratorAgent(audit_logger=audit_logger)
    return _cam_generator_agent


@router.post(
    "/{app_id}/cam",
    response_model=CAMResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Credit Appraisal Memo",
    description="""
    Generate a comprehensive Credit Appraisal Memo (CAM) for an application.
    
    The CAM compiles all analysis results into a professional document with:
    - Executive summary
    - Company overview
    - Financial analysis with tables and charts
    - Risk assessment with factor breakdown
    - Credit recommendation with supporting rationale
    
    Prerequisites:
    - Application must exist
    - Analysis must be complete (use /analyze endpoint first)
    
    **Requirements**: 7.1, 14.1
    """
)
async def generate_cam(
    app_id: str,
    request_data: GenerateCAMRequest,
    request: Request
) -> CAMResponse:
    """
    Generate a Credit Appraisal Memo for an application.
    
    Args:
        app_id: Application ID
        request_data: CAM generation request parameters
        request: FastAPI request object (contains user info)
    
    Returns:
        CAM response with content and metadata
    
    Raises:
        HTTPException: 404 if application or analysis not found,
                      400 if CAM already exists (unless force_regenerate=true)
    """
    try:
        # Check if application exists
        app_repo = get_application_repository()
        application = await app_repo.get_by_id(app_id)
        
        if application is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {app_id} not found"
            )
        
        # Check if analysis exists
        analysis_repo = get_analysis_repository()
        analysis = await analysis_repo.get_by_application_id(app_id)
        
        if analysis is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis not found for application {app_id}. Complete analysis first."
            )
        
        # Check if CAM already exists (unless force_regenerate is True)
        if not request_data.force_regenerate and app_id in _cam_storage:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CAM already exists for this application. Use force_regenerate=true to regenerate."
            )
        
        # Prepare analysis data for CAM generation
        analysis_data = {
            'application_id': app_id,
            'company_name': application.company_name,
            'loan_amount': application.loan_amount,
            'loan_purpose': application.loan_purpose,
            'financial': {
                'ratios': _extract_ratios(analysis),
                'trends': _extract_trends(analysis),
                'benchmarks': {},  # Would be populated from industry data
                'summary': _generate_financial_summary(analysis)
            },
            'forecasts': {
                'forecasts': _extract_forecasts(analysis),
                'confidence_level': _get_average_confidence(analysis),
                'assumptions': _extract_assumptions(analysis)
            },
            'risk': _extract_risk_data(analysis),
            'research': _extract_research_data(analysis),
            'version': request_data.version
        }
        
        # Generate CAM
        cam_agent = get_cam_generator_agent()
        cam = await cam_agent.generate(analysis_data)
        
        # Store CAM
        _cam_storage[app_id] = cam
        
        # Get user ID from request
        user_id = getattr(request.state, "user_id", "system")
        
        # Log CAM generation
        audit_logger = get_audit_logger()
        await audit_logger.log_cam_generation(
            application_id=app_id,
            version=cam.version,
            user_id=user_id
        )
        
        return CAMResponse(
            application_id=cam.application_id,
            company_name=application.company_name,
            content=cam.content,
            version=cam.version,
            generated_at=cam.generated_at,
            sections=cam.sections
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate CAM: {str(e)}"
        )


@router.get(
    "/{app_id}/cam",
    response_model=CAMResponse,
    summary="Get Credit Appraisal Memo content",
    description="""
    Retrieve the Credit Appraisal Memo content for an application.
    
    Returns the complete CAM document with all sections:
    - Executive summary
    - Company overview
    - Financial analysis
    - Risk assessment
    - Credit recommendation
    
    **Requirements**: 7.1, 14.1
    """
)
async def get_cam(app_id: str) -> CAMResponse:
    """
    Get CAM content for an application.
    
    Args:
        app_id: Application ID
    
    Returns:
        CAM response with content and metadata
    
    Raises:
        HTTPException: 404 if application or CAM not found
    """
    try:
        # Check if application exists
        app_repo = get_application_repository()
        application = await app_repo.get_by_id(app_id)
        
        if application is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {app_id} not found"
            )
        
        # Check if CAM exists
        if app_id not in _cam_storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CAM not found for application {app_id}. Generate CAM first."
            )
        
        cam = _cam_storage[app_id]
        
        return CAMResponse(
            application_id=cam.application_id,
            company_name=application.company_name,
            content=cam.content,
            version=cam.version,
            generated_at=cam.generated_at,
            sections=cam.sections
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve CAM: {str(e)}"
        )


@router.get(
    "/{app_id}/cam/export",
    summary="Export Credit Appraisal Memo",
    description="""
    Export the Credit Appraisal Memo in PDF or Word format.
    
    Supported formats:
    - pdf: Portable Document Format (default)
    - word/docx: Microsoft Word format
    
    The exported document includes professional formatting with:
    - Styled headers and sections
    - Tables for financial data
    - Proper page layout and margins
    
    **Requirements**: 7.4, 14.1
    """
)
async def export_cam(
    app_id: str,
    format: Literal["pdf", "word", "docx"] = Query(
        default="pdf",
        description="Export format (pdf or word/docx)"
    )
) -> Response:
    """
    Export CAM to PDF or Word format.
    
    Args:
        app_id: Application ID
        format: Export format ('pdf', 'word', or 'docx')
    
    Returns:
        File response with appropriate content type
    
    Raises:
        HTTPException: 404 if application or CAM not found,
                      400 if format is invalid
    """
    try:
        # Validate format
        cam_agent = get_cam_generator_agent()
        if not cam_agent.validate_export_format(format):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid export format: {format}. Supported formats: pdf, word, docx"
            )
        
        # Check if application exists
        app_repo = get_application_repository()
        application = app_repo.get_by_id(app_id)  # Remove await - synchronous method
        
        if application is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {app_id} not found"
            )
        
        # Check if CAM exists
        if app_id not in _cam_storage:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CAM not found for application {app_id}. Generate CAM first."
            )
        
        cam = _cam_storage[app_id]
        
        # Export based on format
        if format == "pdf":
            file_bytes = await cam_agent.export_to_pdf(cam)
            media_type = "application/pdf"
            file_extension = "pdf"
        else:  # word or docx
            file_bytes = await cam_agent.export_to_word(cam)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            file_extension = "docx"
        
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        company_name_safe = application.company_name.replace(" ", "_").replace("/", "_")
        filename = f"CAM_{company_name_safe}_v{cam.version}_{timestamp}.{file_extension}"
        
        # Return file response
        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        # Export validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export CAM: {str(e)}"
        )


# Helper functions to extract data from analysis results

def _extract_ratios(analysis) -> dict:
    """Extract financial ratios from analysis results."""
    if not analysis or not analysis.financial_metrics:
        return {}
    
    fm = analysis.financial_metrics
    return {
        'current_ratio': {
            'value': fm.current_ratio,
            'formatted_value': f"{fm.current_ratio:.2f}"
        },
        'debt_to_equity': {
            'value': fm.debt_to_equity,
            'formatted_value': f"{fm.debt_to_equity:.2f}"
        },
        'net_profit_margin': {
            'value': fm.net_profit_margin,
            'formatted_value': f"{fm.net_profit_margin * 100:.1f}%"
        },
        'roe': {
            'value': fm.roe,
            'formatted_value': f"{fm.roe * 100:.1f}%"
        },
        'asset_turnover': {
            'value': fm.asset_turnover,
            'formatted_value': f"{fm.asset_turnover:.2f}"
        }
    }


def _extract_trends(analysis) -> dict:
    """Extract trend data from analysis results."""
    if not analysis or not analysis.financial_metrics:
        return {}
    
    fm = analysis.financial_metrics
    trends = {}
    
    if fm.revenue_growth:
        avg_growth = sum(fm.revenue_growth) / len(fm.revenue_growth) if fm.revenue_growth else 0
        trends['revenue'] = {
            'trend_direction': 'increasing' if avg_growth > 0 else 'decreasing',
            'cagr': avg_growth,
            'interpretation': f"Revenue {'growing' if avg_growth > 0 else 'declining'} at {abs(avg_growth):.1f}% annually"
        }
    
    if fm.profit_growth:
        avg_growth = sum(fm.profit_growth) / len(fm.profit_growth) if fm.profit_growth else 0
        trends['profit'] = {
            'trend_direction': 'increasing' if avg_growth > 0 else 'decreasing',
            'cagr': avg_growth,
            'interpretation': f"Profit {'growing' if avg_growth > 0 else 'declining'} at {abs(avg_growth):.1f}% annually"
        }
    
    return trends


def _extract_forecasts(analysis) -> dict:
    """Extract forecast data from analysis results."""
    if not analysis or not analysis.forecasts:
        return {}
    
    forecasts = {}
    for forecast in analysis.forecasts:
        forecasts[forecast.metric_name] = {
            'historical_values': forecast.historical_values,
            'projected_values': forecast.projected_values,
            'confidence_level': forecast.confidence_level
        }
    
    return forecasts


def _get_average_confidence(analysis) -> float:
    """Calculate average confidence level from forecasts."""
    if not analysis or not analysis.forecasts:
        return 0.0
    
    confidences = [f.confidence_level for f in analysis.forecasts if f.confidence_level]
    return sum(confidences) / len(confidences) if confidences else 0.0


def _extract_assumptions(analysis) -> list:
    """Extract forecast assumptions from analysis results."""
    if not analysis or not analysis.forecasts:
        return []
    
    all_assumptions = []
    for forecast in analysis.forecasts:
        all_assumptions.extend(forecast.assumptions)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_assumptions = []
    for assumption in all_assumptions:
        if assumption not in seen:
            seen.add(assumption)
            unique_assumptions.append(assumption)
    
    return unique_assumptions


def _extract_risk_data(analysis) -> dict:
    """Extract risk assessment data from analysis results."""
    if not analysis or not analysis.risk_assessment:
        return {}
    
    ra = analysis.risk_assessment
    
    def factor_to_dict(factor):
        """Convert RiskFactorScore to dict."""
        if hasattr(factor, 'model_dump'):
            # Pydantic v2
            return factor.model_dump()
        elif hasattr(factor, 'dict'):
            # Pydantic v1
            return factor.dict()
        else:
            # Fallback for dataclass or dict
            return {
                'score': getattr(factor, 'score', 0),
                'weight': getattr(factor, 'weight', 0),
                'explanation': getattr(factor, 'explanation', ''),
                'key_findings': getattr(factor, 'key_findings', [])
            }
    
    return {
        'overall_score': ra.overall_score,
        'recommendation': ra.recommendation.value if hasattr(ra.recommendation, 'value') else str(ra.recommendation),
        'summary': ra.summary,
        'financial_health': factor_to_dict(ra.financial_health),
        'cash_flow': factor_to_dict(ra.cash_flow),
        'industry': factor_to_dict(ra.industry),
        'promoter': factor_to_dict(ra.promoter),
        'external_intelligence': factor_to_dict(ra.external_intelligence)
    }


def _extract_research_data(analysis) -> dict:
    """Extract research findings from analysis results."""
    if not analysis or not analysis.research_findings:
        return {}
    
    rf = analysis.research_findings
    return {
        'web': {
            'news_summary': rf.web_research,
            'sources': rf.sources,
            'red_flags': [flag for flag in rf.red_flags if 'web' in flag.lower() or 'news' in flag.lower()],
            'positive_indicators': [ind for ind in rf.positive_indicators if 'market' in ind.lower()]
        },
        'promoter': {
            'background': rf.promoter_analysis,
            'red_flags': [flag for flag in rf.red_flags if 'promoter' in flag.lower() or 'management' in flag.lower()],
            'positive_indicators': [ind for ind in rf.positive_indicators if 'management' in ind.lower() or 'experience' in ind.lower()]
        },
        'industry': {
            'sector_outlook': rf.industry_analysis,
            'industry_risks': [flag for flag in rf.red_flags if 'industry' in flag.lower() or 'sector' in flag.lower()],
            'market_opportunities': [ind for ind in rf.positive_indicators if 'growth' in ind.lower() or 'opportunity' in ind.lower()]
        }
    }


def _generate_financial_summary(analysis) -> str:
    """Generate a brief financial summary from analysis results."""
    if not analysis or not analysis.financial_metrics:
        return "Financial analysis completed"
    
    fm = analysis.financial_metrics
    summary_parts = []
    
    if fm.revenue:
        latest_revenue = fm.revenue[-1] if fm.revenue else 0
        summary_parts.append(f"Latest revenue: ${latest_revenue:,.0f}")
    
    if fm.current_ratio:
        summary_parts.append(f"Current ratio: {fm.current_ratio:.2f}")
    
    if fm.roe:
        summary_parts.append(f"ROE: {fm.roe * 100:.1f}%")
    
    return "; ".join(summary_parts) if summary_parts else "Financial metrics available"
