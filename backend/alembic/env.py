"""
Alembic Environment Configuration
Suporte para migrations com PostgreSQL
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Importar modelos para que Alembic possa detectar mudanças
from app.database import Base
from app.models import (
    License, ValidationLog, AdminUser, User, Subscription  # noqa: F401
)
from app.config import get_settings

# Configurações do Alembic
config = context.config

# Configurar logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData dos modelos para 'autogenerate'
target_metadata = Base.metadata

# Pegar URL do banco de configurações
settings = get_settings()

# Converter para URL sync (psycopg2) para Alembic
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql+asyncpg://"):
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
elif database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
    # Já está no formato correto para psycopg2
    pass

config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline() -> None:
    """
    Executa migrations em modo 'offline'.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Executa migrations em modo 'online' com conexão sync.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
