"""
Testar login do master
"""

import asyncio
import asyncpg
import bcrypt

DATABASE_URL = "postgresql://ifrs16_database_ycs3_user:WUhx3D36NZVEytmT3a90c6ZWNog2pGEZ@dpg-d4r4lrmr433s738i13u0-a.virginia-postgres.render.com:5432/ifrs16_database_ycs3"

async def test():
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Buscar usuário
        user = await conn.fetchrow(
            "SELECT id, username, email, password_hash FROM admin_users WHERE username = 'master'"
        )
        
        print("=" * 60)
        print("🔍 DADOS DO USUÁRIO MASTER")
        print("=" * 60)
        print(f"Email no banco: '{user['email']}'")
        print(f"Email lower: '{user['email'].lower()}'")
        print(f"Email testado: 'fernandocostaxavier@gmail.com'")
        print(f"Emails coincidem? {user['email'].lower() == 'fernandocostaxavier@gmail.com'}")
        print()
        
        # Testar senha
        password = "Master@2025!"
        password_hash = user['password_hash']
        
        print("🔑 TESTE DE SENHA")
        print("=" * 60)
        print(f"Senha testada: '{password}'")
        print(f"Hash no banco: {password_hash[:50]}...")
        
        # Verificar senha
        try:
            is_valid = bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
            print(f"✅ Senha válida: {is_valid}")
        except Exception as e:
            print(f"❌ Erro ao verificar senha: {e}")
        
        print()
        print("🧪 SIMULAÇÃO DO LOGIN")
        print("=" * 60)
        email_input = "fernandocostaxavier@gmail.com"
        email_lower = email_input.lower()
        print(f"Email digitado: '{email_input}'")
        print(f"Email após .lower(): '{email_lower}'")
        print(f"Email no banco: '{user['email']}'")
        print(f"Comparação: {email_lower == user['email'].lower()}")
        
    finally:
        await conn.close()

asyncio.run(test())
