"""Authenticate identity by validating access claims and current account state."""

from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db_session
from app.users.models import User
from app.auth.service import decode_access_token

security = HTTPBearer(auto_error=False)


def invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    if credentials is None:
        raise invalid_credentials()
    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError:
        raise invalid_credentials() from None
    result = await db.execute(
        select(User)
        .where(User.id == UUID(payload["sub"]))
        .execution_options(populate_existing=True)
    )
    user = result.scalar_one_or_none()
    if (
        user is None
        or user.disabled_at is not None
        or user.auth_version != payload["auth_version"]
    ):
        raise invalid_credentials()
    return user
