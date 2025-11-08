from sqladmin import ModelView

from app.databases.models import Sensor, SensorRecord


class SensorsAdmin(ModelView, model=Sensor):
    column_list = [Sensor.id, Sensor.name, SensorRecord.id, Sensor.name]
    column_default_sort = ("id", True)

class SensorRecordAdmin(ModelView, model=SensorRecord):
    column_list = [SensorRecord.id, SensorRecord.sensor_id, SensorRecord.value]
    column_default_sort = ("id", True)
