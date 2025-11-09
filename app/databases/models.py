from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class Sensor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, nullable=False)
    location: Optional[str] = Field(default=None, nullable=True)
    records: List["SensorRecord"] = Relationship(back_populates="sensor")

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