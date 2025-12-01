"""
Sensor management endpoints.

Handles sensor creation, listing, and deletion.
"""
import logging
from typing import List
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.rate_limit import rate_limit_response, limiter
from app.databases.crud import CrudService
from app.databases.manager import get_db
from app.databases.models import User
from app.databases.redis import invalidate_sensor_cache
from app.databases.serializers import SensorCreate, SensorRead


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=SensorRead, status_code=201, responses=rate_limit_response)
@limiter.limit("30/minute")
async def create_sensor(
        request: Request,
        sensor_in: SensorCreate,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    """
    Create a new sensor.
    The sensor is automatically assigned to the authenticated user.
    """
    crud = CrudService(session)
    sensor = await crud.create_sensor(sensor_in, current_user.id)
    return sensor


@router.get("", response_model=List[SensorRead])
async def list_my_sensors(
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    """
    List all sensors owned by the authenticated user.
    """
    crud = CrudService(session)
    sensors = await crud.get_sensors_by_user(current_user.id)
    return sensors


@router.delete("/{sensor_id}", status_code=204)
async def delete_sensor(
        sensor_id: int,
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    """
    Delete a sensor.
    Only the owner can delete their sensor.
    Invalidates all cached data for the sensor.
    """
    crud = CrudService(session)
    deleted = await crud.delete_sensor(sensor_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Sensor not found or you don't have permission to delete it"
        )

    # Invalidate cache
    await invalidate_sensor_cache(sensor_id)

    return None

