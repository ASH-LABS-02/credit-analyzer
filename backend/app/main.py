"""
FastAPI Application Entry Point

This module initializes the FastAPI application with all necessary middleware:
- CORS middleware for cross-origin requests
- Authentication middleware for Firebase token validation
- Error handling middleware for consistent error responses

Requirements: 14.1, 14.4
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.config import settings
from app.api.middleware import AuthMiddleware
from app.api.rate_limiter import RateLimiter
from app.core.error_logger import ErrorLogger, ErrorSeverity
from app.core.startup import startup as run_startup
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown tasks:
    - Startup: Validate configuration, initialize database, setup file storage
    - Shutdown: Clean up resources
    
    Requirements: 6.5, 1.4, 3.1
    """
    # Startup
    logger.info("Application starting up...")
    try:
        run_startup()
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Application shutting down...")


# Initialize FastAPI app with OpenAPI documentation
app = FastAPI(
    title="Intelli-Credit API",
    description="""
    ## AI-Powered Corporate Credit Decisioning Platform
    
    Intelli-Credit automates corporate loan application evaluation through:
    - **Document Processing**: Upload and extract financial data from various formats
    - **Multi-Agent Analysis**: AI-powered research and intelligence gathering
    - **Financial Analysis**: Automated ratio calculations and trend analysis
    - **Risk Scoring**: Explainable credit scores with weighted risk factors
    - **CAM Generation**: Automated Credit Appraisal Memo creation
    - **Continuous Monitoring**: Post-approval monitoring with alerts
    
    ### Authentication
    Authentication is currently disabled for this environment.
    
    ### Rate Limiting
    API requests are rate-limited to prevent abuse. Rate limit headers are included in responses.
    """,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check and system status endpoints"
        },
        {
            "name": "applications",
            "description": "Application management operations"
        },
        {
            "name": "documents",
            "description": "Document upload and management"
        },
        {
            "name": "analysis",
            "description": "Credit analysis operations"
        },
        {
            "name": "cam",
            "description": "Credit Appraisal Memo generation and export"
        },
        {
            "name": "search",
            "description": "Semantic document search"
        },
        {
            "name": "monitoring",
            "description": "Post-approval monitoring and alerts"
        }
    ],
    contact={
        "name": "Intelli-Credit Support",
        "email": "support@intelli-credit.com"
    },
    license_info={
        "name": "Proprietary"
    },
    lifespan=lifespan
)

# Initialize error logger (lazy initialization to avoid issues during testing)
error_logger = None

def get_error_logger():
    """Get or initialize error logger"""
    global error_logger
    if error_logger is None:
        try:
            # ErrorLogger now uses SQLite database session instead of Firestore
            from app.database.config import get_db_config
            db_config = get_db_config()
            db_session = db_config.get_session()
            error_logger = ErrorLogger(db_session)
        except Exception as e:
            logger.warning(f"Failed to initialize error logger: {e}. Error logging will be limited.")
    return error_logger

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Session-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
)

# Authentication middleware removed as per implementation plan

# Add rate limiting middleware
# Configure rate limits: 100 requests per 60 seconds per client
rate_limiter = RateLimiter(max_requests=100, time_window=60)
app.middleware("http")(rate_limiter)


# Error handling middleware
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTP exceptions with consistent error response format.
    
    Requirements: 14.3
    """
    error_response = {
        "error": "http_error",
        "message": exc.detail,
        "status_code": exc.status_code
    }
    
    # Log error if it's a server error (5xx)
    if exc.status_code >= 500:
        try:
            logger_instance = get_error_logger()
            if logger_instance:
                error_id = await logger_instance.log_error(
                    error=Exception(exc.detail),
                    context={
                        "path": request.url.path,
                        "method": request.method,
                        "status_code": exc.status_code
                    },
                    severity=ErrorSeverity.ERROR
                )
                error_response["error_id"] = error_id
        except Exception as log_error:
            logger.error(f"Failed to log error: {log_error}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors with detailed error messages.
    
    Requirements: 14.3
    """
    # Convert validation errors to JSON-serializable format
    errors = []
    for error in exc.errors():
        error_dict = {
            "type": error.get("type"),
            "loc": error.get("loc"),
            "msg": error.get("msg"),
            "input": str(error.get("input"))  # Convert to string to ensure serializability
        }
        errors.append(error_dict)
    
    error_response = {
        "error": "validation_error",
        "message": "Request validation failed",
        "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "details": errors
    }
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle all unhandled exceptions with error logging.
    
    Requirements: 14.3, 15.5
    """
    # Log the error
    error_id = None
    try:
        logger_instance = get_error_logger()
        if logger_instance:
            error_id = await logger_instance.log_error(
                error=exc,
                context={
                    "path": request.url.path,
                    "method": request.method,
                    "user_id": getattr(request.state, "user_id", None)
                },
                severity=ErrorSeverity.CRITICAL,
                user_id=getattr(request.state, "user_id", None)
            )
    except Exception as log_error:
        logger.error(f"Failed to log error: {log_error}")
    
    error_response = {
        "error": "internal_server_error",
        "message": "An unexpected error occurred. Please try again later.",
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR
    }
    
    if error_id:
        error_response["error_id"] = error_id
    
    # In development, include error details
    if settings.ENVIRONMENT == "development":
        error_response["details"] = str(exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


@app.get("/", tags=["health"])
async def root():
    """
    Root endpoint providing API information.
    
    Returns basic information about the API including version and status.
    """
    return {
        "message": "Intelli-Credit API",
        "version": "0.1.0",
        "status": "running",
        "documentation": "/docs"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns the health status of the API. This endpoint does not require authentication.
    """
    return {
        "status": "healthy",
        "version": "0.1.0"
    }


# Include API routers
from app.api.auth import router as auth_router
from app.api.applications import router as applications_router
from app.api.documents import router as documents_router
from app.api.analysis import router as analysis_router
from app.api.simple_analysis import router as simple_analysis_router
from app.api.simple_cam import router as simple_cam_router
from app.api.cam import router as cam_router
from app.api.search_monitoring import search_router, monitoring_router
from app.api.company_insights import router as company_insights_router

app.include_router(auth_router)
app.include_router(applications_router)
app.include_router(documents_router)
app.include_router(analysis_router)
app.include_router(simple_analysis_router)
app.include_router(company_insights_router)
app.include_router(simple_cam_router)
app.include_router(cam_router)
app.include_router(search_router)
app.include_router(monitoring_router)
