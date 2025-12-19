"""Add company_name to users

Revision ID: 0004
Revises: 0003
Create Date: 2025-12-19 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Adicionar coluna company_name à tabela users
    op.add_column('users', sa.Column('company_name', sa.String(length=255), nullable=True))


def downgrade() -> None:
    # Remover coluna company_name da tabela users
    op.drop_column('users', 'company_name')
