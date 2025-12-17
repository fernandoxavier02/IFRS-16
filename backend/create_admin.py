"""
Script para criar o primeiro administrador do sistema
"""

import asyncio
import sys
from getpass import getpass

# Adicionar o diretório ao path
sys.path.insert(0, '.')

from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models import AdminUser, AdminRole
from app.auth import hash_password


async def create_admin():
    print("=" * 50)
    print("🔐 Criar Administrador - IFRS 16")
    print("=" * 50)
    print()
    
    # Inicializar banco
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # Verificar se já existe admin
        result = await db.execute(
            select(AdminUser).where(AdminUser.role == AdminRole.SUPERADMIN)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"⚠️  Já existe um superadmin: {existing.username} ({existing.email})")
            print()
            create_another = input("Deseja criar outro admin? (s/N): ").strip().lower()
            if create_another != 's':
                return
        
        print("📝 Preencha os dados do novo administrador:")
        print()
        
        # Coletar dados
        username = input("Username: ").strip()
        if not username:
            print("❌ Username é obrigatório")
            return
        
        email = input("Email: ").strip()
        if not email or '@' not in email:
            print("❌ Email inválido")
            return
        
        password = getpass("Senha (mín. 8 caracteres): ")
        if len(password) < 8:
            print("❌ Senha deve ter pelo menos 8 caracteres")
            return
        
        confirm = getpass("Confirmar senha: ")
        if password != confirm:
            print("❌ Senhas não conferem")
            return
        
        # Verificar unicidade
        result = await db.execute(
            select(AdminUser).where(AdminUser.username == username)
        )
        if result.scalar_one_or_none():
            print(f"❌ Username '{username}' já existe")
            return
        
        result = await db.execute(
            select(AdminUser).where(AdminUser.email == email.lower())
        )
        if result.scalar_one_or_none():
            print(f"❌ Email '{email}' já cadastrado")
            return
        
        # Perguntar se é superadmin
        role_choice = input("É superadmin? (S/n): ").strip().lower()
        role = AdminRole.SUPERADMIN if role_choice != 'n' else AdminRole.ADMIN
        
        # Criar admin
        admin = AdminUser(
            username=username,
            email=email.lower(),
            password_hash=hash_password(password),
            role=role,
            is_active=True
        )
        
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        
        print()
        print("=" * 50)
        print("✅ Administrador criado com sucesso!")
        print("=" * 50)
        print()
        print(f"   ID: {admin.id}")
        print(f"   Username: {admin.username}")
        print(f"   Email: {admin.email}")
        print(f"   Role: {admin.role.value}")
        print()
        print("💡 Acesse: http://localhost:3000/login.html")
        print("   Use a aba 'Administrador' para fazer login")
        print()


if __name__ == "__main__":
    asyncio.run(create_admin())

