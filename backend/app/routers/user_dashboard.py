"""
Endpoints do painel do usuário
"""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..auth import get_current_user, get_current_user_with_session
from ..models import (
    User, License, Subscription,
    LicenseStatus, SubscriptionStatus
)
from ..schemas import (
    UserResponse,
    UserUpdateRequest,
    SubscriptionResponse,
    SubscriptionWithLicenseResponse,
    LicenseFullResponse,
    LicenseTypeEnum,
)
from ..services.stripe_service import StripeService

router = APIRouter(prefix="/api/user", tags=["Painel do Usuário"])


@router.get(
    "/profile",
    response_model=UserResponse,
    summary="Perfil do Usuário",
    description="Retorna os dados do perfil do usuário"
)
async def get_profile(
    user_data: dict = Depends(get_current_user_with_session)
):
    """
    Retorna os dados do perfil do usuário autenticado.
    """
    user = user_data["user"]
    return UserResponse.model_validate(user)


@router.put(
    "/profile",
    response_model=UserResponse,
    summary="Atualizar Perfil",
    description="Atualiza os dados do perfil do usuário"
)
async def update_profile(
    body: UserUpdateRequest,
    user_data: dict = Depends(get_current_user_with_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza os dados do perfil do usuário.
    
    - **name**: Novo nome (opcional)
    - **email**: Novo email (opcional)
    """
    user = user_data["user"]
    
    # Verificar se novo email já existe
    if body.email and body.email.lower() != user.email:
        result = await db.execute(
            select(User).where(User.email == body.email.lower())
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este email já está em uso"
            )
        user.email = body.email.lower()
    
    if body.name:
        user.name = body.name
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.get(
    "/subscription",
    summary="Assinatura Atual",
    description="Retorna a assinatura ativa do usuário com dados completos"
)
async def get_subscription(
    user_data: dict = Depends(get_current_user_with_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna a assinatura ativa do usuário com dados da licença e contagem de contratos.
    """
    user = user_data["user"]

    # Buscar assinatura ativa (pega a mais recente se houver múltiplas)
    result = await db.execute(
        select(Subscription)
        .where(
            Subscription.user_id == user.id,
            Subscription.status.in_([
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIALING,
                SubscriptionStatus.PAST_DUE
            ])
        )
        .options(selectinload(Subscription.license))
        .order_by(Subscription.created_at.desc())
    )
    subscription = result.scalars().first()

    if not subscription:
        return None

    # Buscar contratos do usuário
    from ..models import Contract
    from sqlalchemy import func

    contracts_result = await db.execute(
        select(func.count())
        .select_from(Contract)
        .where(Contract.user_id == user.id)
    )
    contracts_count = contracts_result.scalar() or 0

    license_data = None
    if subscription.license:
        license_data = {
            "key": subscription.license.key,
            "type": subscription.license.license_type.value,
            "status": subscription.license.status.value,
            "expires_at": subscription.license.expires_at.isoformat() if subscription.license.expires_at else None,
            "features": subscription.license.features
        }

    return {
        "status": subscription.status.value,
        "plan_type": subscription.plan_type.value,
        "current_period_start": subscription.current_period_start.isoformat() if subscription.current_period_start else None,
        "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
        "cancel_at_period_end": subscription.cancel_at_period_end,
        "stripe_subscription_id": subscription.stripe_subscription_id,
        "license": license_data,
        "contracts_count": contracts_count
    }


@router.get(
    "/licenses",
    response_model=List[LicenseFullResponse],
    summary="Licenças do Usuário",
    description="Lista todas as licenças do usuário"
)
async def get_licenses(
    user_data: dict = Depends(get_current_user_with_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todas as licenças associadas ao usuário.
    """
    user = user_data["user"]
    
    result = await db.execute(
        select(License)
        .where(License.user_id == user.id)
        .order_by(License.created_at.desc())
    )
    licenses = result.scalars().all()
    
    return [LicenseFullResponse.model_validate(lic) for lic in licenses]


@router.post(
    "/cancel-subscription",
    summary="Cancelar Assinatura",
    description="Cancela a assinatura no final do período atual"
)
async def cancel_subscription(
    user_data: dict = Depends(get_current_user_with_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancela a assinatura do usuário.
    
    A assinatura permanecerá ativa até o final do período pago.
    """
    user = user_data["user"]
    
    # Buscar assinatura ativa
    result = await db.execute(
        select(Subscription)
        .where(
            Subscription.user_id == user.id,
            Subscription.status == SubscriptionStatus.ACTIVE
        )
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma assinatura ativa encontrada"
        )
    
    # Cancelar no Stripe se for subscription recorrente
    if subscription.stripe_subscription_id:
        import stripe
        from ..config import get_settings
        settings = get_settings()
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        try:
            # Cancelar ao final do período
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True
            )
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao cancelar no Stripe: {str(e)}"
            )
    
    subscription.cancel_at_period_end = True
    await db.commit()
    
    return {
        "success": True,
        "message": "Assinatura será cancelada ao final do período atual",
        "ends_at": subscription.current_period_end.isoformat() if subscription.current_period_end else None
    }


@router.post(
    "/reactivate-subscription",
    summary="Reativar Assinatura",
    description="Cancela o pedido de cancelamento da assinatura"
)
async def reactivate_subscription(
    user_data: dict = Depends(get_current_user_with_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Reativa uma assinatura que estava marcada para cancelamento.
    """
    user = user_data["user"]
    
    result = await db.execute(
        select(Subscription)
        .where(
            Subscription.user_id == user.id,
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.cancel_at_period_end == True
        )
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma assinatura pendente de cancelamento"
        )
    
    # Reativar no Stripe
    if subscription.stripe_subscription_id:
        import stripe
        from ..config import get_settings
        settings = get_settings()
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        try:
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=False
            )
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao reativar no Stripe: {str(e)}"
            )
    
    subscription.cancel_at_period_end = False
    await db.commit()
    
    return {
        "success": True,
        "message": "Assinatura reativada com sucesso"
    }


@router.get(
    "/dashboard-summary",
    summary="Resumo do Dashboard",
    description="Retorna resumo para o dashboard do usuário"
)
async def get_dashboard_summary(
    user_data: dict = Depends(get_current_user_with_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna um resumo com todas as informações para o dashboard.
    """
    user = user_data["user"]
    
    # Buscar assinatura ativa
    result = await db.execute(
        select(Subscription)
        .where(
            Subscription.user_id == user.id,
            Subscription.status.in_([
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIALING,
                SubscriptionStatus.PAST_DUE
            ])
        )
        .options(selectinload(Subscription.license))
        .order_by(Subscription.created_at.desc())
    )
    subscription = result.scalar_one_or_none()
    
    # Buscar licença ativa
    license_data = None
    if subscription and subscription.license:
        license_data = {
            "key": subscription.license.key,
            "type": subscription.license.license_type.value,
            "status": subscription.license.status.value,
            "expires_at": subscription.license.expires_at.isoformat() if subscription.license.expires_at else None,
            "features": subscription.license.features
        }
    
    # Contar validações recentes
    from sqlalchemy import func
    from ..models import ValidationLog
    
    validations_count = 0
    if license_data:
        result = await db.execute(
            select(func.count())
            .select_from(ValidationLog)
            .where(ValidationLog.license_key == license_data["key"])
        )
        validations_count = result.scalar() or 0
    
    return {
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "email_verified": user.email_verified,
            "created_at": user.created_at.isoformat()
        },
        "subscription": {
            "active": subscription is not None,
            "plan": subscription.plan_type.value if subscription else None,
            "status": subscription.status.value if subscription else None,
            "period_end": subscription.current_period_end.isoformat() if subscription and subscription.current_period_end else None,
            "cancel_at_period_end": subscription.cancel_at_period_end if subscription else False
        } if subscription else None,
        "license": license_data,
        "stats": {
            "total_validations": validations_count
        }
    }

