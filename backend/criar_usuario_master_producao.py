"""
Script para criar/verificar usuário master (superadmin) em PRODUÇÃO
Usa a DATABASE_URL do Render
"""

import asyncio
import os
import sys
from datetime import datetime
from uuid import uuid4

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Adicionar path do app
sys.path.insert(0, os.path.dirname(__file__))

# Configurar DATABASE_URL de produção (Render)
DATABASE_URL_PRODUCAO = "postgresql://ifrs16_database_ycs3_user:WUhx3D36NZVEytmT3a90c6ZWNog2pGEZ@dpg-d4r4lrmr433s738i13u0-a.virginia-postgres.render.com:5432/ifrs16_database_ycs3"

# Importar dependências
try:
    import asyncpg
    import bcrypt
except ImportError:
    print("Instalando dependências...")
    os.system("pip install asyncpg bcrypt")
    import asyncpg
    import bcrypt

async def criar_ou_verificar_master():
    """Cria ou verifica usuário master em produção"""
    
    print("=" * 70)
    print("CRIAR/VERIFICAR USUARIO MASTER - PRODUCAO")
    print("=" * 70)
    print()
    
    # Dados do usuário master
    username = "master"
    email = "fernandocostaxavier@gmail.com"
    password = "Master@2025!"
    role = "SUPERADMIN"
    
    print(f"Dados do usuario:")
    print(f"   Username: {username}")
    print(f"   Email: {email}")
    print(f"   Role: {role}")
    print()
    
    # Conectar ao banco de produção
    print("Conectando ao banco de producao...")
    try:
        conn = await asyncpg.connect(DATABASE_URL_PRODUCAO, ssl=True)
        print("Conectado ao banco de producao!")
        print()
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return
    
    try:
        # Verificar se tabela existe
        table_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'admin_users'
            )
        """)
        
        if not table_exists:
            print("ERRO: Tabela 'admin_users' nao existe!")
            print("   Execute as migrations primeiro: alembic upgrade head")
            return
        
        # Verificar se já existe
        existing = await conn.fetchrow(
            "SELECT id, username, email, role, is_active, created_at FROM admin_users WHERE username = $1 OR email = $2",
            username, email
        )
        
        if existing:
            print("Usuario master ja existe no banco de producao!")
            print()
            print("=" * 70)
            print("DADOS DO USUARIO EXISTENTE")
            print("=" * 70)
            print(f"   ID: {existing['id']}")
            print(f"   Username: {existing['username']}")
            print(f"   Email: {existing['email']}")
            print(f"   Role: {existing['role']}")
            print(f"   Ativo: {'Sim' if existing['is_active'] else 'Nao'}")
            print(f"   Criado em: {existing['created_at']}")
            print()
            
            # Perguntar se quer atualizar
            print("=" * 70)
            print("ATUALIZAR USUARIO?")
            print("=" * 70)
            print("Deseja atualizar senha e garantir que está ativo?")
            resposta = input("(s/N): ").strip().lower()
            
            if resposta == 's':
                # Gerar hash da senha
                salt = bcrypt.gensalt()
                password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
                
                await conn.execute(
                    """
                    UPDATE admin_users 
                    SET password_hash = $1, 
                        email = $2, 
                        role = $3, 
                        is_active = true,
                        updated_at = $4
                    WHERE id = $5
                    """,
                    password_hash, email, role, datetime.utcnow(), existing['id']
                )
                print()
                print("Usuario master atualizado com sucesso!")
            else:
                print("Usuario nao foi atualizado")
        else:
            # Criar novo usuário master
            print("Criando novo usuario master...")
            
            # Gerar hash da senha
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            
            # Criar usuário
            user_id = uuid4()
            created_at = datetime.utcnow()
            
            await conn.execute(
                """
                INSERT INTO admin_users (id, username, email, password_hash, role, is_active, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                user_id, username, email, password_hash, role, True, created_at, created_at
            )
            
            print()
            print("Usuario master criado com sucesso!")
        
        print()
        print("=" * 70)
        print("CREDENCIAIS DE ACESSO - PRODUCAO")
        print("=" * 70)
        print()
        print("URL de Login:")
        print("   https://ifrs-16-1.onrender.com/login.html")
        print()
        print("Credenciais:")
        print(f"   Email: {email}")
        print(f"   Senha: {password}")
        print()
        print("IMPORTANTE:")
        print("   1. Use a aba 'Administrador' na pagina de login")
        print("   2. Use o EMAIL (nao o username) para fazer login")
        print("   3. Altere a senha apos o primeiro login")
        print()
        print("=" * 70)
        
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()
        print()
        print("Conexao fechada")

if __name__ == "__main__":
    print()
    print("ATENCAO: Este script vai modificar o banco de PRODUCAO!")
    print()
    confirmar = input("Continuar? (s/N): ").strip().lower()
    
    if confirmar == 's':
        asyncio.run(criar_ou_verificar_master())
    else:
        print("Operacao cancelada")
