import logging
from typing import Optional, List

from fastapi import APIRouter, BackgroundTasks, Request, Query
from fastapi.params import Depends

from app.api.deps import valid_sensor
from app.core.rate_limit import rate_limit_response, limiter
from app.databases.crud import get_records_by_sensor_id
from app.databases.models import Sensor

from app.databases.serializers import SensorRecordCreate, SensorRecordRead


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/records", responses=rate_limit_response)
@limiter.limit("30/minute")
async def save_log(request: Request, item: SensorRecordCreate, background_tasks: BackgroundTasks):
    return {"message": "ok"}


@router.get("/records/{sensor_id}", response_model=List[SensorRecordRead], responses=rate_limit_response)
@limiter.limit("30/minute")
async def list_records(
        request: Request,
        background_tasks: BackgroundTasks,
        sensor: Sensor = Depends(valid_sensor)
):
    records = await get_records_by_sensor_id(sensor.id)
    return records