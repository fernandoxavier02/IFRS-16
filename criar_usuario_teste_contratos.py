"""
Script para criar usuário comum com licença Trial para testar contratos
"""

import asyncio
import sys
import os
from pathlib import Path

# Adicionar backend ao path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.database import AsyncSessionLocal, init_db
from app.models import User, License, LicenseStatus, LicenseType
from app.auth import hash_password
from datetime import datetime, timedelta
from uuid import uuid4

async def criar_usuario_teste():
    """Cria usuário comum com licença Trial para testar contratos"""
    
    print("=" * 60)
    print("CRIAR USUARIO DE TESTE PARA CONTRATOS")
    print("=" * 60)
    print()
    
    # Inicializar banco
    print("Inicializando banco de dados...")
    await init_db()
    print("OK: Banco inicializado")
    print()
    
    async with AsyncSessionLocal() as db:
        # Verificar se usuário já existe
        from sqlalchemy import select
        result = await db.execute(
            select(User).where(User.email == "teste@contratos.com")
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"AVISO: Usuario ja existe: {existing_user.email}")
            user = existing_user
        else:
            # Criar usuário
            print("Criando usuario de teste...")
            user = User(
                id=uuid4(),
                email="teste@contratos.com",
                name="Usuario Teste Contratos",
                password_hash=hash_password("Teste123!"),
                is_active=True,
                email_verified=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print("OK: Usuario criado")
            print()
        
        # Verificar se já tem licença
        result = await db.execute(
            select(License).where(
                License.user_id == user.id,
                License.status == LicenseStatus.ACTIVE
            )
        )
        existing_license = result.scalar_one_or_none()
        
        if existing_license:
            print(f"AVISO: Licenca ja existe: {existing_license.key}")
            license = existing_license
        else:
            # Criar licença Trial
            print("Criando licenca Trial...")
            license = License(
                id=uuid4(),
                key=f"TRIAL-TEST-{uuid4().hex[:8].upper()}",
                user_id=user.id,
                customer_name="Usuario Teste Contratos",
                email="teste@contratos.com",
                status=LicenseStatus.ACTIVE,
                license_type=LicenseType.TRIAL,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=7),
                revoked=False,
                max_activations=1,
                current_activations=0,
            )
            db.add(license)
            await db.commit()
            await db.refresh(license)
            print("OK: Licenca Trial criada")
            print()
        
        print("=" * 60)
        print("CREDENCIAIS DO USUARIO DE TESTE")
        print("=" * 60)
        print(f"   Email: {user.email}")
        print(f"   Senha: Teste123!")
        print(f"   Licenca: {license.key}")
        print(f"   Tipo: {license.license_type.value}")
        print(f"   Limite de contratos: 5 (Trial)")
        print()
        print("Use estas credenciais para testar os endpoints de contratos")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(criar_usuario_teste())
