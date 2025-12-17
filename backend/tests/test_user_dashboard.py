"""
Testes para o dashboard do usuário
"""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, License, Subscription, LicenseStatus, LicenseType, SubscriptionStatus, PlanType
from app.auth import hash_password


async def create_user_with_token(client: AsyncClient, db_session: AsyncSession, email: str = "dashboard@example.com"):
    """Helper para criar usuário e obter token"""
    user = User(
        email=email,
        name="Dashboard Test",
        password_hash=hash_password("Senha123!"),
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    login_response = await client.post("/api/auth/login", json={
        "email": email,
        "password": "Senha123!"
    })
    token = login_response.json()["access_token"]
    
    return user, token


class TestUserProfile:
    """Testes do perfil do usuário"""
    
    @pytest.mark.asyncio
    async def test_get_profile(self, client: AsyncClient, db_session: AsyncSession):
        """Deve retornar perfil do usuário"""
        user, token = await create_user_with_token(client, db_session)
        
        response = await client.get(
            "/api/user/profile",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user.email
        assert data["name"] == user.name
    
    @pytest.mark.asyncio
    async def test_update_profile(self, client: AsyncClient, db_session: AsyncSession):
        """Deve atualizar perfil do usuário"""
        user, token = await create_user_with_token(client, db_session, "update@example.com")
        
        response = await client.put(
            "/api/user/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Novo Nome"}
        )
        
        assert response.status_code == 200
        assert response.json()["name"] == "Novo Nome"


class TestUserSubscription:
    """Testes de assinatura do usuário"""
    
    @pytest.mark.asyncio
    async def test_get_subscription_none(self, client: AsyncClient, db_session: AsyncSession):
        """Deve retornar null se não tiver assinatura"""
        user, token = await create_user_with_token(client, db_session, "nosub@example.com")
        
        response = await client.get(
            "/api/user/subscription",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json() is None
    
    @pytest.mark.asyncio
    async def test_get_subscription_active(self, client: AsyncClient, db_session: AsyncSession):
        """Deve retornar assinatura ativa"""
        user, token = await create_user_with_token(client, db_session, "withsub@example.com")
        
        # Criar licença
        license = License(
            key="TEST-LICENSE-KEY-001",
            user_id=user.id,
            customer_name=user.name,
            email=user.email,
            license_type=LicenseType.PRO,
            status=LicenseStatus.ACTIVE,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db_session.add(license)
        await db_session.flush()
        
        # Criar subscription
        subscription = Subscription(
            user_id=user.id,
            license_id=license.id,
            plan_type=PlanType.MONTHLY,
            status=SubscriptionStatus.ACTIVE,
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        db_session.add(subscription)
        await db_session.commit()
        
        response = await client.get(
            "/api/user/subscription",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data is not None
        assert data["license_key"] == "TEST-LICENSE-KEY-001"


class TestUserLicenses:
    """Testes de licenças do usuário"""
    
    @pytest.mark.asyncio
    async def test_get_licenses_empty(self, client: AsyncClient, db_session: AsyncSession):
        """Deve retornar lista vazia se não tiver licenças"""
        user, token = await create_user_with_token(client, db_session, "nolic@example.com")
        
        response = await client.get(
            "/api/user/licenses",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json() == []
    
    @pytest.mark.asyncio
    async def test_get_licenses_with_license(self, client: AsyncClient, db_session: AsyncSession):
        """Deve retornar licenças do usuário"""
        user, token = await create_user_with_token(client, db_session, "withlic@example.com")
        
        license = License(
            key="TEST-LICENSE-KEY-002",
            user_id=user.id,
            customer_name=user.name,
            email=user.email,
            license_type=LicenseType.BASIC,
            status=LicenseStatus.ACTIVE
        )
        db_session.add(license)
        await db_session.commit()
        
        response = await client.get(
            "/api/user/licenses",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["key"] == "TEST-LICENSE-KEY-002"


class TestDashboardSummary:
    """Testes do resumo do dashboard"""
    
    @pytest.mark.asyncio
    async def test_dashboard_summary_new_user(self, client: AsyncClient, db_session: AsyncSession):
        """Deve retornar resumo para usuário novo"""
        user, token = await create_user_with_token(client, db_session, "newuser@example.com")
        
        response = await client.get(
            "/api/user/dashboard-summary",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "newuser@example.com"
        assert data["subscription"] is None
        assert data["license"] is None
        assert data["stats"]["total_validations"] == 0
    
    @pytest.mark.asyncio
    async def test_dashboard_summary_with_subscription(self, client: AsyncClient, db_session: AsyncSession):
        """Deve retornar resumo completo com assinatura"""
        user, token = await create_user_with_token(client, db_session, "fulluser@example.com")
        
        # Criar licença
        license = License(
            key="FULL-TEST-KEY-003",
            user_id=user.id,
            customer_name=user.name,
            email=user.email,
            license_type=LicenseType.PRO,
            status=LicenseStatus.ACTIVE,
            expires_at=datetime.utcnow() + timedelta(days=365)
        )
        db_session.add(license)
        await db_session.flush()
        
        # Criar subscription
        subscription = Subscription(
            user_id=user.id,
            license_id=license.id,
            plan_type=PlanType.YEARLY,
            status=SubscriptionStatus.ACTIVE,
            current_period_end=datetime.utcnow() + timedelta(days=365)
        )
        db_session.add(subscription)
        await db_session.commit()
        
        response = await client.get(
            "/api/user/dashboard-summary",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["subscription"]["active"] == True
        assert data["subscription"]["plan"] == "yearly"
        assert data["license"]["key"] == "FULL-TEST-KEY-003"
        assert data["license"]["type"] == "pro"


class TestCancelSubscription:
    """Testes de cancelamento de assinatura"""
    
    @pytest.mark.asyncio
    async def test_cancel_no_subscription(self, client: AsyncClient, db_session: AsyncSession):
        """Deve retornar erro se não tiver assinatura"""
        user, token = await create_user_with_token(client, db_session, "nocancel@example.com")
        
        response = await client.post(
            "/api/user/cancel-subscription",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_cancel_subscription_success(self, client: AsyncClient, db_session: AsyncSession):
        """Deve cancelar assinatura com sucesso"""
        user, token = await create_user_with_token(client, db_session, "cancel@example.com")
        
        # Criar subscription sem stripe_subscription_id (para não chamar API do Stripe)
        subscription = Subscription(
            user_id=user.id,
            plan_type=PlanType.MONTHLY,
            status=SubscriptionStatus.ACTIVE,
            current_period_end=datetime.utcnow() + timedelta(days=30)
        )
        db_session.add(subscription)
        await db_session.commit()
        
        response = await client.post(
            "/api/user/cancel-subscription",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["success"] == True
        
        # Verificar que foi marcada para cancelamento
        await db_session.refresh(subscription)
        assert subscription.cancel_at_period_end == True

