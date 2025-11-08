import logging
from fastapi import APIRouter, BackgroundTasks, Request

from app.core.rate_limit import rate_limit_response, limiter

from app.databases.serializers import SensorRecordRead


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/minify", responses=rate_limit_response)
@limiter.limit("30/minute")
async def save_log(request: Request, item: SensorRecordRead, background_tasks: BackgroundTasks):
    return {"message": "ok"}


