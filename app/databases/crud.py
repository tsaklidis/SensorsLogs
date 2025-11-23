import logging

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.databases.models import Sensor, SensorRecord
from app.databases.serializers import SensorRecordCreate

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

    async def add_sensor_record(self, record_in: SensorRecordCreate) -> SensorRecord:
        # Convert Pydantic input to SQLModel ORM instance
        record = SensorRecord(**record_in.model_dump())
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record