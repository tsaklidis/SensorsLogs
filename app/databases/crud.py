import logging
from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
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
        """Authenticate a user by username and password."""
        user = await self.get_user_by_username(username)
        if not user:
            return None
        if not user.verify_password(password):
            return None
        if not user.is_active:
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
