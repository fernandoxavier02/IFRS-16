"""
Script para criar tabela user_sessions no Cloud SQL
Conecta diretamente ao banco de produção e executa a migration
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine

# URL do Cloud SQL (obter do Cloud Run)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:PASSWORD@/ifrs16_licenses?host=/cloudsql/ifrs16-app:us-central1:ifrs16-database"
)

# SQL para criar tabela e índices
CREATE_TABLE_SQL = """
-- Criar tabela user_sessions
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
);

-- Criar índices
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);
"""

async def create_user_sessions_table():
    """Cria tabela user_sessions no Cloud SQL"""
    print(f"[INFO] Conectando ao banco: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'N/A'}")

    engine = create_async_engine(DATABASE_URL, echo=True)

    try:
        async with engine.begin() as conn:
            print("[INFO] Executando SQL para criar tabela user_sessions...")
            await conn.execute(sa.text(CREATE_TABLE_SQL))
            print("[SUCCESS] ✅ Tabela user_sessions criada com sucesso!")

            # Verificar se tabela foi criada
            result = await conn.execute(sa.text("""
                SELECT COUNT(*) as total
                FROM information_schema.columns
                WHERE table_name='user_sessions'
            """))
            row = result.fetchone()
            print(f"[INFO] Tabela user_sessions tem {row[0]} colunas")

    except Exception as e:
        print(f"[ERROR] ❌ Erro ao criar tabela: {e}")
        raise
    finally:
        await engine.dispose()
        print("[INFO] Conexão fechada")

if __name__ == "__main__":
    import sqlalchemy as sa
    print("=" * 60)
    print("CRIAR TABELA USER_SESSIONS NO CLOUD SQL")
    print("=" * 60)
    asyncio.run(create_user_sessions_table())
    print("\n[DONE] Script finalizado!")
