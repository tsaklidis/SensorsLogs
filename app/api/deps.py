from fastapi import Path, HTTPException
from app.databases.crud import get_sensor_by_id

async def valid_sensor(sensor_id: int = Path(...)):
    sensor = await get_sensor_by_id(sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return sensor