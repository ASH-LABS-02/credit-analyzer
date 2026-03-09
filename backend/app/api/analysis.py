"""
Analysis Operation API Endpoints

This module implements RESTful endpoints for triggering and monitoring credit analysis:
- POST /api/v1/applications/{app_id}/analyze - Trigger analysis
- GET /api/v1/applications/{app_id}/status - Get analysis status
- GET /api/v1/applications/{app_id}/results - Get analysis results

Requirements: 3.1, 14.1
"""

import asyncio
import json
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Request, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.models.domain import (
    Application,
    ApplicationStatus,
    AnalysisResults,
    FinancialMetrics,
    Forecast,
    RiskAssessment,
    ResearchFindings
)
from app.repositories.application_repository import ApplicationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.analysis_repository import AnalysisRepository
from app.services.document_processor import DocumentProcessor
from app.agents.orchestrator_agent import OrchestratorAgent
from app.core.audit_logger import AuditLogger


# Request/Response Models
class AnalyzeRequest(BaseModel):
    """Request model for triggering analysis."""
    force_reanalysis: bool = Field(
        default=False,
        description="Force re-analysis even if results already exist"
    )


class AnalysisStatusResponse(BaseModel):
    """Response model for analysis status."""
    application_id: str
    status: str  # "pending", "processing", "complete", "failed"
    progress: Optional[str] = None  # Current stage being processed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class AnalysisResultsResponse(BaseModel):
    """Response model for analysis results."""
    application_id: str
    company_name: str
    generated_at: datetime
    financial_metrics: Optional[Dict[str, Any]] = None
    forecasts: Optional[Dict[str, Any]] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    research_findings: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None
    errors: Optional[list] = None
    warnings: Optional[list] = None


# Initialize router
router = APIRouter(
    prefix="/api/v1/applications",
    tags=["analysis"]
)

# Initialize repositories and services (lazy initialization)
_application_repository = None
_document_repository = None
_analysis_repository = None
_document_processor = None
_audit_logger = None
_orchestrator_agent = None

# Track ongoing analysis tasks
_analysis_tasks: Dict[str, Dict[str, Any]] = {}


def get_application_repository() -> ApplicationRepository:
    """Get or initialize application repository."""
    global _application_repository
    if _application_repository is None:
        _application_repository = ApplicationRepository()
    return _application_repository


def get_document_repository() -> DocumentRepository:
    """Get or initialize document repository."""
    global _document_repository
    if _document_repository is None:
        _document_repository = DocumentRepository()
    return _document_repository


def get_analysis_repository() -> AnalysisRepository:
    """Get or initialize analysis repository."""
    global _analysis_repository
    if _analysis_repository is None:
        _analysis_repository = AnalysisRepository()
    return _analysis_repository


def get_document_processor() -> DocumentProcessor:
    """Get or initialize document processor."""
    global _document_processor
    if _document_processor is None:
        _document_processor = DocumentProcessor()
    return _document_processor


def get_audit_logger() -> AuditLogger:
    """Get or initialize audit logger."""
    global _audit_logger
    if _audit_logger is None:
        from app.database.config import get_db_session
        db_session = get_db_session()
        _audit_logger = AuditLogger(db_session)
    return _audit_logger


def get_orchestrator_agent() -> OrchestratorAgent:
    """Get or initialize orchestrator agent."""
    global _orchestrator_agent
    if _orchestrator_agent is None:
        _orchestrator_agent = OrchestratorAgent(
            document_repository=get_document_repository(),
            application_repository=get_application_repository(),
            document_processor=get_document_processor(),
            audit_logger=get_audit_logger()
        )
    return _orchestrator_agent


