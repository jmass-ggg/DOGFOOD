"""Password hashing and identity-only access credentials."""

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from uuid import UUID

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError
from jose import JWTError, jwt

from app.config import get_settings

_ph = PasswordHasher(type=Type.ID)
# One hash per worker, then the same verification path as an existing account.
# This reduces timing differences; it does not promise constant HTTP latency.
DUMMY_PASSWORD_HASH = _ph.hash(token_urlsafe(32))


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return _ph.verify(password_hash, plain_password)
    except (VerificationError, InvalidHashError):
        return False


def create_access_token(user_id: str, auth_version: int = 1) -> str:
    """Callers issuing user credentials must supply the loaded auth_version."""
    settings = get_settings()
    if type(auth_version) is not int or auth_version < 1:
        raise ValueError("Invalid auth version")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(UUID(user_id)),
        "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
        "iat": now,
        "type": "access",
        "auth_version": auth_version,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={
                "require_exp": True,
                "require_sub": True,
                "require_iat": True,
                "require_iss": True,
                "require_aud": True,
            },
        )
        now = datetime.now(timezone.utc).timestamp()
        if (
            payload.get("type") != "access"
            or type(payload.get("auth_version")) is not int
            or payload["auth_version"] < 1
            or type(payload.get("exp")) is not int
            or type(payload.get("iat")) is not int
            or payload["exp"] <= now
            or payload["iat"] > now
            or payload["exp"] <= payload["iat"]
        ):
            raise JWTError("Invalid access claims")
        UUID(payload["sub"])
        return payload
    except (ValueError, TypeError, AttributeError, KeyError) as exc:
        raise JWTError("Invalid access claims") from exc
