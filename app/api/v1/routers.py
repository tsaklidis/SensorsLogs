import logging
from typing import List
from fastapi import APIRouter, BackgroundTasks, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import valid_sensor_id, valid_sensor_id_from_path, get_current_user
from app.core.rate_limit import rate_limit_response, limiter
from app.core.jwt_service import JWTService
from app.core.config import settings
from app.databases.crud import CrudService
from app.databases.manager import get_db
from app.databases.models import Sensor, User
from app.databases.serializers import (
    SensorRecordCreate, SensorRecordRead,
    UserCreate, UserRead, UserLogin, TokenResponse, TokenRefresh
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Authentication Endpoints
@router.post("/auth/register", response_model=TokenResponse, status_code=201)
async def register(
        user_in: UserCreate,
        session: AsyncSession = Depends(get_db),
):
    """
    Register a new user.
    Returns JWT access and refresh tokens.
    """
    crud = CrudService(session)

    # Check if username already exists
    existing_user = await crud.get_user_by_username(user_in.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Check if email already exists
    existing_email = await crud.get_user_by_email(user_in.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user = await crud.create_user(user_in)

    # Generate JWT tokens
    access_token = JWTService.create_access_token(user.id, user.username)
    refresh_token = JWTService.create_refresh_token(user.id, user.username)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/auth/login", response_model=TokenResponse)
async def login(
        credentials: UserLogin,
        session: AsyncSession = Depends(get_db),
):
    """
    Login with username and password.
    Returns JWT access and refresh tokens.
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

@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(
        token_refresh: TokenRefresh,
        session: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token.
    Returns new access and refresh tokens.
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

# User Management Endpoints
@router.get("/users/me", response_model=UserRead)
async def get_current_user_info(
        current_user: User = Depends(get_current_user),
):
    """Get current authenticated user information."""
    return current_user


# Sensor Record Endpoints
@router.post("/records", response_model=SensorRecordRead, responses=rate_limit_response)
@limiter.limit("30/minute")
async def save_log(
        request: Request,
        item: SensorRecordCreate,
        background_tasks: BackgroundTasks,
        sensor: Sensor = Depends(valid_sensor_id),  # validates and returns Sensor using DB session
        session: AsyncSession = Depends(get_db),    # ensures DB session available for CRUD
        current_user: User = Depends(get_current_user),  # validates authentication token and returns user
):
    """Save a sensor record. User must own the sensor or sensor must have no owner."""
    # Check if sensor belongs to user or has no owner
    if sensor.owner_id is not None and sensor.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to add records to this sensor"
        )

    crud = CrudService(session)
    record = await crud.add_sensor_record(item)
    return record

@router.get("/records/{sensor_id}", response_model=List[SensorRecordRead])
async def list_records(
        sensor_id: int,
        background_tasks: BackgroundTasks,
        sensor: Sensor = Depends(valid_sensor_id_from_path),  # checks if sensor exists
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),  # validates authentication token and returns user
):
    """List sensor records. User must own the sensor or sensor must have no owner."""
    # Check if sensor belongs to user or has no owner
    if sensor.owner_id is not None and sensor.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to view this sensor's records"
        )

    crud = CrudService(session)
    records = await crud.get_records_by_sensor_id(sensor_id)
    return records
