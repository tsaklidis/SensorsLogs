"""
Authentication endpoints.

Handles user login and token refresh.
Note: Public registration is disabled for security.
Users must be created by administrators.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.jwt_service import JWTService
from app.core.config import settings
from app.core.rate_limit import limiter, rate_limit_response
from app.databases.crud import CrudService
from app.databases.manager import get_db
from app.databases.serializers import UserLogin, TokenResponse, TokenRefresh


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/login", response_model=TokenResponse, responses=rate_limit_response)
@limiter.limit("5/minute")  # SECURITY: Prevent brute force attacks - only 5 attempts per minute
async def login(
        request: Request,  # Required for rate limiting
        credentials: UserLogin,
        session: AsyncSession = Depends(get_db),
):
    """
    Login with username and password.
    Returns JWT access and refresh tokens.

    SECURITY: Rate limited to 5 attempts per minute to prevent brute force attacks.
    """
    crud = CrudService(session)

    # Authenticate user
    user = await crud.authenticate_user(credentials.username, credentials.password)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last login
    await crud.update_user_last_login(user.id)

    # Generate JWT tokens
    access_token = JWTService.create_access_token(user.id, user.username)
    refresh_token = JWTService.create_refresh_token(user.id, user.username)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse, responses=rate_limit_response)
@limiter.limit("10/minute")  # SECURITY: Rate limit token refresh to prevent abuse
async def refresh_token(
        request: Request,  # Required for rate limiting
        token_refresh: TokenRefresh,
        session: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token.
    Returns new access and refresh tokens.

    SECURITY: Rate limited to 10 attempts per minute.
    """
    # Verify refresh token
    payload = JWTService.verify_refresh_token(token_refresh.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    username = payload.get("username")

    if not user_id or not username:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user still exists and is active
    crud = CrudService(session)
    user = await crud.get_user_by_id(int(user_id))

    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate new tokens
    access_token = JWTService.create_access_token(user.id, user.username)
    refresh_token = JWTService.create_refresh_token(user.id, user.username)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

