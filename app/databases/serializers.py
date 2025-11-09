from pydantic import BaseModel, constr
from typing import Optional, List
from datetime import datetime

class SensorRecordCreate(BaseModel):
    value: float
    sensor_id: int

class SensorRecordRead(BaseModel):
    value: float
    created_at: datetime

    class Config:
        from_attributes = True

class SensorCreate(BaseModel):
    name: constr(min_length=1)
    location: Optional[str] = None

class SensorRead(BaseModel):
    id: int
    name: constr(min_length=1)
    location: Optional[str] = None
    records: List[SensorRecordRead] = []

    class Config:
        from_attributes = True