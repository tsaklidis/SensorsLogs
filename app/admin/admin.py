from sqladmin import ModelView

from app.databases.models import Sensor, SensorRecord, User


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, User.email, User.full_name, User.is_active, User.created_at]
    column_searchable_list = [User.username, User.email]
    column_sortable_list = [User.id, User.username, User.email, User.created_at]
    column_default_sort = ("id", True)
    column_details_exclude_list = [User.api_token]  # Don't show token in details
    form_excluded_columns = [User.api_token, User.created_at, User.updated_at]  # Don't edit these

    can_create = True
    can_edit = True
    can_delete = True


class SensorsAdmin(ModelView, model=Sensor):
    column_list = [Sensor.id, Sensor.name, Sensor.location, Sensor.owner_id]
    column_searchable_list = [Sensor.name]
    column_sortable_list = [Sensor.id, Sensor.name, Sensor.owner_id]
    column_default_sort = ("id", True)


class SensorRecordAdmin(ModelView, model=SensorRecord):
    column_list = [SensorRecord.id, SensorRecord.sensor, SensorRecord.value, SensorRecord.created_at]
    column_sortable_list = [SensorRecord.id, SensorRecord.value, SensorRecord.created_at]
    column_default_sort = ("id", True)
