"""
Application Management API Endpoints

This module implements RESTful endpoints for managing credit applications:
- POST /api/v1/applications - Create new application
- GET /api/v1/applications - List applications
- GET /api/v1/applications/{app_id} - Get application details
- PATCH /api/v1/applications/{app_id} - Update application
- DELETE /api/v1/applications/{app_id} - Delete application

Requirements: 9.1, 14.1
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Query, Request, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
import uuid

from app.models.domain import (
    Application,
    ApplicationStatus,
    CreditRecommendation
)
from app.repositories.application_repository import ApplicationRepository
from app.core.audit_logger import AuditLogger
from app.api.dependencies import get_current_user
from app.database.models import User
from app.database.config import get_db


# Request/Response Models
class ApplicationCreate(BaseModel):
    """Request model for creating a new application."""
    company_name: str = Field(..., min_length=1, description="Company name")
    loan_amount: float = Field(..., gt=0, description="Requested loan amount")
    loan_purpose: str = Field(..., min_length=1, description="Purpose of the loan")
    applicant_email: str = Field(..., description="Applicant email address")
    
    @field_validator('applicant_email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation."""
        if '@' not in v or '.' not in v.split('@')[-1]:
            raise ValueError('Invalid email format')
        return v.lower()


class ApplicationUpdate(BaseModel):
    """Request model for updating an application."""
    company_name: Optional[str] = Field(None, min_length=1, description="Company name")
    loan_amount: Optional[float] = Field(None, gt=0, description="Requested loan amount")
    loan_purpose: Optional[str] = Field(None, min_length=1, description="Purpose of the loan")
    applicant_email: Optional[str] = Field(None, description="Applicant email address")
    status: Optional[ApplicationStatus] = Field(None, description="Application status")
    credit_score: Optional[float] = Field(None, ge=0, le=100, description="Credit score (0-100)")
    recommendation: Optional[CreditRecommendation] = Field(None, description="Credit recommendation")
    
    @field_validator('applicant_email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Basic email validation."""
        if v is not None:
            if '@' not in v or '.' not in v.split('@')[-1]:
                raise ValueError('Invalid email format')
            return v.lower()
        return v


class ApplicationResponse(BaseModel):
    """Response model for application data."""
    id: str
    company_name: str
    loan_amount: float
    loan_purpose: str
    applicant_email: str
    status: str
    created_at: datetime
    updated_at: datetime
    credit_score: Optional[float] = None
    recommendation: Optional[str] = None


class ApplicationListResponse(BaseModel):
    """Response model for application list."""
    applications: List[ApplicationResponse]
    total: int
    limit: Optional[int] = None
    status_filter: Optional[str] = None


# Initialize router
router = APIRouter(
    prefix="/api/v1/applications",
    tags=["applications"]
)


def application_to_response(app: Application) -> ApplicationResponse:
    """
    Convert Application domain model to ApplicationResponse.
    
    Handles enum to string conversion properly.
    """
    return ApplicationResponse(
        id=app.id,
        company_name=app.company_name,
        loan_amount=app.loan_amount,
        loan_purpose=app.loan_purpose,
        applicant_email=app.applicant_email,
        status=app.status if isinstance(app.status, str) else app.status.value,
        created_at=app.created_at,
        updated_at=app.updated_at,
        credit_score=app.credit_score,
        recommendation=(
            app.recommendation if isinstance(app.recommendation, str) or app.recommendation is None
            else app.recommendation.value
        )
    )


@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new application",
    description="""
    Create a new credit application.
    
    The application is initialized with status "pending" and assigned a unique ID.
    An audit log entry is created to track the creation event.
    
    **Requires authentication**: Valid JWT token required.
    
    **Requirements**: 9.1, 14.1
    """
)
def create_application(
    application_data: ApplicationCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ApplicationResponse:
    """
    Create a new credit application.
    
    Args:
        application_data: Application creation data
        request: FastAPI request object (contains user info from auth middleware)
        current_user: Authenticated user (injected by dependency)
        db: Database session (injected by dependency)
        
    Returns:
        Created application data
        
    Raises:
        HTTPException: 400 if validation fails, 401 if not authenticated, 500 for server errors
    """
    try:
        # Generate unique application ID
        app_id = str(uuid.uuid4())
        
        # Create application data dictionary
        app_data = {
            'id': app_id,
            'user_id': current_user.id,
            'company_name': application_data.company_name,
            'loan_amount': application_data.loan_amount,
            'loan_purpose': application_data.loan_purpose,
            'applicant_email': application_data.applicant_email,
            'status': ApplicationStatus.PENDING.value,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Save to repository
        repo = ApplicationRepository(db)
        created_app = repo.create(app_data)
        
        # Log the creation event with authenticated user ID
        try:
            audit_logger = AuditLogger(db)
            audit_logger.log_user_action(
                action="create",
                resource_type="application",
                resource_id=app_id,
                user_id=current_user.id,
                details={
                    "company_name": application_data.company_name,
                    "loan_amount": application_data.loan_amount,
                    "status": ApplicationStatus.PENDING.value
                }
            )
        except Exception as log_error:
            # Don't fail the request if audit logging fails
            pass
        
        # Convert to domain model then response
        domain_app = Application(
            id=created_app.id,
            company_name=created_app.company_name,
            loan_amount=created_app.loan_amount,
            loan_purpose=created_app.loan_purpose,
            applicant_email=created_app.applicant_email,
            status=ApplicationStatus(created_app.status),
            created_at=created_app.created_at,
            updated_at=created_app.updated_at,
            credit_score=created_app.credit_score,
            recommendation=CreditRecommendation(created_app.recommendation) if created_app.recommendation else None
        )
        
        return application_to_response(domain_app)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create application: {str(e)}"
        )


@router.get(
    "",
    response_model=ApplicationListResponse,
    summary="List applications",
    description="""
    List all credit applications with optional filtering.
    
    Applications are returned in descending order by creation date (newest first).
    You can filter by status and limit the number of results.
    
    **Requirements**: 9.1, 14.1
    """
)
def list_applications(
    db: Session = Depends(get_db),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum number of applications to return"),
    status_filter: Optional[ApplicationStatus] = Query(None, alias="status", description="Filter by application status")
) -> ApplicationListResponse:
    """
    List all applications with optional filtering.
    
    Args:
        db: Database session (injected by dependency)
        limit: Maximum number of applications to return (1-100)
        status_filter: Filter by application status
        
    Returns:
        List of applications with metadata
        
    Raises:
        HTTPException: 500 for server errors
    """
    try:
        repo = ApplicationRepository(db)
        
        # Build filters
        filters = {}
        if status_filter:
            filters['status'] = status_filter.value
        
        # Get applications
        applications = repo.list_with_filters(
            filters=filters if filters else None,
            limit=limit or 100
        )
        
        # Convert to domain models then response models
        app_responses = []
        for app in applications:
            domain_app = Application(
                id=app.id,
                company_name=app.company_name,
                loan_amount=app.loan_amount,
                loan_purpose=app.loan_purpose,
                applicant_email=app.applicant_email,
                status=ApplicationStatus(app.status),
                created_at=app.created_at,
                updated_at=app.updated_at,
                credit_score=app.credit_score,
                recommendation=CreditRecommendation(app.recommendation) if app.recommendation else None
            )
            app_responses.append(application_to_response(domain_app))
        
        return ApplicationListResponse(
            applications=app_responses,
            total=len(app_responses),
            limit=limit,
            status_filter=status_filter.value if status_filter else None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list applications: {str(e)}"
        )


@router.get(
    "/{app_id}",
    response_model=ApplicationResponse,
    summary="Get application details",
    description="""
    Retrieve detailed information about a specific application.
    
    **Requirements**: 9.1, 14.1
    """
)
def get_application(
    app_id: str,
    db: Session = Depends(get_db)
) -> ApplicationResponse:
    """
    Get application details by ID.
    
    Args:
        app_id: Unique application identifier
        db: Database session (injected by dependency)
        
    Returns:
        Application data
        
    Raises:
        HTTPException: 404 if not found, 500 for server errors
    """
    try:
        repo = ApplicationRepository(db)
        application = repo.get_by_id(app_id)
        
        if application is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {app_id} not found"
            )
        
        # Convert to domain model then response
        domain_app = Application(
            id=application.id,
            company_name=application.company_name,
            loan_amount=application.loan_amount,
            loan_purpose=application.loan_purpose,
            applicant_email=application.applicant_email,
            status=ApplicationStatus(application.status),
            created_at=application.created_at,
            updated_at=application.updated_at,
            credit_score=application.credit_score,
            recommendation=CreditRecommendation(application.recommendation) if application.recommendation else None
        )
        
        return application_to_response(domain_app)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve application: {str(e)}"
        )


