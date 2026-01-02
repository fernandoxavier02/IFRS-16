"""Add reajuste_periodicidade to contract_versions

Revision ID: 20260102_periodicidade
Revises: 20260101_notifications
Create Date: 2026-01-02 00:00:00.000000

Adiciona o campo reajuste_periodicidade para permitir reajustes mensais ou anuais.
- 'anual': Usa a taxa acumulada anual do índice (comportamento atual/padrão)
- 'mensal': Usa a taxa mensal do índice

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260102_periodicidade'
down_revision = None  # Será aplicada manualmente
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Adicionar coluna reajuste_periodicidade com valor padrão 'anual'
    op.add_column(
        'contract_versions',
        sa.Column(
            'reajuste_periodicidade',
            sa.String(20),
            nullable=False,
            server_default='anual'
        )
    )

    # Criar índice para consultas por periodicidade
    op.create_index(
        'idx_contract_versions_periodicidade',
        'contract_versions',
        ['reajuste_tipo', 'reajuste_periodicidade']
    )


def downgrade() -> None:
    # Remover índice
    op.drop_index('idx_contract_versions_periodicidade', table_name='contract_versions')

    # Remover coluna
    op.drop_column('contract_versions', 'reajuste_periodicidade')
