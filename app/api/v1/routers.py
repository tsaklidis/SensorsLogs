"""
API v1.0 router configuration.

Aggregates all v1.0 endpoints from individual router modules.
"""
import logging
from fastapi import APIRouter

from app.api.v1 import auth, users, sensors, records


logger = logging.getLogger(__name__)

router = APIRouter()

# Include sub-routers with appropriate prefixes and tags
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(sensors.router, prefix="/sensors", tags=["Sensors"])
router.include_router(records.router, prefix="/records", tags=["Records"])
