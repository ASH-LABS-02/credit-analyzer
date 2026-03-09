"""
Property-Based Tests for Authentication

This module contains property-based tests for authentication and session management,
validating Properties 17 and 19 from the design document.

Property 17: Authentication Enforcement
Property 19: Session Expiration Enforcement
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from app.services.auth_service import AuthService
from app.api.middleware import AuthMiddleware
from fastapi import Request, Response


# Hypothesis strategies for generating test data
token_strategy = st.text(min_size=10, max_size=100, alphabet=st.characters(
    min_codepoint=48, max_codepoint=122,  # 0-9, A-Z, a-z
    blacklist_characters='<>[]{}|\\^`'
))

user_id_strategy = st.text(min_size=5, max_size=50, alphabet=st.characters(
    min_codepoint=48, max_codepoint=122,  # 0-9, A-Z, a-z
    blacklist_characters='<>[]{}|\\^`'
))

email_strategy = st.emails()

session_id_strategy = st.text(min_size=10, max_size=100, alphabet=st.characters(
    min_codepoint=48, max_codepoint=122,  # 0-9, A-Z, a-z
    blacklist_characters='<>[]{}|\\^`'
))

# Time offset in minutes (positive for future, negative for past)
time_offset_strategy = st.integers(min_value=-120, max_value=120)

role_strategy = st.sampled_from(['admin', 'analyst', 'viewer'])


def create_mock_auth_service():
    """Create a mocked AuthService - not a fixture to work with Hypothesis"""
    with patch('app.services.auth_service.get_auth_client') as mock_auth, \
         patch('app.services.auth_service.get_firestore_client') as mock_db, \
         patch('app.services.auth_service.ErrorLogger') as mock_logger:
        
        service = AuthService()
        service.auth_client = mock_auth.return_value
        service.db = mock_db.return_value
        service.error_logger = mock_logger.return_value
        service.error_logger.log_error = AsyncMock()
        
        # Mock Firestore operations
        mock_session_ref = MagicMock()
        mock_user_ref = MagicMock()
        
        def collection_side_effect(name):
            mock_collection = MagicMock()
            if name == 'sessions':
                mock_collection.document.return_value = mock_session_ref
            elif name == 'users':
                mock_collection.document.return_value = mock_user_ref
            return mock_collection
        
        service.db.collection.side_effect = collection_side_effect
        
        return service, mock_session_ref, mock_user_ref


def create_mock_auth_middleware():
    """Create a mocked AuthMiddleware - not a fixture to work with Hypothesis"""
    with patch('app.api.middleware.AuthService') as mock_service:
        middleware = AuthMiddleware()
        middleware.auth_service = mock_service.return_value
        middleware.auth_service.verify_token = AsyncMock()
        middleware.auth_service.validate_session = AsyncMock()
        middleware.auth_service.create_session = AsyncMock()
        
        return middleware


class TestProperty17AuthenticationEnforcement:
    """
    Property 17: Authentication Enforcement
    
    For any API request without valid Firebase Authentication credentials,
    the system should reject the request and return an authentication error.
    
    Validates: Requirements 8.1, 8.3
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        token=token_strategy,
        path=st.sampled_from([
            '/api/v1/applications',
            '/api/v1/documents',
            '/api/v1/applications/123/analyze',
            '/api/v1/monitoring/alerts'
        ])
    )
    async def test_invalid_token_rejected(self, token, path):
        """
        **Validates: Requirements 8.1, 8.3**
        
        Property: For any API request with an invalid token,
        the system must reject the request with an authentication error.
        """
        # Create mock middleware
        mock_auth_middleware = create_mock_auth_middleware()
        
        # Setup: Mock invalid token verification
        mock_auth_middleware.auth_service.verify_token.return_value = None
        
        # Create mock request
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = path
        mock_request.headers = {'Authorization': f'Bearer {token}'}
        mock_request.state = MagicMock()
        
        # Create mock call_next
        async def call_next(request):
            return Response(content="OK", status_code=200)
        
        # Execute
        response = await mock_auth_middleware(mock_request, call_next)
        
        # Verify: Request should be rejected with 401
        assert response.status_code == 401, \
            f"Invalid token should be rejected with 401, got {response.status_code}"
        
        # Verify error message is present
        import json
        content = json.loads(response.body.decode())
        assert 'error' in content, "Response should contain error field"
        assert content['error'] == 'invalid_token', \
            f"Error should be 'invalid_token', got {content['error']}"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        path=st.sampled_from([
            '/api/v1/applications',
            '/api/v1/documents',
            '/api/v1/applications/123/cam',
            '/api/v1/monitoring/alerts'
        ])
    )
    async def test_missing_token_rejected(self, path):
        """
        **Validates: Requirements 8.1, 8.3**
        
        Property: For any API request without an Authorization header,
        the system must reject the request with an authentication error.
        """
        # Create mock middleware
        mock_auth_middleware = create_mock_auth_middleware()
        
        # Create mock request without Authorization header
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = path
        mock_request.headers = {}
        mock_request.state = MagicMock()
        
        # Create mock call_next
        async def call_next(request):
            return Response(content="OK", status_code=200)
        
        # Execute
        response = await mock_auth_middleware(mock_request, call_next)
        
        # Verify: Request should be rejected with 401
        assert response.status_code == 401, \
            f"Missing token should be rejected with 401, got {response.status_code}"
        
        # Verify error message
        import json
        content = json.loads(response.body.decode())
        assert 'error' in content
        assert content['error'] == 'authentication_required'
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        token=token_strategy,
        user_id=user_id_strategy,
        email=email_strategy,
        path=st.sampled_from([
            '/api/v1/applications',
            '/api/v1/documents',
            '/api/v1/applications/123/results'
        ])
    )
    async def test_valid_token_accepted(self, token, user_id, email, path):
        """
        **Validates: Requirements 8.1**
        
        Property: For any API request with a valid Firebase token,
        the system must accept the request and allow it to proceed.
        """
        # Create mock middleware
        mock_auth_middleware = create_mock_auth_middleware()
        
        # Setup: Mock valid token verification
        decoded_token = {
            'uid': user_id,
            'email': email,
            'email_verified': True
        }
        
        session_data = {
            'session_id': f'session_{user_id}',
            'user_id': user_id,
            'email': email,
            'role': 'analyst',
            'permissions': {}
        }
        
        mock_auth_middleware.auth_service.verify_token.return_value = decoded_token
        mock_auth_middleware.auth_service.create_session.return_value = session_data
        
        # Create mock request
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = path
        mock_request.headers = {'Authorization': f'Bearer {token}'}
        mock_request.state = MagicMock()
        
        # Create mock call_next
        async def call_next(request):
            return Response(content="OK", status_code=200)
        
        # Execute
        response = await mock_auth_middleware(mock_request, call_next)
        
        # Verify: Request should be accepted
        assert response.status_code == 200, \
            f"Valid token should be accepted, got {response.status_code}"
        
        # Verify session ID is in response headers
        assert 'X-Session-ID' in response.headers, \
            "Response should include session ID header"
        
        # Verify request state was populated
        assert mock_request.state.user_id == user_id
        assert mock_request.state.email == email


