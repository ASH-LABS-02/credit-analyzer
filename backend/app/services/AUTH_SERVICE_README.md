# Firebase Authentication Service

## Overview

The `AuthService` provides Firebase Authentication integration for the Intelli-Credit platform, handling user authentication, token validation, session management, and role-based access control.

## Features

### 1. Token Validation
- Verifies Firebase ID tokens
- Handles invalid and expired tokens
- Logs authentication errors

### 2. Session Management
- Creates sessions on successful authentication
- Validates existing sessions
- Checks session expiration (default: 60 minutes)
- Updates last activity timestamps
- Supports session invalidation

### 3. Role-Based Access Control
- Three predefined roles: `admin`, `analyst`, `viewer`
- Permission checking for resources and actions
- Configurable permissions per role

## Usage

### Basic Authentication Flow

```python
from app.services.auth_service import AuthService

auth_service = AuthService()

# 1. Verify Firebase token
decoded_token = await auth_service.verify_token(id_token)

if decoded_token:
    # 2. Create session
    session_data = await auth_service.create_session(
        user_id=decoded_token['uid'],
        decoded_token=decoded_token,
        role='analyst'
    )
    
    # 3. Validate session on subsequent requests
    valid_session = await auth_service.validate_session(session_data['session_id'])
    
    # 4. Check permissions
    has_permission = await auth_service.check_permission(
        session_data=valid_session,
        resource_type='application',
        action='view'
    )
```

### Middleware Integration

The `AuthMiddleware` automatically handles authentication for protected routes:

```python
from fastapi import FastAPI
from app.api.middleware import AuthMiddleware

app = FastAPI()

# Add authentication middleware
auth_middleware = AuthMiddleware()
app.middleware("http")(auth_middleware)
```

### Permission Decorator

Use the `require_permission` decorator to enforce permissions on specific routes:

```python
from fastapi import Request
from app.api.middleware import require_permission

@app.get("/api/v1/applications/{app_id}")
@require_permission("application", "view")
async def get_application(app_id: str, request: Request):
    # Only users with 'view' permission on 'application' can access
    return {"app_id": app_id}
```

## Role Permissions

### Admin Role
- **Application**: view, edit, approve, delete
- **Document**: view, upload, delete
- **CAM**: view, generate, export
- **Monitoring**: view, configure

### Analyst Role
- **Application**: view, edit
- **Document**: view, upload
- **CAM**: view, generate, export
- **Monitoring**: view

### Viewer Role
- **Application**: view
- **Document**: view
- **CAM**: view, export
- **Monitoring**: view

## Session Data Structure

```python
{
    'session_id': 'session_user123_1234567890',
    'user_id': 'user123',
    'email': 'user@example.com',
    'role': 'analyst',
    'created_at': datetime.utcnow(),
    'expires_at': datetime.utcnow() + timedelta(minutes=60),
    'last_activity': datetime.utcnow(),
    'permissions': {
        'application': ['view', 'edit'],
        'document': ['view', 'upload'],
        'cam': ['view', 'generate', 'export'],
        'monitoring': ['view']
    }
}
```

## API Request Flow

### 1. Client Request
```
GET /api/v1/applications/123
Authorization: Bearer <firebase_id_token>
X-Session-ID: session_user123_1234567890 (optional)
```

### 2. Middleware Processing
1. Extract token from Authorization header
2. Verify token with Firebase
3. Check for existing session or create new one
4. Validate session expiration
5. Attach user info to request.state
6. Add session ID to response headers

### 3. Route Handler
```python
@app.get("/api/v1/applications/{app_id}")
@require_permission("application", "view")
async def get_application(app_id: str, request: Request):
    # Access user info from request.state
    user_id = request.state.user_id
    email = request.state.email
    session_data = request.state.session_data
    
    # Process request
    return {"app_id": app_id, "user": email}
```

### 4. Response
```
HTTP/1.1 200 OK
X-Session-ID: session_user123_1234567890
Content-Type: application/json

{"app_id": "123", "user": "user@example.com"}
```

## Error Responses

### 401 Unauthorized
- Missing Authorization header
- Invalid token format
- Invalid or expired token
- Session expired

```json
{
    "error": "authentication_required",
    "message": "Authorization header is missing"
}
```

### 403 Forbidden
- Insufficient permissions

```json
{
    "error": "forbidden",
    "message": "Insufficient permissions to edit application"
}
```

## Configuration

### Session Expiration
Default: 60 minutes

To customize:
```python
auth_service = AuthService()
auth_service.session_expiration_minutes = 120  # 2 hours
```

### Public Paths
Paths that don't require authentication (configured in `AuthMiddleware`):
- `/api/v1/auth/login`
- `/docs`
- `/openapi.json`
- `/redoc`
- `/`

## Firestore Collections

### sessions
```
sessions/{session_id}
  - session_id: string
  - user_id: string
  - email: string
  - role: string
  - created_at: timestamp
  - expires_at: timestamp
  - last_activity: timestamp
  - permissions: map
```

### users
```
users/{user_id}
  - email: string
  - created_at: timestamp
  - last_login: timestamp
  - role: string
```

## Testing

Run authentication tests:
```bash
pytest tests/test_auth_service.py -v
pytest tests/test_auth_middleware.py -v
```

## Requirements Validation

This implementation validates the following requirements:

- **Requirement 8.1**: Firebase Authentication credentials required for system access
- **Requirement 8.2**: Session creation with role-based permissions on successful login
- **Requirement 8.3**: Unauthorized access denied with authentication error
- **Requirement 8.4**: Session expiration requires re-authentication
- **Requirement 8.5**: Role-based access control enforced for viewing, editing, and approving

## Security Considerations

1. **Token Validation**: All tokens are verified with Firebase before creating sessions
2. **Session Expiration**: Sessions automatically expire after configured time
3. **Activity Tracking**: Last activity timestamp updated on each request
4. **Error Logging**: All authentication errors logged for security monitoring
5. **Permission Checks**: Explicit permission checks before sensitive operations
6. **HTTPS Required**: All authentication should occur over HTTPS in production