async def run_analysis_workflow(
    application_id: str,
    user_id: str
):
    """
    Background task to run the complete analysis workflow.
    
    This function runs asynchronously in the background and updates
    the analysis status as it progresses through different stages.
    
    Args:
        application_id: Application ID to analyze
        user_id: User ID who triggered the analysis
    """
    try:
        # Update status to processing
        _analysis_tasks[application_id] = {
            "status": "processing",
            "progress": "Initializing analysis",
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "error_message": None
        }
        
        # Update application status
        app_repo = get_application_repository()
        await app_repo.update(application_id, {
            "status": ApplicationStatus.PROCESSING.value
        })
        
        # Run orchestrator
        orchestrator = get_orchestrator_agent()
        result = await orchestrator.process_application(application_id)
        
        # Check if analysis was successful
        if result.get("success"):
            # Save analysis results
            analysis_repo = get_analysis_repository()
            
            # Convert result to AnalysisResults model
            analysis_results = _convert_to_analysis_results(result)
            
            # Save results and update application status atomically
            await analysis_repo.save_with_application_update(
                analysis_results,
                {
                    "status": ApplicationStatus.ANALYSIS_COMPLETE.value,
                    "credit_score": result.get("risk_assessment", {}).get("overall_score"),
                    "recommendation": result.get("risk_assessment", {}).get("recommendation")
                }
            )
            
            # Update task status
            _analysis_tasks[application_id] = {
                "status": "complete",
                "progress": "Analysis complete",
                "started_at": _analysis_tasks[application_id]["started_at"],
                "completed_at": datetime.utcnow(),
                "error_message": None
            }
            
            # Log completion
            audit_logger = get_audit_logger()
            await audit_logger.log_user_action(
                action="analyze_complete",
                resource_type="application",
                resource_id=application_id,
                user_id=user_id,
                details={
                    "success": True,
                    "processing_time": result.get("processing_time"),
                    "credit_score": result.get("risk_assessment", {}).get("overall_score")
                }
            )
        else:
            # Analysis failed
            error_message = "; ".join(result.get("errors", ["Unknown error"]))
            
            _analysis_tasks[application_id] = {
                "status": "failed",
                "progress": "Analysis failed",
                "started_at": _analysis_tasks[application_id]["started_at"],
                "completed_at": datetime.utcnow(),
                "error_message": error_message
            }
            
            # Update application status
            await app_repo.update(application_id, {
                "status": ApplicationStatus.PENDING.value
            })
            
            # Log failure
            audit_logger = get_audit_logger()
            await audit_logger.log_user_action(
                action="analyze_failed",
                resource_type="application",
                resource_id=application_id,
                user_id=user_id,
                details={
                    "success": False,
                    "errors": result.get("errors", [])
                }
            )
    
    except Exception as e:
        # Handle unexpected errors
        error_message = f"Unexpected error during analysis: {str(e)}"
        
        _analysis_tasks[application_id] = {
            "status": "failed",
            "progress": "Analysis failed",
            "started_at": _analysis_tasks.get(application_id, {}).get("started_at", datetime.utcnow()),
            "completed_at": datetime.utcnow(),
            "error_message": error_message
        }
        
        # Update application status
        try:
            app_repo = get_application_repository()
            await app_repo.update(application_id, {
                "status": ApplicationStatus.PENDING.value
            })
        except Exception:
            pass  # Don't fail if status update fails
        
        # Log error
        try:
            audit_logger = get_audit_logger()
            await audit_logger.log_user_action(
                action="analyze_error",
                resource_type="application",
                resource_id=application_id,
                user_id=user_id,
                details={
                    "success": False,
                    "error": error_message
                }
            )
        except Exception:
            pass  # Don't fail if logging fails


