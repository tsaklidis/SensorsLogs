import logging

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.databases.models import Sensor, SensorRecord

logger = logging.getLogger(__name__)

class CrudService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_sensor_by_id(self, sensor_id: int) -> Sensor | None:
        return await self.session.get(Sensor, sensor_id)

    async def get_records_by_sensor_id(self, sensor_id: int) -> list[SensorRecord]:
        result = await self.session.execute(
            select(SensorRecord).where(SensorRecord.sensor_id == sensor_id)
        )
        return result.scalars().all()