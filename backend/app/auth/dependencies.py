"""Authenticate identity against the current account and persisted session."""

from dataclasses import dataclass
from uuid import UUID
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db_session
from app.users.models import User
from app.auth.models import AuthSession
from app.auth.service import decode_access_token

security = HTTPBearer(auto_error=False)


def invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


@dataclass(frozen=True)
class AuthContext:
    user: User
    session: AuthSession


async def get_auth_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db_session),
) -> AuthContext:
    if credentials is None:
        raise invalid_credentials()
    try:
        claims = decode_access_token(credentials.credentials)
    except JWTError:
        raise invalid_credentials() from None
    result = await db.execute(
        select(User, AuthSession)
        .join(AuthSession, AuthSession.user_id == User.id)
        .where(
            User.id == UUID(claims["sub"]),
            AuthSession.id == UUID(claims["sid"]),
            User.disabled_at.is_(None),
            User.auth_version == claims["auth_version"],
            AuthSession.auth_version == User.auth_version,
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > func.clock_timestamp(),
        )
        .execution_options(populate_existing=True)
    )
    row = result.one_or_none()
    if row is None:
        raise invalid_credentials()
    return AuthContext(*row)


async def get_current_user(context: AuthContext = Depends(get_auth_context)) -> User:
    return context.user
