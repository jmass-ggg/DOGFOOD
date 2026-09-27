"""Password hashing and identity-only access credentials."""

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from uuid import UUID, uuid4

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


def create_access_token(
    user_id: str, auth_version: int = 1, session_id: str | None = None
) -> str:
    """Production issuance always supplies the persisted session ID."""
    now = datetime.now(timezone.utc)
    return _encode(
        user_id,
        auth_version,
        session_id or str(uuid4()),
        "access",
        now,
        now + timedelta(minutes=get_settings().jwt_access_token_expire_minutes),
    )


def create_refresh_token(
    user_id: str,
    auth_version: int,
    session_id: str,
    generation: int,
    expires_at: datetime,
) -> str:
    return _encode(
        user_id,
        auth_version,
        session_id,
        "refresh",
        datetime.now(timezone.utc),
        expires_at,
        generation,
    )


def _encode(user_id, auth_version, session_id, kind, now, expiry, generation=None):
    settings = get_settings()
    if type(auth_version) is not int or auth_version < 1:
        raise ValueError("Invalid auth version")
    payload = dict(
        sub=str(UUID(user_id)),
        sid=str(UUID(session_id)),
        exp=expiry,
        iat=now,
        type=kind,
        auth_version=auth_version,
        iss=settings.jwt_issuer,
        aud=settings.jwt_audience,
    )
    if generation is not None:
        if type(generation) is not int or not 0 <= generation < 2**63:
            raise ValueError("Invalid generation")
        payload["generation"] = generation
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str) -> dict:
    return _decode(token, "access")


def decode_refresh_token(token: str) -> dict:
    return _decode(token, "refresh")


def _decode(token: str, expected_type: str) -> dict:
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
            payload.get("type") != expected_type
            or type(payload.get("auth_version")) is not int
            or payload["auth_version"] < 1
            or type(payload.get("exp")) is not int
            or type(payload.get("iat")) is not int
            or payload["exp"] <= now
            or payload["iat"] > now
            or payload["exp"] <= payload["iat"]
        ):
            raise JWTError("Invalid credential claims")
        UUID(payload["sub"])
        UUID(payload["sid"])
        if expected_type == "refresh" and (
            type(payload.get("generation")) is not int
            or not 0 <= payload["generation"] < 2**63
        ):
            raise JWTError("Invalid refresh generation")
        return payload
    except (ValueError, TypeError, AttributeError, KeyError, OverflowError) as exc:
        raise JWTError("Invalid credential claims") from exc
