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

from ..config import get_settings, get_plan_by_price_id, get_plan_config
from ..models import (
    User, License, Subscription,
    LicenseStatus, LicenseType, PlanType, SubscriptionStatus
)

settings = get_settings()

# Configurar Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Serviço para integração com Stripe"""

    # ✓ REMOVIDO: PLAN_LICENSE_MAP, PLAN_DURATION, PLAN_MAX_CONTRACTS
    # ✓ CONSOLIDADO: Tudo agora vem de PLAN_CONFIG em config.py

    @staticmethod
    def get_price_id(plan_type) -> Optional[str]:
        """
        Retorna o price_id do Stripe para o plano.
        Usa PLAN_CONFIG como fonte única de verdade.
        """
        # Converter para string se for enum
        plan_key = plan_type.value if hasattr(plan_type, 'value') else str(plan_type)

        try:
            config = get_plan_config(plan_key)
            return config.get("price_id")
        except ValueError:
            # Fallback para compatibilidade
            return None
    
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
    
    # ✓ REMOVIDO: PRICE_TO_PLAN_MAP (agora usa get_plan_by_price_id de config.py)

    @classmethod
    def get_plan_from_price_id(cls, price_id: str) -> tuple[str, Dict[str, Any]]:
        """
        Retorna (plan_key, config) baseado no price_id.
        Usa PLAN_CONFIG como fonte única de verdade.
        """
        return get_plan_by_price_id(price_id)
    
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
        # ✓ NOVO: Verificar idempotência (se session_id já foi processado)
        stripe_session_id = session.get("id")
        if stripe_session_id:
            result = await db.execute(
                select(Subscription).where(
                    Subscription.stripe_session_id == stripe_session_id
                )
            )
            existing_sub = result.scalar_one_or_none()
            if existing_sub:
                print(f"[WARN] Webhook duplicado (session_id ja processado): {stripe_session_id}")
                return existing_sub

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
                print(f"[OK] Price ID obtido da subscription: {price_id}")
            except Exception as e:
                print(f"[WARN] Erro ao buscar subscription: {e}")
        
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
                
                print(f"[KEY] Senha temporaria: {temp_password} ({len(temp_password)} chars)")

                # Hash diretamente com bcrypt (sem passlib)
                password_bytes = temp_password.encode('utf-8')
                salt = bcrypt.gensalt()
                password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

                print(f"[OK] Hash gerado diretamente com bcrypt")
                
                user = User(
                    email=customer_email,
                    name=customer_name or customer_email.split("@")[0],
                    password_hash=password_hash,
                    is_active=True,
                    stripe_customer_id=stripe_customer_id,
                    password_must_change=True,  # Forçar troca de senha no primeiro login
                )
                db.add(user)
                await db.flush()
                
                print(f"[OK] Novo usuario criado via Pricing Table: {customer_email}")
                
                # Enviar email com senha temporária (será enviado após criar a licença)
                user._temp_password = temp_password  # Guardar para enviar no email
        
        if not user:
            print(f"[WARN] Nao foi possivel identificar usuario para checkout: {session.get('id')}")
            return None
        
        # Atualizar stripe_customer_id se necessário
        if stripe_customer_id and not user.stripe_customer_id:
            user.stripe_customer_id = stripe_customer_id
        
        # ✓ ATUALIZADO: Determinar tipo de licença usando PLAN_CONFIG
        if price_id:
            # Fluxo principal: buscar config por price_id
            plan_name, plan_config = cls.get_plan_from_price_id(price_id)
        elif plan_type_str:
            # Fluxo via API (raro, mas suportado)
            plan_name = plan_type_str
            plan_config = get_plan_config(plan_type_str)
        else:
            # Fallback
            plan_name = "basic_monthly"
            plan_config = get_plan_config("basic_monthly")

        # Extrair configurações do plano
        license_type = LicenseType[plan_config["license_type"].upper()]
        duration_months = plan_config["duration_months"]
        max_activations = plan_config["max_activations"]
        # max_contracts = plan_config["max_contracts"]  # Usado em features

        # Calcular expiração
        expires_at = None
        if duration_months:
            expires_at = datetime.utcnow() + timedelta(days=duration_months * 30)

        # PlanType enum - usar valor exatamente como está no enum (case-sensitive)
        # Os novos valores são lowercase: basic_monthly, pro_monthly, etc
        # Os valores antigos são uppercase: MONTHLY, YEARLY, LIFETIME
        try:
            # Tentar primeiro com o valor exato (para novos valores lowercase)
            plan_type = PlanType(plan_name)
        except ValueError:
            try:
                # Se falhar, tentar uppercase (para valores antigos)
                plan_type = PlanType[plan_name.upper()]
            except KeyError:
                # Fallback final para compatibilidade
                plan_type = PlanType.MONTHLY if "monthly" in plan_name else PlanType.YEARLY

        # Criar/atualizar subscription de forma idempotente
        stripe_subscription_id = session.get("subscription")
        existing_subscription = None
        if stripe_subscription_id:
            result = await db.execute(
                select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
            )
            existing_subscription = result.scalar_one_or_none()

        if existing_subscription:
            existing_subscription.user_id = user.id
            existing_subscription.stripe_session_id = stripe_session_id  # ✓ NOVO: salvar session_id
            existing_subscription.stripe_price_id = price_id
            existing_subscription.plan_type = plan_type
            existing_subscription.status = SubscriptionStatus.ACTIVE
            existing_subscription.current_period_start = datetime.utcnow()
            existing_subscription.current_period_end = expires_at

            license = None
            if existing_subscription.license_id:
                result = await db.execute(
                    select(License).where(License.id == existing_subscription.license_id)
                )
                license = result.scalar_one_or_none()

            if license:
                license.status = LicenseStatus.ACTIVE
                license.expires_at = expires_at
                license.license_type = license_type
                license.max_activations = max_activations
            else:
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
                existing_subscription.license_id = license.id

            await db.commit()
            print(
                f"[OK] Subscription atualizada (idempotente): {stripe_subscription_id} | "
                f"Licença: {license.key} | {user.email} (Plano: {plan_name})"
            )

            # Enviar email de boas-vindas se usuário foi criado agora (tem senha temporária)
            temp_password = getattr(user, '_temp_password', None)
            from .email_service import EmailService
            try:
                if temp_password:
                    await EmailService.send_welcome_email(
                        to_email=user.email,
                        user_name=user.name,
                        temp_password=temp_password,
                        license_key=license.key,
                        plan_name=plan_name
                    )
                    print(f"📧 Email de boas-vindas enviado para: {user.email}")
                else:
                    await EmailService.send_license_activated_email(
                        to_email=user.email,
                        user_name=user.name,
                        license_key=license.key,
                        plan_name=plan_name
                    )
                    print(f"📧 Email de licença ativada enviado para: {user.email}")

                # Enviar notificação ao administrador
                try:
                    await EmailService.send_admin_new_subscription_notification(
                        customer_name=user.name,
                        customer_email=user.email,
                        plan_name=plan_name,
                        license_key=license.key,
                        amount=f"R$ {session.get('amount_total', 0) / 100:.2f}"
                    )
                    print(f"📧 Notificacao de admin enviada para: contato@fxstudioai.com")
                except Exception as e:
                    print(f"[WARN] Erro ao enviar notificacao de admin: {e}")
            except Exception as e:
                print(f"[WARN] Erro ao enviar email pos-checkout: {e}")

            return existing_subscription

        # Caso não exista subscription ainda, criar normalmente
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

        subscription = Subscription(
            user_id=user.id,
            license_id=license.id,
            stripe_subscription_id=stripe_subscription_id,
            stripe_session_id=stripe_session_id,  # ✓ NOVO: para idempotência de webhooks
            stripe_price_id=price_id,
            plan_type=plan_type,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.utcnow(),
            current_period_end=expires_at,
        )
        db.add(subscription)
        await db.commit()

        print(f"[OK] Licenca criada: {license.key} para {user.email} (Plano: {plan_name})")
        
        # Enviar email de boas-vindas se usuário foi criado agora (tem senha temporária)
        temp_password = getattr(user, '_temp_password', None)
        from .email_service import EmailService
        try:
            if temp_password:
                await EmailService.send_welcome_email(
                    to_email=user.email,
                    user_name=user.name,
                    temp_password=temp_password,
                    license_key=license.key,
                    plan_name=plan_name
                )
                print(f"📧 Email de boas-vindas enviado para: {user.email}")
            else:
                await EmailService.send_license_activated_email(
                    to_email=user.email,
                    user_name=user.name,
                    license_key=license.key,
                    plan_name=plan_name
                )
                print(f"📧 Email de licença ativada enviado para: {user.email}")

            # Enviar notificação ao administrador
            try:
                await EmailService.send_admin_new_subscription_notification(
                    customer_name=user.name,
                    customer_email=user.email,
                    plan_name=plan_name,
                    license_key=license.key,
                    amount=f"R$ {session.get('amount_total', 0) / 100:.2f}"
                )
                print(f"📧 Notificacao de admin enviada para: contato@fxstudioai.com")
            except Exception as e:
                print(f"[WARN] Erro ao enviar notificacao de admin: {e}")
        except Exception as e:
            print(f"⚠️ Erro ao enviar email pós-checkout: {e}")

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
            print(f"[WARN] Subscription nao encontrada: {subscription_id}")
            return False

        # Atualizar período usando PLAN_CONFIG
        plan_key = subscription.plan_type.value if hasattr(subscription.plan_type, 'value') else str(subscription.plan_type)
        try:
            plan_config = get_plan_config(plan_key)
            duration_months = plan_config.get("duration_months")
            if duration_months:
                subscription.current_period_start = datetime.utcnow()
                subscription.current_period_end = datetime.utcnow() + timedelta(days=duration_months * 30)
        except ValueError as e:
            print(f"[WARN] Erro ao obter configuracao do plano {plan_key}: {e}")
            # Fallback: manter período atual
        
        subscription.status = SubscriptionStatus.ACTIVE
        
        # Atualizar licença
        license = None
        if subscription.license_id:
            result = await db.execute(
                select(License).where(License.id == subscription.license_id)
            )
            license = result.scalar_one_or_none()
            if license:
                license.status = LicenseStatus.ACTIVE
                license.expires_at = subscription.current_period_end

        await db.commit()
        print(f"[OK] Subscription renovada: {subscription_id}")

        # Enviar email de confirmação de renovação
        if subscription.user_id and license:
            result = await db.execute(
                select(User).where(User.id == subscription.user_id)
            )
            user = result.scalar_one_or_none()

            if user:
                from .email_service import EmailService
                try:
                    # Formatar data de próxima cobrança
                    next_billing_date = subscription.current_period_end.strftime("%d/%m/%Y") if subscription.current_period_end else "Não definido"

                    # Obter nome do plano
                    plan_config = get_plan_config(plan_key)
                    plan_name = plan_config.get("display_name", plan_key)

                    await EmailService.send_subscription_confirmation_email(
                        to_email=user.email,
                        user_name=user.name,
                        plan_name=plan_name,
                        next_billing_date=next_billing_date
                    )
                    print(f"[OK] Email de confirmacao de renovacao enviado para: {user.email}")
                except Exception as e:
                    print(f"[WARN] Erro ao enviar email de renovacao: {e}")

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
        print(f"[WARN] Pagamento falhou: {subscription_id}")

        # Enviar email de alerta de falha de pagamento
        if subscription.user_id:
            result = await db.execute(
                select(User).where(User.id == subscription.user_id)
            )
            user = result.scalar_one_or_none()

            if user:
                from .email_service import EmailService
                try:
                    # Calcular data de próxima tentativa (normalmente Stripe tenta em 3-7 dias)
                    from datetime import datetime, timedelta
                    retry_date = (datetime.utcnow() + timedelta(days=3)).strftime("%d/%m/%Y")

                    # Obter nome do plano
                    plan_key = subscription.plan_type.value if hasattr(subscription.plan_type, 'value') else str(subscription.plan_type)
                    try:
                        plan_config = get_plan_config(plan_key)
                        plan_name = plan_config.get("display_name", plan_key)
                    except ValueError:
                        plan_name = plan_key

                    await EmailService.send_payment_failed_email(
                        to_email=user.email,
                        user_name=user.name,
                        plan_name=plan_name,
                        retry_date=retry_date
                    )
                    print(f"[OK] Email de falha de pagamento enviado para: {user.email}")
                except Exception as e:
                    print(f"[WARN] Erro ao enviar email de falha de pagamento: {e}")

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
        print(f"[CANCEL] Subscription cancelada: {subscription_id}")

        # Enviar email de despedida
        if subscription.user_id:
            result = await db.execute(
                select(User).where(User.id == subscription.user_id)
            )
            user = result.scalar_one_or_none()

            if user:
                from .email_service import EmailService
                try:
                    # Obter nome do plano
                    plan_key = subscription.plan_type.value if hasattr(subscription.plan_type, 'value') else str(subscription.plan_type)
                    try:
                        plan_config = get_plan_config(plan_key)
                        plan_name = plan_config.get("display_name", plan_key)
                    except ValueError:
                        plan_name = plan_key

                    # Determinar motivo do cancelamento
                    cancel_reason = stripe_subscription.get("cancellation_details", {}).get("reason", "Solicitacao do cliente")
                    if cancel_reason == "payment_failed":
                        cancel_reason = "Falha no pagamento"
                    elif cancel_reason == "cancellation_requested":
                        cancel_reason = "Solicitacao do cliente"

                    await EmailService.send_subscription_cancelled_email(
                        to_email=user.email,
                        user_name=user.name,
                        plan_name=plan_name,
                        cancel_reason=cancel_reason
                    )
                    print(f"[OK] Email de cancelamento enviado para: {user.email}")
                except Exception as e:
                    print(f"[WARN] Erro ao enviar email de cancelamento: {e}")

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

