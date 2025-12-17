"""
Script para criar o primeiro administrador automaticamente
"""

import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models import AdminUser, AdminRole
from app.auth import hash_password


async def create_admin():
    print("=" * 50)
    print("🔐 Criando Administrador Padrão - IFRS 16")
    print("=" * 50)
    
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # Verificar se já existe admin
        result = await db.execute(
            select(AdminUser).where(AdminUser.role == AdminRole.SUPERADMIN)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"✅ Superadmin já existe: {existing.username} ({existing.email})")
            return
        
        # Criar admin padrão
        admin = AdminUser(
            username="admin",
            email="admin@ifrs16.local",
            password_hash=hash_password("Admin123!"),
            role=AdminRole.SUPERADMIN,
            is_active=True
        )
        
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        
        print()
        print("✅ Administrador criado com sucesso!")
        print()
        print(f"   👤 Username: admin")
        print(f"   📧 Email: admin@ifrs16.local")
        print(f"   🔑 Senha: Admin123!")
        print(f"   🎭 Role: superadmin")
        print()
        print("⚠️  IMPORTANTE: Altere a senha após o primeiro login!")
        print()


if __name__ == "__main__":
    asyncio.run(create_admin())

