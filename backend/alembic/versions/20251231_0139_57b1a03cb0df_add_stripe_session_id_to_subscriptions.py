"""add stripe_session_id to subscriptions

Revision ID: 57b1a03cb0df
Revises: 0006
Create Date: 2025-12-31 01:39:29.000505

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '57b1a03cb0df'
down_revision: Union[str, None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adicionar coluna stripe_session_id para idempotência de webhooks
    op.add_column('subscriptions', sa.Column('stripe_session_id', sa.String(length=100), nullable=True))

    # Criar índice único para prevenir processamento duplicado
    op.create_index('ix_subscriptions_stripe_session_id', 'subscriptions', ['stripe_session_id'], unique=True)


def downgrade() -> None:
    # Remover índice
    op.drop_index('ix_subscriptions_stripe_session_id', table_name='subscriptions')

    # Remover coluna
    op.drop_column('subscriptions', 'stripe_session_id')

