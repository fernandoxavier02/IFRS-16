"""
Script para resetar senha do usuário master
"""

import asyncio
import asyncpg
import bcrypt

DATABASE_URL = "postgresql://ifrs16_database_ycs3_user:WUhx3D36NZVEytmT3a90c6ZWNog2pGEZ@dpg-d4r4lrmr433s738i13u0-a.virginia-postgres.render.com:5432/ifrs16_database_ycs3"

async def reset_password():
    """Reseta a senha do usuário master"""
    
    # Nova senha
    new_password = "Master@2025!"
    
    print("=" * 60)
    print("🔐 RESETAR SENHA DO USUÁRIO MASTER")
    print("=" * 60)
    print()
    
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Buscar usuário master
        user = await conn.fetchrow(
            "SELECT id, username, email FROM admin_users WHERE username = 'master'"
        )
        
        if not user:
            print("❌ Usuário master não encontrado!")
            return
        
        print(f"👤 Usuário encontrado:")
        print(f"   Username: {user['username']}")
        print(f"   Email: {user['email']}")
        print()
        
        # Gerar novo hash da senha
        print("🔑 Gerando novo hash da senha...")
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), salt).decode('utf-8')
        
        # Atualizar senha
        await conn.execute(
            "UPDATE admin_users SET password_hash = $1 WHERE id = $2",
            password_hash, user['id']
        )
        
        print("✅ Senha resetada com sucesso!")
        print()
        print("=" * 60)
        print("📋 CREDENCIAIS ATUALIZADAS")
        print("=" * 60)
        print(f"   Email: {user['email']}")
        print(f"   Senha: {new_password}")
        print("=" * 60)
        
        # Testar hash
        print()
        print("🧪 Testando hash...")
        test_hash = bcrypt.checkpw(new_password.encode('utf-8'), password_hash.encode('utf-8'))
        print(f"   Hash válido: {test_hash}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(reset_password())

