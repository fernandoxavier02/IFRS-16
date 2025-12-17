"""
Script para corrigir licenças sem user_id vinculando ao usuário teste
"""

import asyncio
import sys
import os
from pathlib import Path

# Adicionar backend ao path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.database import AsyncSessionLocal, init_db
from app.models import License, User
from sqlalchemy import select, update

async def corrigir_licencas():
    """Corrige licenças sem user_id vinculando ao usuário teste"""
    
    print("=" * 60)
    print("CORRIGINDO LICENÇAS DO USUÁRIO TESTE")
    print("=" * 60)
    print()
    
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # Buscar usuário teste
        result = await db.execute(
            select(User).where(User.email == "teste@contratos.com")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ ERRO: Usuário teste@contratos.com não encontrado!")
            return
        
        print(f"✅ Usuário encontrado: {user.email} (ID: {user.id})")
        print()
        
        # Buscar todas as licenças do email teste@contratos.com sem user_id
        result = await db.execute(
            select(License).where(
                License.email == "teste@contratos.com",
                License.user_id.is_(None)
            )
        )
        licenses = result.scalars().all()
        
        if not licenses:
            print("✅ Nenhuma licença sem user_id encontrada para corrigir.")
            return
        
        print(f"📋 Encontradas {len(licenses)} licença(s) para corrigir:")
        print()
        
        for lic in licenses:
            print(f"  - {lic.key} ({lic.license_type.value})")
        
        print()
        print("🔧 Corrigindo licenças...")
        
        # Atualizar todas as licenças
        await db.execute(
            update(License)
            .where(
                License.email == "teste@contratos.com",
                License.user_id.is_(None)
            )
            .values(user_id=user.id)
        )
        
        await db.commit()
        
        print("✅ Licenças corrigidas com sucesso!")
        print()
        
        # Verificar resultado
        result = await db.execute(
            select(License).where(License.email == "teste@contratos.com")
        )
        all_licenses = result.scalars().all()
        
        print("📋 Status final das licenças:")
        for lic in all_licenses:
            status = "✅ Vinculada" if lic.user_id == user.id else "❌ SEM VÍNCULO"
            print(f"  - {lic.key}: {status} (user_id: {lic.user_id})")

if __name__ == "__main__":
    asyncio.run(corrigir_licencas())
