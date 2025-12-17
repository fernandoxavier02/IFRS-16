"""
Testes para endpoints administrativos
"""

import pytest
from httpx import AsyncClient

from app.models import License, LicenseStatus, AdminUser


# ============================================================
# Testes de Autenticação Admin
# ============================================================

@pytest.mark.asyncio
async def test_admin_without_token(client: AsyncClient):
    """Teste: Requisição admin sem token retorna 401"""
    response = await client.get("/api/admin/licenses")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_with_invalid_token(client: AsyncClient):
    """Teste: Token admin inválido retorna 401"""
    response = await client.get(
        "/api/admin/licenses",
        headers={"Authorization": "Bearer invalid-token"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_with_valid_token(
    client: AsyncClient,
    admin_token: str,
    admin_user: AdminUser
):
    """Teste: Token admin válido permite acesso"""
    response = await client.get(
        "/api/admin/licenses",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200


# ============================================================
# Testes de Listagem de Licenças
# ============================================================

@pytest.mark.asyncio
async def test_list_licenses_empty(
    client: AsyncClient,
    admin_token: str,
    admin_user: AdminUser
):
    """Teste: Lista vazia quando não há licenças"""
    response = await client.get(
        "/api/admin/licenses",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["licenses"] == []


@pytest.mark.asyncio
async def test_list_licenses_with_data(
    client: AsyncClient,
    admin_token: str,
    admin_user: AdminUser,
    sample_license: License
):
    """Teste: Lista licenças existentes"""
    response = await client.get(
        "/api/admin/licenses",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["licenses"]) >= 1
    
    # Verificar que a licença de teste está na lista
    keys = [lic["key"] for lic in data["licenses"]]
    assert sample_license.key in keys


@pytest.mark.asyncio
async def test_list_licenses_with_filter(
    client: AsyncClient,
    admin_token: str,
    admin_user: AdminUser,
    sample_license: License,
    suspended_license: License
):
    """Teste: Filtrar licenças por status"""
    response = await client.get(
        "/api/admin/licenses",
        params={"status_filter": "active"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Todas devem ser ativas
    for lic in data["licenses"]:
        assert lic["status"] == "active"


# ============================================================
# Testes de Geração de Licença
# ============================================================

@pytest.mark.asyncio
async def test_generate_license_success(
    client: AsyncClient,
    admin_token: str,
    admin_user: AdminUser
):
    """Teste: Gerar nova licença com sucesso"""
    response = await client.post(
        "/api/admin/generate-license",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "customer_name": "Novo Cliente",
            "email": "novo@cliente.com",
            "license_type": "pro",
            "duration_months": 12,
            "max_activations": 2
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert data["license"]["customer_name"] == "Novo Cliente"
    assert data["license"]["email"] == "novo@cliente.com"
    assert data["license"]["license_type"] == "pro"
    assert data["license"]["status"] == "active"
    assert "FX2025-IFRS16" in data["license"]["key"]


@pytest.mark.asyncio
async def test_generate_license_trial(
    client: AsyncClient,
    admin_token: str,
    admin_user: AdminUser
):
    """Teste: Gerar licença trial"""
    response = await client.post(
        "/api/admin/generate-license",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "customer_name": "Trial User",
            "email": "trial@user.com",
            "license_type": "trial",
            "duration_months": 1
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["license"]["license_type"] == "trial"
    assert data["license"]["expires_at"] is not None


@pytest.mark.asyncio
async def test_generate_license_permanent(
    client: AsyncClient,
    admin_token: str,
    admin_user: AdminUser
):
    """Teste: Gerar licença permanente (sem expiração)"""
    response = await client.post(
        "/api/admin/generate-license",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "customer_name": "Permanent User",
            "email": "permanent@user.com",
            "license_type": "enterprise"
            # Sem duration_months = permanente
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["license"]["expires_at"] is None


@pytest.mark.asyncio
async def test_generate_license_invalid_email(
    client: AsyncClient,
    admin_token: str,
    admin_user: AdminUser
):
    """Teste: Email inválido retorna erro de validação"""
    response = await client.post(
        "/api/admin/generate-license",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "customer_name": "Test",
            "email": "invalid-email",
            "license_type": "trial"
        }
    )
    
    assert response.status_code == 422


# ============================================================
# Testes de Revogação de Licença
# ============================================================

@pytest.mark.asyncio
async def test_revoke_license_success(
    client: AsyncClient,
    admin_token: str,
    admin_user: AdminUser,
    sample_license: License
):
    """Teste: Revogar licença com sucesso"""
    response = await client.post(
        "/api/admin/revoke-license",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "key": sample_license.key,
            "reason": "Pagamento não realizado"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert sample_license.key in data["message"]


@pytest.mark.asyncio
async def test_revoke_license_not_found(
    client: AsyncClient,
    admin_token: str,
    admin_user: AdminUser
):
    """Teste: Revogar licença inexistente retorna 404"""
    response = await client.post(
        "/api/admin/revoke-license",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"key": "LICENCA-INEXISTENTE"}
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_revoke_then_validate_fails(
    client: AsyncClient,
    admin_token: str,
    admin_user: AdminUser,
    sample_license: License
):
    """Teste: Licença revogada não pode ser validada"""
    # Revogar
    await client.post(
        "/api/admin/revoke-license",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"key": sample_license.key}
    )
    
    # Tentar validar
    response = await client.post(
        "/api/validate-license",
        json={"key": sample_license.key}
    )
    
    assert response.status_code == 403
    assert "revogada" in response.json()["detail"].lower()


# ============================================================
# Testes de Reativação de Licença
# ============================================================

@pytest.mark.asyncio
async def test_reactivate_license_success(
    client: AsyncClient,
    admin_token: str,
    admin_user: AdminUser,
    revoked_license: License
):
    """Teste: Reativar licença com sucesso"""
    response = await client.post(
        "/api/admin/reactivate-license",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"key": revoked_license.key}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True


@pytest.mark.asyncio
async def test_reactivate_then_validate_works(
    client: AsyncClient,
    admin_token: str,
    admin_user: AdminUser,
    revoked_license: License
):
    """Teste: Licença reativada pode ser validada"""
    # Reativar
    await client.post(
        "/api/admin/reactivate-license",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"key": revoked_license.key}
    )
    
    # Validar
    response = await client.post(
        "/api/validate-license",
        json={"key": revoked_license.key}
    )
    
    assert response.status_code == 200
    assert response.json()["valid"] is True


@pytest.mark.asyncio
async def test_reactivate_license_not_found(
    client: AsyncClient,
    admin_token: str,
    admin_user: AdminUser
):
    """Teste: Reativar licença inexistente retorna 404"""
    response = await client.post(
        "/api/admin/reactivate-license",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"key": "LICENCA-INEXISTENTE"}
    )
    
    assert response.status_code == 404


# ============================================================
# Testes de Busca de Licença Individual
# ============================================================

@pytest.mark.asyncio
async def test_get_license_by_key(
    client: AsyncClient,
    admin_token: str,
    admin_user: AdminUser,
    sample_license: License
):
    """Teste: Buscar licença por chave"""
    response = await client.get(
        f"/api/admin/license/{sample_license.key}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["key"] == sample_license.key
    assert data["customer_name"] == sample_license.customer_name


@pytest.mark.asyncio
async def test_get_license_not_found(
    client: AsyncClient,
    admin_token: str,
    admin_user: AdminUser
):
    """Teste: Buscar licença inexistente retorna 404"""
    response = await client.get(
        "/api/admin/license/INEXISTENTE",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 404


# ============================================================
# Testes de Logs de Validação
# ============================================================

@pytest.mark.asyncio
async def test_get_license_logs(
    client: AsyncClient,
    admin_token: str,
    admin_user: AdminUser,
    sample_license: License
):
    """Teste: Buscar logs de validação"""
    # Primeiro, fazer uma validação para gerar log
    await client.post(
        "/api/validate-license",
        json={"key": sample_license.key}
    )
    
    # Buscar logs
    response = await client.get(
        f"/api/admin/license/{sample_license.key}/logs",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["license_key"] == sample_license.key
    assert data["total"] >= 1
    assert len(data["logs"]) >= 1

