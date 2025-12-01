"""
Sensor record endpoints.

Handles creating and listing sensor measurements/records.
"""
import logging
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, BackgroundTasks, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    valid_sensor_id,
    valid_sensor_id_from_path,
    get_current_user,
    save_record_to_db
)
from app.core.rate_limit import rate_limit_response, limiter
from app.databases.crud import CrudService
from app.databases.manager import get_db
from app.databases.models import Sensor, User
from app.databases.redis import (
    cache_sensor_record,
    get_cached_sensor_records_list,
    cache_sensor_records_list,
    invalidate_sensor_cache
)
from app.databases.serializers import SensorRecordCreate, SensorRecordRead


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=SensorRecordRead, status_code=201, responses=rate_limit_response)
@limiter.limit("60/minute")
async def create_record(
        request: Request,
        item: SensorRecordCreate,
        background_tasks: BackgroundTasks,
        sensor: Sensor = Depends(valid_sensor_id),
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    """
    Save a sensor record with Redis caching.

    Flow:
    1. Validate permissions
    2. Cache value in Redis (fast response)
    3. Save to database in background
    """
    # Check permissions
    if sensor.owner_id is not None and sensor.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to add records to this sensor"
        )

    # Create timestamp
    timestamp = datetime.now(timezone.utc)

    # Cache in Redis immediately (fast response)
    await cache_sensor_record(
        sensor_id=item.sensor_id,
        value=item.value,
        timestamp=timestamp.isoformat()
    )

    # Invalidate records list cache
    await invalidate_sensor_cache(item.sensor_id)

    # Save to database in background
    background_tasks.add_task(save_record_to_db, session, item)

    # Return cached response immediately
    return SensorRecordRead(
        value=item.value,
        created_at=timestamp
    )


@router.get("/{sensor_id}", response_model=List[SensorRecordRead])
async def list_records(
        sensor_id: int,
        background_tasks: BackgroundTasks,
        sensor: Sensor = Depends(valid_sensor_id_from_path),
        session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    """
    List sensor records with Redis caching.

    Flow:
    1. Check cache for records
    2. If cache miss, fetch from database
    3. Cache results for future requests
    """
    # Check permissions
    if sensor.owner_id is not None and sensor.owner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to view this sensor's records"
        )

    # Try to get from cache first
    cached_records = await get_cached_sensor_records_list(sensor_id)

    if cached_records is not None:
        # Cache hit - return cached data
        return [SensorRecordRead(**record) for record in cached_records]

    # Cache miss - fetch from database
    crud = CrudService(session)
    records = await crud.get_records_by_sensor_id(sensor_id)

    # Convert to dict for caching
    records_data = [
        {"value": r.value, "created_at": r.created_at}
        for r in records
    ]

    # Cache results in background
    background_tasks.add_task(
        cache_sensor_records_list,
        sensor_id,
        records_data
    )

    return records

