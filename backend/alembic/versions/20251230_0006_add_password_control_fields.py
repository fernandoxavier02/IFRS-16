"""Add password control fields to users

Revision ID: 0006
Revises: 0005
Create Date: 2025-12-30 20:00:00.000000

This migration adds password control fields for security:
1. password_must_change - Flag to force password change on first login
2. password_changed_at - Timestamp of last password change

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0006'
down_revision: Union[str, None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade schema to add password control fields.
    """
    # 1. Adicionar campo password_must_change
    op.add_column(
        'users',
        sa.Column('password_must_change', sa.Boolean(), nullable=False, server_default='false')
    )

    # 2. Adicionar campo password_changed_at
    op.add_column(
        'users',
        sa.Column('password_changed_at', sa.DateTime(), nullable=True)
    )

    print("[OK] Migration 0006 aplicada: Campos de controle de senha adicionados")


def downgrade() -> None:
    """
    Downgrade schema to remove password control fields.
    """
    # Remover campos
    op.drop_column('users', 'password_changed_at')
    op.drop_column('users', 'password_must_change')

    print("[WARN] Migration 0006 revertida: Campos de controle de senha removidos")
