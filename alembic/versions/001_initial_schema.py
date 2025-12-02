"""Initial schema with all tables

Revision ID: 001_initial_schema
Revises:
Create Date: 2025-12-02 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables with complete schema."""

    # Create user table with all authentication and security fields
    op.create_table('user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('full_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_failed_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)

    # Remove server defaults after table creation (keep defaults in model only)
    op.alter_column('user', 'is_active', server_default=None)
    op.alter_column('user', 'is_admin', server_default=None)
    op.alter_column('user', 'failed_login_attempts', server_default=None)

    # Create sensor table with owner relationship
    op.create_table('sensor',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('location', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id'], name='fk_sensor_owner'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sensor_name'), 'sensor', ['name'], unique=False)
    op.create_index(op.f('ix_sensor_owner_id'), 'sensor', ['owner_id'], unique=False)

    # Create sensorrecord table
    op.create_table('sensorrecord',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('sensor_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['sensor_id'], ['sensor.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sensorrecord_sensor_id'), 'sensorrecord', ['sensor_id'], unique=False)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index(op.f('ix_sensorrecord_sensor_id'), table_name='sensorrecord')
    op.drop_table('sensorrecord')

    op.drop_index(op.f('ix_sensor_owner_id'), table_name='sensor')
    op.drop_index(op.f('ix_sensor_name'), table_name='sensor')
    op.drop_table('sensor')

    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')

