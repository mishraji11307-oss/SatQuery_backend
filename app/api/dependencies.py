"""
SatQuery AI - FastAPI Dependencies
Database session, authentication guards, and request tracing.
"""
from typing import Optional, AsyncGenerator
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.models import User
from app.db.repositories.user_repo import UserRepository
from app.core.security import decode_access_token
from app.core.exceptions import AuthenticationError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency verifying Bearer JWT and returning active authenticated User."""
    if not token:
        raise AuthenticationError("Authentication token is required.")

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise AuthenticationError("Invalid or expired authentication token.")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(payload["sub"])
    if not user or not user.is_active:
        raise AuthenticationError("User account is inactive or not found.")

    return user


async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Dependency for endpoints that support both anonymous demo mode and authenticated users."""
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None

    user_repo = UserRepository(db)
    return await user_repo.get_by_id(payload["sub"])
