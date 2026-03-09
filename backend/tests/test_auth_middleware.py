"""
Unit tests for Authentication Middleware

Tests token extraction, validation, and session management in middleware.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from app.api.middleware import AuthMiddleware, require_permission


@pytest.fixture
def auth_middleware():
    """Create an AuthMiddleware instance with mocked AuthService"""
    with patch('app.api.middleware.AuthService') as mock_service:
        middleware = AuthMiddleware()
        middleware.auth_service = mock_service.return_value
        middleware.auth_service.verify_token = AsyncMock()
        middleware.auth_service.validate_session = AsyncMock()
        middleware.auth_service.create_session = AsyncMock()
        middleware.auth_service.check_permission = AsyncMock()
        
        yield middleware


@pytest.fixture
def mock_request():
    """Create a mock request"""
    request = MagicMock(spec=Request)
    request.url.path = "/api/v1/applications"
    request.headers = {}
    request.state = MagicMock()
    return request


@pytest.fixture
def mock_call_next():
    """Create a mock call_next function"""
    async def call_next(request):
        response = Response(content="OK", status_code=200)
        return response
    return call_next


@pytest.mark.asyncio
class TestAuthMiddleware:
    """Tests for AuthMiddleware"""
    
    async def test_public_path_no_auth_required(self, auth_middleware, mock_request, mock_call_next):
        """Test that public paths don't require authentication"""
        mock_request.url.path = "/api/v1/auth/login"
        
        response = await auth_middleware(mock_request, mock_call_next)
        
        assert response.status_code == 200
        # Verify token was not checked
        auth_middleware.auth_service.verify_token.assert_not_called()
    
    async def test_docs_path_no_auth_required(self, auth_middleware, mock_request, mock_call_next):
        """Test that documentation paths don't require authentication"""
        mock_request.url.path = "/docs"
        
        response = await auth_middleware(mock_request, mock_call_next)
        
        assert response.status_code == 200
        auth_middleware.auth_service.verify_token.assert_not_called()
    
    async def test_missing_authorization_header(self, auth_middleware, mock_request, mock_call_next):
        """Test request without Authorization header"""
        mock_request.url.path = "/api/v1/applications"
        mock_request.headers = {}
        
        response = await auth_middleware(mock_request, mock_call_next)
        
        assert response.status_code == 401
        # Parse JSON response
        import json
        content = json.loads(response.body.decode())
        assert content['error'] == 'authentication_required'
    
    async def test_invalid_authorization_header_format(self, auth_middleware, mock_request, mock_call_next):
        """Test request with invalid Authorization header format"""
        mock_request.url.path = "/api/v1/applications"
        mock_request.headers = {'Authorization': 'InvalidFormat token123'}
        
        response = await auth_middleware(mock_request, mock_call_next)
        
        assert response.status_code == 401
        import json
        content = json.loads(response.body.decode())
        assert content['error'] == 'invalid_token_format'
    
    async def test_invalid_token(self, auth_middleware, mock_request, mock_call_next):
        """Test request with invalid token"""
        mock_request.url.path = "/api/v1/applications"
        mock_request.headers = {'Authorization': 'Bearer invalid_token'}
        
        # Mock token verification failure
        auth_middleware.auth_service.verify_token.return_value = None
        
        response = await auth_middleware(mock_request, mock_call_next)
        
        assert response.status_code == 401
        import json
        content = json.loads(response.body.decode())
        assert content['error'] == 'invalid_token'
    
    async def test_valid_token_creates_new_session(self, auth_middleware, mock_request, mock_call_next):
        """Test valid token creates a new session"""
        mock_request.url.path = "/api/v1/applications"
        mock_request.headers = {'Authorization': 'Bearer valid_token'}
        
        decoded_token = {
            'uid': 'user123',
            'email': 'test@example.com'
        }
        
        session_data = {
            'session_id': 'session_123',
            'user_id': 'user123',
            'email': 'test@example.com',
            'role': 'analyst',
            'permissions': {}
        }
        
        # Mock successful token verification and session creation
        auth_middleware.auth_service.verify_token.return_value = decoded_token
        auth_middleware.auth_service.create_session.return_value = session_data
        
        response = await auth_middleware(mock_request, mock_call_next)
        
        assert response.status_code == 200
        assert 'X-Session-ID' in response.headers
        assert response.headers['X-Session-ID'] == 'session_123'
        
        # Verify session was created
        auth_middleware.auth_service.create_session.assert_called_once()
        
        # Verify request state was populated
        assert mock_request.state.user_id == 'user123'
        assert mock_request.state.email == 'test@example.com'
        assert mock_request.state.session_id == 'session_123'
    
    async def test_valid_token_with_existing_valid_session(self, auth_middleware, mock_request, mock_call_next):
        """Test valid token with existing valid session"""
        mock_request.url.path = "/api/v1/applications"
        mock_request.headers = {
            'Authorization': 'Bearer valid_token',
            'X-Session-ID': 'existing_session_123'
        }
        
        decoded_token = {
            'uid': 'user123',
            'email': 'test@example.com'
        }
        
        session_data = {
            'session_id': 'existing_session_123',
            'user_id': 'user123',
            'email': 'test@example.com',
            'role': 'analyst',
            'permissions': {}
        }
        
        # Mock successful token verification and session validation
        auth_middleware.auth_service.verify_token.return_value = decoded_token
        auth_middleware.auth_service.validate_session.return_value = session_data
        
        response = await auth_middleware(mock_request, mock_call_next)
        
        assert response.status_code == 200
        
        # Verify session was validated, not created
        auth_middleware.auth_service.validate_session.assert_called_once_with('existing_session_123')
        auth_middleware.auth_service.create_session.assert_not_called()
    
    async def test_valid_token_with_expired_session(self, auth_middleware, mock_request, mock_call_next):
        """Test valid token with expired session"""
        mock_request.url.path = "/api/v1/applications"
        mock_request.headers = {
            'Authorization': 'Bearer valid_token',
            'X-Session-ID': 'expired_session_123'
        }
        
        decoded_token = {
            'uid': 'user123',
            'email': 'test@example.com'
        }
        
        # Mock successful token verification but expired session
        auth_middleware.auth_service.verify_token.return_value = decoded_token
        auth_middleware.auth_service.validate_session.return_value = None
        
        response = await auth_middleware(mock_request, mock_call_next)
        
        assert response.status_code == 401
        import json
        content = json.loads(response.body.decode())
        assert content['error'] == 'session_expired'


