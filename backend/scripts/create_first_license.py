"""
Script para criar a primeira licença no banco de dados
Execute: python -m scripts.create_first_license
"""

import asyncio
import sys
from pathlib import Path

# Adicionar pasta raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import AsyncSessionLocal, init_db
from app.models import License, LicenseStatus, LicenseType
from app.crud import generate_license_key


async def create_first_license():
    """Cria a primeira licença administrativa"""
    
    print("=" * 60)
    print("IFRS 16 - Criação de Licença Administrativa")
    print("=" * 60)
    
    # Inicializar banco
    print("\n📦 Inicializando banco de dados...")
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # Verificar se já existe alguma licença
        from sqlalchemy import select, func
        result = await db.execute(select(func.count(License.id)))
        count = result.scalar()
        
        if count > 0:
            print(f"\n⚠️  Já existem {count} licença(s) no banco de dados.")
            confirm = input("Deseja criar uma nova licença mesmo assim? (s/N): ")
            if confirm.lower() != 's':
                print("Operação cancelada.")
                return
        
        # Coletar dados
        print("\n📝 Dados da nova licença:")
        customer_name = input("Nome do cliente [Admin]: ").strip() or "Admin"
        email = input("Email [admin@ifrs16.local]: ").strip() or "admin@ifrs16.local"
        
        print("\nTipos de licença disponíveis:")
        print("  1 - trial (demonstração)")
        print("  2 - basic")
        print("  3 - pro")
        print("  4 - enterprise")
        
        type_choice = input("Tipo [4]: ").strip() or "4"
        type_map = {"1": LicenseType.TRIAL, "2": LicenseType.BASIC, "3": LicenseType.PRO, "4": LicenseType.ENTERPRISE}
        license_type = type_map.get(type_choice, LicenseType.ENTERPRISE)
        
        permanent = input("Licença permanente (sem expiração)? (S/n): ").strip().lower()
        expires_at = None
        if permanent == 'n':
            months = int(input("Duração em meses: ") or "12")
            from datetime import datetime, timedelta
            expires_at = datetime.utcnow() + timedelta(days=30 * months)
        
        # Gerar chave
        key = generate_license_key(license_type)
        
        # Criar licença
        license = License(
            key=key,
            customer_name=customer_name,
            email=email,
            license_type=license_type,
            status=LicenseStatus.ACTIVE,
            expires_at=expires_at,
            max_activations=5 if license_type == LicenseType.ENTERPRISE else 1,
        )
        
        db.add(license)
        await db.commit()
        
        print("\n" + "=" * 60)
        print("✅ LICENÇA CRIADA COM SUCESSO!")
        print("=" * 60)
        print(f"\n🔑 Chave: {key}")
        print(f"👤 Cliente: {customer_name}")
        print(f"📧 Email: {email}")
        print(f"📦 Tipo: {license_type.value}")
        print(f"📅 Expira: {'Nunca (permanente)' if not expires_at else expires_at.strftime('%d/%m/%Y')}")
        print("\n⚠️  GUARDE ESTA CHAVE! Ela será usada para ativar a calculadora.")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(create_first_license())

