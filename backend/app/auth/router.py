"""FastAPI router for authentication endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db_session
from app.users.models import User
from app.auth import schemas
from app.auth.service import hash_password, verify_password, create_access_token
from app.auth.dependencies import get_current_user


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED
)
async def register(
    request: schemas.UserRegisterRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Register a new user account.
    
    Args:
        request: User registration data
        db: Database session
        
    Returns:
        Created user information (no password hash)
        
    Raises:
        HTTPException: 409 if email already exists
    """
    # Normalize email
    email_normalized = request.email.lower().strip()
    
    # Check if email already exists
    result = await db.execute(
        select(func.count())
        .select_from(User)
        .where(func.lower(func.btrim(User.email)) == email_normalized)
    )
    if result.scalar() > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = hash_password(request.password)
    
    # Create user
    user = User(
        email=request.email,
        username=request.username,
        password_hash=password_hash,
        full_name=request.full_name,
        country=request.country
    )
    
    db.add(user)
    await db.flush()
    await db.refresh(user)
    
    return schemas.UserResponse.model_validate(user)


@router.post("/login", response_model=schemas.LoginResponse)
async def login(
    request: schemas.UserLoginRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Authenticate and log in a user.
    
    TODO: Integration point for refresh token issuance.
    Advanced token management is handled by the security layer.
    
    Args:
        request: User login credentials
        db: Database session
        
    Returns:
        Access token and user information
        
    Raises:
        HTTPException: 401 if credentials are invalid or account is disabled
    """
    # Normalize email
    email_normalized = request.email.lower().strip()
    
    # Look up user
    result = await db.execute(
        select(User).where(func.lower(func.btrim(User.email)) == email_normalized)
    )
    user = result.scalar_one_or_none()
    
    # Verify credentials (use generic error message)
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is disabled
    if user.disabled_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled"
        )
    
    # Create access token
    access_token = create_access_token(str(user.id))
    
    return schemas.LoginResponse(
        access_token=access_token,
        user=schemas.UserResponse.model_validate(user)
    )


@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user's information.
    
    Args:
        current_user: Authenticated user from dependency
        
    Returns:
        Current user information (no password hash)
    """
    return schemas.UserResponse.model_validate(current_user)
