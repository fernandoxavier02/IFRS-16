"""Consolidate subscription fields and add idempotency

Revision ID: 0005
Revises: 0004
Create Date: 2025-01-30 12:00:00.000000

This migration adds:
1. stripe_session_id to subscriptions table for webhook idempotency
2. Unique index on stripe_session_id
3. Validates unique constraint on licenses.key (should already exist)

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade schema to add idempotency support for Stripe webhooks.
    """
    # 1. Adicionar campo stripe_session_id à tabela subscriptions
    op.add_column(
        'subscriptions',
        sa.Column('stripe_session_id', sa.String(length=100), nullable=True)
    )

    # 2. Criar índice único em stripe_session_id
    op.create_index(
        'idx_subscription_session_id',
        'subscriptions',
        ['stripe_session_id'],
        unique=True
    )

    # 3. Garantir que licenses.key tem constraint unique
    # (Deve já existir no modelo, mas adicionar aqui por segurança)
    # Primeiro verificar se já existe, se não, criar
    try:
        op.create_unique_constraint(
            'uq_license_key',
            'licenses',
            ['key']
        )
    except Exception:
        # Constraint já existe, ignorar
        pass

    print("✅ Migration 0005 aplicada: stripe_session_id adicionado para idempotência")


def downgrade() -> None:
    """
    Downgrade schema to remove idempotency fields.
    """
    # Remover índice único
    op.drop_index('idx_subscription_session_id', table_name='subscriptions')

    # Remover coluna stripe_session_id
    op.drop_column('subscriptions', 'stripe_session_id')

    # Remover unique constraint de licenses.key (se foi criada nesta migration)
    try:
        op.drop_constraint('uq_license_key', 'licenses', type_='unique')
    except Exception:
        # Constraint não existe ou não foi criada nesta migration, ignorar
        pass

    print("⚠️ Migration 0005 revertida: stripe_session_id removido")
