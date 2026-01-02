"""Add notifications table

Revision ID: 20260101_notifications
Revises: 20260101_add_economic_indexes_table
Create Date: 2026-01-01 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260101_notifications'
down_revision = None  # Será aplicada manualmente
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Criar enum para notification_type
    notification_type_enum = postgresql.ENUM(
        'contract_expiring',
        'contract_expired',
        'remeasurement_done',
        'index_updated',
        'license_expiring',
        'system_alert',
        name='notificationtype',
        create_type=False
    )

    # Criar o enum primeiro
    op.execute("CREATE TYPE notificationtype AS ENUM ('contract_expiring', 'contract_expired', 'remeasurement_done', 'index_updated', 'license_expiring', 'system_alert')")

    # Criar tabela notifications
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('notification_type', sa.Enum('contract_expiring', 'contract_expired', 'remeasurement_done', 'index_updated', 'license_expiring', 'system_alert', name='notificationtype'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('read', sa.Boolean(), nullable=False, default=False),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Criar índices
    op.create_index('idx_notification_user_read', 'notifications', ['user_id', 'read'])
    op.create_index('idx_notification_user_type', 'notifications', ['user_id', 'notification_type'])
    op.create_index('idx_notification_created_at', 'notifications', ['created_at'])


def downgrade() -> None:
    # Remover índices
    op.drop_index('idx_notification_created_at', table_name='notifications')
    op.drop_index('idx_notification_user_type', table_name='notifications')
    op.drop_index('idx_notification_user_read', table_name='notifications')

    # Remover tabela
    op.drop_table('notifications')

    # Remover enum
    op.execute("DROP TYPE notificationtype")
