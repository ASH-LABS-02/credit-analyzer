"""
Unit tests for JWT-based AuthService (SQLite3 migration).

Tests password hashing, JWT token creation/validation, and user authentication.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
from app.services.auth_service import AuthService


@pytest.fixture
def auth_service():
    """Create an AuthService instance for testing"""
    return AuthService(secret_key="test_secret_key_12345", access_token_expire_minutes=30)


class TestPasswordHashing:
    """Tests for password hashing and verification"""
    
    def test_hash_password(self, auth_service):
        """Test password hashing produces a bcrypt hash"""
        password = "mypassword123"
        hashed = auth_service.hash_password(password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")  # bcrypt hash prefix
        assert hashed != password  # Hash should not equal plain password
    
    def test_hash_password_different_hashes(self, auth_service):
        """Test that hashing the same password twice produces different hashes"""
        password = "mypassword123"
        hash1 = auth_service.hash_password(password)
        hash2 = auth_service.hash_password(password)
        
        # Bcrypt uses salt, so hashes should be different
        assert hash1 != hash2
    
    def test_verify_password_correct(self, auth_service):
        """Test verifying a correct password"""
        password = "mypassword123"
        hashed = auth_service.hash_password(password)
        
        result = auth_service.verify_password(password, hashed)
        
        assert result is True
    
    def test_verify_password_incorrect(self, auth_service):
        """Test verifying an incorrect password"""
        password = "mypassword123"
        wrong_password = "wrongpassword"
        hashed = auth_service.hash_password(password)
        
        result = auth_service.verify_password(wrong_password, hashed)
        
        assert result is False
    
    def test_verify_password_empty_string(self, auth_service):
        """Test verifying an empty password"""
        password = "mypassword123"
        hashed = auth_service.hash_password(password)
        
        result = auth_service.verify_password("", hashed)
        
        assert result is False


class TestJWTTokenCreation:
    """Tests for JWT token creation"""
    
    def test_create_access_token(self, auth_service):
        """Test creating a JWT access token"""
        data = {"sub": "user123", "email": "test@example.com"}
        token = auth_service.create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_with_custom_expiration(self, auth_service):
        """Test creating a token with custom expiration"""
        data = {"sub": "user123"}
        expires_delta = timedelta(minutes=60)
        token = auth_service.create_access_token(data, expires_delta=expires_delta)
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_create_access_token_includes_expiration(self, auth_service):
        """Test that created token includes expiration claim"""
        data = {"sub": "user123"}
        token = auth_service.create_access_token(data)
        
        # Decode to verify expiration is included
        payload = auth_service.decode_access_token(token)
        
        assert "exp" in payload
        assert isinstance(payload["exp"], int)


class TestJWTTokenDecoding:
    """Tests for JWT token decoding and validation"""
    
    def test_decode_access_token(self, auth_service):
        """Test decoding a valid JWT token"""
        data = {"sub": "user123", "email": "test@example.com"}
        token = auth_service.create_access_token(data)
        
        payload = auth_service.decode_access_token(token)
        
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["email"] == "test@example.com"
        assert "exp" in payload
    
    def test_decode_access_token_invalid(self, auth_service):
        """Test decoding an invalid token raises ValueError"""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(ValueError) as exc_info:
            auth_service.decode_access_token(invalid_token)
        
        assert "Invalid token" in str(exc_info.value)
    
    def test_decode_access_token_expired(self, auth_service):
        """Test decoding an expired token raises ValueError"""
        data = {"sub": "user123"}
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = auth_service.create_access_token(data, expires_delta=expires_delta)
        
        with pytest.raises(ValueError) as exc_info:
            auth_service.decode_access_token(token)
        
        assert "Invalid token" in str(exc_info.value)
    
    def test_decode_access_token_wrong_secret(self):
        """Test decoding a token with wrong secret raises ValueError"""
        auth_service1 = AuthService(secret_key="secret1")
        auth_service2 = AuthService(secret_key="secret2")
        
        data = {"sub": "user123"}
        token = auth_service1.create_access_token(data)
        
        with pytest.raises(ValueError) as exc_info:
            auth_service2.decode_access_token(token)
        
        assert "Invalid token" in str(exc_info.value)


class TestUserAuthentication:
    """Tests for user authentication"""
    
    def test_authenticate_user_valid(self, auth_service):
        """Test authenticating a user with valid credentials"""
        # Create a mock user with hashed password
        user = Mock()
        user.hashed_password = auth_service.hash_password("password123")
        
        result = auth_service.authenticate_user(user, "password123")
        
        assert result is True
    
    def test_authenticate_user_invalid_password(self, auth_service):
        """Test authenticating a user with invalid password"""
        # Create a mock user with hashed password
        user = Mock()
        user.hashed_password = auth_service.hash_password("password123")
        
        result = auth_service.authenticate_user(user, "wrongpassword")
        
        assert result is False
    
    def test_authenticate_user_none(self, auth_service):
        """Test authenticating when user is None"""
        result = auth_service.authenticate_user(None, "password123")
        
        assert result is False
    
    def test_authenticate_user_empty_password(self, auth_service):
        """Test authenticating with empty password"""
        user = Mock()
        user.hashed_password = auth_service.hash_password("password123")
        
        result = auth_service.authenticate_user(user, "")
        
        assert result is False


class TestTokenRoundTrip:
    """Tests for complete token creation and validation flow"""
    
    def test_token_round_trip(self, auth_service):
        """Test creating and decoding a token preserves data"""
        original_data = {
            "sub": "user123",
            "email": "test@example.com",
            "role": "analyst"
        }
        
        # Create token
        token = auth_service.create_access_token(original_data)
        
        # Decode token
        decoded_data = auth_service.decode_access_token(token)
        
        # Verify original data is preserved
        assert decoded_data["sub"] == original_data["sub"]
        assert decoded_data["email"] == original_data["email"]
        assert decoded_data["role"] == original_data["role"]
    
    def test_authentication_flow(self, auth_service):
        """Test complete authentication flow"""
        # 1. Hash password for storage
        password = "securepassword123"
        hashed_password = auth_service.hash_password(password)
        
        # 2. Create mock user
        user = Mock()
        user.id = "user123"
        user.email = "test@example.com"
        user.hashed_password = hashed_password
        
        # 3. Authenticate user
        is_authenticated = auth_service.authenticate_user(user, password)
        assert is_authenticated is True
        
        # 4. Create access token
        token_data = {"sub": user.id, "email": user.email}
        token = auth_service.create_access_token(token_data)
        
        # 5. Decode and validate token
        decoded = auth_service.decode_access_token(token)
        assert decoded["sub"] == user.id
        assert decoded["email"] == user.email


class TestAuthServiceConfiguration:
    """Tests for AuthService configuration"""
    
    def test_custom_algorithm(self):
        """Test creating AuthService with custom algorithm"""
        auth_service = AuthService(
            secret_key="test_secret",
            algorithm="HS512"
        )
        
        assert auth_service.algorithm == "HS512"
        
        # Verify token creation works with custom algorithm
        token = auth_service.create_access_token({"sub": "user123"})
        payload = auth_service.decode_access_token(token)
        assert payload["sub"] == "user123"
    
    def test_custom_expiration_time(self):
        """Test creating AuthService with custom expiration time"""
        auth_service = AuthService(
            secret_key="test_secret",
            access_token_expire_minutes=60
        )
        
        assert auth_service.access_token_expire_minutes == 60
