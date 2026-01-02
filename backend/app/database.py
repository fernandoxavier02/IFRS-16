"""
Configuração do banco de dados PostgreSQL com SQLAlchemy async
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from .config import get_settings

settings = get_settings()

# Usar a URL já convertida para asyncpg
database_url = settings.async_database_url

# Engine async (suporta PostgreSQL e SQLite)
# Configuração específica para SQLite
connect_args = {}
if "sqlite" in database_url:
    connect_args = {"check_same_thread": False}
    engine = create_async_engine(
        database_url,
        echo=settings.DEBUG,
        connect_args=connect_args,
    )
else:
    # PostgreSQL com SSL para Render
    # asyncpg aceita ssl='require' para SSL obrigatório
    engine = create_async_engine(
        database_url,
        echo=settings.DEBUG,
        future=True,
        pool_pre_ping=True,  # Testa conexão antes de usar
        pool_size=1,  # Mínimo para free tier
        max_overflow=2,  # Reduzido para free tier
        pool_recycle=300,  # Recicla a cada 5 min (evita conexões antigas)
        pool_timeout=30,  # Timeout para obter conexão do pool
        connect_args={
            "ssl": "require",  # SSL obrigatório para Cloud SQL
            "command_timeout": 60,  # Timeout para comandos SQL
        },
    )

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base para modelos
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency para injetar sessão do banco de dados nos endpoints.
    Uso: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Inicializa o banco de dados criando todas as tabelas.
    Use apenas em desenvolvimento. Em produção, use Alembic migrations.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def ensure_user_sessions_table():
    """
    Garante que a tabela user_sessions existe no banco de dados.
    Cria a tabela e índices se não existirem.
    """
    import sqlalchemy as sa
    async with engine.begin() as conn:
        # Criar tabela user_sessions se não existir
        await conn.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                session_token VARCHAR(500) NOT NULL UNIQUE,
                device_fingerprint VARCHAR(255),
                ip_address VARCHAR(45),
                user_agent VARCHAR(500),
                device_name VARCHAR(255),
                last_activity TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT true
            )
        """))

        # Criar índices se não existirem
        await conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)
        """))

        await conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token)
        """))

        await conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(user_id, is_active)
        """))

        await conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at)
        """))

    print("[OK] Tabela user_sessions verificada/criada com sucesso!")


async def ensure_economic_indexes_table():
    """
    Garante que a tabela economic_indexes existe no banco de dados.
    Cria a tabela e índices se não existirem.
    """
    import sqlalchemy as sa
    async with engine.begin() as conn:
        # Criar tabela economic_indexes se não existir
        await conn.execute(sa.text("""
            CREATE TABLE IF NOT EXISTS economic_indexes (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                index_type VARCHAR(20) NOT NULL,
                reference_date TIMESTAMP NOT NULL,
                value VARCHAR(50) NOT NULL,
                source VARCHAR(50) NOT NULL DEFAULT 'BCB',
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """))

        # Criar índice único para evitar duplicatas
        await conn.execute(sa.text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_economic_index_type_date
            ON economic_indexes (index_type, reference_date)
        """))

        # Criar índice para consultas
        await conn.execute(sa.text("""
            CREATE INDEX IF NOT EXISTS idx_economic_index_type_date
            ON economic_indexes (index_type, reference_date)
        """))

    print("[OK] Tabela economic_indexes verificada/criada com sucesso!")


async def close_db():
    """
    Fecha todas as conexões do pool.
    Chamar ao encerrar a aplicação.
    """
    await engine.dispose()

