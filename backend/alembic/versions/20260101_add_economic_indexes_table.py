"""add economic indexes table

Revision ID: 20260101_economic_indexes
Revises: 20251231_add_user_sessions
Create Date: 2026-01-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260101_economic_indexes'
down_revision = '20251231_add_user_sessions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Criar tabela de índices econômicos
    op.create_table(
        'economic_indexes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('index_type', sa.String(20), nullable=False),  # selic, igpm, ipca, cdi, inpc, tr
        sa.Column('reference_date', sa.DateTime, nullable=False),
        sa.Column('value', sa.String(50), nullable=False),  # String para preservar precisão
        sa.Column('source', sa.String(50), nullable=False, server_default='BCB'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
    )

    # Índice único para evitar duplicatas (tipo + data)
    op.create_index(
        'uq_economic_index_type_date',
        'economic_indexes',
        ['index_type', 'reference_date'],
        unique=True
    )

    # Índice para consultas por tipo e data
    op.create_index(
        'idx_economic_index_type_date',
        'economic_indexes',
        ['index_type', 'reference_date']
    )


def downgrade() -> None:
    op.drop_index('idx_economic_index_type_date')
    op.drop_index('uq_economic_index_type_date')
    op.drop_table('economic_indexes')
