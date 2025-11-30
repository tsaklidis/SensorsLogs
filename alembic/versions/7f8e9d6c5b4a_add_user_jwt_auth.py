"""add user model with jwt authentication

Revision ID: 7f8e9d6c5b4a
Revises: 663557b07ebd
Create Date: 2025-11-30 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '7f8e9d6c5b4a'
down_revision: Union[str, None] = '663557b07ebd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add User table with JWT authentication and sensor ownership."""
    # Create user table with hashed_password for JWT authentication
    op.create_table('user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('full_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)

    # Add owner_id column to sensor table
    op.add_column('sensor', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_sensor_owner_id'), 'sensor', ['owner_id'], unique=False)
    op.create_foreign_key('fk_sensor_owner', 'sensor', 'user', ['owner_id'], ['id'])


def downgrade() -> None:
    """Remove User table and sensor ownership."""
    # Remove foreign key and owner_id from sensor
    op.drop_constraint('fk_sensor_owner', 'sensor', type_='foreignkey')
    op.drop_index(op.f('ix_sensor_owner_id'), table_name='sensor')
    op.drop_column('sensor', 'owner_id')

    # Drop user table
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')