class TestProperty26APITokenValidation:
    """
    Property 26: API Token Validation
    
    For any API request with an invalid or missing authentication token,
    the system should reject the request with an appropriate HTTP 401 or 403 status code.
    
    Validates: Requirements 12.4
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        malformed_header=st.sampled_from([
            'InvalidFormat token123',
            'Token token123',
            'Basic token123',
            'token123',  # no prefix
            'Bearer',  # no token
            'Bearer ',  # empty token
        ]),
        path=st.sampled_from([
            '/api/v1/applications',
            '/api/v1/documents',
            '/api/v1/applications/123/analyze',
            '/api/v1/monitoring/alerts'
        ])
    )
    async def test_malformed_authorization_header_rejected(self, malformed_header, path):
        """
        **Validates: Requirements 12.4**
        
        Property: For any API request with a malformed Authorization header
        (not in "Bearer <token>" format), the system must reject the request with HTTP 401.
        """
        # Create mock middleware
        mock_auth_middleware = create_mock_auth_middleware()
        
        # Create mock request with malformed header
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = path
        mock_request.headers = {'Authorization': malformed_header}
        mock_request.state = MagicMock()
        
        # Create mock call_next
        async def call_next(request):
            return Response(content="OK", status_code=200)
        
        # Execute
        response = await mock_auth_middleware(mock_request, call_next)
        
        # Verify: Request should be rejected with 401
        assert response.status_code == 401, \
            f"Malformed authorization header '{malformed_header}' should be rejected with 401, got {response.status_code}"
        
        # Verify error message is present
        import json
        content = json.loads(response.body.decode())
        assert 'error' in content, "Response should contain error field"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        token=token_strategy,
        path=st.sampled_from([
            '/api/v1/applications',
            '/api/v1/documents/123',
            '/api/v1/applications/456/cam',
            '/api/v1/monitoring/alerts'
        ])
    )
    async def test_invalid_token_returns_401(self, token, path):
        """
        **Validates: Requirements 12.4**
        
        Property: For any API request with an invalid authentication token
        (token that fails Firebase verification), the system must reject
        the request with HTTP 401 status code.
        """
        # Create mock middleware
        mock_auth_middleware = create_mock_auth_middleware()
        
        # Setup: Mock token verification failure
        mock_auth_middleware.auth_service.verify_token.return_value = None
        
        # Create mock request
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = path
        mock_request.headers = {'Authorization': f'Bearer {token}'}
        mock_request.state = MagicMock()
        
        # Create mock call_next
        async def call_next(request):
            return Response(content="OK", status_code=200)
        
        # Execute
        response = await mock_auth_middleware(mock_request, call_next)
        
        # Verify: Must return 401 status code
        assert response.status_code == 401, \
            f"Invalid token must return HTTP 401, got {response.status_code}"
        
        # Verify: Response contains error information
        import json
        content = json.loads(response.body.decode())
        assert 'error' in content, "Response must contain error field"
        assert 'message' in content, "Response must contain message field"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        path=st.sampled_from([
            '/api/v1/applications',
            '/api/v1/documents',
            '/api/v1/applications/123/analyze',
            '/api/v1/monitoring/alerts',
            '/api/v1/applications/456/cam/export'
        ])
    )
    async def test_missing_authorization_header_returns_401(self, path):
        """
        **Validates: Requirements 12.4**
        
        Property: For any API request without an Authorization header,
        the system must reject the request with HTTP 401 status code.
        """
        # Create mock middleware
        mock_auth_middleware = create_mock_auth_middleware()
        
        # Create mock request without Authorization header
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = path
        mock_request.headers = {}
        mock_request.state = MagicMock()
        
        # Create mock call_next
        async def call_next(request):
            return Response(content="OK", status_code=200)
        
        # Execute
        response = await mock_auth_middleware(mock_request, call_next)
        
        # Verify: Must return 401 status code
        assert response.status_code == 401, \
            f"Missing authorization header must return HTTP 401, got {response.status_code}"
        
        # Verify: Response contains error information
        import json
        content = json.loads(response.body.decode())
        assert 'error' in content
        assert content['error'] == 'authentication_required'
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        token=token_strategy,
        user_id=user_id_strategy,
        email=email_strategy,
        path=st.sampled_from([
            '/api/v1/applications',
            '/api/v1/documents',
            '/api/v1/applications/123/results',
            '/api/v1/monitoring/alerts'
        ])
    )
    async def test_valid_token_allows_request(self, token, user_id, email, path):
        """
        **Validates: Requirements 12.4**
        
        Property: For any API request with a valid authentication token,
        the system must allow the request to proceed (not return 401/403).
        """
        # Create mock middleware
        mock_auth_middleware = create_mock_auth_middleware()
        
        # Setup: Mock valid token verification
        decoded_token = {
            'uid': user_id,
            'email': email,
            'email_verified': True
        }
        
        session_data = {
            'session_id': f'session_{user_id}',
            'user_id': user_id,
            'email': email,
            'role': 'analyst',
            'permissions': {}
        }
        
        mock_auth_middleware.auth_service.verify_token.return_value = decoded_token
        mock_auth_middleware.auth_service.create_session.return_value = session_data
        
        # Create mock request
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = path
        mock_request.headers = {'Authorization': f'Bearer {token}'}
        mock_request.state = MagicMock()
        
        # Create mock call_next
        async def call_next(request):
            return Response(content="OK", status_code=200)
        
        # Execute
        response = await mock_auth_middleware(mock_request, call_next)
        
        # Verify: Valid token should NOT return 401 or 403
        assert response.status_code not in [401, 403], \
            f"Valid token should not be rejected, got {response.status_code}"
        
        # Verify: Request should succeed
        assert response.status_code == 200, \
            f"Valid token should allow request to proceed, got {response.status_code}"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        empty_token=st.sampled_from(['', '   ', '\t', '\n']),
        path=st.sampled_from([
            '/api/v1/applications',
            '/api/v1/documents',
            '/api/v1/applications/123/analyze'
        ])
    )
    async def test_empty_token_rejected(self, empty_token, path):
        """
        **Validates: Requirements 12.4**
        
        Property: For any API request with an empty or whitespace-only token,
        the system must reject the request with HTTP 401.
        """
        # Create mock middleware
        mock_auth_middleware = create_mock_auth_middleware()
        
        # Create mock request with empty token
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = path
        mock_request.headers = {'Authorization': f'Bearer {empty_token}'}
        mock_request.state = MagicMock()
        
        # Create mock call_next
        async def call_next(request):
            return Response(content="OK", status_code=200)
        
        # Execute
        response = await mock_auth_middleware(mock_request, call_next)
        
        # Verify: Empty token should be rejected with 401
        assert response.status_code == 401, \
            f"Empty token should be rejected with 401, got {response.status_code}"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        public_path=st.sampled_from([
            '/api/v1/auth/login',
            '/docs',
            '/openapi.json',
            '/redoc',
            '/'
        ])
    )
    async def test_public_paths_bypass_token_validation(self, public_path):
        """
        **Validates: Requirements 12.4**
        
        Property: For any request to public paths (login, docs, etc.),
        the system must allow the request without token validation.
        """
        # Create mock middleware
        mock_auth_middleware = create_mock_auth_middleware()
        
        # Create mock request without Authorization header
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = public_path
        mock_request.headers = {}
        mock_request.state = MagicMock()
        
        # Create mock call_next
        async def call_next(request):
            return Response(content="OK", status_code=200)
        
        # Execute
        response = await mock_auth_middleware(mock_request, call_next)
        
        # Verify: Public paths should not require authentication
        assert response.status_code == 200, \
            f"Public path {public_path} should not require authentication, got {response.status_code}"
        
        # Verify: Token verification should not be called for public paths
        mock_auth_middleware.auth_service.verify_token.assert_not_called()


class TestProperty19SessionExpirationEnforcement:
    """
    Property 19: Session Expiration Enforcement
    
    For any expired user session, subsequent API requests should be rejected
    and require re-authentication.
    
    Validates: Requirements 8.4
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        session_id=session_id_strategy,
        user_id=user_id_strategy,
        email=email_strategy,
        expiration_minutes_ago=st.integers(min_value=1, max_value=120)
    )
    async def test_expired_session_rejected(
        self,
        session_id,
        user_id,
        email,
        expiration_minutes_ago
    ):
        """
        **Validates: Requirements 8.4**
        
        Property: For any session that has expired (expires_at < current_time),
        validation must return None and the session must be deleted.
        """
        # Create mock service
        service, mock_session_ref, _ = create_mock_auth_service()
        
        # Setup: Create expired session data
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'email': email,
            'role': 'analyst',
            'created_at': datetime.utcnow() - timedelta(minutes=expiration_minutes_ago + 60),
            'expires_at': datetime.utcnow() - timedelta(minutes=expiration_minutes_ago),
            'last_activity': datetime.utcnow() - timedelta(minutes=expiration_minutes_ago)
        }
        
        # Mock Firestore get to return expired session
        mock_session_doc = MagicMock()
        mock_session_doc.exists = True
        mock_session_doc.to_dict.return_value = session_data
        mock_session_ref.get.return_value = mock_session_doc
        
        # Execute
        result = await service.validate_session(session_id)
        
        # Verify: Expired session should be rejected
        assert result is None, \
            f"Expired session should return None, got {result}"
        
        # Verify: Session should be deleted
        mock_session_ref.delete.assert_called_once(), \
            "Expired session should be deleted from Firestore"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        session_id=session_id_strategy,
        user_id=user_id_strategy,
        email=email_strategy,
        expires_in_minutes=st.integers(min_value=1, max_value=120)
    )
    async def test_valid_session_accepted(
        self,
        session_id,
        user_id,
        email,
        expires_in_minutes
    ):
        """
        **Validates: Requirements 8.4**
        
        Property: For any session that has not expired (expires_at > current_time),
        validation must return the session data and update last activity.
        """
        # Create mock service
        service, mock_session_ref, _ = create_mock_auth_service()
        
        # Setup: Create valid (non-expired) session data
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'email': email,
            'role': 'analyst',
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(minutes=expires_in_minutes),
            'last_activity': datetime.utcnow()
        }
        
        # Mock Firestore get to return valid session
        mock_session_doc = MagicMock()
        mock_session_doc.exists = True
        mock_session_doc.to_dict.return_value = session_data
        mock_session_ref.get.return_value = mock_session_doc
        
        # Execute
        result = await service.validate_session(session_id)
        
        # Verify: Valid session should be accepted
        assert result is not None, \
            "Valid session should return session data"
        assert result['session_id'] == session_id
        assert result['user_id'] == user_id
        
        # Verify: Last activity should be updated
        mock_session_ref.update.assert_called_once()
        update_call_args = mock_session_ref.update.call_args[0][0]
        assert 'last_activity' in update_call_args, \
            "Session update should include last_activity"
        
        # Verify: Session should NOT be deleted
        mock_session_ref.delete.assert_not_called(), \
            "Valid session should not be deleted"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        token=token_strategy,
        session_id=session_id_strategy,
        user_id=user_id_strategy,
        email=email_strategy,
        expiration_minutes_ago=st.integers(min_value=1, max_value=120),
        path=st.sampled_from([
            '/api/v1/applications',
            '/api/v1/documents',
            '/api/v1/applications/123/analyze'
        ])
    )
    async def test_expired_session_in_middleware_rejected(
        self,
        token,
        session_id,
        user_id,
        email,
        expiration_minutes_ago,
        path
    ):
        """
        **Validates: Requirements 8.4**
        
        Property: For any API request with an expired session,
        the middleware must reject the request and require re-authentication.
        """
        # Create mock middleware
        mock_auth_middleware = create_mock_auth_middleware()
        
        # Setup: Mock valid token but expired session
        decoded_token = {
            'uid': user_id,
            'email': email
        }
        
        mock_auth_middleware.auth_service.verify_token.return_value = decoded_token
        mock_auth_middleware.auth_service.validate_session.return_value = None  # Expired
        
        # Create mock request with expired session
        mock_request = MagicMock(spec=Request)
        mock_request.url.path = path
        mock_request.headers = {
            'Authorization': f'Bearer {token}',
            'X-Session-ID': session_id
        }
        mock_request.state = MagicMock()
        
        # Create mock call_next
        async def call_next(request):
            return Response(content="OK", status_code=200)
        
        # Execute
        response = await mock_auth_middleware(mock_request, call_next)
        
        # Verify: Request should be rejected with 401
        assert response.status_code == 401, \
            f"Expired session should be rejected with 401, got {response.status_code}"
        
        # Verify error message
        import json
        content = json.loads(response.body.decode())
        assert 'error' in content
        assert content['error'] == 'session_expired', \
            f"Error should be 'session_expired', got {content['error']}"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=20, deadline=None)
    @given(
        user_id=user_id_strategy,
        email=email_strategy,
        role=role_strategy,
        session_expiration_minutes=st.integers(min_value=30, max_value=120)
    )
    async def test_session_creation_sets_expiration(
        self,
        user_id,
        email,
        role,
        session_expiration_minutes
    ):
        """
        **Validates: Requirements 8.2, 8.4**
        
        Property: For any created session, the expires_at timestamp
        must be set to created_at + session_expiration_minutes.
        """
        # Create mock service
        service, mock_session_ref, mock_user_ref = create_mock_auth_service()
        
        # Set custom expiration time
        service.session_expiration_minutes = session_expiration_minutes
        
        # Mock user exists
        mock_user_doc = MagicMock()
        mock_user_doc.exists = True
        mock_user_ref.get.return_value = mock_user_doc
        
        # Create decoded token
        decoded_token = {
            'uid': user_id,
            'email': email
        }
        
        # Execute
        before_creation = datetime.utcnow()
        session_data = await service.create_session(
            user_id=user_id,
            decoded_token=decoded_token,
            role=role
        )
        after_creation = datetime.utcnow()
        
        # Verify: Session has expiration set
        assert 'expires_at' in session_data, \
            "Session must have expires_at field"
        
        expires_at = session_data['expires_at']
        created_at = session_data['created_at']
        
        # Verify: Expiration is in the future
        assert expires_at > created_at, \
            "expires_at must be after created_at"
        
        # Verify: Expiration is approximately session_expiration_minutes in the future
        expected_expiration = created_at + timedelta(minutes=session_expiration_minutes)
        time_diff = abs((expires_at - expected_expiration).total_seconds())
        
        assert time_diff < 5, \
            f"Expiration should be {session_expiration_minutes} minutes from creation, " \
            f"but difference is {time_diff} seconds"
        
        # Verify: Expiration is reasonable (not too far in past or future)
        assert before_creation < expires_at < after_creation + timedelta(minutes=session_expiration_minutes + 1), \
            "Expiration time should be reasonable"
