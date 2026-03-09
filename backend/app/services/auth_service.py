"""
JWT-based Authentication Service for SQLite3 migration.

This service replaces Firebase Authentication with JWT-based authentication,
providing password hashing, token generation/validation, and user authentication.
"""

from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import jwt, JWTError


class AuthService:
    """
    Service for JWT-based authentication.
    
    Provides password hashing with bcrypt, JWT token creation and validation,
    and user authentication methods. This replaces Firebase Authentication
    as part of the SQLite3 migration.
    """
    
    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30
    ):
        """
        Initialize the AuthService.
        
        Args:
            secret_key: Secret key for JWT token signing
            algorithm: JWT signing algorithm (default: HS256)
            access_token_expire_minutes: Token expiration time in minutes (default: 30)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Bcrypt hashed password string
            
        Example:
            >>> auth_service = AuthService(secret_key="secret")
            >>> hashed = auth_service.hash_password("mypassword123")
            >>> hashed.startswith("$2b$")
            True
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Bcrypt hashed password to verify against
            
        Returns:
            True if password matches hash, False otherwise
            
        Example:
            >>> auth_service = AuthService(secret_key="secret")
            >>> hashed = auth_service.hash_password("mypassword123")
            >>> auth_service.verify_password("mypassword123", hashed)
            True
            >>> auth_service.verify_password("wrongpassword", hashed)
            False
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Dictionary of claims to encode in the token
            expires_delta: Optional custom expiration time delta
            
        Returns:
            Encoded JWT token string
            
        Example:
            >>> auth_service = AuthService(secret_key="secret")
            >>> token = auth_service.create_access_token({"sub": "user123"})
            >>> isinstance(token, str)
            True
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def decode_access_token(self, token: str) -> dict:
        """
        Decode and validate a JWT access token.
        
        Args:
            token: JWT token string to decode
            
        Returns:
            Dictionary of decoded token claims
            
        Raises:
            ValueError: If token is invalid or expired
            
        Example:
            >>> auth_service = AuthService(secret_key="secret")
            >>> token = auth_service.create_access_token({"sub": "user123"})
            >>> payload = auth_service.decode_access_token(token)
            >>> payload["sub"]
            'user123'
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")
    
    def authenticate_user(self, user, password: str) -> bool:
        """
        Authenticate a user with password verification.
        
        This method verifies that the provided password matches the user's
        hashed password. It expects a user object with a hashed_password attribute.
        
        Args:
            user: User object with hashed_password attribute (or None)
            password: Plain text password to verify
            
        Returns:
            True if user exists and password is correct, False otherwise
            
        Example:
            >>> from unittest.mock import Mock
            >>> auth_service = AuthService(secret_key="secret")
            >>> user = Mock()
            >>> user.hashed_password = auth_service.hash_password("password123")
            >>> auth_service.authenticate_user(user, "password123")
            True
            >>> auth_service.authenticate_user(user, "wrongpassword")
            False
            >>> auth_service.authenticate_user(None, "password123")
            False
        """
        if not user:
            return False
        if not self.verify_password(password, user.hashed_password):
            return False
        return True
