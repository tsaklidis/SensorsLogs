import logging.config

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from sqladmin import Admin

from app.admin.admin import SensorsAdmin, SensorRecordAdmin
from app.api import base as api_endpoints
from app.core.config import settings
from app.core.rate_limit import limiter
from app.databases.manager import AsyncDatabaseManager
from app.loggers import LOGGING_CONFIG


logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="Sensors Logs",
    description="Save sensors logs API",
    version="1.0.0",
    contact={
        "name": "Stefanos I. Tsaklidis",
        "url": "https://tsaklidis.gr",
    },
    # docs_url=None, redoc_url=None, openapi_url=None
)

# Add exception handler and limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.state.limiter = limiter

db_manager = AsyncDatabaseManager()
engine = db_manager.get_engine()
admin = Admin(
    app,
    engine,
    base_url=settings.ADMIN_URL,
)
admin.add_view(SensorsAdmin)
admin.add_view(SensorRecordAdmin)


# Register specific routers FIRST
app.include_router(api_endpoints.api_router)
app.include_router(api_endpoints.health_router)
