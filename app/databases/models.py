from typing import Optional, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(SQLModel, table=True):
    """User model for authentication and authorization."""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False, max_length=100)
    email: str = Field(index=True, unique=True, nullable=False, max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=255)
    hashed_password: str = Field(nullable=False, max_length=255)
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    sensors: List["Sensor"] = Relationship(back_populates="owner")

    def __repr__(self):
        return f"User(id={self.id}, username={self.username})"

    def verify_password(self, password: str) -> bool:
        """Verify a password against the hash."""
        return pwd_context.verify(password, self.hashed_password)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password for storing."""
        return pwd_context.hash(password)


class Sensor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, nullable=False)
    location: Optional[str] = Field(default=None, nullable=True)
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)

    # Relationships
    records: List["SensorRecord"] = Relationship(back_populates="sensor")
    owner: Optional["User"] = Relationship(back_populates="sensors")

    def __repr__(self):
        return f"Sensor_id:{self.id}"

class SensorRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    value: float = Field(nullable=False)
    sensor_id: int = Field(foreign_key="sensor.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), nullable=False)
    sensor: Optional[Sensor] = Relationship(back_populates="records")

    def __repr__(self):
        return (
            f"SensorRecord value={self.value}, created_at={self.created_at}"
        )