def _convert_to_analysis_results(result: Dict[str, Any]) -> AnalysisResults:
    """
    Convert orchestrator result to AnalysisResults model.
    
    Args:
        result: Orchestrator result dictionary
    
    Returns:
        AnalysisResults instance
    """
    # Extract data from result
    application_id = result.get("application_id")
    
    # Convert financial metrics (simplified for now)
    financial_data = result.get("extracted_data", {}).get("financial_data", {})
    financial_metrics = FinancialMetrics(
        revenue=financial_data.get("revenue", []),
        profit=financial_data.get("profit", []),
        debt=financial_data.get("debt", []),
        cash_flow=financial_data.get("cash_flow", []),
        current_assets=financial_data.get("current_assets", 0.0),
        current_liabilities=financial_data.get("current_liabilities", 0.0),
        total_assets=financial_data.get("total_assets", 0.0),
        total_equity=financial_data.get("total_equity", 0.0),
        total_debt=financial_data.get("total_debt", 0.0),
        current_ratio=result.get("financial_analysis", {}).get("ratios", {}).get("current_ratio", 0.0),
        debt_to_equity=result.get("financial_analysis", {}).get("ratios", {}).get("debt_to_equity", 0.0),
        net_profit_margin=result.get("financial_analysis", {}).get("ratios", {}).get("net_profit_margin", 0.0),
        roe=result.get("financial_analysis", {}).get("ratios", {}).get("roe", 0.0),
        asset_turnover=result.get("financial_analysis", {}).get("ratios", {}).get("asset_turnover", 0.0),
        revenue_growth=result.get("financial_analysis", {}).get("trends", {}).get("revenue_growth", []),
        profit_growth=result.get("financial_analysis", {}).get("trends", {}).get("profit_growth", [])
    )
    
    # Convert forecasts
    forecasts_data = result.get("forecasts", {}).get("forecasts", {})
    forecasts = [
        Forecast(
            metric_name=metric_name,
            historical_values=data.get("historical", []),
            projected_values=data.get("projected", []),
            confidence_level=result.get("forecasts", {}).get("confidence_level", 0.0),
            assumptions=result.get("forecasts", {}).get("assumptions", [])
        )
        for metric_name, data in forecasts_data.items()
    ]
    
    # Convert risk assessment (already in correct format from orchestrator)
    risk_data = result.get("risk_assessment", {})
    from app.models.domain import RiskFactorScore, CreditRecommendation
    
    risk_assessment = RiskAssessment(
        overall_score=risk_data.get("overall_score", 0.0),
        recommendation=CreditRecommendation(risk_data.get("recommendation", "approve_with_conditions")),
        financial_health=RiskFactorScore(**risk_data.get("financial_health", {})),
        cash_flow=RiskFactorScore(**risk_data.get("cash_flow", {})),
        industry=RiskFactorScore(**risk_data.get("industry", {})),
        promoter=RiskFactorScore(**risk_data.get("promoter", {})),
        external_intelligence=RiskFactorScore(**risk_data.get("external_intelligence", {})),
        summary=risk_data.get("summary", "")
    )
    
    # Convert research findings
    research_data = result.get("research", {})
    research_findings = ResearchFindings(
        web_research=research_data.get("web", {}).get("summary", ""),
        promoter_analysis=research_data.get("promoter", {}).get("summary", ""),
        industry_analysis=research_data.get("industry", {}).get("summary", ""),
        sources=research_data.get("web", {}).get("sources", []),
        red_flags=(
            research_data.get("web", {}).get("red_flags", []) +
            research_data.get("promoter", {}).get("red_flags", []) +
            research_data.get("industry", {}).get("industry_risks", [])
        ),
        positive_indicators=(
            research_data.get("web", {}).get("positive_indicators", []) +
            research_data.get("promoter", {}).get("positive_indicators", []) +
            research_data.get("industry", {}).get("market_opportunities", [])
        )
    )
    
    return AnalysisResults(
        application_id=application_id,
        financial_metrics=financial_metrics,
        forecasts=forecasts,
        risk_assessment=risk_assessment,
        research_findings=research_findings,
        generated_at=datetime.utcnow()
    )


