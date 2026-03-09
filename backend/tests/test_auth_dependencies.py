"""
Tests for JWT Authentication Dependencies

This module tests the FastAPI dependencies for JWT-based authentication:
- get_current_user dependency
- OAuth2 password bearer scheme
- Token validation and user retrieval

Requirements: 4.6
"""

import pytest
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch
import uuid

from app.api.dependencies import (
    get_current_user,
    get_auth_service,
    get_current_active_user,
    get_optional_user
)
from app.services.auth_service import AuthService
from app.database.models import User
from app.repositories.user_repository import UserRepository


class TestGetAuthService:
    """Tests for get_auth_service dependency"""
    
    def test_returns_auth_service_instance(self):
        """Test that get_auth_service returns an AuthService instance"""
        auth_service = get_auth_service()
        
        assert isinstance(auth_service, AuthService)
        assert auth_service.algorithm == "HS256"
        assert auth_service.access_token_expire_minutes == 30
    
    def test_uses_default_secret_key(self):
        """Test that get_auth_service uses default secret key when not configured"""
        auth_service = get_auth_service()
        
        # Should have a secret key (either from settings or default)
        assert auth_service.secret_key is not None
        assert len(auth_service.secret_key) > 0


class TestGetCurrentUser:
    """Tests for get_current_user dependency"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def auth_service(self):
        """Create a real AuthService for testing"""
        return AuthService(secret_key="test-secret-key")
    
    @pytest.fixture
    def test_user(self):
        """Create a test user"""
        return User(
            id=str(uuid.uuid4()),
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self, mock_db, auth_service, test_user):
        """Test that a valid token returns the authenticated user"""
        # Create a valid token
        token = auth_service.create_access_token({"sub": test_user.id})
        
        # Mock the UserRepository to return our test user
        with patch('app.api.dependencies.UserRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo.get_by_id.return_value = test_user
            mock_repo_class.return_value = mock_repo
            
            # Call the dependency
            user = await get_current_user(token, mock_db, auth_service)
            
            # Verify the user was returned
            assert user == test_user
            mock_repo.get_by_id.assert_called_once_with(test_user.id)
    
    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self, mock_db, auth_service):
        """Test that an invalid token raises 401 Unauthorized"""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(invalid_token, mock_db, auth_service)
        
        assert exc_info.value.status_code == 401
        assert "WWW-Authenticate" in exc_info.value.headers
    
    @pytest.mark.asyncio
    async def test_expired_token_raises_401(self, mock_db, auth_service):
        """Test that an expired token raises 401 Unauthorized"""
        # Create a token that expires immediately
        token = auth_service.create_access_token(
            {"sub": "user123"},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token, mock_db, auth_service)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_token_without_user_id_raises_401(self, mock_db, auth_service):
        """Test that a token without user ID raises 401 Unauthorized"""
        # Create a token without 'sub' claim
        token = auth_service.create_access_token({"email": "test@example.com"})
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token, mock_db, auth_service)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_nonexistent_user_raises_401(self, mock_db, auth_service):
        """Test that a token for a nonexistent user raises 401 Unauthorized"""
        token = auth_service.create_access_token({"sub": "nonexistent-user-id"})
        
        # Mock the UserRepository to return None (user not found)
        with patch('app.api.dependencies.UserRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo.get_by_id.return_value = None
            mock_repo_class.return_value = mock_repo
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token, mock_db, auth_service)
            
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_inactive_user_raises_403(self, mock_db, auth_service, test_user):
        """Test that an inactive user raises 403 Forbidden"""
        # Make the user inactive
        test_user.is_active = False
        
        token = auth_service.create_access_token({"sub": test_user.id})
        
        # Mock the UserRepository to return our inactive test user
        with patch('app.api.dependencies.UserRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo.get_by_id.return_value = test_user
            mock_repo_class.return_value = mock_repo
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(token, mock_db, auth_service)
            
            assert exc_info.value.status_code == 403
            assert "inactive" in exc_info.value.detail.lower()


class TestGetCurrentActiveUser:
    """Tests for get_current_active_user dependency"""
    
    @pytest.fixture
    def test_user(self):
        """Create a test user"""
        return User(
            id=str(uuid.uuid4()),
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @pytest.mark.asyncio
    async def test_active_user_returns_user(self, test_user):
        """Test that an active user is returned"""
        user = await get_current_active_user(test_user)
        assert user == test_user
    
    @pytest.mark.asyncio
    async def test_inactive_user_raises_403(self, test_user):
        """Test that an inactive user raises 403 Forbidden"""
        test_user.is_active = False
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(test_user)
        
        assert exc_info.value.status_code == 403


class TestGetOptionalUser:
    """Tests for get_optional_user dependency"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def auth_service(self):
        """Create a real AuthService for testing"""
        return AuthService(secret_key="test-secret-key")
    
    @pytest.fixture
    def test_user(self):
        """Create a test user"""
        return User(
            id=str(uuid.uuid4()),
            email="test@example.com",
            hashed_password="hashed_password",
            full_name="Test User",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @pytest.mark.asyncio
    async def test_valid_token_returns_user(self, mock_db, auth_service, test_user):
        """Test that a valid token returns the user"""
        token = auth_service.create_access_token({"sub": test_user.id})
        
        with patch('app.api.dependencies.UserRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo.get_by_id.return_value = test_user
            mock_repo_class.return_value = mock_repo
            
            user = await get_optional_user(token, mock_db, auth_service)
            
            assert user == test_user
    
    @pytest.mark.asyncio
    async def test_no_token_returns_none(self, mock_db, auth_service):
        """Test that no token returns None instead of raising"""
        user = await get_optional_user(None, mock_db, auth_service)
        assert user is None
    
    @pytest.mark.asyncio
    async def test_invalid_token_returns_none(self, mock_db, auth_service):
        """Test that an invalid token returns None instead of raising"""
        invalid_token = "invalid.token.here"
        
        user = await get_optional_user(invalid_token, mock_db, auth_service)
        assert user is None
    
    @pytest.mark.asyncio
    async def test_inactive_user_returns_none(self, mock_db, auth_service, test_user):
        """Test that an inactive user returns None"""
        test_user.is_active = False
        token = auth_service.create_access_token({"sub": test_user.id})
        
        with patch('app.api.dependencies.UserRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo.get_by_id.return_value = test_user
            mock_repo_class.return_value = mock_repo
            
            user = await get_optional_user(token, mock_db, auth_service)
            
            assert user is None
