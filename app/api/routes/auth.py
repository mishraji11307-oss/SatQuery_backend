"""
SatQuery AI - Authentication API Endpoints
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.repositories.user_repo import UserRepository
from app.db.models import User
from app.schemas.response import APIResponse
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    AuthMeResponse,
)
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.core.exceptions import AuthenticationError, SatQueryException
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=APIResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def register_user(
    req: UserRegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Registers a new user analyst account."""
    user_repo = UserRepository(db)
    existing = await user_repo.get_by_email(req.email)
    if existing:
        raise SatQueryException(
            message=f"User with email '{req.email}' already exists.",
            code="USER_ALREADY_EXISTS",
            status_code=status.HTTP_409_CONFLICT
        )

    user = await user_repo.create(
        email=req.email,
        password=req.password,
        full_name=req.full_name
    )

    request_id = getattr(request.state, "request_id", "unknown")
    return APIResponse(
        success=True,
        data=UserResponse.model_validate(user),
        request_id=request_id
    )


@router.post("/login", response_model=APIResponse[TokenResponse])
async def login_user(
    req: UserLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Authenticates analyst credentials and generates JWT bearer token."""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(req.email)
    if not user or not verify_password(req.password, user.hashed_password):
        raise AuthenticationError("Incorrect email or password.")

    if not user.is_active:
        raise AuthenticationError("User account is disabled.")

    access_token = create_access_token(
        data={"sub": user.id, "email": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    request_id = getattr(request.state, "request_id", "unknown")
    return APIResponse(
        success=True,
        data=TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        ),
        request_id=request_id
    )


@router.get("/me", response_model=APIResponse[AuthMeResponse])
async def get_current_user_profile(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Returns profile for currently authenticated analyst."""
    request_id = getattr(request.state, "request_id", "unknown")
    return APIResponse(
        success=True,
        data=AuthMeResponse(user=UserResponse.model_validate(current_user)),
        request_id=request_id
    )
