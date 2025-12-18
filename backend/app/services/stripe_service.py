"""
Serviço de integração com Stripe para pagamentos
"""

import stripe
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID
import secrets
import string

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..config import get_settings
from ..models import (
    User, License, Subscription,
    LicenseStatus, LicenseType, PlanType, SubscriptionStatus
)

settings = get_settings()

# Configurar Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Serviço para integração com Stripe"""
    
    # Mapeamento de planos para tipos de licença
    PLAN_LICENSE_MAP = {
        "basic_monthly": LicenseType.BASIC,
        "basic_yearly": LicenseType.BASIC,
        "pro_monthly": LicenseType.PRO,
        "pro_yearly": LicenseType.PRO,
        "enterprise_monthly": LicenseType.ENTERPRISE,
        "enterprise_yearly": LicenseType.ENTERPRISE,
        # Compatibilidade com tipos antigos
        PlanType.MONTHLY: LicenseType.BASIC,
        PlanType.YEARLY: LicenseType.PRO,
        PlanType.LIFETIME: LicenseType.ENTERPRISE,
    }
    
    # Duração dos planos em meses (None = vitalício)
    PLAN_DURATION = {
        "basic_monthly": 1,
        "basic_yearly": 12,
        "pro_monthly": 1,
        "pro_yearly": 12,
        "enterprise_monthly": 1,
        "enterprise_yearly": 12,
        # Compatibilidade com tipos antigos
        PlanType.MONTHLY: 1,
        PlanType.YEARLY: 12,
        PlanType.LIFETIME: None,
    }
    
    # Limite de contratos por plano
    PLAN_MAX_CONTRACTS = {
        "basic_monthly": 3,
        "basic_yearly": 3,
        "pro_monthly": 20,
        "pro_yearly": 20,
        "enterprise_monthly": -1,  # ilimitado
        "enterprise_yearly": -1,   # ilimitado
    }
    
    # Máximo de ativações por tipo de licença
    LICENSE_MAX_ACTIVATIONS = {
        LicenseType.TRIAL: 1,
        LicenseType.BASIC: 3,
        LicenseType.PRO: 5,
        LicenseType.ENTERPRISE: 10,  # Enterprise tem mais ativações
    }
    
    @staticmethod
    def get_price_id(plan_type) -> Optional[str]:
        """Retorna o price_id do Stripe para o plano"""
        # Converter para string se for enum
        plan_key = plan_type.value if hasattr(plan_type, 'value') else str(plan_type)
        
        price_map = {
            "basic_monthly": settings.STRIPE_PRICE_BASIC_MONTHLY,
            "basic_yearly": settings.STRIPE_PRICE_BASIC_YEARLY,
            "pro_monthly": settings.STRIPE_PRICE_PRO_MONTHLY,
            "pro_yearly": settings.STRIPE_PRICE_PRO_YEARLY,
            "enterprise_monthly": settings.STRIPE_PRICE_ENTERPRISE_MONTHLY,
            "enterprise_yearly": settings.STRIPE_PRICE_ENTERPRISE_YEARLY,
            # Compatibilidade com tipos antigos
            "monthly": settings.STRIPE_PRICE_BASIC_MONTHLY,
            "yearly": settings.STRIPE_PRICE_PRO_YEARLY,
            "lifetime": settings.STRIPE_PRICE_ENTERPRISE_YEARLY,
        }
        return price_map.get(plan_key)
    
    @staticmethod
    def generate_license_key() -> str:
        """Gera uma chave de licença única"""
        chars = string.ascii_uppercase + string.digits
        date_part = datetime.now().strftime("%Y%m%d")
        random_part = ''.join(secrets.choice(chars) for _ in range(8))
        return f"FX{date_part}-IFRS16-{random_part}"
    
    @classmethod
    async def create_or_get_customer(
        cls,
        db: AsyncSession,
        user: User
    ) -> str:
        """
        Cria ou retorna o customer_id do Stripe para o usuário.
        """
        if user.stripe_customer_id:
            return user.stripe_customer_id
        
        # Criar customer no Stripe
        customer = stripe.Customer.create(
            email=user.email,
            name=user.name,
            metadata={
                "user_id": str(user.id)
            }
        )
        
        # Salvar no banco
        user.stripe_customer_id = customer.id
        await db.commit()
        
        return customer.id
    
    @classmethod
    async def create_checkout_session(
        cls,
        db: AsyncSession,
        user: User,
        plan_type: PlanType,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Cria uma sessão de checkout do Stripe.
        
        Returns:
            Dict com checkout_url e session_id
        """
        # Obter ou criar customer
        customer_id = await cls.create_or_get_customer(db, user)
        
        # Obter price_id
        price_id = cls.get_price_id(plan_type)
        if not price_id:
            raise ValueError(f"Price ID não configurado para o plano {plan_type}")
        
        # URLs padrão
        if not success_url:
            success_url = f"{settings.FRONTEND_URL}/dashboard.html?success=true"
        if not cancel_url:
            cancel_url = f"{settings.FRONTEND_URL}/pricing.html?cancelled=true"
        
        # Configurar checkout
        checkout_params = {
            "customer": customer_id,
            "payment_method_types": ["card"],
            "line_items": [{
                "price": price_id,
                "quantity": 1,
            }],
            "success_url": success_url + "&session_id={CHECKOUT_SESSION_ID}",
            "cancel_url": cancel_url,
            "metadata": {
                "user_id": str(user.id),
                "plan_type": plan_type.value,
            },
            "allow_promotion_codes": True,
        }
        
        # Modo subscription ou payment único
        if plan_type == PlanType.LIFETIME:
            checkout_params["mode"] = "payment"
        else:
            checkout_params["mode"] = "subscription"
        
        # Criar sessão
        session = stripe.checkout.Session.create(**checkout_params)
        
        return {
            "checkout_url": session.url,
            "session_id": session.id
        }
    
    @classmethod
    async def create_customer_portal_session(
        cls,
        db: AsyncSession,
        user: User,
        return_url: Optional[str] = None
    ) -> str:
        """
        Cria uma sessão do Customer Portal do Stripe.
        
        Returns:
            URL do portal
        """
        if not user.stripe_customer_id:
            raise ValueError("Usuário não tem customer_id do Stripe")
        
        if not return_url:
            return_url = f"{settings.FRONTEND_URL}/dashboard.html"
        
        session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=return_url
        )
        
        return session.url
    
    # Mapeamento de price_id para tipo de plano
    PRICE_TO_PLAN_MAP = {
        # Esses valores serão preenchidos com os price_ids reais
        "price_1Sbs0oGEyVmwHCe6P9IylBWe": ("basic_monthly", LicenseType.BASIC, 1),
        "price_1SbrmCGEyVmwHCe6wlkuX7Z9": ("basic_yearly", LicenseType.BASIC, 12),
        "price_1Sbs0pGEyVmwHCe6pRDe6BfP": ("pro_monthly", LicenseType.PRO, 1),
        "price_1Sbs0qGEyVmwHCe6NbW9697S": ("pro_yearly", LicenseType.PRO, 12),
        "price_1Sbs0sGEyVmwHCe6gRVChJI6": ("enterprise_monthly", LicenseType.ENTERPRISE, 1),
        "price_1Sbs0uGEyVmwHCe6MHEVICw5": ("enterprise_yearly", LicenseType.ENTERPRISE, 12),
    }
    
    @classmethod
    def get_plan_from_price_id(cls, price_id: str) -> tuple:
        """Retorna (plan_name, license_type, duration_months) baseado no price_id"""
        return cls.PRICE_TO_PLAN_MAP.get(price_id, ("basic_monthly", LicenseType.BASIC, 1))
    
    @classmethod
    async def handle_checkout_completed(
        cls,
        db: AsyncSession,
        session: Dict[str, Any]
    ) -> Optional[Subscription]:
        """
        Processa o evento checkout.session.completed.
        Cria licença e subscription para o usuário.
        
        Suporta dois fluxos:
        1. Checkout via API (com metadata user_id)
        2. Stripe Pricing Table (sem metadata, usa email do cliente)
        """
        user_id = session.get("metadata", {}).get("user_id")
        plan_type_str = session.get("metadata", {}).get("plan_type")
        
        # Obter email e nome do cliente da sessão
        customer_email = session.get("customer_email") or session.get("customer_details", {}).get("email")
        customer_name = session.get("customer_details", {}).get("name", "")
        stripe_customer_id = session.get("customer")
        
        # Obter price_id da sessão para determinar o plano
        line_items = session.get("line_items", {}).get("data", [])
        price_id = None
        if line_items:
            price_id = line_items[0].get("price", {}).get("id")
        
        # Se não veio nos line_items, tentar buscar da subscription
        if not price_id and session.get("subscription"):
            try:
                stripe_sub = stripe.Subscription.retrieve(session.get("subscription"))
                # O retorno é um objeto Stripe, não um dict
                if stripe_sub.items and stripe_sub.items.data:
                    price_id = stripe_sub.items.data[0].price.id
                print(f"✅ Price ID obtido da subscription: {price_id}")
            except Exception as e:
                print(f"⚠️ Erro ao buscar subscription: {e}")
        
        user = None
        
        # Fluxo 1: Checkout via API (tem user_id nos metadados)
        if user_id:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
        
        # Fluxo 2: Pricing Table (buscar/criar usuário pelo email)
        if not user and customer_email:
            # Tentar encontrar usuário existente pelo email
            result = await db.execute(
                select(User).where(User.email == customer_email)
            )
            user = result.scalar_one_or_none()
            
            # Se não encontrou, criar novo usuário
            if not user:
                import secrets as sec
                import bcrypt
                
                # Gerar senha temporária simples (8 chars = bem abaixo de 72 bytes)
                temp_password = sec.token_hex(4)  # 8 caracteres hex
                
                print(f"🔑 Senha temporária: {temp_password} ({len(temp_password)} chars)")
                
                # Hash diretamente com bcrypt (sem passlib)
                password_bytes = temp_password.encode('utf-8')
                salt = bcrypt.gensalt()
                password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
                
                print(f"✅ Hash gerado diretamente com bcrypt")
                
                user = User(
                    email=customer_email,
                    name=customer_name or customer_email.split("@")[0],
                    password_hash=password_hash,
                    is_active=True,
                    stripe_customer_id=stripe_customer_id,
                )
                db.add(user)
                await db.flush()
                
                print(f"✅ Novo usuário criado via Pricing Table: {customer_email}")
                
                # Enviar email com senha temporária (será enviado após criar a licença)
                user._temp_password = temp_password  # Guardar para enviar no email
        
        if not user:
            print(f"⚠️ Não foi possível identificar usuário para checkout: {session.get('id')}")
            return None
        
        # Atualizar stripe_customer_id se necessário
        if stripe_customer_id and not user.stripe_customer_id:
            user.stripe_customer_id = stripe_customer_id
        
        # Determinar tipo de licença e duração
        if plan_type_str:
            # Fluxo via API
            plan_type = PlanType(plan_type_str)
            license_type = cls.PLAN_LICENSE_MAP.get(plan_type_str, LicenseType.BASIC)
            duration_months = cls.PLAN_DURATION.get(plan_type_str, 1)
            plan_name = plan_type_str
        elif price_id:
            # Fluxo via Pricing Table
            plan_name, license_type, duration_months = cls.get_plan_from_price_id(price_id)
            plan_type = PlanType.MONTHLY if "monthly" in plan_name else PlanType.YEARLY
        else:
            # Fallback
            plan_name = "basic_monthly"
            license_type = LicenseType.BASIC
            duration_months = 1
            plan_type = PlanType.MONTHLY
        
        # Calcular expiração
        expires_at = None
        if duration_months:
            expires_at = datetime.utcnow() + timedelta(days=duration_months * 30)
        
        # Determinar max_activations baseado no tipo de licença
        max_activations = cls.LICENSE_MAX_ACTIVATIONS.get(license_type, 3)
        
        # Criar licença
        license = License(
            key=cls.generate_license_key(),
            user_id=user.id,
            customer_name=user.name,
            email=user.email,
            license_type=license_type,
            status=LicenseStatus.ACTIVE,
            expires_at=expires_at,
            max_activations=max_activations,
        )
        db.add(license)
        await db.flush()
        
        # Criar subscription
        stripe_subscription_id = session.get("subscription")
        
        subscription = Subscription(
            user_id=user.id,
            license_id=license.id,
            stripe_subscription_id=stripe_subscription_id,
            stripe_price_id=price_id,
            plan_type=plan_type,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.utcnow(),
            current_period_end=expires_at,
        )
        db.add(subscription)
        await db.commit()
        
        print(f"✅ Licença criada: {license.key} para {user.email} (Plano: {plan_name})")
        
        # Enviar email de boas-vindas se usuário foi criado agora (tem senha temporária)
        temp_password = getattr(user, '_temp_password', None)
        if temp_password:
            from .email_service import EmailService
            try:
                await EmailService.send_welcome_email(
                    to_email=user.email,
                    user_name=user.name,
                    temp_password=temp_password,
                    license_key=license.key,
                    plan_name=plan_name
                )
                print(f"📧 Email de boas-vindas enviado para: {user.email}")
            except Exception as e:
                print(f"⚠️ Erro ao enviar email de boas-vindas: {e}")
        
        return subscription
    
    @classmethod
    async def handle_invoice_paid(
        cls,
        db: AsyncSession,
        invoice: Dict[str, Any]
    ) -> bool:
        """
        Processa o evento invoice.paid.
        Renova a licença do usuário.
        """
        subscription_id = invoice.get("subscription")
        
        if not subscription_id:
            return False
        
        # Buscar subscription
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == subscription_id
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            print(f"⚠️ Subscription não encontrada: {subscription_id}")
            return False
        
        # Atualizar período
        duration_months = cls.PLAN_DURATION.get(subscription.plan_type)
        if duration_months:
            subscription.current_period_start = datetime.utcnow()
            subscription.current_period_end = datetime.utcnow() + timedelta(days=duration_months * 30)
        
        subscription.status = SubscriptionStatus.ACTIVE
        
        # Atualizar licença
        if subscription.license_id:
            result = await db.execute(
                select(License).where(License.id == subscription.license_id)
            )
            license = result.scalar_one_or_none()
            if license:
                license.status = LicenseStatus.ACTIVE
                license.expires_at = subscription.current_period_end
        
        await db.commit()
        print(f"✅ Subscription renovada: {subscription_id}")
        
        return True
    
    @classmethod
    async def handle_invoice_payment_failed(
        cls,
        db: AsyncSession,
        invoice: Dict[str, Any]
    ) -> bool:
        """
        Processa o evento invoice.payment_failed.
        Marca a licença como pendente.
        """
        subscription_id = invoice.get("subscription")
        
        if not subscription_id:
            return False
        
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == subscription_id
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return False
        
        subscription.status = SubscriptionStatus.PAST_DUE
        
        # Não suspende a licença imediatamente, apenas marca
        await db.commit()
        print(f"⚠️ Pagamento falhou: {subscription_id}")
        
        return True
    
    @classmethod
    async def handle_subscription_deleted(
        cls,
        db: AsyncSession,
        stripe_subscription: Dict[str, Any]
    ) -> bool:
        """
        Processa o evento customer.subscription.deleted.
        Cancela a licença do usuário.
        """
        subscription_id = stripe_subscription.get("id")
        
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == subscription_id
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return False
        
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancelled_at = datetime.utcnow()
        
        # Revogar licença
        if subscription.license_id:
            result = await db.execute(
                select(License).where(License.id == subscription.license_id)
            )
            license = result.scalar_one_or_none()
            if license:
                license.status = LicenseStatus.CANCELLED
                license.revoked = True
                license.revoked_at = datetime.utcnow()
                license.revoke_reason = "Assinatura cancelada"
        
        await db.commit()
        print(f"❌ Subscription cancelada: {subscription_id}")
        
        return True
    
    @classmethod
    async def get_customer_invoices(
        cls,
        user: User,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retorna as faturas do cliente no Stripe.
        """
        if not user.stripe_customer_id:
            return []
        
        invoices = stripe.Invoice.list(
            customer=user.stripe_customer_id,
            limit=limit
        )
        
        return [
            {
                "id": inv.id,
                "amount": inv.amount_paid,
                "currency": inv.currency,
                "status": inv.status,
                "created": datetime.fromtimestamp(inv.created),
                "invoice_pdf": inv.invoice_pdf,
                "hosted_invoice_url": inv.hosted_invoice_url,
            }
            for inv in invoices.data
        ]
    
    @classmethod
    def construct_webhook_event(
        cls,
        payload: bytes,
        sig_header: str
    ) -> stripe.Event:
        """
        Constrói e verifica um evento de webhook do Stripe.
        """
        return stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )

