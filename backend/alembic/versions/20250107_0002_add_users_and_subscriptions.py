"""Add users, admin_users and subscriptions tables

Revision ID: 0002
Revises: 0001
Create Date: 2025-01-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Criar enum types adicionais
    admin_role = postgresql.ENUM(
        'superadmin', 'admin',
        name='adminrole',
        create_type=True
    )
    subscription_status = postgresql.ENUM(
        'active', 'past_due', 'cancelled', 'incomplete', 'trialing',
        name='subscriptionstatus',
        create_type=True
    )
    plan_type = postgresql.ENUM(
        'monthly', 'yearly', 'lifetime',
        name='plantype',
        create_type=True
    )
    
    admin_role.create(op.get_bind(), checkfirst=True)
    subscription_status.create(op.get_bind(), checkfirst=True)
    plan_type.create(op.get_bind(), checkfirst=True)
    
    # Adicionar coluna user_id na tabela licenses se não existir
    try:
        op.add_column('licenses', sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            'fk_license_user_id',
            'licenses', 'users',
            ['user_id'], ['id'],
            ondelete='SET NULL'
        )
        op.create_index('idx_license_user_id', 'licenses', ['user_id'])
    except Exception:
        # Coluna já existe ou erro
        pass
    
    # Criar tabela admin_users
    op.create_table(
        'admin_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', admin_role, nullable=False, server_default='admin'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    
    op.create_index('idx_admin_username', 'admin_users', ['username'])
    op.create_index('idx_admin_email', 'admin_users', ['email'])
    
    # Criar tabela users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('stripe_customer_id', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('stripe_customer_id')
    )
    
    op.create_index('idx_user_email', 'users', ['email'])
    op.create_index('idx_user_stripe_customer', 'users', ['stripe_customer_id'])
    
    # Criar tabela subscriptions
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('license_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(100), nullable=True),
        sa.Column('stripe_price_id', sa.String(100), nullable=True),
        sa.Column('plan_type', plan_type, nullable=False),
        sa.Column('status', subscription_status, nullable=False, server_default='active'),
        sa.Column('current_period_start', sa.DateTime(), nullable=False),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['license_id'], ['licenses.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('idx_subscription_user_id', 'subscriptions', ['user_id'])
    op.create_index('idx_subscription_license_id', 'subscriptions', ['license_id'])
    op.create_index('idx_subscription_stripe_id', 'subscriptions', ['stripe_subscription_id'])


def downgrade() -> None:
    # Remover tabelas
    op.drop_table('subscriptions')
    op.drop_table('users')
    op.drop_table('admin_users')
    
    # Remover coluna user_id de licenses
    try:
        op.drop_constraint('fk_license_user_id', 'licenses', type_='foreignkey')
        op.drop_index('idx_license_user_id', 'licenses')
        op.drop_column('licenses', 'user_id')
    except Exception:
        pass
    
    # Remover enum types
    op.execute('DROP TYPE IF EXISTS plantype')
    op.execute('DROP TYPE IF EXISTS subscriptionstatus')
    op.execute('DROP TYPE IF EXISTS adminrole')