@router.post(
    "/{app_id}/analyze",
    response_model=AnalysisStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger credit analysis",
    description="""
    Trigger the complete credit analysis workflow for an application.
    
    The analysis runs asynchronously in the background and processes:
    1. Document intelligence (extract financial data)
    2. Multi-agent research (web, promoter, industry)
    3. Financial analysis and forecasting
    4. Risk scoring and credit recommendation
    5. CAM generation
    
    Use the status endpoint to monitor progress and the results endpoint
    to retrieve the completed analysis.
    
    **Requirements**: 3.1, 14.1
    """
)
async def trigger_analysis(
    app_id: str,
    request_data: AnalyzeRequest,
    request: Request,
    background_tasks: BackgroundTasks
) -> AnalysisStatusResponse:
    """
    Trigger credit analysis for an application.
    
    Args:
        app_id: Application ID to analyze
        request_data: Analysis request parameters
        request: FastAPI request object (contains user info)
        background_tasks: FastAPI background tasks
    
    Returns:
        Analysis status response
    
    Raises:
        HTTPException: 404 if application not found, 400 for validation errors
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
        
        # Check if analysis is already in progress
        if app_id in _analysis_tasks:
            task_status = _analysis_tasks[app_id]["status"]
            if task_status == "processing":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Analysis is already in progress for this application"
                )
        
        # Check if analysis already exists (unless force_reanalysis is True)
        if not request_data.force_reanalysis:
            analysis_repo = get_analysis_repository()
            existing_analysis = await analysis_repo.get_by_application_id(app_id)
            
            if existing_analysis is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Analysis already exists for this application. Use force_reanalysis=true to re-analyze."
                )
        
        # Get user ID from request
        user_id = getattr(request.state, "user_id", "system")
        
        # Log the analysis trigger
        audit_logger = get_audit_logger()
        await audit_logger.log_user_action(
            action="analyze_triggered",
            resource_type="application",
            resource_id=app_id,
            user_id=user_id,
            details={
                "force_reanalysis": request_data.force_reanalysis
            }
        )
        
        # Start analysis in background
        background_tasks.add_task(run_analysis_workflow, app_id, user_id)
        
        # Initialize task tracking
        _analysis_tasks[app_id] = {
            "status": "processing",
            "progress": "Analysis queued",
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "error_message": None
        }
        
        return AnalysisStatusResponse(
            application_id=app_id,
            status="processing",
            progress="Analysis queued",
            started_at=datetime.utcnow(),
            completed_at=None,
            error_message=None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger analysis: {str(e)}"
        )


@router.get(
    "/{app_id}/status",
    response_model=AnalysisStatusResponse,
    summary="Get analysis status",
    description="""
    Get the current status of the analysis workflow for an application.
    
    Status values:
    - "pending": Analysis has not been started
    - "processing": Analysis is currently running
    - "complete": Analysis completed successfully
    - "failed": Analysis failed with errors
    
    **Requirements**: 3.1, 14.1
    """
)
async def get_analysis_status(app_id: str) -> AnalysisStatusResponse:
    """
    Get analysis status for an application.
    
    Args:
        app_id: Application ID
    
    Returns:
        Analysis status response
    
    Raises:
        HTTPException: 404 if application not found
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
        
        # Check if analysis task is tracked
        if app_id in _analysis_tasks:
            task_info = _analysis_tasks[app_id]
            return AnalysisStatusResponse(
                application_id=app_id,
                status=task_info["status"],
                progress=task_info.get("progress"),
                started_at=task_info.get("started_at"),
                completed_at=task_info.get("completed_at"),
                error_message=task_info.get("error_message")
            )
        
        # Check if analysis results exist
        analysis_repo = get_analysis_repository()
        analysis = await analysis_repo.get_by_application_id(app_id)
        
        if analysis is not None:
            return AnalysisStatusResponse(
                application_id=app_id,
                status="complete",
                progress="Analysis complete",
                started_at=None,
                completed_at=analysis.generated_at,
                error_message=None
            )
        
        # No analysis started yet
        return AnalysisStatusResponse(
            application_id=app_id,
            status="pending",
            progress="Analysis not started",
            started_at=None,
            completed_at=None,
            error_message=None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis status: {str(e)}"
        )


