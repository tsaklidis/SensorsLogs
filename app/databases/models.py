from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.orm import relationship
import bcrypt


class User(SQLModel, table=True):
    """User model for authentication and authorization."""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False, max_length=100)
    email: str = Field(index=True, unique=True, nullable=False, max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=255)
    hashed_password: str = Field(nullable=False, max_length=255)
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    sensors: List["Sensor"] = Relationship(back_populates="owner")

    def __repr__(self):
        return f"User(id={self.id}, username={self.username})"

    def verify_password(self, password: str) -> bool:
        """
        Verify a password against the hash.

        SECURITY: Bcrypt automatically truncates passwords to 72 bytes.
        This is handled in the UserCreate validator.
        """
        # Truncate password to 72 bytes for bcrypt
        password_bytes = password.encode('utf-8')[:72]
        # Bcrypt expects bytes for both password and hash
        return bcrypt.checkpw(password_bytes, self.hashed_password.encode('utf-8'))

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password for storing. Returns string hash.

        SECURITY: Bcrypt automatically truncates passwords to 72 bytes.
        Password validation should be done before calling this method.
        """
        # Truncate password to 72 bytes for bcrypt
        password_bytes = password.encode('utf-8')[:72]
        # Generate salt and hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        # Return as string for database storage
        return hashed.decode('utf-8')


class Sensor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, nullable=False)
    location: Optional[str] = Field(default=None, nullable=True)
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)

    # Relationships
    records: List["SensorRecord"] = Relationship(
        back_populates="sensor",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    owner: Optional["User"] = Relationship(back_populates="sensors")

    def __repr__(self):
        return f"Sensor_id:{self.id}"

class SensorRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    value: float = Field(nullable=False)
    sensor_id: int = Field(foreign_key="sensor.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    sensor: Optional[Sensor] = Relationship(back_populates="records")

    def __repr__(self):
        return (
            f"SensorRecord value={self.value}, created_at={self.created_at}"
        )