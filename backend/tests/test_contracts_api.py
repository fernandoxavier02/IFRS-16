"""
Testes para API de contratos
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from datetime import datetime, timedelta

from app.models import User, License, LicenseStatus, LicenseType, Contract, ContractStatus
from app.auth import hash_password, create_user_token


@pytest_asyncio.fixture
async def user_with_trial_license(db_session: AsyncSession) -> tuple[User, License, str]:
    """Cria um usuário com licença Trial e retorna (user, license, token)"""
    user = User(
        id=uuid4(),
        email="trial@test.com",
        name="Trial User",
        password_hash=hash_password("TestUser123!"),
        is_active=True,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    license = License(
        id=uuid4(),
        key="TRIAL-TEST-001",
        user_id=user.id,
        customer_name="Trial User",
        email="trial@test.com",
        status=LicenseStatus.ACTIVE,
        license_type=LicenseType.TRIAL,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=7),
        revoked=False,
        max_activations=1,
        current_activations=0,
    )
    db_session.add(license)
    await db_session.commit()
    await db_session.refresh(license)
    
    token = create_user_token(user.id, user.email)
    
    return user, license, token


@pytest_asyncio.fixture
async def user_with_basic_license(db_session: AsyncSession):
    """Cria um usuário com licença Basic e retorna (user, license, token)"""
    user = User(
        id=uuid4(),
        email="basic@test.com",
        name="Basic User",
        password_hash=hash_password("TestUser123!"),
        is_active=True,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    license = License(
        id=uuid4(),
        key="BASIC-TEST-001",
        user_id=user.id,
        customer_name="Basic User",
        email="basic@test.com",
        status=LicenseStatus.ACTIVE,
        license_type=LicenseType.BASIC,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30),
        revoked=False,
        max_activations=1,
        current_activations=0,
    )
    db_session.add(license)
    await db_session.commit()
    await db_session.refresh(license)
    
    token = create_user_token(user.id, user.email)
    
    return user, license, token


@pytest_asyncio.fixture
async def user_with_pro_license(db_session: AsyncSession) -> tuple[User, License, str]:
    """Cria um usuário com licença Pro e retorna (user, license, token)"""
    user = User(
        id=uuid4(),
        email="pro@test.com",
        name="Pro User",
        password_hash=hash_password("TestUser123!"),
        is_active=True,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    license = License(
        id=uuid4(),
        key="PRO-TEST-001",
        user_id=user.id,
        customer_name="Pro User",
        email="pro@test.com",
        status=LicenseStatus.ACTIVE,
        license_type=LicenseType.PRO,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=365),
        revoked=False,
        max_activations=1,
        current_activations=0,
    )
    db_session.add(license)
    await db_session.commit()
    await db_session.refresh(license)
    
    token = create_user_token(user.id, user.email)
    
    return user, license, token


@pytest_asyncio.fixture
async def user_with_enterprise_license(db_session: AsyncSession):
    """Cria um usuário com licença Enterprise e retorna (user, license, token)"""
    user = User(
        id=uuid4(),
        email="enterprise@test.com",
        name="Enterprise User",
        password_hash=hash_password("TestUser123!"),
        is_active=True,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    license = License(
        id=uuid4(),
        key="ENTERPRISE-TEST-001",
        user_id=user.id,
        customer_name="Enterprise User",
        email="enterprise@test.com",
        status=LicenseStatus.ACTIVE,
        license_type=LicenseType.ENTERPRISE,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=365),
        revoked=False,
        max_activations=1,
        current_activations=0,
    )
    db_session.add(license)
    await db_session.commit()
    await db_session.refresh(license)
    
    token = create_user_token(user.id, user.email)
    
    return user, license, token


@pytest_asyncio.fixture
async def user_without_license(db_session: AsyncSession):
    """Cria um usuário sem licença e retorna (user, token)"""
    user = User(
        id=uuid4(),
        email="nolicense@test.com",
        name="No License User",
        password_hash=hash_password("TestUser123!"),
        is_active=True,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    token = create_user_token(user.id, user.email)
    
    return user, token


class TestCreateContract:
    """Testes de criação de contratos"""
    
    @pytest.mark.asyncio
    async def test_create_contract_success(
        self,
        client: AsyncClient,
        user_with_trial_license: tuple[User, License, str]
    ):
        """Deve criar um contrato com sucesso"""
        user, license, token = user_with_trial_license
        
        response = await client.post(
            "/api/contracts",
            json={
                "name": "Contrato Teste",
                "description": "Descrição do contrato",
                "contract_code": "CT-001",
                "status": "draft"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Contrato Teste"
        assert data["description"] == "Descrição do contrato"
        assert data["contract_code"] == "CT-001"
        assert data["status"] == "draft"
        assert data["user_id"] == str(user.id)
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    @pytest.mark.asyncio
    async def test_create_contract_without_license(
        self,
        client: AsyncClient,
        user_without_license: tuple[User, str]
    ):
        """Deve rejeitar criação de contrato sem licença ativa"""
        user, token = user_without_license
        
        response = await client.post(
            "/api/contracts",
            json={
                "name": "Contrato Teste",
                "description": "Descrição do contrato"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "licença ativa" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_create_contract_exceeds_trial_limit(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user_with_trial_license: tuple[User, License, str]
    ):
        """Deve rejeitar criação do 6º contrato com Trial (limite: 5)"""
        user, license, token = user_with_trial_license
        
        # Criar 5 contratos (limite do Trial)
        for i in range(5):
            contract = Contract(
                id=uuid4(),
                user_id=user.id,
                name=f"Contrato {i+1}",
                status=ContractStatus.DRAFT,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db_session.add(contract)
        await db_session.commit()
        
        # Tentar criar o 6º contrato
        response = await client.post(
            "/api/contracts",
            json={
                "name": "Contrato 6",
                "description": "Sexto contrato"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "limite" in response.json()["detail"].lower()
        assert "5" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_contract_exceeds_basic_limit(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user_with_basic_license: tuple[User, License, str]
    ):
        """Deve rejeitar criação do 51º contrato com Basic (limite: 50)"""
        user, license, token = user_with_basic_license
        
        # Criar 50 contratos (limite do Basic)
        for i in range(50):
            contract = Contract(
                id=uuid4(),
                user_id=user.id,
                name=f"Contrato {i+1}",
                status=ContractStatus.DRAFT,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db_session.add(contract)
        await db_session.commit()
        
        # Tentar criar o 51º contrato
        response = await client.post(
            "/api/contracts",
            json={
                "name": "Contrato 51",
                "description": "Quinquagésimo primeiro contrato"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "limite" in response.json()["detail"].lower()
        assert "50" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_contract_unlimited_enterprise(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user_with_enterprise_license: tuple[User, License, str]
    ):
        """Deve permitir criar múltiplos contratos com Enterprise (ilimitado)"""
        user, license, token = user_with_enterprise_license
        
        # Criar 10 contratos (Enterprise é ilimitado)
        for i in range(10):
            response = await client.post(
                "/api/contracts",
                json={
                    "name": f"Contrato Enterprise {i+1}",
                    "description": f"Descrição {i+1}"
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 201
        
        # Verificar que todos foram criados
        list_response = await client.get(
            "/api/contracts",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert list_response.status_code == 200
        data = list_response.json()
        assert data["total"] == 10


class TestListContracts:
    """Testes de listagem de contratos"""
    
    @pytest.mark.asyncio
    async def test_list_contracts_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user_with_trial_license: tuple[User, License, str]
    ):
        """Deve listar contratos do usuário"""
        user, license, token = user_with_trial_license
        
        # Criar alguns contratos
        for i in range(3):
            contract = Contract(
                id=uuid4(),
                user_id=user.id,
                name=f"Contrato {i+1}",
                status=ContractStatus.DRAFT,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db_session.add(contract)
        await db_session.commit()
        
        response = await client.get(
            "/api/contracts",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["contracts"]) == 3
    
    @pytest.mark.asyncio
    async def test_list_contracts_empty(
        self,
        client: AsyncClient,
        user_with_trial_license: tuple[User, License, str]
    ):
        """Deve retornar lista vazia quando não há contratos"""
        user, license, token = user_with_trial_license
        
        response = await client.get(
            "/api/contracts",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["contracts"]) == 0
    
    @pytest.mark.asyncio
    async def test_list_contracts_excludes_deleted(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user_with_trial_license: tuple[User, License, str]
    ):
        """Deve excluir contratos deletados da listagem por padrão"""
        user, license, token = user_with_trial_license
        
        # Criar contrato ativo
        active_contract = Contract(
            id=uuid4(),
            user_id=user.id,
            name="Contrato Ativo",
            status=ContractStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(active_contract)
        
        # Criar contrato deletado
        deleted_contract = Contract(
            id=uuid4(),
            user_id=user.id,
            name="Contrato Deletado",
            status=ContractStatus.DRAFT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            deleted_at=datetime.utcnow(),
        )
        db_session.add(deleted_contract)
        await db_session.commit()
        
        response = await client.get(
            "/api/contracts",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["contracts"][0]["name"] == "Contrato Ativo"
        
        # Com include_deleted=True
        response_with_deleted = await client.get(
            "/api/contracts?include_deleted=true",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response_with_deleted.status_code == 200
        data_with_deleted = response_with_deleted.json()
        assert data_with_deleted["total"] == 2


class TestGetContract:
    """Testes de obtenção de contrato específico"""
    
    @pytest.mark.asyncio
    async def test_get_contract_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user_with_trial_license: tuple[User, License, str]
    ):
        """Deve obter um contrato específico"""
        user, license, token = user_with_trial_license
        
        contract = Contract(
            id=uuid4(),
            user_id=user.id,
            name="Contrato Teste",
            description="Descrição",
            status=ContractStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(contract)
        await db_session.commit()
        
        response = await client.get(
            f"/api/contracts/{contract.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(contract.id)
        assert data["name"] == "Contrato Teste"
        assert data["description"] == "Descrição"
    
    @pytest.mark.asyncio
    async def test_get_contract_not_found(
        self,
        client: AsyncClient,
        user_with_trial_license: tuple[User, License, str]
    ):
        """Deve retornar 404 para contrato inexistente"""
        user, license, token = user_with_trial_license
        fake_id = uuid4()
        
        response = await client.get(
            f"/api/contracts/{fake_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_contract_other_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user_with_trial_license: tuple[User, License, str],
        user_with_basic_license: tuple[User, License, str]
    ):
        """Deve retornar 404 ao tentar acessar contrato de outro usuário"""
        user1, license1, token1 = user_with_trial_license
        user2, license2, token2 = user_with_basic_license
        
        # Criar contrato para user2
        contract = Contract(
            id=uuid4(),
            user_id=user2.id,
            name="Contrato do User2",
            status=ContractStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(contract)
        await db_session.commit()
        
        # User1 tenta acessar contrato do User2
        response = await client.get(
            f"/api/contracts/{contract.id}",
            headers={"Authorization": f"Bearer {token1}"}
        )
        
        assert response.status_code == 404


class TestUpdateContract:
    """Testes de atualização de contratos"""
    
    @pytest.mark.asyncio
    async def test_update_contract_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user_with_trial_license: tuple[User, License, str]
    ):
        """Deve atualizar um contrato com sucesso"""
        user, license, token = user_with_trial_license
        
        contract = Contract(
            id=uuid4(),
            user_id=user.id,
            name="Contrato Original",
            description="Descrição original",
            status=ContractStatus.DRAFT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(contract)
        await db_session.commit()
        
        response = await client.put(
            f"/api/contracts/{contract.id}",
            json={
                "name": "Contrato Atualizado",
                "description": "Nova descrição",
                "status": "active"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Contrato Atualizado"
        assert data["description"] == "Nova descrição"
        assert data["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_update_contract_partial(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user_with_trial_license: tuple[User, License, str]
    ):
        """Deve atualizar apenas campos fornecidos"""
        user, license, token = user_with_trial_license
        
        contract = Contract(
            id=uuid4(),
            user_id=user.id,
            name="Contrato Original",
            description="Descrição original",
            status=ContractStatus.DRAFT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(contract)
        await db_session.commit()
        
        response = await client.put(
            f"/api/contracts/{contract.id}",
            json={
                "name": "Apenas Nome Atualizado"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Apenas Nome Atualizado"
        assert data["description"] == "Descrição original"  # Não mudou
    
    @pytest.mark.asyncio
    async def test_update_contract_other_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user_with_trial_license: tuple[User, License, str],
        user_with_basic_license: tuple[User, License, str]
    ):
        """Deve retornar 404 ao tentar atualizar contrato de outro usuário"""
        user1, license1, token1 = user_with_trial_license
        user2, license2, token2 = user_with_basic_license
        
        contract = Contract(
            id=uuid4(),
            user_id=user2.id,
            name="Contrato do User2",
            status=ContractStatus.DRAFT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(contract)
        await db_session.commit()
        
        response = await client.put(
            f"/api/contracts/{contract.id}",
            json={"name": "Tentativa de atualização"},
            headers={"Authorization": f"Bearer {token1}"}
        )
        
        assert response.status_code == 404


class TestDeleteContract:
    """Testes de exclusão de contratos"""
    
    @pytest.mark.asyncio
    async def test_delete_contract_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user_with_trial_license: tuple[User, License, str]
    ):
        """Deve realizar soft delete de um contrato"""
        user, license, token = user_with_trial_license
        
        contract = Contract(
            id=uuid4(),
            user_id=user.id,
            name="Contrato para Deletar",
            status=ContractStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(contract)
        await db_session.commit()
        
        response = await client.delete(
            f"/api/contracts/{contract.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 204
        
        # Verificar que não aparece mais na listagem padrão
        list_response = await client.get(
            "/api/contracts",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert list_response.status_code == 200
        data = list_response.json()
        assert data["total"] == 0
    
    @pytest.mark.asyncio
    async def test_delete_contract_other_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user_with_trial_license: tuple[User, License, str],
        user_with_basic_license: tuple[User, License, str]
    ):
        """Deve retornar 404 ao tentar deletar contrato de outro usuário"""
        user1, license1, token1 = user_with_trial_license
        user2, license2, token2 = user_with_basic_license
        
        contract = Contract(
            id=uuid4(),
            user_id=user2.id,
            name="Contrato do User2",
            status=ContractStatus.ACTIVE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(contract)
        await db_session.commit()
        
        response = await client.delete(
            f"/api/contracts/{contract.id}",
            headers={"Authorization": f"Bearer {token1}"}
        )
        
        assert response.status_code == 404


class TestContractLimits:
    """Testes de limites de contratos por plano"""
    
    @pytest.mark.asyncio
    async def test_contract_limit_trial(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user_with_trial_license: tuple[User, License, str]
    ):
        """Deve permitir até 5 contratos com Trial"""
        user, license, token = user_with_trial_license
        
        # Criar 5 contratos (limite)
        for i in range(5):
            response = await client.post(
                "/api/contracts",
                json={"name": f"Contrato {i+1}"},
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 201
        
        # Tentar criar o 6º deve falhar
        response = await client.post(
            "/api/contracts",
            json={"name": "Contrato 6"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_contract_limit_basic(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user_with_basic_license: tuple[User, License, str]
    ):
        """Deve permitir até 50 contratos com Basic"""
        user, license, token = user_with_basic_license
        
        # Criar 50 contratos (limite)
        for i in range(50):
            contract = Contract(
                id=uuid4(),
                user_id=user.id,
                name=f"Contrato {i+1}",
                status=ContractStatus.DRAFT,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db_session.add(contract)
        await db_session.commit()
        
        # Tentar criar o 51º deve falhar
        response = await client.post(
            "/api/contracts",
            json={"name": "Contrato 51"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_contract_limit_pro(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        user_with_pro_license: tuple[User, License, str]
    ):
        """Deve permitir até 500 contratos com Pro"""
        user, license, token = user_with_pro_license
        
        # Criar 500 contratos (limite)
        for i in range(500):
            contract = Contract(
                id=uuid4(),
                user_id=user.id,
                name=f"Contrato {i+1}",
                status=ContractStatus.DRAFT,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db_session.add(contract)
        await db_session.commit()
        
        # Tentar criar o 501º deve falhar
        response = await client.post(
            "/api/contracts",
            json={"name": "Contrato 501"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403
    
    @pytest.mark.asyncio
    async def test_contract_unlimited_enterprise(
        self,
        client: AsyncClient,
        user_with_enterprise_license: tuple[User, License, str]
    ):
        """Deve permitir contratos ilimitados com Enterprise"""
        user, license, token = user_with_enterprise_license
        
        # Criar múltiplos contratos (Enterprise é ilimitado)
        for i in range(20):
            response = await client.post(
                "/api/contracts",
                json={"name": f"Contrato Enterprise {i+1}"},
                headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 201
        
        # Verificar que todos foram criados
        list_response = await client.get(
            "/api/contracts",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert list_response.status_code == 200
        data = list_response.json()
        assert data["total"] == 20
