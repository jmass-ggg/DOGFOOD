"""Authentication endpoints; account-wide logout uses existing auth_version."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool

from app.core.database import get_db_session
from app.users.models import User
from app.auth import schemas
from app.auth.service import (
    DUMMY_PASSWORD_HASH,
    hash_password,
    verify_password,
    create_access_token,
)
from app.auth.dependencies import get_current_user, invalid_credentials

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
    return schemas.LoginResponse(
        access_token=create_access_token(str(user.id), user.auth_version),
        user=schemas.UserResponse.model_validate(user),
    )


@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    response: Response, current_user: User = Depends(get_current_user)
):
    response.headers["Cache-Control"] = "no-store"
    return schemas.UserResponse.model_validate(current_user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Invalidate ALL previously issued credentials for this account, not one session."""
    result = await db.execute(
        update(User)
        .where(
            User.id == current_user.id,
            User.auth_version == current_user.auth_version,
            User.disabled_at.is_(None),
        )
        .values(auth_version=User.auth_version + 1)
    )
    if result.rowcount != 1:
        await db.rollback()
        raise invalid_credentials()
    await db.commit()
    return Response(status_code=204, headers={"Cache-Control": "no-store"})