@router.get(
    "/{app_id}/results",
    response_model=AnalysisResultsResponse,
    summary="Get analysis results",
    description="""
    Retrieve the complete analysis results for an application.
    
    This endpoint returns the full analysis including:
    - Financial metrics and ratios
    - 3-year forecasts
    - Risk assessment with credit score and recommendation
    - Research findings (web, promoter, industry)
    
    **Requirements**: 3.1, 14.1
    """
)
def get_analysis_results(
    app_id: str,
    db: Session = Depends(get_db)
) -> AnalysisResultsResponse:
    """
    Get analysis results for an application.
    
    Args:
        app_id: Application ID
        db: Database session
    
    Returns:
        Analysis results response
    
    Raises:
        HTTPException: 404 if application or results not found
    """
    try:
        # Check if application exists
        app_repo = ApplicationRepository(db)
        application = app_repo.get_by_id(app_id)
        
        if application is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {app_id} not found"
            )
        
        # Get analysis results
        analysis_repo = AnalysisRepository(db)
        analyses = analysis_repo.get_by_application_id(app_id)
        
        if not analyses or len(analyses) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis results not found for application {app_id}. Run analysis first."
            )
        
        # Get the most recent analysis
        analysis = analyses[0]
        
        # Parse the results JSON
        try:
            results_data = json.loads(analysis.analysis_results) if analysis.analysis_results else {}
        except:
            results_data = {}
        
        financial_metrics = results_data.get("financial_metrics", {})
        risk_score = results_data.get("risk_score", 0.0)
        risk_analysis = results_data.get("risk_analysis", {})
        recommendation = results_data.get("recommendation", "review_required")
        
        return AnalysisResultsResponse(
            application_id=analysis.application_id,
            company_name=application.company_name,
            generated_at=analysis.created_at,
            financial_metrics=financial_metrics,
            forecasts=None,  # Not implemented in simple analysis
            risk_assessment={
                "overall_score": risk_score,
                "recommendation": recommendation,
                "risk_factors": risk_analysis.get("risk_factors", {}),
                "key_strengths": risk_analysis.get("key_strengths", []),
                "key_concerns": risk_analysis.get("key_concerns", []),
                "recommendation_rationale": risk_analysis.get("recommendation_rationale", "")
            },
            research_findings=None,  # Not implemented in simple analysis
            processing_time=None,
            errors=None,
            warnings=None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis results: {str(e)}"
        )
        
        if analysis is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis results not found for application {app_id}. Trigger analysis first."
            )
        
        # Convert to response model
        def serialize_model(obj):
            """Recursively serialize Pydantic model or dataclass to dict."""
            if obj is None:
                return None
            from dataclasses import is_dataclass, fields
            from enum import Enum
            from pydantic import BaseModel
            
            if isinstance(obj, BaseModel):
                # Pydantic model - use model_dump
                return obj.model_dump()
            elif is_dataclass(obj):
                # Dataclass - manually serialize
                result = {}
                for field in fields(obj):
                    value = getattr(obj, field.name)
                    if isinstance(value, Enum):
                        result[field.name] = value.value
                    elif isinstance(value, (BaseModel, type)) and is_dataclass(value):
                        result[field.name] = serialize_model(value)
                    elif isinstance(value, list):
                        result[field.name] = [
                            serialize_model(item) if isinstance(item, (BaseModel, type)) or is_dataclass(item) else item 
                            for item in value
                        ]
                    else:
                        result[field.name] = value
                return result
            return obj
        
        # Serialize all model fields
        financial_metrics_dict = serialize_model(analysis.financial_metrics)
        risk_assessment_dict = serialize_model(analysis.risk_assessment)
        research_findings_dict = serialize_model(analysis.research_findings)
        
        return AnalysisResultsResponse(
            application_id=analysis.application_id,
            company_name=application.company_name,
            generated_at=analysis.generated_at,
            financial_metrics=financial_metrics_dict,
            forecasts={
                f.metric_name: {
                    "historical": f.historical_values,
                    "projected": f.projected_values,
                    "confidence": f.confidence_level,
                    "assumptions": f.assumptions
                }
                for f in analysis.forecasts
            } if analysis.forecasts else None,
            risk_assessment=risk_assessment_dict,
            research_findings=research_findings_dict,
            processing_time=None,  # Not stored in AnalysisResults
            errors=None,  # Not stored in AnalysisResults
            warnings=None  # Not stored in AnalysisResults
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis results: {str(e)}"
        )
