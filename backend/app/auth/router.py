"""Authentication endpoints with persisted rotating sessions."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool

from app.core.database import get_db_session
from app.users.models import User
from app.auth import schemas
from app.auth.service import (
    DUMMY_PASSWORD_HASH,
    hash_password,
    verify_password,
)
from app.auth.dependencies import get_current_user, get_auth_context, AuthContext
from app.auth import sessions

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: schemas.UserRegisterRequest, db: AsyncSession = Depends(get_db_session)
):
    user = User(
        email=request.email,
        username=request.username,
        password_hash=await run_in_threadpool(hash_password, request.password),
        full_name=request.full_name,
        country=request.country,
    )
    db.add(user)
    try:
        await db.flush()
        await db.refresh(user)
        result = schemas.UserResponse.model_validate(user)
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        name = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
        if name in {"uq_users_email", "uq_users_username"}:
            field = "Email" if name == "uq_users_email" else "Username"
            raise HTTPException(
                status_code=409, detail=f"{field} already registered"
            ) from None
        raise
    return result


@router.post("/login", response_model=schemas.LoginResponse)
async def login(
    request: schemas.UserLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(User).where(User.email_key == func.lower(func.btrim(request.email)))
    )
    user = result.scalar_one_or_none()
    valid = await run_in_threadpool(
        verify_password,
        request.password,
        user.password_hash if user is not None else DUMMY_PASSWORD_HASH,
    )
    if user is None or not valid or user.disabled_at is not None:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return await sessions.open_session(db, user)


@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    response: Response, current_user: User = Depends(get_current_user)
):
    response.headers["Cache-Control"] = "no-store"
    return schemas.UserResponse.model_validate(current_user)


@router.post("/refresh", response_model=schemas.LoginResponse)
async def refresh(
    request: schemas.RefreshRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return await sessions.rotate(db, request.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    context: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db_session),
):
    """Revoke this session only, including its previously issued access tokens."""
    await sessions.revoke(
        db, context.user.id, context.session.id, context.user.auth_version
    )
    return Response(status_code=204, headers={"Cache-Control": "no-store"})


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    context: AuthContext = Depends(get_auth_context),
    db: AsyncSession = Depends(get_db_session),
):
    await sessions.revoke(
        db,
        context.user.id,
        context.session.id,
        context.user.auth_version,
        all_sessions=True,
    )
    return Response(status_code=204, headers={"Cache-Control": "no-store"})
