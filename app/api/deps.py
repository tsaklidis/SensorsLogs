from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.databases.manager import get_db
from app.databases.models import Sensor
from app.databases.serializers import SensorRecordCreate


# Validates sensor for POST
async def valid_sensor_id(
        item: SensorRecordCreate,
        session: AsyncSession = Depends(get_db),
) -> Sensor:
    sensor = await session.get(Sensor, item.sensor_id)
    if sensor is None:
        raise HTTPException(status_code=404, detail=f"Sensor with id={item.sensor_id} not found.")
    return sensor

# Validates sensor by id for GET/other paths
async def valid_sensor_id_from_path(
        sensor_id: int,
        session: AsyncSession = Depends(get_db),
) -> Sensor:
    sensor = await session.get(Sensor, sensor_id)
    if sensor is None:
        raise HTTPException(status_code=404, detail=f"Sensor with id={sensor_id} not found.")
    return sensor