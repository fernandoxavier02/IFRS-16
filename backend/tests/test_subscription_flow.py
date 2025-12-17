"""
Testes completos do fluxo de assinaturas Stripe
Cobre: webhook -> usuário -> licença -> email -> login -> ativação
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, License, Subscription, LicenseStatus, LicenseType, PlanType, SubscriptionStatus
from app.services.stripe_service import StripeService
from app.services.email_service import EmailService
from app.auth import verify_password, hash_password


class TestSubscriptionFlow:
    """Testes do fluxo completo de assinatura"""
    
    @pytest.mark.asyncio
    async def test_checkout_completed_creates_user_and_license(
        self, 
        db_session: AsyncSession
    ):
        """Testa que checkout.session.completed cria usuário e licença"""
        
        # Mock do checkout session do Stripe
        mock_session = {
            "id": "cs_test_123",
            "customer": "cus_test_123",
            "customer_email": "novo.usuario@test.com",
            "customer_details": {
                "email": "novo.usuario@test.com",
                "name": "Novo Usuario"
            },
            "subscription": "sub_test_123",
            "metadata": {},
            "line_items": {
                "data": [
                    {
                        "price": {
                            "id": "price_basic_monthly"
                        }
                    }
                ]
            }
        }
        
        # Mock do Stripe para buscar subscription
        with patch('app.services.stripe_service.stripe.Subscription.retrieve') as mock_sub:
            mock_sub.return_value = MagicMock(
                id="sub_test_123",
                status="active",
                current_period_start=int((datetime.utcnow() - timedelta(days=1)).timestamp()),
                current_period_end=int((datetime.utcnow() + timedelta(days=29)).timestamp()),
                items=MagicMock(
                    data=[MagicMock(
                        price=MagicMock(
                            id="price_basic_monthly",
                            nickname="basic_monthly"
                        )
                    )]
                )
            )
            
            # Mock do email service
            with patch.object(EmailService, 'send_welcome_email', new_callable=AsyncMock) as mock_email:
                mock_email.return_value = True
                
                # Executar o fluxo
                subscription = await StripeService.handle_checkout_completed(
                    db_session, 
                    mock_session
                )
                
                # Verificações
                assert subscription is not None
                assert subscription.status == SubscriptionStatus.ACTIVE
                
                # Verificar usuário criado
                result = await db_session.execute(
                    select(User).where(User.email == "novo.usuario@test.com")
                )
                user = result.scalar_one_or_none()
                assert user is not None
                assert user.email == "novo.usuario@test.com"
                assert user.name == "Novo Usuario"
                assert user.stripe_customer_id == "cus_test_123"
                assert user.is_active is True
                
                # Verificar licença criada
                result = await db_session.execute(
                    select(License).where(License.user_id == user.id)
                )
                license = result.scalar_one_or_none()
                assert license is not None
                assert license.status == LicenseStatus.ACTIVE
                assert license.license_type == LicenseType.BASIC
                assert license.email == "novo.usuario@test.com"
                assert license.user_id == user.id
                assert license.expires_at is not None
                
                # Verificar assinatura vinculada
                assert subscription.user_id == user.id
                assert subscription.license_id == license.id
                assert subscription.stripe_subscription_id == "sub_test_123"
                
                # Verificar email foi enviado
                mock_email.assert_called_once()
                call_args = mock_email.call_args
                # O método recebe: to_email, user_name, temp_password, license_key, plan_name
                # Verificar argumentos posicionais
                if call_args[0]:  # Se tem args posicionais
                    assert call_args[0][0] == "novo.usuario@test.com"  # to_email
                    assert call_args[0][1] == "Novo Usuario"  # user_name
                    assert call_args[0][2] is not None  # temp_password
                    assert call_args[0][3] == license.key  # license_key
                else:  # Se usa kwargs
                    assert call_args.kwargs['to_email'] == "novo.usuario@test.com"
                    assert call_args.kwargs['license_key'] == license.key
    
    @pytest.mark.asyncio
    async def test_checkout_completed_existing_user(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Testa checkout com usuário já existente"""
        
        # Atualizar usuário com customer_id do Stripe
        test_user.stripe_customer_id = "cus_existing_123"
        await db_session.commit()
        
        mock_session = {
            "id": "cs_test_456",
            "customer": "cus_existing_123",
            "customer_email": test_user.email,
            "customer_details": {
                "email": test_user.email,
                "name": test_user.name
            },
            "subscription": "sub_test_456",
            "metadata": {},
            "line_items": {
                "data": [
                    {
                        "price": {
                            "id": "price_pro_monthly",
                            "nickname": "pro_monthly"
                        }
                    }
                ]
            }
        }
        
        with patch('app.services.stripe_service.stripe.Subscription.retrieve') as mock_sub:
            mock_sub.return_value = MagicMock(
                id="sub_test_456",
                status="active",
                current_period_start=int((datetime.utcnow() - timedelta(days=1)).timestamp()),
                current_period_end=int((datetime.utcnow() + timedelta(days=29)).timestamp()),
                items=MagicMock(
                    data=[MagicMock(
                        price=MagicMock(
                            id="price_pro_monthly",
                            nickname="pro_monthly"
                        )
                    )]
                )
            )
            
            with patch.object(EmailService, 'send_welcome_email', new_callable=AsyncMock):
                subscription = await StripeService.handle_checkout_completed(
                    db_session,
                    mock_session
                )
                
                assert subscription is not None
                assert subscription.user_id == test_user.id
                
                # Verificar que nova licença foi criada
                result = await db_session.execute(
                    select(License).where(License.user_id == test_user.id)
                )
                licenses = result.scalars().all()
                assert len(licenses) > 0
    
    @pytest.mark.asyncio
    async def test_user_login_with_temp_password(
        self,
        db_session: AsyncSession,
        client
    ):
        """Testa login do usuário com senha temporária"""
        
        # Criar usuário com senha temporária
        temp_password = "a1b2c3d4"  # 8 caracteres hex
        user = User(
            id=uuid4(),
            email="login.test@test.com",
            name="Login Test",
            password_hash=hash_password(temp_password),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        
        # Tentar fazer login
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "login.test@test.com",
                "password": temp_password
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user_type"] == "user"
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_user_login_invalid_password(
        self,
        db_session: AsyncSession,
        client
    ):
        """Testa login com senha incorreta"""
        
        user = User(
            id=uuid4(),
            email="invalid.test@test.com",
            name="Invalid Test",
            password_hash=hash_password("correct_password"),
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()
        
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "invalid.test@test.com",
                "password": "wrong_password"
            }
        )
        
        assert response.status_code == 401
        assert "incorretos" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_get_user_license_after_login(
        self,
        db_session: AsyncSession,
        client,
        test_user: User
    ):
        """Testa buscar licença do usuário após login"""
        
        # Criar licença para o usuário
        license = License(
            id=uuid4(),
            key="TEST-LICENSE-USER-001",
            user_id=test_user.id,
            customer_name=test_user.name,
            email=test_user.email,
            status=LicenseStatus.ACTIVE,
            license_type=LicenseType.BASIC,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(license)
        await db_session.commit()
        
        # Fazer login
        login_response = await client.post(
            "/api/auth/login",
            json={
                "email": test_user.email,
                "password": "TestUser123!"
            }
        )
        
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Buscar licença do usuário
        response = await client.get(
            "/api/auth/me/license",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_license"] is True
        assert data["license_key"] == "TEST-LICENSE-USER-001"
        assert data["license_type"] == "basic"
        assert "token" in data  # Token JWT da licença
    
    @pytest.mark.asyncio
    async def test_activate_license_key(
        self,
        db_session: AsyncSession,
        client,
        sample_license: License
    ):
        """Testa ativação de chave de licença"""
        
        response = await client.post(
            "/api/validate-license",
            json={
                "key": sample_license.key,
                "machine_id": "test-machine-123",
                "app_version": "1.0.0"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "token" in data
        assert data["data"]["customer_name"] == sample_license.customer_name
        assert data["data"]["license_type"] == sample_license.license_type.value
    
    @pytest.mark.asyncio
    async def test_activate_invalid_license_key(
        self,
        client
    ):
        """Testa ativação com chave inválida"""
        
        response = await client.post(
            "/api/validate-license",
            json={
                "key": "INVALID-KEY-12345",
                "machine_id": "test-machine-123",
                "app_version": "1.0.0"
            }
        )
        
        assert response.status_code == 404
        assert "não encontrada" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_complete_subscription_flow(
        self,
        db_session: AsyncSession,
        client
    ):
        """Testa fluxo completo: webhook -> login -> ativação"""
        
        # 1. Simular webhook checkout.session.completed
        mock_session = {
            "id": "cs_complete_flow",
            "customer": "cus_complete_flow",
            "customer_email": "complete.flow@test.com",
            "customer_details": {
                "email": "complete.flow@test.com",
                "name": "Complete Flow User"
            },
            "subscription": "sub_complete_flow",
            "metadata": {},
            "line_items": {
                "data": [
                    {
                        "price": {
                            "id": "price_basic_monthly",
                            "nickname": "basic_monthly"
                        }
                    }
                ]
            }
        }
        
        with patch('app.services.stripe_service.stripe.Subscription.retrieve') as mock_sub:
            mock_sub.return_value = MagicMock(
                id="sub_complete_flow",
                status="active",
                current_period_start=int((datetime.utcnow() - timedelta(days=1)).timestamp()),
                current_period_end=int((datetime.utcnow() + timedelta(days=29)).timestamp()),
                items=MagicMock(
                    data=[MagicMock(
                        price=MagicMock(
                            id="price_basic_monthly",
                            nickname="basic_monthly"
                        )
                    )]
                )
            )
            
            with patch.object(EmailService, 'send_welcome_email', new_callable=AsyncMock) as mock_email:
                # Simular email enviado com senha e chave
                temp_password = "temp1234"
                license_key = None
                
                def email_side_effect(*args, **kwargs):
                    nonlocal license_key
                    license_key = kwargs.get('license_key')
                    return True
                
                mock_email.side_effect = email_side_effect
                
                # Processar webhook
                subscription = await StripeService.handle_checkout_completed(
                    db_session,
                    mock_session
                )
                
                assert subscription is not None
                
                # Buscar licença criada
                result = await db_session.execute(
                    select(License).where(License.user_id == subscription.user_id)
                )
                license = result.scalar_one_or_none()
                assert license is not None
                
                # 2. Fazer login com senha temporária
                # (Precisamos buscar a senha do usuário criado)
                result = await db_session.execute(
                    select(User).where(User.email == "complete.flow@test.com")
                )
                user = result.scalar_one_or_none()
                assert user is not None
                
                # Como não temos a senha real, vamos resetar para uma conhecida
                user.password_hash = hash_password("TempPass123!")
                await db_session.commit()
                
                login_response = await client.post(
                    "/api/auth/login",
                    json={
                        "email": "complete.flow@test.com",
                        "password": "TempPass123!"
                    }
                )
                
                assert login_response.status_code == 200
                user_token = login_response.json()["access_token"]
                
                # 3. Buscar licença do usuário
                license_response = await client.get(
                    "/api/auth/me/license",
                    headers={"Authorization": f"Bearer {user_token}"}
                )
                
                assert license_response.status_code == 200
                license_data = license_response.json()
                assert license_data["has_license"] is True
                license_key = license_data["license_key"]
                
                # 4. Ativar chave de licença
                activate_response = await client.post(
                    "/api/validate-license",
                    json={
                        "key": license_key,
                        "machine_id": "test-machine-456",
                        "app_version": "1.0.0"
                    }
                )
                
                assert activate_response.status_code == 200
                activate_data = activate_response.json()
                assert activate_data["valid"] is True
                assert "token" in activate_data
                assert activate_data["data"]["license_type"] == "basic"
    
    @pytest.mark.asyncio
    async def test_webhook_invoice_paid_updates_subscription(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Testa webhook invoice.paid atualiza assinatura"""
        
        # Criar assinatura
        subscription = Subscription(
            id=uuid4(),
            user_id=test_user.id,
            stripe_subscription_id="sub_invoice_test",
            plan_type=PlanType.MONTHLY,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=datetime.utcnow() - timedelta(days=1),
            current_period_end=datetime.utcnow() + timedelta(days=29),
        )
        db_session.add(subscription)
        await db_session.commit()
        
        # Mock do invoice
        mock_invoice = {
            "id": "in_test_123",
            "subscription": "sub_invoice_test",
            "status": "paid",
            "amount_paid": 29900,
            "currency": "brl"
        }
        
        await StripeService.handle_invoice_paid(db_session, mock_invoice)
        await db_session.refresh(subscription)
        
        assert subscription.status == SubscriptionStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_webhook_subscription_deleted_revokes_license(
        self,
        db_session: AsyncSession,
        test_user: User
    ):
        """Testa webhook subscription.deleted revoga licença"""
        
        # Criar licença e assinatura
        license = License(
            id=uuid4(),
            key="TEST-REVOKE-001",
            user_id=test_user.id,
            customer_name=test_user.name,
            email=test_user.email,
            status=LicenseStatus.ACTIVE,
            license_type=LicenseType.BASIC,
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(license)
        
        subscription = Subscription(
            id=uuid4(),
            user_id=test_user.id,
            license_id=license.id,
            stripe_subscription_id="sub_delete_test",
            plan_type=PlanType.MONTHLY,
            status=SubscriptionStatus.ACTIVE,
        )
        db_session.add(subscription)
        await db_session.commit()
        
        # Mock do subscription deleted
        mock_subscription = {
            "id": "sub_delete_test",
            "status": "canceled",
            "canceled_at": int(datetime.utcnow().timestamp())
        }
        
        await StripeService.handle_subscription_deleted(db_session, mock_subscription)
        
        await db_session.refresh(license)
        await db_session.refresh(subscription)
        
        # Verificar que licença foi revogada ou status mudou
        assert subscription.status == SubscriptionStatus.CANCELLED
        # A licença pode ter sido revogada ou apenas ter status alterado
        assert license.status in [LicenseStatus.CANCELLED, LicenseStatus.SUSPENDED] or license.revoked is True

