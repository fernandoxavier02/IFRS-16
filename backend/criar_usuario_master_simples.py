"""
Script simples para criar usuário master no ambiente de produção
"""

import asyncio
import sys
import os

# Adicionar o diretório app ao path
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from uuid import uuid4
import secrets
import string

from app.models import User, License, LicenseStatus, LicenseType
from app.auth import hash_password

DATABASE_URL = "postgresql+asyncpg://ifrs16_database_ycs3_user:WUhx3D36NZVEytmT3a90c6ZWNog2pGEZ@dpg-d4r4lrmr433s738i13u0-a.virginia-postgres.render.com:5432/ifrs16_database_ycs3"

def gerar_chave_licenca():
    """Gera uma chave de licença no formato XXXX-XXXX-XXXX-XXXX"""
    chars = string.ascii_uppercase + string.digits
    parts = []
    for _ in range(4):
        part = ''.join(secrets.choice(chars) for _ in range(4))
        parts.append(part)
    return '-'.join(parts)

async def criar_usuario_master():
    print("=" * 70)
    print("👤 CRIAR USUÁRIO MASTER - AMBIENTE DE PRODUÇÃO")
    print("=" * 70)
    print()
    
    # Dados
    nome = "Master User"
    email = "fernandocostaxavier@gmail.com"
    senha = "Master@2025!"
    tipo_licenca = LicenseType.ENTERPRISE
    validade_dias = 3650  # 10 anos
    
    print(f"📋 Nome: {nome}")
    print(f"📧 Email: {email}")
    print(f"🔑 Senha: {senha}")
    print(f"📦 Licença: {tipo_licenca.value}")
    print()
    
    # Criar engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Verificar se usuário existe
            result = await session.execute(
                select(User).where(User.email == email.lower())
            )
            user = result.scalar_one_or_none()
            
            if user:
                print(f"⚠️  Usuário já existe (ID: {user.id})")
                # Atualizar senha
                user.password_hash = hash_password(senha)
                user.is_active = True
                user.email_verified = True
                print("✅ Senha atualizada!")
            else:
                # Criar usuário
                user = User(
                    id=uuid4(),
                    name=nome,
                    email=email.lower(),
                    password_hash=hash_password(senha),
                    is_active=True,
                    email_verified=True,
                    created_at=datetime.utcnow()
                )
                session.add(user)
                print(f"✅ Usuário criado (ID: {user.id})")
            
            await session.commit()
            print()
            
            # Verificar licença
            result = await session.execute(
                select(License).where(
                    License.user_id == user.id,
                    License.status == LicenseStatus.ACTIVE
                )
            )
            license = result.scalar_one_or_none()
            
            if license:
                print(f"⚠️  Licença ativa já existe:")
                print(f"   Chave: {license.key}")
                print(f"   Tipo: {license.license_type.value}")
                print(f"   Expira: {license.expires_at}")
                chave = license.key
                expira = license.expires_at
            else:
                # Criar licença
                chave = gerar_chave_licenca()
                expira = datetime.utcnow() + timedelta(days=validade_dias)
                
                license = License(
                    id=uuid4(),
                    key=chave,
                    user_id=user.id,
                    customer_name=nome,
                    email=email.lower(),
                    status=LicenseStatus.ACTIVE,
                    license_type=tipo_licenca,
                    max_activations=999,
                    current_activations=0,
                    expires_at=expira,
                    created_at=datetime.utcnow()
                )
                session.add(license)
                await session.commit()
                
                print(f"✅ Licença criada:")
                print(f"   Chave: {chave}")
                print(f"   Tipo: {tipo_licenca.value}")
                print(f"   Expira: {expira.strftime('%d/%m/%Y')}")
            
            print()
            print("=" * 70)
            print("📋 CREDENCIAIS - AMBIENTE DE PRODUÇÃO")
            print("=" * 70)
            print()
            print(f"🌐 URL: https://ifrs-16-1.onrender.com/Calculadora_IFRS16_Deploy.html")
            print()
            print(f"👤 Login:")
            print(f"   Email: {email}")
            print(f"   Senha: {senha}")
            print()
            print(f"🔑 Chave de Licença: {chave}")
            print(f"📦 Tipo: {tipo_licenca.value}")
            print(f"⏰ Válida até: {expira.strftime('%d/%m/%Y')}")
            print()
            print("=" * 70)
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
        finally:
            await engine.dispose()

if __name__ == "__main__":
    asyncio.run(criar_usuario_master())

