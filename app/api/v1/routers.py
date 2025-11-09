import logging
from fastapi import APIRouter, BackgroundTasks, Request

from app.core.rate_limit import rate_limit_response, limiter

from app.databases.serializers import SensorRecordCreate


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/record", responses=rate_limit_response)
@limiter.limit("30/minute")
async def save_log(request: Request, item: SensorRecordCreate, background_tasks: BackgroundTasks):
    return {"message": "ok"}


