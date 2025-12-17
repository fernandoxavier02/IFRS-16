"""
Script para criar usuário master no Cloud SQL
"""
import asyncio
import os
import sys
sys.path.insert(0, '.')

# Configurar DATABASE_URL do Cloud SQL
os.environ['DATABASE_URL'] = 'postgresql://ifrs16_user:ihU40nPKL38tCzTFvfNM@136.112.221.225:5432/ifrs16_licenses'
os.environ['ENVIRONMENT'] = 'production'

from sqlalchemy import select
from app.database import AsyncSessionLocal, init_db
from app.models import AdminUser, AdminRole
from app.auth import hash_password


async def create_master():
    print("=" * 50)
    print("Criando Usuario Master no Cloud SQL")
    print("=" * 50)
    
    # Inicializar banco (criar tabelas se não existirem)
    try:
        await init_db()
        print("Banco inicializado")
    except Exception as e:
        print(f"AVISO ao inicializar banco: {e}")
        # Continuar mesmo com erro - tabelas podem já existir
    
    async with AsyncSessionLocal() as db:
        # Verificar se já existe
        result = await db.execute(
            select(AdminUser).where(
                (AdminUser.username == "master") | 
                (AdminUser.email == "fernandocostaxavier@gmail.com")
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"Usuario master ja existe: {existing.username} ({existing.email})")
            print("Atualizando senha...")
            existing.password_hash = hash_password("Master@2025!")
            existing.role = AdminRole.SUPERADMIN
            existing.is_active = True
            await db.commit()
            print("OK: Senha atualizada!")
        else:
            # Criar usuário master
            admin = AdminUser(
                username="master",
                email="fernandocostaxavier@gmail.com",
                password_hash=hash_password("Master@2025!"),
                role=AdminRole.SUPERADMIN,
                is_active=True
            )
            
            db.add(admin)
            await db.commit()
            await db.refresh(admin)
            
            print()
            print("OK: Usuario master criado com sucesso!")
        
        print()
        print("=" * 50)
        print("CREDENCIAIS DO USUARIO MASTER")
        print("=" * 50)
        print("   Username: master")
        print("   Email: fernandocostaxavier@gmail.com")
        print("   Senha: Master@2025!")
        print("   Role: superadmin")
        print()
        print("Acesse: https://ifrs16-app.web.app/login.html")
        print("   Use a aba 'Administrador' para fazer login")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(create_master())
