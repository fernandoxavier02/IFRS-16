"""
Rotas para integração com Stripe
Gerenciamento de checkout e portal do cliente
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional
import stripe

from ..database import get_db
from ..config import get_settings
from ..auth import get_current_user
from ..models import User

settings = get_settings()
stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter(prefix="/api/stripe", tags=["Stripe"])


class CheckoutSessionRequest(BaseModel):
    """Request para criar sessão de checkout"""
    price_id: str = Field(..., description="ID do preço do Stripe")
    success_url: Optional[str] = Field(None, description="URL de sucesso (opcional)")
    cancel_url: Optional[str] = Field(None, description="URL de cancelamento (opcional)")


class CheckoutSessionResponse(BaseModel):
    """Response com URL da sessão de checkout"""
    session_id: str
    url: str


class PortalSessionResponse(BaseModel):
    """Response com URL do portal do cliente"""
    url: str


@router.post(
    "/create-checkout-session",
    response_model=CheckoutSessionResponse,
    summary="Criar Sessão de Checkout",
    description="Cria uma sessão de checkout do Stripe para o usuário assinar um plano"
)
async def create_checkout_session(
    body: CheckoutSessionRequest,
    user_data: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cria uma sessão de checkout do Stripe.
    
    - **price_id**: ID do preço do Stripe (ex: price_1234567890)
    - **success_url**: URL para redirecionar após sucesso (opcional)
    - **cancel_url**: URL para redirecionar após cancelamento (opcional)
    
    Retorna a URL da sessão de checkout para redirecionar o usuário.
    """
    user: User = user_data["user"]
    
    # URLs padrão se não fornecidas
    success_url = body.success_url or f"{settings.FRONTEND_URL}/dashboard?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = body.cancel_url or f"{settings.FRONTEND_URL}/dashboard?canceled=true"
    
    try:
        # Verificar se usuário já tem customer_id no Stripe
        if not user.stripe_customer_id:
            # Criar customer no Stripe
            customer = stripe.Customer.create(
                email=user.email,
                name=user.name,
                metadata={
                    "user_id": str(user.id),
                    "company_name": user.company_name or ""
                }
            )
            
            # Atualizar user com stripe_customer_id
            user.stripe_customer_id = customer.id
            await db.commit()
        
        # Criar sessão de checkout
        checkout_session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": body.price_id,
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": str(user.id),
            },
            allow_promotion_codes=True,
            billing_address_collection="required",
        )
        
        return CheckoutSessionResponse(
            session_id=checkout_session.id,
            url=checkout_session.url
        )
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao criar sessão de checkout: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao processar checkout: {str(e)}"
        )


@router.post(
    "/create-portal-session",
    response_model=PortalSessionResponse,
    summary="Criar Sessão do Portal",
    description="Cria uma sessão do portal do cliente Stripe para gerenciar assinatura"
)
async def create_portal_session(
    user_data: dict = Depends(get_current_user),
    return_url: Optional[str] = None
):
    """
    Cria uma sessão do portal do cliente Stripe.
    
    Permite ao usuário:
    - Atualizar método de pagamento
    - Ver histórico de faturas
    - Cancelar assinatura
    - Atualizar informações de cobrança
    
    - **return_url**: URL para retornar após gerenciar assinatura (opcional)
    """
    user: User = user_data["user"]
    
    # Verificar se usuário tem customer_id
    if not user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário não possui conta no Stripe. Assine um plano primeiro."
        )
    
    # URL de retorno padrão
    return_url = return_url or f"{settings.FRONTEND_URL}/dashboard"
    
    try:
        # Criar sessão do portal
        portal_session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=return_url,
        )
        
        return PortalSessionResponse(url=portal_session.url)
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao criar sessão do portal: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao processar portal: {str(e)}"
        )


@router.get(
    "/prices",
    summary="Listar Preços",
    description="Lista todos os preços ativos do Stripe"
)
async def list_prices():
    """
    Lista todos os preços ativos configurados no Stripe.
    
    Útil para o frontend exibir os planos disponíveis.
    """
    try:
        prices = stripe.Price.list(active=True, expand=["data.product"])
        
        return {
            "prices": [
                {
                    "id": price.id,
                    "product_id": price.product.id if hasattr(price, 'product') else None,
                    "product_name": price.product.name if hasattr(price, 'product') else None,
                    "unit_amount": price.unit_amount,
                    "currency": price.currency,
                    "recurring": {
                        "interval": price.recurring.interval,
                        "interval_count": price.recurring.interval_count,
                    } if price.recurring else None,
                }
                for price in prices.data
            ]
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao listar preços: {str(e)}"
        )
