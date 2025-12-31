"""
Endpoints de pagamento e integração Stripe
"""

import stripe
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..database import get_db
from ..auth import get_current_user
from ..schemas import (
    CreateCheckoutRequest,
    CheckoutResponse,
    PortalResponse,
    InvoiceResponse,
    PlanTypeEnum,
)
from ..models import PlanType
from ..services.stripe_service import StripeService
from ..config import get_settings, LICENSE_LIMITS

settings = get_settings()

router = APIRouter(prefix="/api/payments", tags=["Pagamentos"])
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/create-checkout",
    response_model=CheckoutResponse,
    summary="Criar Sessão de Checkout",
    description="Cria uma sessão de checkout do Stripe para pagamento"
)
async def create_checkout(
    body: CreateCheckoutRequest,
    user_data: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cria uma sessão de checkout do Stripe.
    
    - **plan_type**: Tipo do plano (monthly, yearly, lifetime)
    - **success_url**: URL de redirecionamento após sucesso (opcional)
    - **cancel_url**: URL de redirecionamento após cancelamento (opcional)
    
    Retorna a URL do checkout para redirecionar o usuário.
    """
    user = user_data["user"]
    plan_type = PlanType(body.plan_type.value)
    
    try:
        result = await StripeService.create_checkout_session(
            db=db,
            user=user,
            plan_type=plan_type,
            success_url=body.success_url,
            cancel_url=body.cancel_url
        )
        
        return CheckoutResponse(
            checkout_url=result["checkout_url"],
            session_id=result["session_id"]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no Stripe: {str(e)}"
        )


@router.get(
    "/portal",
    response_model=PortalResponse,
    summary="Portal do Cliente",
    description="Retorna URL do portal do cliente Stripe para gerenciar assinatura"
)
async def get_customer_portal(
    return_url: str = None,
    user_data: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Gera URL do portal do cliente Stripe.
    
    O portal permite que o usuário:
    - Veja faturas
    - Atualize método de pagamento
    - Cancele assinatura
    - Altere plano
    """
    user = user_data["user"]
    
    if not user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você ainda não tem uma assinatura ativa"
        )
    
    try:
        portal_url = await StripeService.create_customer_portal_session(
            db=db,
            user=user,
            return_url=return_url
        )
        
        return PortalResponse(portal_url=portal_url)
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no Stripe: {str(e)}"
        )


