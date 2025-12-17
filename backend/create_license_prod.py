"""Criar licenca de teste no banco de producao"""
import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta
sys.path.insert(0, '.')
os.environ['DATABASE_URL'] = 'postgresql://ifrs16_database_user:DmgbPA9jjyA587ot8Rc4Kt4fnAr0opM7@dpg-d4qvp9ggjchc73bk1rvg-a.virginia-postgres.render.com/ifrs16_database'

from app.database import AsyncSessionLocal
from app.models import License, LicenseStatus, LicenseType

async def create():
    async with AsyncSessionLocal() as db:
        # Gerar chave de licenca
        license_key = f"IFRS16-{uuid.uuid4().hex[:8].upper()}-PROD"
        
        license = License(
            key=license_key,
            customer_name="Fernando Xavier",
            email="fernandocostaxavier@gmail.com",
            license_type=LicenseType.PRO,
            status=LicenseStatus.ACTIVE,
            expires_at=datetime.utcnow() + timedelta(days=365),
            max_activations=5,
            current_activations=0
        )
        
        db.add(license)
        await db.commit()
        await db.refresh(license)
        
        print()
        print("=" * 50)
        print("LICENCA CRIADA COM SUCESSO!")
        print("=" * 50)
        print()
        print(f"Chave: {license_key}")
        print(f"Cliente: Fernando Xavier")
        print(f"Tipo: PROFESSIONAL")
        print(f"Expira em: {license.expires_at}")
        print()
        print("Use esta chave no frontend para testar!")
        print()

asyncio.run(create())

