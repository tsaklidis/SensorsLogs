from sqladmin import ModelView
from wtforms import PasswordField, Form
from wtforms.validators import Optional as OptionalValidator

from app.databases.models import Sensor, SensorRecord, User


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.username, User.email, User.full_name, User.is_active, User.created_at]
    column_searchable_list = [User.username, User.email]
    column_sortable_list = [User.id, User.username, User.email, User.created_at]
    column_default_sort = ("id", True)
    column_details_exclude_list = [User.hashed_password]
    form_excluded_columns = [User.hashed_password, User.created_at, User.updated_at, User.sensors]

    can_create = True
    can_edit = True
    can_delete = True

    async def scaffold_form(self, rules=None):
        """Add password field to form."""
        form_class = await super().scaffold_form(rules)

        # Add password field
        form_class.password = PasswordField(
            'Password',
            validators=[OptionalValidator()],
            render_kw={
                "placeholder": "Enter password (required for new users)",
                "autocomplete": "new-password"
            }
        )

        return form_class

    async def on_model_change(self, data, model: User, is_created: bool, request) -> None:
        """Hash the password before saving."""
        password = data.get('password') if isinstance(data, dict) else None

        if password and isinstance(password, str):
            password = password.strip()

        if password:
            # Hash the password and set it on the model
            model.hashed_password = User.hash_password(password)
            # Remove password from data dict so SQLAdmin doesn't try to set it
            if isinstance(data, dict):
                data.pop('password', None)
        elif is_created:
            # For new users, require a password
            if not model.hashed_password:
                raise ValueError("Password is required for new users")



class SensorsAdmin(ModelView, model=Sensor):
    column_list = [Sensor.id, Sensor.name, Sensor.location, Sensor.owner_id]
    column_searchable_list = [Sensor.name]
    column_sortable_list = [Sensor.id, Sensor.name, Sensor.owner_id]
    column_default_sort = ("id", True)


class SensorRecordAdmin(ModelView, model=SensorRecord):
    column_list = [SensorRecord.id, SensorRecord.sensor, SensorRecord.value, SensorRecord.created_at]
    column_sortable_list = [SensorRecord.id, SensorRecord.value, SensorRecord.created_at]
    column_default_sort = ("id", True)