@router.patch(
    "/{app_id}",
    response_model=ApplicationResponse,
    summary="Update application",
    description="""
    Update an existing application with partial data.
    
    Only the fields provided in the request body will be updated.
    The updated_at timestamp is automatically set to the current time.
    An audit log entry is created to track the update event.
    
    **Requires authentication**: Valid JWT token required.
    
    **Requirements**: 9.1, 14.1
    """
)
def update_application(
    app_id: str,
    update_data: ApplicationUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ApplicationResponse:
    """
    Update an application with partial data.
    
    Args:
        app_id: Unique application identifier
        update_data: Fields to update
        request: FastAPI request object (contains user info from auth middleware)
        current_user: Authenticated user (injected by dependency)
        db: Database session (injected by dependency)
        
    Returns:
        Updated application data
        
    Raises:
        HTTPException: 404 if not found, 400 for validation errors, 401 if not authenticated, 500 for server errors
    """
    try:
        # Build updates dictionary (only include provided fields)
        updates = {}
        if update_data.company_name is not None:
            updates['company_name'] = update_data.company_name
        if update_data.loan_amount is not None:
            updates['loan_amount'] = update_data.loan_amount
        if update_data.loan_purpose is not None:
            updates['loan_purpose'] = update_data.loan_purpose
        if update_data.applicant_email is not None:
            updates['applicant_email'] = update_data.applicant_email
        if update_data.status is not None:
            updates['status'] = update_data.status.value
        if update_data.credit_score is not None:
            updates['credit_score'] = update_data.credit_score
        if update_data.recommendation is not None:
            updates['recommendation'] = update_data.recommendation.value
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update"
            )
        
        # Update in repository
        repo = ApplicationRepository(db)
        updated_app = repo.update(app_id, updates)
        
        if updated_app is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {app_id} not found"
            )
        
        # Log the update event
        try:
            audit_logger = AuditLogger(db)
            audit_logger.log_user_action(
                action="update",
                resource_type="application",
                resource_id=app_id,
                user_id=current_user.id,
                details={"updated_fields": list(updates.keys())}
            )
        except Exception as log_error:
            # Don't fail the request if audit logging fails
            pass
        
        # Convert to domain model then response
        domain_app = Application(
            id=updated_app.id,
            company_name=updated_app.company_name,
            loan_amount=updated_app.loan_amount,
            loan_purpose=updated_app.loan_purpose,
            applicant_email=updated_app.applicant_email,
            status=ApplicationStatus(updated_app.status),
            created_at=updated_app.created_at,
            updated_at=updated_app.updated_at,
            credit_score=updated_app.credit_score,
            recommendation=CreditRecommendation(updated_app.recommendation) if updated_app.recommendation else None
        )
        
        return application_to_response(domain_app)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update application: {str(e)}"
        )


@router.delete(
    "/{app_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete application",
    description="""
    Delete an application by ID.
    
    This operation permanently removes the application from the system.
    An audit log entry is created to track the deletion event.
    
    **Requires authentication**: Valid JWT token required.
    
    **Requirements**: 9.1, 14.1
    """
)
def delete_application(
    app_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an application by ID.
    
    Args:
        app_id: Unique application identifier
        request: FastAPI request object (contains user info from auth middleware)
        current_user: Authenticated user (injected by dependency)
        db: Database session (injected by dependency)
        
    Returns:
        No content (204 status code)
        
    Raises:
        HTTPException: 404 if not found, 401 if not authenticated, 500 for server errors
    """
    try:
        repo = ApplicationRepository(db)
        deleted = repo.delete(app_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {app_id} not found"
            )
        
        # Log the deletion event
        try:
            audit_logger = AuditLogger(db)
            audit_logger.log_user_action(
                action="delete",
                resource_type="application",
                resource_id=app_id,
                user_id=current_user.id,
                details={}
            )
        except Exception as log_error:
            # Don't fail the request if audit logging fails
            pass
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete application: {str(e)}"
        )
