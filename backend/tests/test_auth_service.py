"""
Unit tests for AuthService

Tests token validation, session management, and permission checking.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from app.services.auth_service import AuthService


@pytest.fixture
def auth_service():
    """Create an AuthService instance with mocked dependencies"""
    with patch('app.services.auth_service.get_auth_client') as mock_auth, \
         patch('app.services.auth_service.get_firestore_client') as mock_db, \
         patch('app.services.auth_service.ErrorLogger') as mock_logger:
        
        service = AuthService()
        service.auth_client = mock_auth.return_value
        service.db = mock_db.return_value
        service.error_logger = mock_logger.return_value
        service.error_logger.log_error = AsyncMock()
        
        yield service


@pytest.fixture
def valid_decoded_token():
    """Sample valid decoded token"""
    return {
        'uid': 'user123',
        'email': 'test@example.com',
        'email_verified': True,
        'iat': int(datetime.utcnow().timestamp()),
        'exp': int((datetime.utcnow() + timedelta(hours=1)).timestamp())
    }


@pytest.mark.asyncio
class TestTokenVerification:
    """Tests for token verification"""
    
    async def test_verify_valid_token(self, auth_service, valid_decoded_token):
        """Test verifying a valid token"""
        # Mock successful token verification
        auth_service.auth_client.verify_id_token = Mock(return_value=valid_decoded_token)
        
        result = await auth_service.verify_token("valid_token")
        
        assert result is not None
        assert result['uid'] == 'user123'
        assert result['email'] == 'test@example.com'
        auth_service.auth_client.verify_id_token.assert_called_once_with("valid_token")
    
    async def test_verify_invalid_token(self, auth_service):
        """Test verifying an invalid token"""
        # Mock invalid token error
        auth_service.auth_client.verify_id_token = Mock(
            side_effect=ValueError("Invalid token")
        )
        
        result = await auth_service.verify_token("invalid_token")
        
        assert result is None
        assert auth_service.error_logger.log_error.called
    
    async def test_verify_expired_token(self, auth_service):
        """Test verifying an expired token"""
        # Mock expired token error
        auth_service.auth_client.verify_id_token = Mock(
            side_effect=ValueError("Token expired")
        )
        
        result = await auth_service.verify_token("expired_token")
        
        assert result is None
        assert auth_service.error_logger.log_error.called
    
    async def test_verify_token_unknown_error(self, auth_service):
        """Test handling unknown errors during token verification"""
        # Mock unknown error
        auth_service.auth_client.verify_id_token = Mock(
            side_effect=Exception("Unknown error")
        )
        
        result = await auth_service.verify_token("token")
        
        assert result is None
        assert auth_service.error_logger.log_error.called


@pytest.mark.asyncio
class TestSessionManagement:
    """Tests for session creation and management"""
    
    async def test_create_session(self, auth_service, valid_decoded_token):
        """Test creating a new session"""
        # Mock Firestore operations
        mock_session_ref = MagicMock()
        auth_service.db.collection.return_value.document.return_value = mock_session_ref
        
        mock_user_ref = MagicMock()
        mock_user_doc = MagicMock()
        mock_user_doc.exists = True
        mock_user_ref.get.return_value = mock_user_doc
        
        # Setup collection mock to return different refs for sessions and users
        def collection_side_effect(name):
            mock_collection = MagicMock()
            if name == 'sessions':
                mock_collection.document.return_value = mock_session_ref
            elif name == 'users':
                mock_collection.document.return_value = mock_user_ref
            return mock_collection
        
        auth_service.db.collection.side_effect = collection_side_effect
        
        session_data = await auth_service.create_session(
            user_id='user123',
            decoded_token=valid_decoded_token,
            role='analyst'
        )
        
        assert session_data is not None
        assert session_data['user_id'] == 'user123'
        assert session_data['email'] == 'test@example.com'
        assert session_data['role'] == 'analyst'
        assert 'session_id' in session_data
        assert 'created_at' in session_data
        assert 'expires_at' in session_data
        assert 'permissions' in session_data
        
        # Verify session was stored
        mock_session_ref.set.assert_called_once()
    
    async def test_validate_valid_session(self, auth_service):
        """Test validating a valid, non-expired session"""
        session_id = "session_user123_123456"
        session_data = {
            'session_id': session_id,
            'user_id': 'user123',
            'email': 'test@example.com',
            'role': 'analyst',
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(minutes=30),
            'last_activity': datetime.utcnow()
        }
        
        # Mock Firestore get
        mock_session_ref = MagicMock()
        mock_session_doc = MagicMock()
        mock_session_doc.exists = True
        mock_session_doc.to_dict.return_value = session_data
        mock_session_ref.get.return_value = mock_session_doc
        
        auth_service.db.collection.return_value.document.return_value = mock_session_ref
        
        result = await auth_service.validate_session(session_id)
        
        assert result is not None
        assert result['session_id'] == session_id
        assert result['user_id'] == 'user123'
        
        # Verify last activity was updated
        mock_session_ref.update.assert_called_once()
    
    async def test_validate_expired_session(self, auth_service):
        """Test validating an expired session"""
        session_id = "session_user123_123456"
        session_data = {
            'session_id': session_id,
            'user_id': 'user123',
            'expires_at': datetime.utcnow() - timedelta(minutes=10)  # Expired
        }
        
        # Mock Firestore get
        mock_session_ref = MagicMock()
        mock_session_doc = MagicMock()
        mock_session_doc.exists = True
        mock_session_doc.to_dict.return_value = session_data
        mock_session_ref.get.return_value = mock_session_doc
        
        auth_service.db.collection.return_value.document.return_value = mock_session_ref
        
        result = await auth_service.validate_session(session_id)
        
        assert result is None
        # Verify session was deleted
        mock_session_ref.delete.assert_called_once()
    
    async def test_validate_nonexistent_session(self, auth_service):
        """Test validating a session that doesn't exist"""
        session_id = "nonexistent_session"
        
        # Mock Firestore get returning no document
        mock_session_ref = MagicMock()
        mock_session_doc = MagicMock()
        mock_session_doc.exists = False
        mock_session_ref.get.return_value = mock_session_doc
        
        auth_service.db.collection.return_value.document.return_value = mock_session_ref
        
        result = await auth_service.validate_session(session_id)
        
        assert result is None
    
    async def test_invalidate_session(self, auth_service):
        """Test invalidating a session"""
        session_id = "session_user123_123456"
        
        # Mock Firestore delete
        mock_session_ref = MagicMock()
        auth_service.db.collection.return_value.document.return_value = mock_session_ref
        
        result = await auth_service.invalidate_session(session_id)
        
        assert result is True
        mock_session_ref.delete.assert_called_once()


@pytest.mark.asyncio
class TestPermissions:
    """Tests for permission checking"""
    
    async def test_check_permission_admin_has_all_permissions(self, auth_service):
        """Test that admin role has all permissions"""
        session_data = {
            'user_id': 'admin123',
            'role': 'admin',
            'permissions': auth_service._get_role_permissions('admin')
        }
        
        # Admin should have all permissions
        assert await auth_service.check_permission(session_data, 'application', 'view')
        assert await auth_service.check_permission(session_data, 'application', 'edit')
        assert await auth_service.check_permission(session_data, 'application', 'approve')
        assert await auth_service.check_permission(session_data, 'application', 'delete')
        assert await auth_service.check_permission(session_data, 'document', 'upload')
        assert await auth_service.check_permission(session_data, 'cam', 'generate')
    
    async def test_check_permission_analyst_limited_permissions(self, auth_service):
        """Test that analyst role has limited permissions"""
        session_data = {
            'user_id': 'analyst123',
            'role': 'analyst',
            'permissions': auth_service._get_role_permissions('analyst')
        }
        
        # Analyst should have view and edit, but not approve or delete
        assert await auth_service.check_permission(session_data, 'application', 'view')
        assert await auth_service.check_permission(session_data, 'application', 'edit')
        assert not await auth_service.check_permission(session_data, 'application', 'approve')
        assert not await auth_service.check_permission(session_data, 'application', 'delete')
    
    async def test_check_permission_viewer_read_only(self, auth_service):
        """Test that viewer role has read-only permissions"""
        session_data = {
            'user_id': 'viewer123',
            'role': 'viewer',
            'permissions': auth_service._get_role_permissions('viewer')
        }
        
        # Viewer should only have view permissions
        assert await auth_service.check_permission(session_data, 'application', 'view')
        assert not await auth_service.check_permission(session_data, 'application', 'edit')
        assert not await auth_service.check_permission(session_data, 'application', 'approve')
        assert not await auth_service.check_permission(session_data, 'document', 'upload')
    
    async def test_check_permission_unknown_role_defaults_to_viewer(self, auth_service):
        """Test that unknown roles default to viewer permissions"""
        permissions = auth_service._get_role_permissions('unknown_role')
        viewer_permissions = auth_service._get_role_permissions('viewer')
        
        assert permissions == viewer_permissions
    
    async def test_check_permission_missing_permissions(self, auth_service):
        """Test permission check with missing permissions in session data"""
        session_data = {
            'user_id': 'user123',
            'role': 'analyst'
            # Missing 'permissions' key
        }
        
        result = await auth_service.check_permission(session_data, 'application', 'view')
        
        # Should return False when permissions are missing
        assert result is False


@pytest.mark.asyncio
class TestRolePermissions:
    """Tests for role-based permission definitions"""
    
    def test_get_role_permissions_admin(self, auth_service):
        """Test admin role permissions"""
        permissions = auth_service._get_role_permissions('admin')
        
        assert 'application' in permissions
        assert 'approve' in permissions['application']
        assert 'delete' in permissions['application']
        assert 'monitoring' in permissions
        assert 'configure' in permissions['monitoring']
    
    def test_get_role_permissions_analyst(self, auth_service):
        """Test analyst role permissions"""
        permissions = auth_service._get_role_permissions('analyst')
        
        assert 'application' in permissions
        assert 'view' in permissions['application']
        assert 'edit' in permissions['application']
        assert 'approve' not in permissions['application']
        assert 'delete' not in permissions['application']
    
    def test_get_role_permissions_viewer(self, auth_service):
        """Test viewer role permissions"""
        permissions = auth_service._get_role_permissions('viewer')
        
        assert 'application' in permissions
        assert 'view' in permissions['application']
        assert 'edit' not in permissions['application']
        assert 'document' in permissions
        assert 'view' in permissions['document']
        assert 'upload' not in permissions['document']
