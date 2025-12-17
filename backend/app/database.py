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


async def close_db():
    """
    Fecha todas as conexões do pool.
    Chamar ao encerrar a aplicação.
    """
    await engine.dispose()

