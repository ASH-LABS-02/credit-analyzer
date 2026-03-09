"""
FastAPI Dependencies for Authentication and Database Access

This module provides reusable dependencies for FastAPI endpoints:
- get_current_user: Validates JWT tokens and returns authenticated user
- get_auth_service: Provides AuthService instance
- OAuth2 password bearer scheme for token extraction

Requirements: 4.6
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database.config import get_db
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.database.models import User
from app.core.config import settings


# OAuth2 password bearer scheme for token extraction
# This extracts the token from the Authorization header: "Bearer <token>"
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scheme_name="JWT"
)


def get_auth_service() -> AuthService:
    """
    FastAPI dependency to get AuthService instance.
    
    Returns:
        Configured AuthService instance with JWT settings
        
    Example:
        @app.post("/login")
        def login(auth_service: AuthService = Depends(get_auth_service)):
            token = auth_service.create_access_token({"sub": user_id})
            return {"access_token": token}
    """
    # Get JWT configuration from settings
    # For now, use a default secret key if not configured
    # TODO: Add JWT_SECRET_KEY to settings in task 10.1
    secret_key = getattr(settings, 'JWT_SECRET_KEY', 'temporary-secret-key-change-in-production')
    algorithm = getattr(settings, 'JWT_ALGORITHM', 'HS256')
    expire_minutes = getattr(settings, 'JWT_ACCESS_TOKEN_EXPIRE_MINUTES', 30)
    
    return AuthService(
        secret_key=secret_key,
        algorithm=algorithm,
        access_token_expire_minutes=expire_minutes
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """
    FastAPI dependency to get the current authenticated user.
    
    This dependency:
    1. Extracts the JWT token from the Authorization header
    2. Validates and decodes the token
    3. Retrieves the user from the database
    4. Returns the authenticated user
    
    Args:
        token: JWT token from Authorization header (extracted by oauth2_scheme)
        db: Database session
        auth_service: AuthService instance for token validation
        
    Returns:
        Authenticated User object
        
    Raises:
        HTTPException: 401 Unauthorized if:
            - Token is missing or invalid
            - Token is expired
            - User ID not found in token
            - User not found in database
            - User account is inactive
            
    Example:
        @app.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.id, "email": current_user.email}
    
    Requirements: 4.6
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode and validate the JWT token
        payload = auth_service.decode_access_token(token)
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
            
    except ValueError as e:
        # Token is invalid or expired
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Retrieve user from database
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    
    if user is None:
        raise credentials_exception
    
    # Check if user account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    FastAPI dependency to get the current active user.
    
    This is a convenience dependency that ensures the user is active.
    It's redundant with get_current_user (which already checks is_active),
    but provided for clarity and future extensibility.
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        Active User object
        
    Raises:
        HTTPException: 403 Forbidden if user is inactive
        
    Example:
        @app.get("/admin")
        def admin_route(user: User = Depends(get_current_active_user)):
            return {"message": "Admin access granted"}
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return current_user


# Optional dependency for endpoints that may or may not require authentication
async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """
    FastAPI dependency to optionally get the current user.
    
    This dependency returns the user if a valid token is provided,
    or None if no token is provided or the token is invalid.
    Useful for endpoints that have different behavior for authenticated users.
    
    Args:
        token: Optional JWT token from Authorization header
        db: Database session
        auth_service: AuthService instance
        
    Returns:
        User object if authenticated, None otherwise
        
    Example:
        @app.get("/public")
        def public_route(user: Optional[User] = Depends(get_optional_user)):
            if user:
                return {"message": f"Hello {user.email}"}
            return {"message": "Hello guest"}
    """
    if not token:
        return None
    
    try:
        payload = auth_service.decode_access_token(token)
        user_id: str = payload.get("sub")
        
        if user_id is None:
            return None
        
        user_repo = UserRepository(db)
        user = user_repo.get_by_id(user_id)
        
        if user and user.is_active:
            return user
            
    except (ValueError, Exception):
        # Invalid token or other error - return None instead of raising
        pass
    
    return None
