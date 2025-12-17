"""
Script para testar o fluxo de webhook do Stripe localmente.
Simula o evento checkout.session.completed.
"""

import asyncio
import sys
sys.path.insert(0, '.')

from app.database import AsyncSessionLocal
from app.services.stripe_service import StripeService
from app.models import User, License, Subscription
from sqlalchemy import select


async def test_checkout_flow():
    """Testa o fluxo de criação de licença via webhook"""
    
    print("=" * 60)
    print("🧪 TESTE DO FLUXO DE CHECKOUT")
    print("=" * 60)
    
    # Simular dados do checkout session
    mock_session = {
        "id": "cs_test_local_123",
        "customer": "cus_test_local_123",
        "customer_email": "teste.webhook@exemplo.com",
        "customer_details": {
            "email": "teste.webhook@exemplo.com",
            "name": "Usuario Teste Webhook"
        },
        "subscription": "sub_test_local_123",
        "metadata": {},  # Sem metadata = fluxo Pricing Table
        "line_items": {
            "data": [
                {
                    "price": {
                        "id": "price_1Sbs0oGEyVmwHCe6P9IylBWe"  # Básico Mensal
                    }
                }
            ]
        }
    }
    
    print("\n📦 Dados do checkout simulado:")
    print(f"   Email: {mock_session['customer_email']}")
    print(f"   Nome: {mock_session['customer_details']['name']}")
    print(f"   Price ID: {mock_session['line_items']['data'][0]['price']['id']}")
    
    async with AsyncSessionLocal() as db:
        try:
            # Verificar se usuário já existe
            result = await db.execute(
                select(User).where(User.email == mock_session['customer_email'])
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"\n⚠️ Usuário já existe: {existing_user.email}")
                print(f"   ID: {existing_user.id}")
                
                # Verificar licenças existentes
                result = await db.execute(
                    select(License).where(License.user_id == existing_user.id)
                )
                licenses = result.scalars().all()
                print(f"   Licenças: {len(licenses)}")
                for lic in licenses:
                    print(f"      - {lic.key} ({lic.license_type.value}) - {lic.status.value}")
            else:
                print("\n✅ Usuário não existe, será criado...")
            
            # Executar o fluxo
            print("\n🚀 Executando handle_checkout_completed...")
            subscription = await StripeService.handle_checkout_completed(db, mock_session)
            
            if subscription:
                print("\n✅ SUCESSO! Subscription criada:")
                print(f"   ID: {subscription.id}")
                print(f"   User ID: {subscription.user_id}")
                print(f"   License ID: {subscription.license_id}")
                print(f"   Plan: {subscription.plan_type.value}")
                print(f"   Status: {subscription.status.value}")
                
                # Buscar licença criada
                result = await db.execute(
                    select(License).where(License.id == subscription.license_id)
                )
                license = result.scalar_one_or_none()
                
                if license:
                    print(f"\n🔑 Licença criada:")
                    print(f"   Chave: {license.key}")
                    print(f"   Tipo: {license.license_type.value}")
                    print(f"   Status: {license.status.value}")
                    print(f"   Email: {license.email}")
                    print(f"   Expira em: {license.expires_at}")
                
                # Buscar usuário criado
                result = await db.execute(
                    select(User).where(User.id == subscription.user_id)
                )
                user = result.scalar_one_or_none()
                
                if user:
                    print(f"\n👤 Usuário:")
                    print(f"   Email: {user.email}")
                    print(f"   Nome: {user.name}")
                    print(f"   Stripe Customer: {user.stripe_customer_id}")
            else:
                print("\n❌ FALHA: Nenhuma subscription retornada")
                
        except Exception as e:
            print(f"\n❌ ERRO: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🏁 TESTE FINALIZADO")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_checkout_flow())

