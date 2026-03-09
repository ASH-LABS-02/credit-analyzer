"""
Search and Monitoring API Endpoints

This module implements RESTful endpoints for semantic search and monitoring operations:
- POST /api/v1/applications/{app_id}/search - Semantic document search
- GET /api/v1/monitoring/alerts - Get monitoring alerts
- GET /api/v1/monitoring/applications/{app_id} - Get monitoring status

Requirements: 10.1, 16.2, 14.1
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Query, Request
from pydantic import BaseModel, Field

from app.services.vector_search_engine import VectorSearchEngine
from app.services.monitoring_service import MonitoringService
from app.repositories.application_repository import ApplicationRepository
from app.repositories.document_repository import DocumentRepository
from app.core.audit_logger import AuditLogger


# Request/Response Models for Search
class SemanticSearchRequest(BaseModel):
    """Request model for semantic document search."""
    query: str = Field(..., min_length=1, description="Search query text")
    max_results: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of results to return (1-20)"
    )
    min_relevance: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum relevance score threshold (0.0-1.0)"
    )


class SearchResult(BaseModel):
    """Individual search result."""
    doc_id: str
    chunk: str
    chunk_index: int
    total_chunks: int
    relevance_score: float
    filename: Optional[str] = None
    document_type: Optional[str] = None


class SemanticSearchResponse(BaseModel):
    """Response model for semantic search."""
    application_id: str
    query: str
    results: List[SearchResult]
    total_results: int
    search_timestamp: datetime


# Response Models for Monitoring
class MonitoringAlertResponse(BaseModel):
    """Response model for monitoring alert."""
    id: str
    application_id: str
    alert_type: str
    severity: str
    message: str
    details: dict
    created_at: datetime
    acknowledged: bool
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None


class MonitoringAlertsListResponse(BaseModel):
    """Response model for list of monitoring alerts."""
    alerts: List[MonitoringAlertResponse]
    total: int
    limit: Optional[int] = None
    application_filter: Optional[str] = None


class MonitoringStatusResponse(BaseModel):
    """Response model for monitoring status."""
    application_id: str
    company_name: str
    status: str
    activated_at: Optional[datetime] = None
    last_check: Optional[datetime] = None
    next_check: Optional[datetime] = None
    check_interval_days: int
    total_checks: int
    total_alerts: int
    additional_context: dict


# Initialize routers
search_router = APIRouter(
    prefix="/api/v1/applications",
    tags=["search"]
)

monitoring_router = APIRouter(
    prefix="/api/v1/monitoring",
    tags=["monitoring"]
)

# Initialize services (lazy initialization)
_vector_search_engine = None
_monitoring_service = None
_application_repository = None
_document_repository = None
_audit_logger = None


def get_vector_search_engine() -> VectorSearchEngine:
    """Get or initialize vector search engine."""
    global _vector_search_engine
    if _vector_search_engine is None:
        _vector_search_engine = VectorSearchEngine()
    return _vector_search_engine


def get_monitoring_service() -> MonitoringService:
    """Get or initialize monitoring service."""
    global _monitoring_service
    if _monitoring_service is None:
        from app.database.config import get_db_session
        db_session = get_db_session()
        audit_logger = get_audit_logger()
        _monitoring_service = MonitoringService(
            db_session=db_session,
            audit_logger=audit_logger
        )
    return _monitoring_service


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


def get_audit_logger() -> AuditLogger:
    """Get or initialize audit logger."""
    global _audit_logger
    if _audit_logger is None:
        from app.database.config import get_db_session
        db_session = get_db_session()
        _audit_logger = AuditLogger(db_session)
    return _audit_logger


# Search Endpoints

@search_router.post(
    "/{app_id}/search",
    response_model=SemanticSearchResponse,
    summary="Semantic document search",
    description="""
    Perform semantic search across all documents in an application.
    
    This endpoint uses vector embeddings and FAISS indexing to find relevant
    document sections based on natural language queries. Results are ranked
    by relevance score.
    
    Prerequisites:
    - Application must exist
    - Documents must be uploaded and indexed
    
    **Requirements**: 16.2, 14.1
    **Property 35**: Semantic Search Functionality
    
    Example query: "What is the company's revenue for 2023?"
    """
)
async def semantic_search(
    app_id: str,
    search_request: SemanticSearchRequest,
    request: Request
) -> SemanticSearchResponse:
    """
    Perform semantic search across application documents.
    
    Args:
        app_id: Application ID
        search_request: Search parameters (query, max_results, min_relevance)
        request: FastAPI request object (contains user info)
    
    Returns:
        Search results with relevance scores
    
    Raises:
        HTTPException: 404 if application not found,
                      400 if no documents are indexed,
                      500 for server errors
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
        
        # Get vector search engine
        search_engine = get_vector_search_engine()
        
        # Check if any documents are indexed
        if search_engine.get_index_size() == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No documents are indexed for search. Upload and process documents first."
            )
        
        # Perform semantic search
        search_results = await search_engine.search(
            query=search_request.query,
            k=search_request.max_results,
            min_score=search_request.min_relevance
        )
        
        # Filter results to only include documents from this application
        # Get all document IDs for this application
        doc_repo = get_document_repository()
        app_documents = await doc_repo.list_by_application(app_id)
        app_doc_ids = {doc.id for doc in app_documents}
        
        # Filter search results
        filtered_results = [
            result for result in search_results
            if result['doc_id'] in app_doc_ids
        ]
        
        # Enrich results with document metadata
        enriched_results = []
        for result in filtered_results:
            # Find the document to get metadata
            doc = next((d for d in app_documents if d.id == result['doc_id']), None)
            
            enriched_results.append(SearchResult(
                doc_id=result['doc_id'],
                chunk=result['chunk'],
                chunk_index=result['chunk_index'],
                total_chunks=result['total_chunks'],
                relevance_score=result['relevance_score'],
                filename=doc.filename if doc else None,
                document_type=result.get('document_type')  # Get from result metadata if available
            ))
        
        # Log the search
        try:
            audit_logger = get_audit_logger()
            user_id = getattr(request.state, "user_id", "system")
            await audit_logger.log_user_action(
                action="semantic_search",
                resource_type="application",
                resource_id=app_id,
                user_id=user_id,
                details={
                    "query": search_request.query,
                    "max_results": search_request.max_results,
                    "min_relevance": search_request.min_relevance,
                    "results_found": len(enriched_results)
                }
            )
        except Exception as log_error:
            # Don't fail the request if audit logging fails
            pass
        
        return SemanticSearchResponse(
            application_id=app_id,
            query=search_request.query,
            results=enriched_results,
            total_results=len(enriched_results),
            search_timestamp=datetime.utcnow()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform semantic search: {str(e)}"
        )


