import logging

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.databases.manager import DatabaseManager
from app.databases.models import Sensor, SensorRecord

logger = logging.getLogger(__name__)


db_manager = DatabaseManager()

class CrudService:
    def __init__(self, session: AsyncSession | None = None):
        self.session = session or db_manager.get_session()

    async def get_sensor_by_id(self, sensor_id: int) -> Sensor | None:
        return await self.session.get(Sensor, sensor_id)

    async def get_records_by_sensor_id(self, sensor_id: int) -> list[SensorRecord]:
        results = await self.session.exec(
            select(SensorRecord).where(Sensor.id == sensor_id)
        )

        return [record for record in results.all()]
