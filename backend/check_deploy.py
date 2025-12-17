"""
Script para verificar se o deploy está funcionando corretamente
"""

import asyncio
import sys
import os
sys.path.insert(0, '.')

from app.database import AsyncSessionLocal, init_db
from app.models import AdminUser, User, License, Subscription
from sqlalchemy import select, func
from app.config import get_settings

settings = get_settings()


async def check_deploy():
    """Verifica o status do deploy"""
    print("=" * 50)
    print("🔍 Verificação de Deploy - IFRS 16")
    print("=" * 50)
    print()
    
    # Verificar configurações
    print("📋 Configurações:")
    print(f"   Ambiente: {settings.ENVIRONMENT}")
    print(f"   Debug: {settings.DEBUG}")
    print(f"   Database URL: {settings.DATABASE_URL[:30]}...")
    print()
    
    # Verificar conexão com banco
    print("🔌 Testando conexão com banco de dados...")
    try:
        async with AsyncSessionLocal() as db:
            # Testar query simples
            result = await db.execute(select(func.count()).select_from(AdminUser))
            admin_count = result.scalar() or 0
            
            result = await db.execute(select(func.count()).select_from(User))
            user_count = result.scalar() or 0
            
            result = await db.execute(select(func.count()).select_from(License))
            license_count = result.scalar() or 0
            
            result = await db.execute(select(func.count()).select_from(Subscription))
            subscription_count = result.scalar() or 0
            
            print("✅ Conexão com banco OK!")
            print()
            print("📊 Estatísticas:")
            print(f"   Admins: {admin_count}")
            print(f"   Usuários: {user_count}")
            print(f"   Licenças: {license_count}")
            print(f"   Assinaturas: {subscription_count}")
            print()
            
            # Verificar se existe admin
            if admin_count == 0:
                print("⚠️  Nenhum admin encontrado!")
                print("   Execute: python init_production_db.py")
            else:
                result = await db.execute(
                    select(AdminUser).where(AdminUser.role == "superadmin")
                )
                superadmin = result.scalar_one_or_none()
                if superadmin:
                    print(f"✅ Superadmin encontrado: {superadmin.username}")
                else:
                    print("⚠️  Nenhum superadmin encontrado!")
            
    except Exception as e:
        print(f"❌ Erro ao conectar ao banco: {str(e)}")
        return False
    
    print()
    print("=" * 50)
    print("✅ Verificação concluída!")
    print("=" * 50)
    
    return True


if __name__ == "__main__":
    asyncio.run(check_deploy())

