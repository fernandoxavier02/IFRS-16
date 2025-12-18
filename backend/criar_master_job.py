
import asyncio
import os
import sys
import asyncpg
import bcrypt
from datetime import datetime

# Configurações
# O Cloud Run injeta a variavel DATABASE_URL automaticamente com o socket connection se configurado corretamente
# Mas como estamos rodando um Job, precisamos garantir que as env vars estao la.
# Vamos pegar a DATABASE_URL do environment, que deve estar apontando para o unix socket
# Ex: postgresql+asyncpg://user:pass@/dbname?host=/cloudsql/project:region:instance

DATABASE_URL = os.getenv("DATABASE_URL")
# Se vier no formato SQLAlchemy (postgresql+asyncpg://), precisamos limpar para asyncpg puro se necessario,
# mas o asyncpg geralmente aceita se for postgres://.
# Vamos reconstruir a string de conexao para garantir, usando os dados atomicamente se disponiveis.

DB_USER = os.getenv("CLOUD_SQL_USER", "ifrs16_user")
DB_PASS = os.getenv("CLOUD_SQL_PASSWORD", "bBMOLk2HURjQAvDiPNYE")
DB_NAME = "ifrs16_licenses"
INSTANCE_CONNECTION_NAME = "ifrs16-app:us-central1:ifrs16-database"

# No Cloud Run, conectamos via Unix Socket: /cloudsql/INSTANCE_CONNECTION_NAME
DSN = f"postgresql://{DB_USER}:{DB_PASS}@/{DB_NAME}?host=/cloudsql/{INSTANCE_CONNECTION_NAME}"

async def run():
    print("="*60)
    print("JOB: CRIAR USUARIO MASTER")
    print(f"Connecting to: {INSTANCE_CONNECTION_NAME}")
    print("="*60)

    try:
        # Tenta conectar
        conn = await asyncpg.connect(DSN)
        print("✅ Conectado ao banco de dados!")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        # Tentar fallback TCP caso nao esteja no ambiente esperado (mas no Cloud Run deve ser socket)
        return

    try:
        # Dados do usuário
        email = "fernandocostaxavier@gmail.com"
        username = "fernando.costa"
        raw_password = "Fcxv020781@"
        role = "SUPERADMIN"
        
        # Gerar Hash
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(raw_password.encode('utf-8'), salt).decode('utf-8')
        
        # SQL UPSERT
        sql = """
        INSERT INTO admin_users (id, username, email, password_hash, role, is_active, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW())
        ON CONFLICT (email) DO UPDATE 
        SET password_hash = $4, 
            role = $5, 
            is_active = $6, 
            updated_at = NOW()
        RETURNING id;
        """
        
        # Gera UUID se necessario (mas aqui deixamos o banco gerar se for default, ou geramos no python)
        # O admin_users geralmente espera UUID no ID.
        import uuid
        user_id = str(uuid.uuid4())
        
        print("Executando Query...")
        result_id = await conn.fetchval(sql, user_id, username, email, password_hash, role, True)
        
        print(f"✅ Usuário processado com sucesso! ID: {result_id}")
        print(f"   Email: {email}")
        print(f"   Senha: {raw_password}")
        
    except Exception as e:
        print(f"❌ Erro ao criar usuário: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run())
