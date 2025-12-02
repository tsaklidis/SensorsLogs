import logging.config

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.sessions import SessionMiddleware

from sqladmin import Admin

from app.admin.admin import SensorsAdmin, SensorRecordAdmin, UserAdmin, AdminAuth
from app.api import base as api_endpoints
from app.core.config import settings
from app.core.rate_limit import limiter
from app.databases.manager import AsyncDatabaseManager
from app.loggers import LOGGING_CONFIG
from app.middleware import SecurityHeadersMiddleware


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

# SECURITY: Add CORS middleware to control which origins can access the API
# TODO: Update allowed origins with your actual frontend domain(s)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.BASE_URL,
        # "https://yourdomain.com",  # Add your production domain
        # "https://app.yourdomain.com",  # Add your app domain
        # For development only - remove in production:
        "http://localhost:3000",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600,
)

# SECURITY: Add session middleware for admin authentication
# Session secret should be secure and persistent
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.JWT_SECRET_KEY,  # Reuse JWT secret for session encryption
    session_cookie="admin_session",
    max_age=3600,  # 1 hour session timeout
    same_site="lax",
    https_only=False,  # Set to True in production with HTTPS
)

# SECURITY: Add security headers to all responses
app.add_middleware(SecurityHeadersMiddleware)

# Add exception handler and limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.state.limiter = limiter

db_manager = AsyncDatabaseManager()
engine = db_manager.get_engine()

# SECURITY: Create authentication backend for admin panel
authentication_backend = AdminAuth(secret_key=settings.JWT_SECRET_KEY)

# Create admin with authentication
admin = Admin(
    app,
    engine,
    base_url=settings.ADMIN_URL,
    authentication_backend=authentication_backend,
    title="Sensors Admin Panel",
)

# Add model views
admin.add_view(UserAdmin)
admin.add_view(SensorsAdmin)
admin.add_view(SensorRecordAdmin)

logger.info(f"✅ Admin panel secured with authentication at: {settings.ADMIN_URL}")


# Register specific routers FIRST
app.include_router(api_endpoints.api_router)
app.include_router(api_endpoints.health_router)
