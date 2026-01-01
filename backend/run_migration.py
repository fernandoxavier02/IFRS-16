"""
Script para executar migration no banco de produção via Cloud SQL
"""
import asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import get_settings

async def run_migration():
    settings = get_settings()

    # Conectar ao banco de produção
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True,
        pool_pre_ping=True
    )

    async with engine.begin() as conn:
        # Criar tabela user_sessions
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

        print("[OK] Tabela user_sessions criada!")

        # Criar índices
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

        print("[OK] Índices criados!")

    await engine.dispose()
    print("[SUCESSO] Migration concluída!")

if __name__ == "__main__":
    asyncio.run(run_migration())
