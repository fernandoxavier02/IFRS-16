"""
Testes completos para todas as funcionalidades do admin.html
Cobre todos os endpoints e fluxos administrativos
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import (
    AdminUser, User, License, Subscription,
    LicenseStatus, LicenseType, PlanType, SubscriptionStatus, AdminRole
)
from app.auth import hash_password, create_admin_token


# ============================================================
# FIXTURES
# ============================================================

@pytest_asyncio.fixture
async def admin_user_custom(db_session: AsyncSession) -> AdminUser:
    """Cria um usuário admin para testes (custom para não conflitar com conftest)"""
    admin = AdminUser(
        id=uuid4(),
        username="test_admin",
        email="admin@test.com",
        password_hash=hash_password("AdminPass123!"),
        role=AdminRole.ADMIN,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def superadmin_user(db_session: AsyncSession) -> AdminUser:
    """Cria um superadmin para testes"""
    admin = AdminUser(
        id=uuid4(),
        username="superadmin",
        email="superadmin@test.com",
        password_hash=hash_password("SuperAdmin123!"),
        role=AdminRole.SUPERADMIN,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
def admin_token_custom(admin_user_custom: AdminUser) -> str:
    """Gera token JWT para o admin (custom)"""
    return create_admin_token(admin_user_custom.id, admin_user_custom.username, admin_user_custom.role.value)


@pytest.fixture
def superadmin_token(superadmin_user: AdminUser) -> str:
    """Gera token JWT para o superadmin"""
    return create_admin_token(superadmin_user.id, superadmin_user.username, superadmin_user.role.value)


@pytest_asyncio.fixture
async def test_user_custom(db_session: AsyncSession) -> User:
    """Cria um usuário cliente para testes"""
    user = User(
        id=uuid4(),
        email="cliente@test.com",
        name="Cliente Teste",
        password_hash=hash_password("UserPass123!"),
        is_active=True,
        email_verified=True,
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_license_custom(db_session: AsyncSession, test_user_custom: User) -> License:
    """Cria uma licença de teste"""
    license = License(
        id=uuid4(),
        key="FX2025-IFRS16-TEST-XXXXX",
        user_id=test_user_custom.id,
        customer_name=test_user_custom.name,
        email=test_user_custom.email,
        status=LicenseStatus.ACTIVE,
        license_type=LicenseType.PRO,
        expires_at=datetime.utcnow() + timedelta(days=30),
        max_activations=1,
        current_activations=0,
        created_at=datetime.utcnow()
    )
    db_session.add(license)
    await db_session.commit()
    await db_session.refresh(license)
    return license


@pytest_asyncio.fixture
async def revoked_license_custom(db_session: AsyncSession, test_user_custom: User) -> License:
    """Cria uma licença revogada para testes"""
    license = License(
        id=uuid4(),
        key="FX2025-IFRS16-REVOKED-XXXXX",
        user_id=test_user_custom.id,
        customer_name=test_user_custom.name,
        email=test_user_custom.email,
        status=LicenseStatus.ACTIVE,
        license_type=LicenseType.BASIC,
        revoked=True,
        revoked_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30),
        max_activations=1,
        current_activations=0,
        created_at=datetime.utcnow()
    )
    db_session.add(license)
    await db_session.commit()
    await db_session.refresh(license)
    return license


# ============================================================
# TESTES DE AUTENTICAÇÃO ADMIN
# ============================================================

class TestAdminAuthentication:
    """Testes de autenticação de administrador"""
    
    @pytest.mark.asyncio
    async def test_admin_login_success(
        self,
        client: AsyncClient,
        admin_user_custom: AdminUser
    ):
        """Teste: Login de admin com credenciais corretas"""
        response = await client.post(
            "/api/auth/admin/login",
            json={
                "email": "admin@test.com",
                "password": "AdminPass123!"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_type"] == "admin"
        assert data["expires_in"] > 0
    
    @pytest.mark.asyncio
    async def test_admin_login_wrong_password(
        self,
        client: AsyncClient,
        admin_user_custom: AdminUser
    ):
        """Teste: Login com senha incorreta"""
        response = await client.post(
            "/api/auth/admin/login",
            json={
                "email": "admin@test.com",
                "password": "WrongPassword123!"
            }
        )
        
        assert response.status_code == 401
        assert "incorretos" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_admin_login_wrong_email(
        self,
        client: AsyncClient
    ):
        """Teste: Login com email inexistente"""
        response = await client.post(
            "/api/auth/admin/login",
            json={
                "email": "inexistente@test.com",
                "password": "AnyPassword123!"
            }
        )
        
        assert response.status_code == 401
        assert "incorretos" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_admin_login_inactive_account(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Teste: Login com conta inativa"""
        # Criar admin inativo
        inactive_admin = AdminUser(
            id=uuid4(),
            username="inactive_admin",
            email="inactive@test.com",
            password_hash=hash_password("Pass123!"),
            role=AdminRole.ADMIN,
            is_active=False,
            created_at=datetime.utcnow()
        )
        db_session.add(inactive_admin)
        await db_session.commit()
        
        response = await client.post(
            "/api/auth/admin/login",
            json={
                "email": "inactive@test.com",
                "password": "Pass123!"
            }
        )
        
        assert response.status_code == 401
        assert "desativada" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_admin_me_success(
        self,
        client: AsyncClient,
        admin_token_custom: str,
        admin_user_custom: AdminUser
    ):
        """Teste: Obter dados do admin logado"""
        response = await client.get(
            "/api/auth/admin/me",
            headers={"Authorization": f"Bearer {admin_token_custom}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == admin_user_custom.email
        assert data["username"] == admin_user_custom.username
        assert data["role"] == admin_user_custom.role.value
    
    @pytest.mark.asyncio
    async def test_admin_me_without_token(
        self,
        client: AsyncClient
    ):
        """Teste: Acessar /me sem token retorna 401"""
        response = await client.get("/api/auth/admin/me")
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_admin_me_invalid_token(
        self,
        client: AsyncClient
    ):
        """Teste: Acessar /me com token inválido retorna 401"""
        response = await client.get(
            "/api/auth/admin/me",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        
        assert response.status_code == 401


# ============================================================
# TESTES DE GERENCIAMENTO DE LICENÇAS
# ============================================================

class TestLicenseManagement:
    """Testes de gerenciamento de licenças"""
    
    @pytest.mark.asyncio
    async def test_generate_license_success(
        self,
        client: AsyncClient,
        admin_token_custom: str
    ):
        """Teste: Gerar nova licença com sucesso"""
        response = await client.post(
            "/api/admin/generate-license",
            headers={"Authorization": f"Bearer {admin_token_custom}"},
            json={
                "customer_name": "Novo Cliente Admin",
                "email": "novo.cliente@test.com",
                "license_type": "pro",
                "duration_months": 12,
                "max_activations": 3
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "FX2025-IFRS16" in data["license"]["key"]
        assert data["license"]["customer_name"] == "Novo Cliente Admin"
        assert data["license"]["email"] == "novo.cliente@test.com"
        assert data["license"]["license_type"] == "pro"
        assert data["license"]["status"] == "active"
        assert data["license"]["expires_at"] is not None
    
    @pytest.mark.asyncio
    async def test_generate_license_permanent(
        self,
        client: AsyncClient,
        admin_token_custom: str
    ):
        """Teste: Gerar licença permanente (sem expiração)"""
        response = await client.post(
            "/api/admin/generate-license",
            headers={"Authorization": f"Bearer {admin_token_custom}"},
            json={
                "customer_name": "Cliente Permanente",
                "email": "permanente@test.com",
                "license_type": "enterprise"
                # Sem duration_months = permanente
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["license"]["expires_at"] is None
    
    @pytest.mark.asyncio
    async def test_generate_license_trial(
        self,
        client: AsyncClient,
        admin_token_custom: str
    ):
        """Teste: Gerar licença trial"""
        response = await client.post(
            "/api/admin/generate-license",
            headers={"Authorization": f"Bearer {admin_token_custom}"},
            json={
                "customer_name": "Cliente Trial",
                "email": "trial@test.com",
                "license_type": "trial",
                "duration_months": 1
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["license"]["license_type"] == "trial"
        assert data["license"]["expires_at"] is not None
    
    @pytest.mark.asyncio
    async def test_generate_license_invalid_email(
        self,
        client: AsyncClient,
        admin_token_custom: str
    ):
        """Teste: Gerar licença com email inválido"""
        response = await client.post(
            "/api/admin/generate-license",
            headers={"Authorization": f"Bearer {admin_token_custom}"},
            json={
                "customer_name": "Test",
                "email": "email-invalido",
                "license_type": "basic"
            }
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_list_licenses_empty(
        self,
        client: AsyncClient,
        admin_token_custom: str
    ):
        """Teste: Listar licenças quando não há nenhuma"""
        response = await client.get(
            "/api/admin/licenses",
            headers={"Authorization": f"Bearer {admin_token_custom}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["licenses"] == []
    
    @pytest.mark.asyncio
    async def test_list_licenses_with_data(
        self,
        client: AsyncClient,
        admin_token_custom: str,
        test_license_custom: License
    ):
        """Teste: Listar licenças existentes"""
        response = await client.get(
            "/api/admin/licenses",
            headers={"Authorization": f"Bearer {admin_token_custom}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["licenses"]) >= 1
        
        # Verificar que a licença de teste está na lista
        keys = [lic["key"] for lic in data["licenses"]]
        assert test_license_custom.key in keys
    
    @pytest.mark.asyncio
    async def test_list_licenses_with_filter(
        self,
        client: AsyncClient,
        admin_token_custom: str,
        test_license_custom: License,
        revoked_license_custom: License
    ):
        """Teste: Filtrar licenças por status"""
        response = await client.get(
            "/api/admin/licenses",
            params={"status_filter": "active"},
            headers={"Authorization": f"Bearer {admin_token_custom}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Todas devem ser ativas
        for lic in data["licenses"]:
            assert lic["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_list_licenses_pagination(
        self,
        client: AsyncClient,
        admin_token_custom: str,
        db_session: AsyncSession,
        test_user_custom: User
    ):
        """Teste: Paginação de licenças"""
        # Criar múltiplas licenças
        for i in range(5):
            license = License(
                id=uuid4(),
                key=f"FX2025-IFRS16-PAG-{i:05d}",
                user_id=test_user_custom.id,
                customer_name=f"Cliente {i}",
                email=f"cliente{i}@test.com",
                status=LicenseStatus.ACTIVE,
                license_type=LicenseType.BASIC,
                expires_at=datetime.utcnow() + timedelta(days=30),
                max_activations=1,
                current_activations=0,
                created_at=datetime.utcnow()
            )
            db_session.add(license)
        await db_session.commit()
        
        # Primeira página
        response = await client.get(
            "/api/admin/licenses",
            params={"skip": 0, "limit": 2},
            headers={"Authorization": f"Bearer {admin_token_custom}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["licenses"]) <= 2
    
    @pytest.mark.asyncio
    async def test_get_license_by_key(
        self,
        client: AsyncClient,
        admin_token_custom: str,
        test_license_custom: License
    ):
        """Teste: Buscar licença por chave"""
        response = await client.get(
            f"/api/admin/license/{test_license_custom.key}",
            headers={"Authorization": f"Bearer {admin_token_custom}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == test_license_custom.key
        assert data["customer_name"] == test_license_custom.customer_name
        assert data["email"] == test_license_custom.email
        assert data["license_type"] == test_license_custom.license_type.value
        assert data["status"] == test_license_custom.status.value
    
    @pytest.mark.asyncio
    async def test_get_license_not_found(
        self,
        client: AsyncClient,
        admin_token_custom: str
    ):
        """Teste: Buscar licença inexistente"""
        response = await client.get(
            "/api/admin/license/INEXISTENTE-12345",
            headers={"Authorization": f"Bearer {admin_token_custom}"}
        )
        
        assert response.status_code == 404
        assert "não encontrada" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_revoke_license_success(
        self,
        client: AsyncClient,
        admin_token_custom: str,
        test_license_custom: License
    ):
        """Teste: Revogar licença com sucesso"""
        response = await client.post(
            "/api/admin/revoke-license",
            headers={"Authorization": f"Bearer {admin_token_custom}"},
            json={
                "key": test_license_custom.key,
                "reason": "Pagamento não realizado"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert test_license_custom.key in data["message"]
        
        # Verificar que a licença foi revogada
        get_response = await client.get(
            f"/api/admin/license/{test_license_custom.key}",
            headers={"Authorization": f"Bearer {admin_token_custom}"}
        )
        assert get_response.json()["revoked"] is True
    
    @pytest.mark.asyncio
    async def test_revoke_license_not_found(
        self,
        client: AsyncClient,
        admin_token_custom: str
    ):
        """Teste: Revogar licença inexistente"""
        response = await client.post(
            "/api/admin/revoke-license",
            headers={"Authorization": f"Bearer {admin_token_custom}"},
            json={"key": "LICENCA-INEXISTENTE"}
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_reactivate_license_success(
        self,
        client: AsyncClient,
        admin_token_custom: str,
        revoked_license_custom: License
    ):
        """Teste: Reativar licença revogada"""
        response = await client.post(
            "/api/admin/reactivate-license",
            headers={"Authorization": f"Bearer {admin_token_custom}"},
            json={"key": revoked_license_custom.key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verificar que a licença foi reativada
        get_response = await client.get(
            f"/api/admin/license/{revoked_license_custom.key}",
            headers={"Authorization": f"Bearer {admin_token_custom}"}
        )
        assert get_response.json()["revoked"] is False
    
    @pytest.mark.asyncio
    async def test_reactivate_license_not_found(
        self,
        client: AsyncClient,
        admin_token_custom: str
    ):
        """Teste: Reativar licença inexistente"""
        response = await client.post(
            "/api/admin/reactivate-license",
            headers={"Authorization": f"Bearer {admin_token_custom}"},
            json={"key": "LICENCA-INEXISTENTE"}
        )
        
        assert response.status_code == 404


# ============================================================
# TESTES DE GERENCIAMENTO DE USUÁRIOS
# ============================================================

class TestUserManagement:
    """Testes de gerenciamento de usuários"""
    
    @pytest.mark.asyncio
    async def test_list_users_empty(
        self,
        client: AsyncClient,
        admin_token_custom: str
    ):
        """Teste: Listar usuários quando não há nenhum"""
        response = await client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token_custom}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["users"] == []
    
    @pytest.mark.asyncio
    async def test_list_users_with_data(
        self,
        client: AsyncClient,
        admin_token_custom: str,
        test_user_custom: User
    ):
        """Teste: Listar usuários existentes"""
        response = await client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token_custom}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["users"]) >= 1
        
        # Verificar que o usuário de teste está na lista
        emails = [user["email"] for user in data["users"]]
        assert test_user_custom.email in emails
    
    @pytest.mark.asyncio
    async def test_list_users_filter_active(
        self,
        client: AsyncClient,
        admin_token_custom: str,
        db_session: AsyncSession
    ):
        """Teste: Filtrar usuários por status ativo"""
        # Criar usuário inativo
        inactive_user = User(
            id=uuid4(),
            email="inactive@test.com",
            name="Inativo",
            password_hash=hash_password("Pass123!"),
            is_active=False,
            created_at=datetime.utcnow()
        )
        db_session.add(inactive_user)
        await db_session.commit()
        
        # Filtrar apenas ativos
        response = await client.get(
            "/api/admin/users",
            params={"is_active": True},
            headers={"Authorization": f"Bearer {admin_token_custom}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Todos devem ser ativos
        for user in data["users"]:
            assert user["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_list_users_pagination(
        self,
        client: AsyncClient,
        admin_token_custom: str,
        db_session: AsyncSession
    ):
        """Teste: Paginação de usuários"""
        # Criar múltiplos usuários
        for i in range(5):
            user = User(
                id=uuid4(),
                email=f"user{i}@test.com",
                name=f"User {i}",
                password_hash=hash_password("Pass123!"),
                is_active=True,
                created_at=datetime.utcnow()
            )
            db_session.add(user)
        await db_session.commit()
        
        # Primeira página
        response = await client.get(
            "/api/admin/users",
            params={"skip": 0, "limit": 2},
            headers={"Authorization": f"Bearer {admin_token_custom}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) <= 2
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(
        self,
        client: AsyncClient,
        admin_token_custom: str,
        test_user_custom: User
    ):
        """Teste: Buscar usuário por ID"""
        response = await client.get(
            f"/api/admin/users/{test_user_custom.id}",
            headers={"Authorization": f"Bearer {admin_token_custom}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_user_custom.id)
        assert data["email"] == test_user_custom.email
        assert data["name"] == test_user_custom.name
        assert data["is_active"] == test_user_custom.is_active
    
    @pytest.mark.asyncio
    async def test_get_user_not_found(
        self,
        client: AsyncClient,
        admin_token_custom: str
    ):
        """Teste: Buscar usuário inexistente"""
        fake_id = str(uuid4())
        response = await client.get(
            f"/api/admin/users/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token_custom}"}
        )
        
        assert response.status_code == 404
        assert "não encontrado" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_update_user_activate(
        self,
        client: AsyncClient,
        admin_token_custom: str,
        db_session: AsyncSession
    ):
        """Teste: Ativar usuário inativo"""
        # Criar usuário inativo
        inactive_user = User(
            id=uuid4(),
            email="to_activate@test.com",
            name="To Activate",
            password_hash=hash_password("Pass123!"),
            is_active=False,
            created_at=datetime.utcnow()
        )
        db_session.add(inactive_user)
        await db_session.commit()
        
        # Ativar
        response = await client.put(
            f"/api/admin/users/{inactive_user.id}",
            params={"is_active": True},
            headers={"Authorization": f"Bearer {admin_token_custom}"}
        )
        
        assert response.status_code == 200
        assert response.json()["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_update_user_deactivate(
        self,
        client: AsyncClient,
        admin_token_custom: str,
        test_user_custom: User
    ):
        """Teste: Desativar usuário ativo"""
        response = await client.put(
            f"/api/admin/users/{test_user_custom.id}",
            params={"is_active": False},
            headers={"Authorization": f"Bearer {admin_token_custom}"}
        )
        
        assert response.status_code == 200
        assert response.json()["is_active"] is False
    
    @pytest.mark.asyncio
    async def test_update_user_verify_email(
        self,
        client: AsyncClient,
        admin_token_custom: str,
        db_session: AsyncSession
    ):
        """Teste: Marcar email como verificado"""
        # Criar usuário com email não verificado
        unverified_user = User(
            id=uuid4(),
            email="unverified@test.com",
            name="Unverified",
            password_hash=hash_password("Pass123!"),
            is_active=True,
            email_verified=False,
            created_at=datetime.utcnow()
        )
        db_session.add(unverified_user)
        await db_session.commit()
        
        # Verificar email
        response = await client.put(
            f"/api/admin/users/{unverified_user.id}",
            params={"email_verified": True},
            headers={"Authorization": f"Bearer {admin_token_custom}"}
        )
        
        assert response.status_code == 200
        assert response.json()["email_verified"] is True
    
    @pytest.mark.asyncio
    async def test_delete_user_success(
        self,
        client: AsyncClient,
        admin_token_custom: str,
        db_session: AsyncSession
    ):
        """Teste: Excluir usuário"""
        # Criar usuário para excluir
        user_to_delete = User(
            id=uuid4(),
            email="to_delete@test.com",
            name="To Delete",
            password_hash=hash_password("Pass123!"),
            is_active=True,
            created_at=datetime.utcnow()
        )
        db_session.add(user_to_delete)
        await db_session.commit()
        user_email = user_to_delete.email
        
        # Excluir
        response = await client.delete(
            f"/api/admin/users/{user_to_delete.id}",
            headers={"Authorization": f"Bearer {admin_token_custom}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert user_email in data["message"]
        
        # Verificar que foi excluído
        get_response = await client.get(
            f"/api/admin/users/{user_to_delete.id}",
            headers={"Authorization": f"Bearer {admin_token_custom}"}
        )
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_user_not_found(
        self,
        client: AsyncClient,
        admin_token_custom: str
    ):
        """Teste: Excluir usuário inexistente"""
        fake_id = str(uuid4())
        response = await client.delete(
            f"/api/admin/users/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token_custom}"}
        )
        
        assert response.status_code == 404


# ============================================================
# TESTES DE PERMISSÕES E SEGURANÇA
# ============================================================

class TestAdminSecurity:
    """Testes de segurança e permissões"""
    
    @pytest.mark.asyncio
    async def test_admin_endpoints_require_auth(
        self,
        client: AsyncClient
    ):
        """Teste: Endpoints admin requerem autenticação"""
        endpoints = [
            ("GET", "/api/admin/licenses"),
            ("POST", "/api/admin/generate-license"),
            ("GET", "/api/admin/users"),
        ]
        
        for method, endpoint in endpoints:
            if method == "GET":
                response = await client.get(endpoint)
            elif method == "POST":
                response = await client.post(endpoint, json={})
            
            assert response.status_code == 401, f"{method} {endpoint} deveria retornar 401"
    
    @pytest.mark.asyncio
    async def test_admin_endpoints_reject_invalid_token(
        self,
        client: AsyncClient
    ):
        """Teste: Endpoints admin rejeitam token inválido"""
        headers = {"Authorization": "Bearer invalid_token_12345"}
        
        response = await client.get(
            "/api/admin/licenses",
            headers=headers
        )
        
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_admin_cannot_access_superadmin_endpoints(
        self,
        client: AsyncClient,
        admin_token_custom: str
    ):
        """Teste: Admin normal não pode acessar endpoints de superadmin"""
        # Endpoint que requer superadmin
        response = await client.get(
            "/api/admin/admins",
            headers={"Authorization": f"Bearer {admin_token_custom}"}
        )
        
        # Deve retornar 403 (Forbidden) ou 401
        assert response.status_code in [401, 403]
    
    @pytest.mark.asyncio
    async def test_superadmin_can_access_all_endpoints(
        self,
        client: AsyncClient,
        superadmin_token: str
    ):
        """Teste: Superadmin pode acessar todos os endpoints"""
        # Endpoint de superadmin
        response = await client.get(
            "/api/admin/admins",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        
        assert response.status_code == 200


# ============================================================
# TESTES DE INTEGRAÇÃO COMPLETA
# ============================================================

class TestAdminIntegration:
    """Testes de integração completa do fluxo admin"""
    
    @pytest.mark.asyncio
    async def test_complete_admin_workflow(
        self,
        client: AsyncClient,
        admin_user_custom: AdminUser
    ):
        """Teste: Fluxo completo de trabalho do admin"""
        # 1. Login
        login_response = await client.post(
            "/api/auth/admin/login",
            json={
                "email": admin_user_custom.email,
                "password": "AdminPass123!"
            }
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Verificar dados do admin
        me_response = await client.get("/api/auth/admin/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["email"] == admin_user_custom.email
        
        # 3. Gerar nova licença
        generate_response = await client.post(
            "/api/admin/generate-license",
            headers=headers,
            json={
                "customer_name": "Cliente Integração",
                "email": "integracao@test.com",
                "license_type": "pro",
                "duration_months": 6
            }
        )
        assert generate_response.status_code == 200
        license_key = generate_response.json()["license"]["key"]
        
        # 4. Listar licenças
        list_response = await client.get("/api/admin/licenses", headers=headers)
        assert list_response.status_code == 200
        assert list_response.json()["total"] >= 1
        
        # 5. Buscar licença específica
        get_response = await client.get(
            f"/api/admin/license/{license_key}",
            headers=headers
        )
        assert get_response.status_code == 200
        assert get_response.json()["key"] == license_key
        
        # 6. Revogar licença
        revoke_response = await client.post(
            "/api/admin/revoke-license",
            headers=headers,
            json={"key": license_key, "reason": "Teste de integração"}
        )
        assert revoke_response.status_code == 200
        
        # 7. Reativar licença
        reactivate_response = await client.post(
            "/api/admin/reactivate-license",
            headers=headers,
            json={"key": license_key}
        )
        assert reactivate_response.status_code == 200
        
        # 8. Listar usuários
        users_response = await client.get("/api/admin/users", headers=headers)
        assert users_response.status_code == 200

