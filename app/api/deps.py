from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.databases.manager import get_db
from app.databases.models import Sensor, User
from app.databases.serializers import SensorRecordCreate
from app.databases.crud import CrudService
from app.core.jwt_service import JWTService

# Security scheme for Bearer token
security = HTTPBearer()

# Token validation dependency
async def verify_token(
        credentials: HTTPAuthorizationCredentials = Security(security),
        session: AsyncSession = Depends(get_db),
) -> User:
    """
    Validates the JWT access token from the Authorization header.
    Returns the authenticated User if valid, raises HTTPException if invalid.
    """
    token = credentials.credentials

    # Decode and verify JWT token
    payload = JWTService.verify_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user ID from token
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    crud = CrudService(session)
    user = await crud.get_user_by_id(int(user_id))

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Inactive user account",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# Get current active user (alias for verify_token for clarity)
async def get_current_user(
        user: User = Depends(verify_token)
) -> User:
    """Get the current authenticated user."""
    return user


# Validates sensor for POST
async def valid_sensor_id(
        item: SensorRecordCreate,
        session: AsyncSession = Depends(get_db),
) -> Sensor:
    sensor = await session.get(Sensor, item.sensor_id)
    if sensor is None:
        raise HTTPException(status_code=404, detail=f"Sensor with id={item.sensor_id} not found.")
    return sensor

# Validates sensor by id for GET/other paths
async def valid_sensor_id_from_path(
        sensor_id: int,
        session: AsyncSession = Depends(get_db),
) -> Sensor:
    sensor = await session.get(Sensor, sensor_id)
    if sensor is None:
        raise HTTPException(status_code=404, detail=f"Sensor with id={sensor_id} not found.")
    return sensor