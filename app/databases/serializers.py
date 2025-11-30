from pydantic import BaseModel, constr, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# User Serializers
class UserCreate(BaseModel):
    username: constr(min_length=3, max_length=100)
    email: EmailStr
    password: constr(min_length=8)  # Minimum 8 characters
    full_name: Optional[str] = None

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