@router.get(
    "/invoices",
    response_model=list[InvoiceResponse],
    summary="Listar Faturas",
    description="Lista as faturas do usuário"
)
async def list_invoices(
    limit: int = 10,
    user_data: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista as faturas do usuário no Stripe.
    """
    user = user_data["user"]
    
    if not user.stripe_customer_id:
        return []
    
    try:
        invoices = await StripeService.get_customer_invoices(user, limit=limit)
        return [InvoiceResponse(**inv) for inv in invoices]
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro no Stripe: {str(e)}"
        )


@router.post(
    "/webhook",
    summary="Webhook Stripe",
    description="Endpoint para receber webhooks do Stripe",
    include_in_schema=False  # Não mostrar na documentação
)
@limiter.limit("100/minute")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature")
):
    """
    Recebe e processa webhooks do Stripe.
    
    Eventos tratados:
    - checkout.session.completed
    - invoice.paid
    - invoice.payment_failed
    - customer.subscription.deleted
    """
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe-Signature header ausente"
        )
    
    # Ler payload raw
    payload = await request.body()
    
    try:
        event = StripeService.construct_webhook_event(
            payload,
            stripe_signature
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload inválido"
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assinatura inválida"
        )
    
    event_type = event["type"]
    data = event["data"]["object"]
    
    print(f"📥 Webhook recebido: {event_type}")
    print(f"📦 Dados: customer={data.get('customer')}, email={data.get('customer_details', {}).get('email')}")
    
    # Criar nova sessão de DB para cada webhook (evita problemas de conexão)
    from ..database import AsyncSessionLocal
    import asyncio
    
    # Retry logic para lidar com cold start do DB free-tier
    max_retries = 3
    retry_delay = 2  # segundos
    
    for attempt in range(max_retries):
        try:
            print(f"🔄 Tentativa {attempt + 1}/{max_retries}")
            
            async with AsyncSessionLocal() as db:
                # Processar evento
                if event_type == "checkout.session.completed":
                    print("🔄 Processando checkout.session.completed...")
                    result = await StripeService.handle_checkout_completed(db, data)
                    print(f"✅ Resultado: {result}")
                
                elif event_type == "invoice.paid":
                    await StripeService.handle_invoice_paid(db, data)
                
                elif event_type == "invoice.payment_failed":
                    await StripeService.handle_invoice_payment_failed(db, data)
                
                elif event_type == "customer.subscription.deleted":
                    await StripeService.handle_subscription_deleted(db, data)
                
                else:
                    print(f"⚠️ Evento não tratado: {event_type}")
                
                # Commit explícito
                await db.commit()
                print("✅ Webhook processado com sucesso!")
                break  # Sucesso, sair do loop
                
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"❌ ERRO na tentativa {attempt + 1}: {error_msg}")
            
            if attempt < max_retries - 1:
                print(f"⏳ Aguardando {retry_delay}s antes de tentar novamente...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Backoff exponencial
            else:
                # Última tentativa falhou
                print(f"❌ FALHA após {max_retries} tentativas")
                import traceback
                traceback.print_exc()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Erro ao processar webhook: {error_msg}"
                )
    
    return {"received": True}


# Endpoint público para obter preços (sem autenticação)
@router.get(
    "/prices",
    summary="Listar Preços",
    description="Retorna os preços dos planos disponíveis"
)
async def get_prices():
    """
    Retorna informações dos planos disponíveis.

    Usa PLAN_CONFIG como única fonte de verdade.

    Preços por CNPJ:
    - Básico: R$ 299/mês ou R$ 3.229,20/ano (10% desc) - até 3 contratos
    - Pro: R$ 499/mês ou R$ 5.389,20/ano (10% desc) - até 20 contratos
    - Enterprise: R$ 999/mês ou R$ 10.789,20/ano (10% desc) - ilimitado
    """
    from ..config import PLAN_CONFIG, get_plan_config

    plans = []
    for plan_key in PLAN_CONFIG.keys():
        try:
            config = get_plan_config(plan_key)

            # Montar lista de features baseada na config
            features_list = []

            # Contratos
            max_contracts = config["max_contracts"]
            if max_contracts == -1:
                features_list.append("Contratos ilimitados por CNPJ")
            else:
                features_list.append(f"Até {max_contracts} contratos por CNPJ")

            # Features do plano
            plan_features = config.get("features", {})
            if plan_features.get("export_excel") or plan_features.get("export_csv"):
                features_list.append("Exportação Excel e CSV")

            # Suporte
            support_type = plan_features.get("support", "email")
            if support_type == "email":
                features_list.append("Suporte por email")
            elif support_type == "priority":
                features_list.append("Suporte prioritário")
            elif support_type == "dedicated":
                features_list.append("Suporte dedicado + SLA")

            # Multi-user
            if plan_features.get("multi_user"):
                max_users = plan_features.get("max_users", 5)
                if max_users == -1:
                    features_list.append("Usuários ilimitados")
                else:
                    features_list.append(f"Multi-usuário (até {max_users})")

            # API
            if plan_features.get("api_access"):
                features_list.append("API de integração")

            # Treinamento
            if plan_features.get("training"):
                features_list.append("Treinamento incluído")

            # Economia para planos anuais
            if "yearly" in plan_key:
                monthly_equivalent = config["amount"] / 12
                yearly_price = config["amount"]
                monthly_plan_key = plan_key.replace("yearly", "monthly")

                if monthly_plan_key in PLAN_CONFIG:
                    monthly_config = get_plan_config(monthly_plan_key)
                    monthly_price = monthly_config["amount"]
                    savings = (monthly_price * 12) - yearly_price
                    if savings > 0:
                        features_list.append(f"Economia de R$ {savings:,.2f}")

            plans.append({
                "type": plan_key,
                "name": config["display_name"],
                "price": float(config["amount"]),
                "currency": config["currency"],
                "interval": "year" if "yearly" in plan_key else "month",
                "max_contracts": config["max_contracts"],
                "price_id": config["price_id"],
                "features": features_list
            })

        except ValueError as e:
            print(f"⚠️ Erro ao carregar plano {plan_key}: {e}")
            continue

    return {"plans": plans}
