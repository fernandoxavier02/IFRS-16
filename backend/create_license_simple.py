"""
Script simplificado para criar primeira licença
"""
import asyncio
import os
from datetime import datetime, timedelta

# Configurar SQLite
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./ifrs16_licenses.db"

async def create_license():
    """Cria uma licença de exemplo"""
    from app.database import AsyncSessionLocal, init_db
    from app.models import License, LicenseStatus, LicenseType
    from app.crud import generate_license_key
    
    # Inicializar banco
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # Verificar se já existe
        from sqlalchemy import select, func
        result = await db.execute(select(func.count(License.id)))
        count = result.scalar()
        
        if count > 0:
            print(f"⚠️  Já existem {count} licença(s) no banco.")
            # Buscar primeira licença
            result = await db.execute(select(License).limit(1))
            license = result.scalar_one_or_none()
            if license:
                print(f"\n✅ Licença existente encontrada:")
                print(f"🔑 Chave: {license.key}")
                print(f"👤 Cliente: {license.customer_name}")
                print(f"📧 Email: {license.email}")
                return license.key
        
        # Criar nova licença
        key = generate_license_key(LicenseType.PRO)
        license = License(
            key=key,
            customer_name="Admin",
            email="admin@ifrs16.local",
            license_type=LicenseType.PRO,
            status=LicenseStatus.ACTIVE,
            expires_at=None,  # Permanente
            max_activations=5,
        )
        
        db.add(license)
        await db.commit()
        await db.refresh(license)
        
        print("\n" + "=" * 60)
        print("✅ LICENÇA CRIADA COM SUCESSO!")
        print("=" * 60)
        print(f"\n🔑 Chave: {key}")
        print(f"👤 Cliente: Admin")
        print(f"📧 Email: admin@ifrs16.local")
        print(f"📦 Tipo: pro")
        print(f"📅 Expira: Nunca (permanente)")
        print("\n⚠️  GUARDE ESTA CHAVE! Ela será usada para ativar a calculadora.")
        print("=" * 60)
        
        return key

if __name__ == "__main__":
    key = asyncio.run(create_license())
    print(f"\n💡 Use esta chave no HTML: {key}")

