import logging
from datetime import datetime, timedelta, timezone

import bcrypt
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.databases.models import Sensor, SensorRecord, User
from app.databases.serializers import SensorRecordCreate, UserCreate, SensorCreate

logger = logging.getLogger(__name__)

class CrudService:
    def __init__(self, session: AsyncSession):
        self.session = session

    # User methods
    async def get_user_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        return await self.session.get(User, user_id)

    async def get_user_by_username(self, username: str) -> User | None:
        """Get user by username."""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def create_user(self, user_in: UserCreate) -> User:
        """Create a new user with hashed password."""
        user = User(
            username=user_in.username,
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=User.hash_password(user_in.password),
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def authenticate_user(self, username: str, password: str) -> User | None:
        """
        Authenticate a user by username and password.

        SECURITY:
        - Uses constant-time comparison to prevent timing attacks
        - Checks account lockout status to prevent brute force

        Returns None if:
        - User doesn't exist
        - Password is incorrect
        - User is not active
        - Account is locked due to failed attempts
        """

        user = await self.get_user_by_username(username)

        # SECURITY: Check if account is locked
        if user and user.is_locked():
            logger.warning(f"Login attempt on locked account: username={username}")
            # Still perform password verification for timing consistency
            user.verify_password(password)
            return None

        # SECURITY: Always verify password even if user doesn't exist
        # This prevents timing attacks that reveal valid usernames
        if user:
            password_valid = user.verify_password(password)
        else:
            # Perform fake hash verification to maintain constant time
            # This makes invalid username attempts take the same time as valid ones
            fake_hash = bcrypt.hashpw(b"dummy_password", bcrypt.gensalt()).decode('utf-8')
            try:
                bcrypt.checkpw(password.encode('utf-8')[:72], fake_hash.encode('utf-8'))
            except Exception:
                pass
            password_valid = False

        # Only return user if all checks pass
        if not user or not password_valid or not user.is_active:
            return None

        return user

    async def update_user_last_login(self, user_id: int) -> User | None:
        """Update user's last login timestamp."""
        user = await self.get_user_by_id(user_id)
        if user:
            user.updated_at = datetime.utcnow()
            await self.session.commit()
            await self.session.refresh(user)
        return user

    async def record_failed_login(self, username: str) -> None:
        """
        Record a failed login attempt and lock account if threshold exceeded.

        SECURITY: Prevents brute force attacks by locking accounts after
        multiple failed attempts.
        """

        user = await self.get_user_by_username(username)
        if not user:
            # Don't reveal if username exists - timing attack protection
            return

        now = datetime.now(timezone.utc)

        # Check if we should reset the counter (no failures for a while)
        if user.last_failed_login:
            last_failed_aware = user.last_failed_login.replace(tzinfo=timezone.utc) if user.last_failed_login.tzinfo is None else user.last_failed_login
            time_since_last_failure = (now - last_failed_aware).total_seconds() / 60

            if time_since_last_failure > settings.FAILED_ATTEMPTS_RESET_MINUTES:
                # Reset counter if enough time has passed
                user.failed_login_attempts = 0

        # Increment failed attempts
        user.failed_login_attempts += 1
        user.last_failed_login = now

        # Lock account if threshold exceeded
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.locked_until = now + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
            logger.warning(
                f"Account locked due to {user.failed_login_attempts} failed login attempts: "
                f"username={user.username}, locked_until={user.locked_until}"
            )
        else:
            logger.info(
                f"Failed login attempt {user.failed_login_attempts}/{settings.MAX_LOGIN_ATTEMPTS}: "
                f"username={user.username}"
            )

        await self.session.commit()
        await self.session.refresh(user)

    async def reset_failed_login_attempts(self, user_id: int) -> None:
        """
        Reset failed login attempts counter after successful login.

        SECURITY: Clears lockout state on successful authentication.
        """
        user = await self.get_user_by_id(user_id)
        if user:
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_failed_login = None
            await self.session.commit()
            await self.session.refresh(user)
            logger.info(f"Reset failed login attempts for user: {user.username}")

    # Sensor methods
    async def get_sensor_by_id(self, sensor_id: int) -> Sensor | None:
        return await self.session.get(Sensor, sensor_id)

    async def get_records_by_sensor_id(self, sensor_id: int) -> list[SensorRecord]:
        result = await self.session.execute(
            select(SensorRecord).where(SensorRecord.sensor_id == sensor_id)
        )
        return result.scalars().all()

    async def add_sensor_record(self, record_in: SensorRecordCreate) -> SensorRecord:
        # Convert Pydantic input to SQLModel ORM instance
        record = SensorRecord(**record_in.model_dump())
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    # Sensor CRUD operations
    async def create_sensor(self, sensor_in: SensorCreate, user_id: int) -> Sensor:
        """Create a new sensor owned by the user."""
        sensor = Sensor(
            name=sensor_in.name,
            location=sensor_in.location,
            owner_id=user_id
        )
        self.session.add(sensor)
        await self.session.commit()
        await self.session.refresh(sensor)
        return sensor

    async def get_sensors_by_user(self, user_id: int) -> list[Sensor]:
        """Get all sensors owned by a user."""
        result = await self.session.execute(
            select(Sensor).where(Sensor.owner_id == user_id)
        )
        return result.scalars().all()

    async def delete_sensor(self, sensor_id: int, user_id: int) -> bool:
        """Delete a sensor if it belongs to the user. Returns True if deleted, False if not found."""
        sensor = await self.get_sensor_by_id(sensor_id)
        if not sensor or sensor.owner_id != user_id:
            return False

        await self.session.delete(sensor)
        await self.session.commit()
        return True
