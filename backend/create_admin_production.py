"""
Script para criar admin no banco de producao do Render
"""

import asyncio
import os
import sys
sys.path.insert(0, '.')

# Configurar DATABASE_URL de producao
os.environ['DATABASE_URL'] = 'postgresql://ifrs16_database_user:DmgbPA9jjyA587ot8Rc4Kt4fnAr0opM7@dpg-d4qvp9ggjchc73bk1rvg-a.virginia-postgres.render.com/ifrs16_database'
os.environ['ENVIRONMENT'] = 'production'

from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models import AdminUser, AdminRole
from app.auth import hash_password


async def create_admin():
    print("=" * 50)
    print("Criando Administrador no Banco de Producao")
    print("=" * 50)
    
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # Verificar se ja existe admin
        result = await db.execute(
            select(AdminUser).where(AdminUser.role == AdminRole.SUPERADMIN)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"Admin ja existe: {existing.username} ({existing.email})")
            return
        
        # Criar admin
        admin = AdminUser(
            username="admin",
            email="fernandocostaxavier@gmail.com",
            password_hash=hash_password("Admin123!"),
            role=AdminRole.SUPERADMIN,
            is_active=True
        )
        
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        
        print()
        print("Admin criado com sucesso!")
        print()
        print(f"   Username: admin")
        print(f"   Email: fernandocostaxavier@gmail.com")
        print(f"   Senha: Admin123!")
        print(f"   Role: superadmin")
        print()


if __name__ == "__main__":
    asyncio.run(create_admin())

