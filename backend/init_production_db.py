"""
Script para inicializar o banco de dados em produção
Executa migrações e cria admin inicial se necessário
"""

import asyncio
import sys
import os
sys.path.insert(0, '.')

from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models import AdminUser, AdminRole
from app.auth import hash_password
from app.config import get_settings

settings = get_settings()


async def init_production_db():
    """Inicializa banco de dados em produção"""
    print("=" * 50)
    print("🚀 Inicialização do Banco de Dados - Produção")
    print("=" * 50)
    print()
    
    # Verificar se estamos em produção
    if settings.ENVIRONMENT != "production":
        print("⚠️  ATENÇÃO: Este script é para produção!")
        print(f"   Ambiente atual: {settings.ENVIRONMENT}")
        response = input("   Continuar mesmo assim? (s/N): ").strip().lower()
        if response != 's':
            print("❌ Cancelado")
            return
    
    print("📦 Inicializando banco de dados...")
    await init_db()
    print("✅ Tabelas criadas/verificadas")
    print()
    
    # Verificar se existe admin
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AdminUser).where(AdminUser.role == AdminRole.SUPERADMIN)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"✅ Superadmin já existe: {existing.username} ({existing.email})")
            return
        
        # Criar admin padrão se não existir
        print("👤 Criando superadmin padrão...")
        admin = AdminUser(
            username="admin",
            email=os.getenv("ADMIN_EMAIL", "admin@ifrs16.local"),
            password_hash=hash_password(os.getenv("ADMIN_PASSWORD", "Admin123!")),
            role=AdminRole.SUPERADMIN,
            is_active=True
        )
        
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        
        print()
        print("=" * 50)
        print("✅ Superadmin criado com sucesso!")
        print("=" * 50)
        print()
        print(f"   👤 Username: {admin.username}")
        print(f"   📧 Email: {admin.email}")
        print(f"   🔑 Senha: {os.getenv('ADMIN_PASSWORD', 'Admin123!')}")
        print()
        print("⚠️  IMPORTANTE: Altere a senha após o primeiro login!")
        print()


if __name__ == "__main__":
    asyncio.run(init_production_db())