class TestHelperMethods:
    """Tests for helper methods in AuthMiddleware"""
    
    def test_is_public_path_login(self, auth_middleware):
        """Test that login path is recognized as public"""
        assert auth_middleware._is_public_path("/api/v1/auth/login")
    
    def test_is_public_path_docs(self, auth_middleware):
        """Test that docs paths are recognized as public"""
        assert auth_middleware._is_public_path("/docs")
        assert auth_middleware._is_public_path("/docs/")
        assert auth_middleware._is_public_path("/openapi.json")
        assert auth_middleware._is_public_path("/redoc")
    
    def test_is_public_path_protected(self, auth_middleware):
        """Test that protected paths are not recognized as public"""
        assert not auth_middleware._is_public_path("/api/v1/applications")
        assert not auth_middleware._is_public_path("/api/v1/documents")
    
    def test_extract_bearer_token_valid(self, auth_middleware):
        """Test extracting token from valid Bearer header"""
        token = auth_middleware._extract_bearer_token("Bearer abc123xyz")
        assert token == "abc123xyz"
    
    def test_extract_bearer_token_invalid_format(self, auth_middleware):
        """Test extracting token from invalid header format"""
        assert auth_middleware._extract_bearer_token("InvalidFormat token") is None
        assert auth_middleware._extract_bearer_token("Bearer") is None
        assert auth_middleware._extract_bearer_token("token123") is None
    
    def test_extract_bearer_token_case_insensitive(self, auth_middleware):
        """Test that Bearer keyword is case-insensitive"""
        token = auth_middleware._extract_bearer_token("bearer abc123xyz")
        assert token == "abc123xyz"
        
        token = auth_middleware._extract_bearer_token("BEARER abc123xyz")
        assert token == "abc123xyz"
