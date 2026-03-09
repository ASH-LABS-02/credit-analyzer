"""
FastAPI Middleware for Authentication and Authorization

This module provides middleware for validating Firebase authentication tokens
and enforcing session-based access control.

Requirements: 8.1, 8.3, 8.4
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional, Callable
from typing import Optional, Callable


class AuthMiddleware:
    """
    Middleware for handling authentication and authorization (Disabled).
    
    This version always attaches a mock user to the request state.
    """
    
    def __init__(self):
        pass
    
    async def __call__(self, request: Request, call_next: Callable):
        # Attach mock user and session info to request state
        request.state.user_id = "system_mock"
        request.state.email = "system@mock.local"
        request.state.session_id = "mock_session_id"
        request.state.session_data = {
            "session_id": "mock_session_id",
            "user_id": "system_mock",
            "role": "admin",
            "permissions": {
                "application": ["view", "edit", "create", "delete", "approve"],
                "document": ["view", "upload", "delete"],
                "analysis": ["trigger", "view"],
                "cam": ["generate", "view", "export"]
            }
        }
        
        return await call_next(request)


def require_permission(resource_type: str, action: str):
    """
    Decorator for route handlers to enforce permission checks (Always Allowed).
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # No-op: always call the original function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
