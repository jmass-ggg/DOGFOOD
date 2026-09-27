"""Session lifecycle transactions. Lock order: user, then session(s)."""

from datetime import timedelta
from uuid import UUID
from jose import JWTError
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.models import AuthSession
from app.auth.dependencies import invalid_credentials
from app.auth.service import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.auth.schemas import LoginResponse, UserResponse
from app.config import get_settings
from app.users.models import User


def credentials(user: User, session: AuthSession) -> LoginResponse:
    return LoginResponse(
        access_token=create_access_token(
            str(user.id), user.auth_version, str(session.id)
        ),
        refresh_token=create_refresh_token(
            str(user.id),
            user.auth_version,
            str(session.id),
            session.generation,
            session.expires_at,
        ),
        user=UserResponse.model_validate(user),
    )


async def locked_user(db, user_id):
    return await db.scalar(
        select(User)
        .where(User.id == user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


async def open_session(db: AsyncSession, user: User) -> LoginResponse:
    # Snapshot values before populate_existing reloads the identity map.
    verified_hash, verified_version = user.password_hash, user.auth_version
    user = await locked_user(db, user.id)
    if (
        user is None
        or user.disabled_at is not None
        or user.password_hash != verified_hash
        or user.auth_version != verified_version
    ):
        await db.rollback()
        raise invalid_credentials()
    now = await db.scalar(select(func.clock_timestamp()))
    session = AuthSession(
        user_id=user.id,
        auth_version=user.auth_version,
        expires_at=now + timedelta(days=get_settings().jwt_refresh_token_expire_days),
    )
    db.add(session)
    await db.flush()
    result = credentials(user, session)
    await db.commit()
    return result


async def lock_current(db, user_id, session_id, version):
    user = await locked_user(db, user_id)
    session = await db.scalar(
        select(AuthSession)
        .where(AuthSession.id == session_id, AuthSession.user_id == user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    now = await db.scalar(select(func.clock_timestamp()))
    if (
        user is None
        or session is None
        or user.disabled_at is not None
        or user.auth_version != version
        or session.auth_version != version
        or session.revoked_at is not None
        or session.expires_at <= now
    ):
        await db.rollback()
        raise invalid_credentials()
    return user, session, now


async def rotate(db: AsyncSession, token: str) -> LoginResponse:
    try:
        claims = decode_refresh_token(token)
    except JWTError:
        raise invalid_credentials() from None
    user, session, now = await lock_current(
        db, UUID(claims["sub"]), UUID(claims["sid"]), claims["auth_version"]
    )
    # Recheck signed expiry after lock acquisition. Sliding lifetime is not used.
    if claims["exp"] <= now.timestamp() or claims["exp"] != int(
        session.expires_at.timestamp()
    ):
        await db.rollback()
        raise invalid_credentials()
    if claims["generation"] != session.generation:
        session.revoked_at = now
        # Persist replay revocation BEFORE raising; dependency cleanup must not undo it.
        await db.commit()
        raise invalid_credentials()
    if session.generation == 2**63 - 1:
        session.revoked_at = now
        await db.commit()
        raise invalid_credentials()
    session.generation += 1
    await db.flush()
    result = credentials(user, session)
    await db.commit()
    return result


async def revoke(db: AsyncSession, user_id, session_id, version, *, all_sessions=False):
    user, session, now = await lock_current(db, user_id, session_id, version)
    if all_sessions:
        user.auth_version += 1
        await db.execute(
            update(AuthSession)
            .where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
    else:
        session.revoked_at = now
    await db.commit()
