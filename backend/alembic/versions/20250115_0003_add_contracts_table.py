"""Add contracts table

Revision ID: 0003
Revises: 0002
Create Date: 2025-01-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Criar enum type para contract status
    contract_status = postgresql.ENUM(
        'draft', 'active', 'terminated',
        name='contractstatus',
        create_type=True
    )
    
    contract_status.create(op.get_bind(), checkfirst=True)
    
    # Criar tabela contracts
    op.create_table(
        'contracts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('contract_code', sa.String(100), nullable=True),
        sa.Column('status', contract_status, nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    
    # Criar índices
    op.create_index('idx_contract_user_deleted', 'contracts', ['user_id', 'deleted_at'])
    op.create_index(op.f('ix_contracts_user_id'), 'contracts', ['user_id'], unique=False)


def downgrade() -> None:
    # Remover índices
    op.drop_index(op.f('ix_contracts_user_id'), table_name='contracts')
    op.drop_index('idx_contract_user_deleted', table_name='contracts')
    
    # Remover tabela
    op.drop_table('contracts')
    
    # Remover enum type
    contract_status = postgresql.ENUM(
        'draft', 'active', 'terminated',
        name='contractstatus',
        create_type=False
    )
    contract_status.drop(op.get_bind(), checkfirst=True)
