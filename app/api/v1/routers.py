import logging
from typing import Optional, List

from fastapi import APIRouter, BackgroundTasks, Request, Query
from fastapi.params import Depends

from app.api.deps import valid_sensor
from app.core.rate_limit import rate_limit_response, limiter
from app.databases.crud import CrudService
from app.databases.manager import get_db

from app.databases.serializers import SensorRecordCreate, SensorRecordRead


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/records", responses=rate_limit_response)
@limiter.limit("30/minute")
async def save_log(request: Request, item: SensorRecordCreate, background_tasks: BackgroundTasks):
    return {"message": "ok"}


@router.get("/records/{sensor_id}", response_model=List[SensorRecordRead])
async def list_records(
        sensor_id: int,
        background_tasks: BackgroundTasks,
        session=Depends(get_db)
):
    crud = CrudService(session)
    records = await crud.get_records_by_sensor_id(sensor_id)
    return records