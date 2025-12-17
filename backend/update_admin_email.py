"""
Script para atualizar o email do administrador
"""

import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models import AdminUser, AdminRole


async def update_admin_email():
    print("=" * 50)
    print("📧 Atualizar Email do Administrador - IFRS 16")
    print("=" * 50)
    print()
    
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # Buscar o primeiro superadmin ou admin
        result = await db.execute(
            select(AdminUser).where(
                AdminUser.role == AdminRole.SUPERADMIN
            ).order_by(AdminUser.created_at)
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            # Se não existe superadmin, buscar qualquer admin
            result = await db.execute(
                select(AdminUser).order_by(AdminUser.created_at)
            )
            admin = result.scalar_one_or_none()
        
        new_email = "fernandocostaxavier@gmail.com"
        
        if admin:
            # Verificar se o email já está em uso por outro admin
            result = await db.execute(
                select(AdminUser).where(
                    AdminUser.email == new_email.lower(),
                    AdminUser.id != admin.id
                )
            )
            if result.scalar_one_or_none():
                print(f"❌ Email '{new_email}' já está em uso por outro admin")
                return
            
            old_email = admin.email
            admin.email = new_email.lower()
            await db.commit()
            await db.refresh(admin)
            
            print("✅ Email atualizado com sucesso!")
            print()
            print(f"   👤 Username: {admin.username}")
            print(f"   📧 Email antigo: {old_email}")
            print(f"   📧 Email novo: {admin.email}")
            print(f"   🎭 Role: {admin.role.value}")
            print()
        else:
            # Criar novo admin se não existir nenhum
            from app.auth import hash_password
            
            admin = AdminUser(
                username="fernando",
                email=new_email.lower(),
                password_hash=hash_password("Admin123!"),
                role=AdminRole.SUPERADMIN,
                is_active=True
            )
            
            db.add(admin)
            await db.commit()
            await db.refresh(admin)
            
            print("✅ Novo administrador criado com sucesso!")
            print()
            print(f"   👤 Username: {admin.username}")
            print(f"   📧 Email: {admin.email}")
            print(f"   🔑 Senha: Admin123!")
            print(f"   🎭 Role: {admin.role.value}")
            print()
            print("⚠️  IMPORTANTE: Altere a senha após o primeiro login!")
            print()


if __name__ == "__main__":
    asyncio.run(update_admin_email())

