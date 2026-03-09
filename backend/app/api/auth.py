"""
Authentication API Endpoints

This module implements JWT-based authentication endpoints:
- POST /api/v1/auth/register - User registration
- POST /api/v1/auth/login - User login (returns JWT token)
- GET /api/v1/auth/me - Get current user info

Requirements: 4.4, 4.5, 4.6
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
import uuid

from app.database.config import get_db
from app.database.models import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.api.dependencies import get_auth_service, get_current_user


# Request/Response Models
class UserRegister(BaseModel):
    """Request model for user registration."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    full_name: Optional[str] = Field(None, description="User full name")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation."""
        v = v.lower().strip()
        if '@' not in v or '.' not in v.split('@')[-1]:
            raise ValueError('Invalid email format')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Password strength validation."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserResponse(BaseModel):
    """Response model for user data."""
    id: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """Response model for authentication token."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class LoginRequest(BaseModel):
    """Request model for JSON-based login."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


# Initialize router
router = APIRouter(
    prefix="/api/v1/auth",
    tags=["authentication"]
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="""
    Register a new user account.
    
    The password is hashed using bcrypt before storage.
    Email addresses must be unique.
    
    **Requirements**: 4.4
    """
)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """
    Register a new user.
    
    Args:
        user_data: User registration data
        db: Database session
        auth_service: AuthService for password hashing
        
    Returns:
        Created user data (without password)
        
    Raises:
        HTTPException: 400 if email already exists, 500 for server errors
    """
    try:
        user_repo = UserRepository(db)
        
        # Check if user already exists
        existing_user = user_repo.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = auth_service.hash_password(user_data.password)
        
        # Create user data dictionary
        user_dict = {
            'id': str(uuid.uuid4()),
            'email': user_data.email,
            'hashed_password': hashed_password,
            'full_name': user_data.full_name,
            'is_active': True,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        created_user = user_repo.create(user_dict)
        
        return UserResponse(
            id=created_user.id,
            email=created_user.email,
            full_name=created_user.full_name,
            is_active=created_user.is_active,
            created_at=created_user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register user: {str(e)}"
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="""
    Authenticate user and return JWT access token.
    
    Send JSON body with email and password.
    
    Use the returned token in the Authorization header for protected endpoints:
    `Authorization: Bearer <token>`
    
    **Requirements**: 4.5
    """
)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """
    Authenticate user and return JWT token.
    
    Args:
        login_data: JSON login data (email and password)
        db: Database session
        auth_service: AuthService for authentication
        
    Returns:
        JWT access token and user data
        
    Raises:
        HTTPException: 401 if credentials are invalid
    """
    try:
        user_repo = UserRepository(db)
        
        # Get user by email
        user = user_repo.get_by_email(login_data.email.lower())
        
        # Authenticate user
        if not auth_service.authenticate_user(user, login_data.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        # Create access token
        access_token = auth_service.create_access_token(
            data={"sub": user.id, "email": user.email}
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                created_at=user.created_at
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to authenticate: {str(e)}"
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="""
    Get information about the currently authenticated user.
    
    Requires valid JWT token in Authorization header.
    
    **Requirements**: 4.6
    """
)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current user from JWT token (injected by dependency)
        
    Returns:
        Current user data
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )
