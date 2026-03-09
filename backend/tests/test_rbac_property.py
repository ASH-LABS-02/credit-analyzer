"""
Property-Based Tests for Role-Based Access Control (RBAC)

This module contains property-based tests for RBAC functionality,
validating Property 18 from the design document.

Property 18: Session Creation and Permissions
For any successful user login, the system should create a session with
role-based permissions that correctly enforce access rules for viewing,
editing, and approving applications.

Validates: Requirements 8.2, 8.5
"""

import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from app.services.auth_service import AuthService


# Hypothesis strategies for generating test data
user_id_strategy = st.text(min_size=5, max_size=50, alphabet=st.characters(
    min_codepoint=48, max_codepoint=122,  # 0-9, A-Z, a-z
    blacklist_characters='<>[]{}|\\^`'
))

email_strategy = st.emails()

role_strategy = st.sampled_from(['admin', 'analyst', 'viewer'])

resource_type_strategy = st.sampled_from(['application', 'document', 'cam', 'monitoring'])

action_strategy = st.sampled_from(['view', 'edit', 'approve', 'delete', 'upload', 'generate', 'export', 'configure'])


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
        
        # Mock user exists
        mock_user_doc = MagicMock()
        mock_user_doc.exists = True
        mock_user_ref.get.return_value = mock_user_doc
        
        return service, mock_session_ref, mock_user_ref


class TestProperty18SessionCreationAndPermissions:
    """
    Property 18: Session Creation and Permissions
    
    For any successful user login, the system should create a session with
    role-based permissions that correctly enforce access rules for viewing,
    editing, and approving applications.
    
    Validates: Requirements 8.2, 8.5
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=50, deadline=None)
    @given(
        user_id=user_id_strategy,
        email=email_strategy,
        role=role_strategy
    )
    async def test_session_creation_includes_permissions(self, user_id, email, role):
        """
        **Validates: Requirements 8.2, 8.5**
        
        Property: For any successful login with a valid role,
        the created session must include role-based permissions.
        """
        # Create mock service
        service, mock_session_ref, _ = create_mock_auth_service()
        
        # Create decoded token
        decoded_token = {
            'uid': user_id,
            'email': email,
            'email_verified': True
        }
        
        # Execute
        session_data = await service.create_session(
            user_id=user_id,
            decoded_token=decoded_token,
            role=role
        )
        
        # Verify: Session was created
        assert session_data is not None, "Session should be created"
        
        # Verify: Session includes required fields
        assert 'session_id' in session_data, "Session must have session_id"
        assert 'user_id' in session_data, "Session must have user_id"
        assert 'email' in session_data, "Session must have email"
        assert 'role' in session_data, "Session must have role"
        assert 'permissions' in session_data, "Session must have permissions"
        assert 'created_at' in session_data, "Session must have created_at"
        assert 'expires_at' in session_data, "Session must have expires_at"
        
        # Verify: Session data matches input
        assert session_data['user_id'] == user_id
        assert session_data['email'] == email
        assert session_data['role'] == role
        
        # Verify: Permissions are not empty
        permissions = session_data['permissions']
        assert isinstance(permissions, dict), "Permissions must be a dictionary"
        assert len(permissions) > 0, "Permissions should not be empty"
        
        # Verify: Session was stored in Firestore
        mock_session_ref.set.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=30, deadline=None)
    @given(
        user_id=user_id_strategy,
        email=email_strategy
    )
    async def test_admin_role_has_all_permissions(self, user_id, email):
        """
        **Validates: Requirements 8.5**
        
        Property: For any session with admin role,
        the user must have all permissions (view, edit, approve, delete)
        for all resource types.
        """
        # Create mock service
        service, _, _ = create_mock_auth_service()
        
        decoded_token = {
            'uid': user_id,
            'email': email
        }
        
        # Execute: Create session with admin role
        session_data = await service.create_session(
            user_id=user_id,
            decoded_token=decoded_token,
            role='admin'
        )
        
        permissions = session_data['permissions']
        
        # Verify: Admin has permissions for all resource types
        assert 'application' in permissions, "Admin must have application permissions"
        assert 'document' in permissions, "Admin must have document permissions"
        assert 'cam' in permissions, "Admin must have CAM permissions"
        assert 'monitoring' in permissions, "Admin must have monitoring permissions"
        
        # Verify: Admin has all critical permissions for applications
        app_permissions = permissions['application']
        assert 'view' in app_permissions, "Admin must be able to view applications"
        assert 'edit' in app_permissions, "Admin must be able to edit applications"
        assert 'approve' in app_permissions, "Admin must be able to approve applications"
        assert 'delete' in app_permissions, "Admin must be able to delete applications"
        
        # Verify: Admin can upload and delete documents
        doc_permissions = permissions['document']
        assert 'view' in doc_permissions, "Admin must be able to view documents"
        assert 'upload' in doc_permissions, "Admin must be able to upload documents"
        assert 'delete' in doc_permissions, "Admin must be able to delete documents"
        
        # Verify: Admin can configure monitoring
        monitoring_permissions = permissions['monitoring']
        assert 'configure' in monitoring_permissions, "Admin must be able to configure monitoring"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=30, deadline=None)
    @given(
        user_id=user_id_strategy,
        email=email_strategy
    )
    async def test_analyst_role_has_limited_permissions(self, user_id, email):
        """
        **Validates: Requirements 8.5**
        
        Property: For any session with analyst role,
        the user must have view and edit permissions but NOT approve or delete.
        """
        # Create mock service
        service, _, _ = create_mock_auth_service()
        
        decoded_token = {
            'uid': user_id,
            'email': email
        }
        
        # Execute: Create session with analyst role
        session_data = await service.create_session(
            user_id=user_id,
            decoded_token=decoded_token,
            role='analyst'
        )
        
        permissions = session_data['permissions']
        
        # Verify: Analyst has application permissions
        assert 'application' in permissions, "Analyst must have application permissions"
        app_permissions = permissions['application']
        
        # Verify: Analyst can view and edit
        assert 'view' in app_permissions, "Analyst must be able to view applications"
        assert 'edit' in app_permissions, "Analyst must be able to edit applications"
        
        # Verify: Analyst CANNOT approve or delete
        assert 'approve' not in app_permissions, "Analyst must NOT be able to approve applications"
        assert 'delete' not in app_permissions, "Analyst must NOT be able to delete applications"
        
        # Verify: Analyst can upload documents but not delete
        doc_permissions = permissions['document']
        assert 'view' in doc_permissions, "Analyst must be able to view documents"
        assert 'upload' in doc_permissions, "Analyst must be able to upload documents"
        assert 'delete' not in doc_permissions, "Analyst must NOT be able to delete documents"
        
        # Verify: Analyst can generate and export CAMs
        cam_permissions = permissions['cam']
        assert 'view' in cam_permissions, "Analyst must be able to view CAMs"
        assert 'generate' in cam_permissions, "Analyst must be able to generate CAMs"
        assert 'export' in cam_permissions, "Analyst must be able to export CAMs"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=30, deadline=None)
    @given(
        user_id=user_id_strategy,
        email=email_strategy
    )
    async def test_viewer_role_has_read_only_permissions(self, user_id, email):
        """
        **Validates: Requirements 8.5**
        
        Property: For any session with viewer role,
        the user must have only view permissions (read-only access).
        """
        # Create mock service
        service, _, _ = create_mock_auth_service()
        
        decoded_token = {
            'uid': user_id,
            'email': email
        }
        
        # Execute: Create session with viewer role
        session_data = await service.create_session(
            user_id=user_id,
            decoded_token=decoded_token,
            role='viewer'
        )
        
        permissions = session_data['permissions']
        
        # Verify: Viewer has application permissions
        assert 'application' in permissions, "Viewer must have application permissions"
        app_permissions = permissions['application']
        
        # Verify: Viewer can only view
        assert 'view' in app_permissions, "Viewer must be able to view applications"
        assert 'edit' not in app_permissions, "Viewer must NOT be able to edit applications"
        assert 'approve' not in app_permissions, "Viewer must NOT be able to approve applications"
        assert 'delete' not in app_permissions, "Viewer must NOT be able to delete applications"
        
        # Verify: Viewer can only view documents, not upload or delete
        doc_permissions = permissions['document']
        assert 'view' in doc_permissions, "Viewer must be able to view documents"
        assert 'upload' not in doc_permissions, "Viewer must NOT be able to upload documents"
        assert 'delete' not in doc_permissions, "Viewer must NOT be able to delete documents"
        
        # Verify: Viewer can view and export CAMs but not generate
        cam_permissions = permissions['cam']
        assert 'view' in cam_permissions, "Viewer must be able to view CAMs"
        assert 'export' in cam_permissions, "Viewer must be able to export CAMs"
        assert 'generate' not in cam_permissions, "Viewer must NOT be able to generate CAMs"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=100, deadline=None)
    @given(
        user_id=user_id_strategy,
        email=email_strategy,
        role=role_strategy,
        resource_type=resource_type_strategy,
        action=action_strategy
    )
    async def test_permission_check_enforces_role_rules(
        self,
        user_id,
        email,
        role,
        resource_type,
        action
    ):
        """
        **Validates: Requirements 8.5**
        
        Property: For any session with a given role,
        permission checks must correctly enforce the role's access rules.
        """
        # Create mock service
        service, _, _ = create_mock_auth_service()
        
        decoded_token = {
            'uid': user_id,
            'email': email
        }
        
        # Execute: Create session
        session_data = await service.create_session(
            user_id=user_id,
            decoded_token=decoded_token,
            role=role
        )
        
        # Execute: Check permission
        has_permission = await service.check_permission(
            session_data=session_data,
            resource_type=resource_type,
            action=action
        )
        
        # Verify: Permission check result matches role definition
        permissions = session_data['permissions']
        expected_has_permission = (
            resource_type in permissions and
            action in permissions[resource_type]
        )
        
        assert has_permission == expected_has_permission, \
            f"Permission check for {role} role, {resource_type}.{action} " \
            f"should return {expected_has_permission}, got {has_permission}"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=50, deadline=None)
    @given(
        user_id=user_id_strategy,
        email=email_strategy,
        role=role_strategy
    )
    async def test_permission_check_with_missing_permissions_returns_false(
        self,
        user_id,
        email,
        role
    ):
        """
        **Validates: Requirements 8.5**
        
        Property: For any permission check on a session without permissions field,
        the check must return False (deny access).
        """
        # Create mock service
        service, _, _ = create_mock_auth_service()
        
        # Create session data WITHOUT permissions field
        session_data = {
            'session_id': f'session_{user_id}',
            'user_id': user_id,
            'email': email,
            'role': role
            # Missing 'permissions' field
        }
        
        # Execute: Check permission
        has_permission = await service.check_permission(
            session_data=session_data,
            resource_type='application',
            action='view'
        )
        
        # Verify: Permission check returns False when permissions are missing
        assert has_permission is False, \
            "Permission check must return False when permissions field is missing"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=50, deadline=None)
    @given(
        user_id=user_id_strategy,
        email=email_strategy,
        role=role_strategy
    )
    async def test_permission_check_with_unknown_resource_returns_false(
        self,
        user_id,
        email,
        role
    ):
        """
        **Validates: Requirements 8.5**
        
        Property: For any permission check on an unknown resource type,
        the check must return False (deny access).
        """
        # Create mock service
        service, _, _ = create_mock_auth_service()
        
        decoded_token = {
            'uid': user_id,
            'email': email
        }
        
        # Execute: Create session
        session_data = await service.create_session(
            user_id=user_id,
            decoded_token=decoded_token,
            role=role
        )
        
        # Execute: Check permission for unknown resource type
        has_permission = await service.check_permission(
            session_data=session_data,
            resource_type='unknown_resource_type',
            action='view'
        )
        
        # Verify: Permission check returns False for unknown resource
        assert has_permission is False, \
            "Permission check must return False for unknown resource types"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=50, deadline=None)
    @given(
        user_id=user_id_strategy,
        email=email_strategy,
        role=role_strategy,
        resource_type=resource_type_strategy
    )
    async def test_permission_check_with_unknown_action_returns_false(
        self,
        user_id,
        email,
        role,
        resource_type
    ):
        """
        **Validates: Requirements 8.5**
        
        Property: For any permission check with an unknown action,
        the check must return False (deny access).
        """
        # Create mock service
        service, _, _ = create_mock_auth_service()
        
        decoded_token = {
            'uid': user_id,
            'email': email
        }
        
        # Execute: Create session
        session_data = await service.create_session(
            user_id=user_id,
            decoded_token=decoded_token,
            role=role
        )
        
        # Execute: Check permission for unknown action
        has_permission = await service.check_permission(
            session_data=session_data,
            resource_type=resource_type,
            action='unknown_action_xyz'
        )
        
        # Verify: Permission check returns False for unknown action
        assert has_permission is False, \
            "Permission check must return False for unknown actions"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @settings(max_examples=30, deadline=None)
    @given(
        user_id=user_id_strategy,
        email=email_strategy
    )
    async def test_unknown_role_defaults_to_viewer_permissions(self, user_id, email):
        """
        **Validates: Requirements 8.5**
        
        Property: For any session with an unknown/invalid role,
        the system must default to viewer (most restrictive) permissions.
        """
        # Create mock service
        service, _, _ = create_mock_auth_service()
        
        decoded_token = {
            'uid': user_id,
            'email': email
        }
        
        # Execute: Create session with unknown role
        session_data = await service.create_session(
            user_id=user_id,
            decoded_token=decoded_token,
            role='unknown_role_xyz'
        )
        
        permissions = session_data['permissions']
        
        # Get viewer permissions for comparison
        viewer_permissions = service._get_role_permissions('viewer')
        
        # Verify: Unknown role gets viewer permissions
        assert permissions == viewer_permissions, \
            "Unknown role should default to viewer permissions"
        
        # Verify: Has only view permissions for applications
        app_permissions = permissions.get('application', [])
        assert 'view' in app_permissions, "Should have view permission"
        assert 'edit' not in app_permissions, "Should NOT have edit permission"
        assert 'approve' not in app_permissions, "Should NOT have approve permission"
