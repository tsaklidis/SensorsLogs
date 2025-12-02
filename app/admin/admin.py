from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from wtforms import PasswordField
from wtforms.validators import Optional as OptionalValidator

from app.databases.models import Sensor, SensorRecord, User
from app.core.jwt_service import JWTService
from app.core.config import settings
from app.databases.manager import AsyncDatabaseManager
from app.databases.crud import CrudService
import logging

logger = logging.getLogger(__name__)


class AdminAuth(AuthenticationBackend):
    """
    SECURITY: Authentication backend for SQLAdmin panel.
    Requires users to login with valid credentials before accessing admin interface.
    """

    async def login(self, request: Request) -> bool:
        """
        Handle admin login.

        SECURITY: Only users with is_admin=True can access admin panel.

        Args:
            request: The incoming request with form data

        Returns:
            True if authentication successful, False otherwise
        """
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if not username or not password:
            return False

        # Get database session
        db_manager = AsyncDatabaseManager()
        sessionmaker = db_manager.get_sessionmaker()

        async with sessionmaker() as session:
            crud = CrudService(session)

            # Authenticate user
            user = await crud.authenticate_user(username, password)

            # SECURITY: Check if user is active AND is an admin
            if user and user.is_active and user.is_admin:
                # Store user information in session
                request.session.update({
                    "user_id": user.id,
                    "username": user.username,
                    "is_admin": True,
                    "authenticated": True
                })

                logger.info(f"Admin login successful: {username}")
                return True
            else:
                # Log the reason for failure (without exposing to user)
                if user and not user.is_admin:
                    logger.warning(f"Admin login denied - not admin: {username}")
                else:
                    logger.warning(f"Admin login failed: {username}")
                return False

    async def logout(self, request: Request) -> bool:
        """
        Handle admin logout.

        Args:
            request: The incoming request

        Returns:
            True always (logout successful)
        """
        username = request.session.get("username", "unknown")
        request.session.clear()
        logger.info(f"Admin logout: {username}")
        return True

    async def authenticate(self, request: Request) -> bool:
        """
        Check if user is authenticated for accessing admin panel.

        SECURITY: Validates user is active AND has admin privileges.

        Args:
            request: The incoming request

        Returns:
            True if authenticated as admin, False otherwise
        """
        user_id = request.session.get("user_id")
        is_admin = request.session.get("is_admin", False)
        authenticated = request.session.get("authenticated", False)

        if not user_id or not authenticated or not is_admin:
            return False

        # Verify user still exists, is active, and is admin
        db_manager = AsyncDatabaseManager()
        sessionmaker = db_manager.get_sessionmaker()

        async with sessionmaker() as session:
            crud = CrudService(session)
            user = await crud.get_user_by_id(user_id)

            # SECURITY: Check user exists, is active, AND is admin
            if user and user.is_active and user.is_admin:
                return True
            else:
                # User no longer exists, is inactive, or is no longer admin - clear session
                if user and not user.is_admin:
                    logger.warning(f"Admin access revoked - admin privilege removed: {user.username}")
                request.session.clear()
                return False


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, User.email, User.full_name, User.is_active, User.is_admin, User.created_at]
    column_searchable_list = [User.username, User.email]
    column_sortable_list = [User.id, User.username, User.email, User.is_admin, User.created_at]
    column_default_sort = ("id", True)
    column_details_exclude_list = [User.hashed_password]
    form_excluded_columns = [User.hashed_password, User.created_at, User.updated_at, User.sensors]

    can_create = True
    can_edit = True
    can_delete = True

    async def scaffold_form(self, rules=None):
        """Add password field to form."""
        form_class = await super().scaffold_form(rules)

        # Add password field
        form_class.password = PasswordField(
            'Password',
            validators=[OptionalValidator()],
            render_kw={
                "placeholder": "Enter password (required for new users)",
                "autocomplete": "new-password"
            }
        )

        return form_class

    async def on_model_change(self, data, model: User, is_created: bool, request) -> None:
        """Hash the password before saving."""
        password = data.get('password') if isinstance(data, dict) else None

        if password and isinstance(password, str):
            password = password.strip()

        if password:
            # Hash the password and set it on the model
            model.hashed_password = User.hash_password(password)
            # Remove password from data dict so SQLAdmin doesn't try to set it
            if isinstance(data, dict):
                data.pop('password', None)
        elif is_created:
            # For new users, require a password
            if not model.hashed_password:
                raise ValueError("Password is required for new users")

    async def after_model_change(self, data, model: User, is_created: bool, request) -> None:
        """Show instructions after user is created."""
        if is_created:
            # Generate a sample token to show the user
            access_token = JWTService.create_access_token(model.id, model.username)

            instructions = f"""
<div style="background: #e7f3e7; border: 2px solid #4caf50; padding: 15px; border-radius: 5px; margin: 10px 0;">
    <h3 style="color: #2e7d32; margin-top: 0;">✅ User '{model.username}' Created Successfully!</h3>
    
    <p><strong>📝 To get a JWT token, the user must login via API:</strong></p>
    
    <pre style="background: #f5f5f5; padding: 10px; border-radius: 3px; overflow-x: auto;">
curl -X POST "http://localhost:8000/api/v1.0/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{{"username": "{model.username}", "password": "THE_PASSWORD_YOU_ENTERED"}}'
    </pre>
    
    <p><strong>Response will include:</strong></p>
    <ul>
        <li>access_token (expires in {settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES} minutes)</li>
        <li>refresh_token (expires in {settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS} days)</li>
    </ul>
    
    <p><strong>📧 Send these instructions to the user at: {model.email}</strong></p>
    
    <p style="color: #d32f2f;"><strong>⚠️ IMPORTANT:</strong> Make sure to securely communicate the password to the user!</p>
</div>
"""
            # SQLAdmin doesn't support flash messages well, so we'll log it
            print("\n" + "="*80)
            print(f"USER CREATED: {model.username}")
            print(f"Email: {model.email}")
            print(f"User ID: {model.id}")
            print("\nINSTRUCTIONS TO PROVIDE TO USER:")
            print("-" * 80)
            print(f"1. Login to get JWT token:")
            print(f'   curl -X POST "http://localhost:8000/api/v1.0/auth/login" \\')
            print(f'     -H "Content-Type: application/json" \\')
            print(f'     -d \'{{"username": "{model.username}", "password": "YOUR_PASSWORD"}}\'')
            print(f"\n2. Use the returned access_token in API requests:")
            print(f'   Authorization: Bearer <access_token>')
            print("\n3. Sample token for testing (valid for {settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES} minutes):")
            print(f"   {access_token[:50]}...")
            print("="*80 + "\n")



class SensorsAdmin(ModelView, model=Sensor):
    column_list = [Sensor.id, Sensor.name, Sensor.location, Sensor.owner_id]
    column_searchable_list = [Sensor.name]
    column_sortable_list = [Sensor.id, Sensor.name, Sensor.owner_id]
    column_default_sort = ("id", True)


class SensorRecordAdmin(ModelView, model=SensorRecord):
    column_list = [SensorRecord.id, SensorRecord.sensor, SensorRecord.value, SensorRecord.created_at]
    column_sortable_list = [SensorRecord.id, SensorRecord.value, SensorRecord.created_at]
    column_default_sort = ("id", True)
