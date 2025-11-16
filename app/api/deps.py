from fastapi import Depends, HTTPException
from app.databases.manager import get_db
from app.databases.crud import CrudService

async def valid_sensor(sensor_id: int, session=Depends(get_db)):
    crud = CrudService(session)
    sensor = await crud.get_sensor_by_id(sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return sensor