"""Initial migration - Create licenses and validation_logs tables

Revision ID: 0001
Revises: 
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Criar enum types
    license_status = postgresql.ENUM(
        'active', 'suspended', 'expired', 'cancelled',
        name='licensestatus',
        create_type=True
    )
    license_type = postgresql.ENUM(
        'trial', 'basic', 'pro', 'enterprise',
        name='licensetype',
        create_type=True
    )
    
    license_status.create(op.get_bind(), checkfirst=True)
    license_type.create(op.get_bind(), checkfirst=True)

    # Criar tabela licenses
    op.create_table(
        'licenses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key', sa.String(50), nullable=False),
        sa.Column('customer_name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('status', license_status, nullable=False, server_default='active'),
        sa.Column('license_type', license_type, nullable=False, server_default='trial'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('revoke_reason', sa.Text(), nullable=True),
        sa.Column('machine_id', sa.String(64), nullable=True),
        sa.Column('max_activations', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('current_activations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_validation', sa.DateTime(), nullable=True),
        sa.Column('last_validation_ip', sa.String(45), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    
    # Criar índices para licenses
    op.create_index('idx_license_key', 'licenses', ['key'])
    op.create_index('idx_license_status_type', 'licenses', ['status', 'license_type'])
    op.create_index('idx_license_email', 'licenses', ['email'])

    # Criar tabela validation_logs
    op.create_table(
        'validation_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('license_key', sa.String(50), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('message', sa.String(255), nullable=True),
        sa.Column('machine_id', sa.String(64), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('app_version', sa.String(20), nullable=True),
        sa.ForeignKeyConstraint(['license_key'], ['licenses.key'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Criar índices para validation_logs
    op.create_index('idx_validation_license_key', 'validation_logs', ['license_key'])
    op.create_index('idx_validation_timestamp', 'validation_logs', ['timestamp'])


def downgrade() -> None:
    # Remover tabelas
    op.drop_table('validation_logs')
    op.drop_table('licenses')
    
    # Remover enum types
    op.execute('DROP TYPE IF EXISTS licensestatus')
    op.execute('DROP TYPE IF EXISTS licensetype')