# Monitoring Endpoints

@monitoring_router.get(
    "/alerts",
    response_model=MonitoringAlertsListResponse,
    summary="Get monitoring alerts",
    description="""
    Retrieve monitoring alerts across all applications or for a specific application.
    
    Alerts are generated when material adverse changes are detected during
    continuous monitoring of approved applications. Results are ordered by
    creation time (newest first).
    
    **Requirements**: 10.3, 14.1
    **Property 23**: Alert Generation and Notification
    """
)
async def get_monitoring_alerts(
    application_id: Optional[str] = Query(
        None,
        description="Filter alerts by application ID"
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of alerts to return (1-100)"
    ),
    severity: Optional[str] = Query(
        None,
        description="Filter by severity (low, medium, high, critical)"
    )
) -> MonitoringAlertsListResponse:
    """
    Get monitoring alerts with optional filtering.
    
    Args:
        application_id: Optional filter by application ID
        limit: Maximum number of alerts to return (1-100)
        severity: Optional filter by severity level
    
    Returns:
        List of monitoring alerts with metadata
    
    Raises:
        HTTPException: 500 for server errors
    """
    try:
        monitoring_service = get_monitoring_service()
        
        if application_id:
            # Get alerts for specific application
            alerts_data = await monitoring_service.get_alerts_for_application(
                application_id=application_id,
                limit=limit
            )
        else:
            # Get all alerts (would need to implement in monitoring service)
            # For now, return empty list if no application_id specified
            alerts_data = []
        
        # Filter by severity if specified
        if severity:
            alerts_data = [
                alert for alert in alerts_data
                if alert.get('severity', '').lower() == severity.lower()
            ]
        
        # Convert to response models
        alert_responses = []
        for alert_dict in alerts_data:
            alert_responses.append(MonitoringAlertResponse(
                id=alert_dict['id'],
                application_id=alert_dict['application_id'],
                alert_type=alert_dict['alert_type'],
                severity=alert_dict['severity'],
                message=alert_dict['message'],
                details=alert_dict.get('details', {}),
                created_at=datetime.fromisoformat(alert_dict['created_at'].replace('Z', '+00:00'))
                    if isinstance(alert_dict['created_at'], str)
                    else alert_dict['created_at'],
                acknowledged=alert_dict.get('acknowledged', False),
                acknowledged_by=alert_dict.get('acknowledged_by'),
                acknowledged_at=datetime.fromisoformat(alert_dict['acknowledged_at'].replace('Z', '+00:00'))
                    if alert_dict.get('acknowledged_at') and isinstance(alert_dict['acknowledged_at'], str)
                    else alert_dict.get('acknowledged_at')
            ))
        
        return MonitoringAlertsListResponse(
            alerts=alert_responses,
            total=len(alert_responses),
            limit=limit,
            application_filter=application_id
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve monitoring alerts: {str(e)}"
        )


@monitoring_router.get(
    "/applications/{app_id}",
    response_model=MonitoringStatusResponse,
    summary="Get monitoring status",
    description="""
    Retrieve the monitoring status for a specific application.
    
    Returns information about:
    - Whether monitoring is active
    - Last check timestamp
    - Next scheduled check
    - Total checks performed
    - Total alerts generated
    
    **Requirements**: 10.1, 14.1
    **Property 22**: Monitoring Activation on Approval
    """
)
async def get_monitoring_status(app_id: str) -> MonitoringStatusResponse:
    """
    Get monitoring status for an application.
    
    Args:
        app_id: Application ID
    
    Returns:
        Monitoring status information
    
    Raises:
        HTTPException: 404 if application or monitoring not found,
                      500 for server errors
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
        
        # Get monitoring status
        monitoring_service = get_monitoring_service()
        monitoring_status = await monitoring_service.get_monitoring_status(app_id)
        
        if monitoring_status is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Monitoring not configured for application {app_id}"
            )
        
        # Parse datetime strings
        def parse_datetime(dt_str):
            if dt_str is None:
                return None
            if isinstance(dt_str, datetime):
                return dt_str
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        
        return MonitoringStatusResponse(
            application_id=app_id,
            company_name=monitoring_status['company_name'],
            status=monitoring_status['status'],
            activated_at=parse_datetime(monitoring_status.get('activated_at')),
            last_check=parse_datetime(monitoring_status.get('last_check')),
            next_check=parse_datetime(monitoring_status.get('next_check')),
            check_interval_days=monitoring_status.get('check_interval_days', 7),
            total_checks=monitoring_status.get('total_checks', 0),
            total_alerts=monitoring_status.get('total_alerts', 0),
            additional_context=monitoring_status.get('additional_context', {})
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve monitoring status: {str(e)}"
        )


# Export routers
__all__ = ['search_router', 'monitoring_router']
