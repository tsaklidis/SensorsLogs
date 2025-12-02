from typing import Optional, List
from datetime import datetime, timezone

import bcrypt
from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    """User model for authentication and authorization."""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False, max_length=100)
    email: str = Field(index=True, unique=True, nullable=False, max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=255)
    hashed_password: str = Field(nullable=False, max_length=255)
    is_active: bool = Field(default=True, nullable=False)
    is_admin: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # SECURITY: Account lockout fields to prevent brute force attacks
    failed_login_attempts: int = Field(default=0, nullable=False)
    locked_until: Optional[datetime] = Field(default=None, nullable=True)
    last_failed_login: Optional[datetime] = Field(default=None, nullable=True)

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

    def is_locked(self) -> bool:
        """
        Check if account is currently locked due to failed login attempts.

        SECURITY: Prevents brute force attacks by temporarily locking accounts.
        """
        if self.locked_until is None:
            return False

        # Check if lockout period has expired
        now = datetime.now(timezone.utc)
        locked_until_aware = self.locked_until.replace(tzinfo=timezone.utc) if self.locked_until.tzinfo is None else self.locked_until

        return now < locked_until_aware

    def get_lockout_time_remaining(self) -> int:
        """
        Get remaining lockout time in seconds.
        Returns 0 if not locked.
        """
        if not self.is_locked():
            return 0

        now = datetime.now(timezone.utc)
        locked_until_aware = self.locked_until.replace(tzinfo=timezone.utc) if self.locked_until.tzinfo is None else self.locked_until

        remaining = (locked_until_aware - now).total_seconds()
        return max(0, int(remaining))


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