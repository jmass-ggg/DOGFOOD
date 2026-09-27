"""Authentication service functions for password hashing and JWT token management."""

from datetime import datetime, timedelta, timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import jwt
from app.config import get_settings


# Initialize Argon2 password hasher
_ph = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a password using Argon2.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Argon2 password hash
    """
    return _ph.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a password against an Argon2 hash.
    
    Args:
        plain_password: Plain text password to verify
        password_hash: Stored Argon2 hash
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        _ph.verify(password_hash, plain_password)
        return True
    except VerifyMismatchError:
        return False


def create_access_token(user_id: str) -> str:
    """Create a basic JWT access token for a user.
    
    NOTE: This is the integration point for the advanced security layer.
    Refresh tokens, token families, and invalidation are NOT implemented here.
    
    Args:
        user_id: User ID to encode in token
        
    Returns:
        JWT access token string
    """
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    
    to_encode = {
        "sub": user_id,
        "exp": expire
    }
    
    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT access token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        jose.JWTError: If token is invalid or expired
    """
    settings = get_settings()
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm]
    )
