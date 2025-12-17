"""
Script para criar usuário master (superadmin) no banco de dados
"""

import asyncio
import asyncpg
from datetime import datetime
from uuid import uuid4
import bcrypt

# Configuração do banco - Cloud SQL
import os
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://ifrs16_user:ihU40nPKL38tCzTFvfNM@136.112.221.225:5432/ifrs16_licenses")

async def create_master_user():
    """Cria usuário master (superadmin)"""
    
    print("=" * 60)
    print("CRIAR USUARIO MASTER (SUPERADMIN)")
    print("=" * 60)
    print()
    
    # Dados do usuário master
    username = "master"
    email = "fernandocostaxavier@gmail.com"
    password = "Master@2025!"  # Senha forte padrão
    role = "SUPERADMIN"  # Enum no banco está em MAIÚSCULAS
    
    # Conectar ao banco com SSL
    conn = await asyncpg.connect(DATABASE_URL, ssl="require")
    
    try:
        # Verificar se já existe
        existing = await conn.fetchrow(
            "SELECT id, username, email, role FROM admin_users WHERE username = $1 OR email = $2",
            username, email
        )
        
        if existing:
            print(f"⚠️  Usuário master já existe:")
            print(f"   Username: {existing['username']}")
            print(f"   Email: {existing['email']}")
            print(f"   Role: {existing['role']}")
            print()
            
            update = input("Deseja atualizar senha e email? (s/N): ").strip().lower()
            if update == 's':
                # Gerar hash da senha
                salt = bcrypt.gensalt()
                password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
                
                await conn.execute(
                    "UPDATE admin_users SET password_hash = $1, email = $2, role = $3, is_active = true WHERE id = $4",
                    password_hash, email, role, existing['id']
                )
                print("OK: Senha e email atualizados com sucesso!")
                print(f"   Novo email: {email}")
            else:
                print("ERRO: Operacao cancelada")
                return
        else:
            # Gerar hash da senha
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            
            # Criar usuário master
            user_id = uuid4()
            await conn.execute(
                """
                INSERT INTO admin_users (id, username, email, password_hash, role, is_active, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                user_id, username, email, password_hash, role, True, datetime.utcnow()
            )
            
            print("OK: Usuario master criado com sucesso!")
            print()
            print("=" * 60)
            print("CREDENCIAIS DO USUARIO MASTER")
            print("=" * 60)
            print(f"   Username: {username}")
            print(f"   Email: {email}")
            print(f"   Senha: {password}")
            print(f"   Role: {role}")
            print()
            print("IMPORTANTE: Altere a senha apos o primeiro login!")
            print()
            print("Acesse: https://ifrs16-app.web.app/login.html")
            print("   Use a aba 'Administrador' para fazer login")
            print("=" * 60)
        
    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_master_user())

