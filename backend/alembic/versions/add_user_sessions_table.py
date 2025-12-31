"""add user sessions table

Revision ID: add_user_sessions
Revises:
Create Date: 2025-12-31

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_user_sessions'
down_revision = None  # Será preenchido automaticamente
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Criar tabela de sessões ativas
    op.create_table(
        'user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_token', sa.String(500), nullable=False, unique=True),
        sa.Column('device_fingerprint', sa.String(255), nullable=True),  # Hash do dispositivo
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('device_name', sa.String(255), nullable=True),  # Ex: "Chrome on Windows"
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
    )

    # Índices para performance
    op.create_index('idx_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('idx_user_sessions_token', 'user_sessions', ['session_token'])
    op.create_index('idx_user_sessions_active', 'user_sessions', ['user_id', 'is_active'])
    op.create_index('idx_user_sessions_expires', 'user_sessions', ['expires_at'])


def downgrade() -> None:
    op.drop_index('idx_user_sessions_expires')
    op.drop_index('idx_user_sessions_active')
    op.drop_index('idx_user_sessions_token')
    op.drop_index('idx_user_sessions_user_id')
    op.drop_table('user_sessions')
