from pydantic import BaseModel, constr, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
import math


# User Serializers
class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=100)
    email: EmailStr
    password: constr(min_length=12)  # SECURITY: Increased from 8 to 12 characters minimum
    full_name: Optional[str] = None

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """SECURITY: Enforce strong password policy."""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character')
        # SECURITY: Bcrypt truncates at 72 bytes - enforce limit
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password is too long (maximum 72 bytes for bcrypt)')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class UserRead(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    """Response containing JWT tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires

class TokenRefresh(BaseModel):
    """Request to refresh access token."""
    refresh_token: str


# Sensor Record Serializers
class SensorRecordCreate(BaseModel):
    value: float
    sensor_id: int

    @field_validator('value')
    @classmethod
    def validate_finite_value(cls, v):
        """SECURITY: Prevent NaN and Infinity values that could corrupt data."""
        if not math.isfinite(v):
            raise ValueError('Sensor value must be a finite number (not NaN or Infinity)')
        return v

class SensorRecordRead(BaseModel):
    value: float
    created_at: datetime

    class Config:
        from_attributes = True

class SensorCreate(BaseModel):
    name: constr(min_length=1, max_length=255)
    location: Optional[str] = Field(None, max_length=255)

class SensorRead(BaseModel):
    id: int
    name: str
    location: Optional[str] = None
    owner_id: Optional[int] = None

    class Config:
        from_attributes = True

class SensorReadWithRecords(BaseModel):
    """Sensor with all its records."""
    id: int
    name: str
    location: Optional[str] = None
    owner_id: Optional[int] = None
    records: List[SensorRecordRead] = []

    class Config:
        from_attributes = True