"""
Script para verificar o usuário master no banco
"""

import asyncio
import asyncpg

DATABASE_URL = "postgresql://ifrs16_database_ycs3_user:WUhx3D36NZVEytmT3a90c6ZWNog2pGEZ@dpg-d4r4lrmr433s738i13u0-a.virginia-postgres.render.com:5432/ifrs16_database_ycs3"

async def verificar():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Buscar usuário master
        result = await conn.fetchrow(
            "SELECT id, username, email, role, is_active, created_at FROM admin_users WHERE username = 'master'"
        )
        
        if result:
            print("=" * 60)
            print("👤 USUÁRIO MASTER ENCONTRADO")
            print("=" * 60)
            print(f"   ID: {result['id']}")
            print(f"   Username: {result['username']}")
            print(f"   Email: {result['email']}")
            print(f"   Role: {result['role']}")
            print(f"   Ativo: {result['is_active']}")
            print(f"   Criado em: {result['created_at']}")
            print("=" * 60)
        else:
            print("❌ Usuário master não encontrado!")
            
        # Listar todos os admins
        print("\n📋 TODOS OS ADMINS:")
        admins = await conn.fetch("SELECT username, email, role, is_active FROM admin_users")
        for admin in admins:
            print(f"   - {admin['username']} ({admin['email']}) - {admin['role']} - Ativo: {admin['is_active']}")
            
    finally:
        await conn.close()

asyncio.run(verificar())

