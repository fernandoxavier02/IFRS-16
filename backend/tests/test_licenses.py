"""
Testes para endpoints de validação de licença
"""

import pytest
from httpx import AsyncClient

from app.models import License


# ============================================================
# Testes de Validação de Licença
# ============================================================

@pytest.mark.asyncio
async def test_validate_valid_license(
    client: AsyncClient,
    sample_license: License
):
    """Teste: Licença válida retorna token"""
    response = await client.post(
        "/api/validate-license",
        json={
            "key": sample_license.key,
            "machine_id": "test-machine-001",
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
async def test_validate_license_case_insensitive(
    client: AsyncClient,
    sample_license: License
):
    """Teste: Validação deve ser case-insensitive"""
    response = await client.post(
        "/api/validate-license",
        json={"key": sample_license.key.lower()}
    )
    
    assert response.status_code == 200
    assert response.json()["valid"] is True


@pytest.mark.asyncio
async def test_validate_invalid_license(client: AsyncClient):
    """Teste: Chave inexistente retorna 404"""
    response = await client.post(
        "/api/validate-license",
        json={"key": "CHAVE-INEXISTENTE-123"}
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "não encontrada" in data["detail"].lower()


@pytest.mark.asyncio
async def test_validate_expired_license(
    client: AsyncClient,
    expired_license: License
):
    """Teste: Licença expirada retorna 403"""
    response = await client.post(
        "/api/validate-license",
        json={"key": expired_license.key}
    )
    
    assert response.status_code == 403
    data = response.json()
    assert "expirada" in data["detail"].lower()


@pytest.mark.asyncio
async def test_validate_revoked_license(
    client: AsyncClient,
    revoked_license: License
):
    """Teste: Licença revogada retorna 403"""
    response = await client.post(
        "/api/validate-license",
        json={"key": revoked_license.key}
    )
    
    assert response.status_code == 403
    data = response.json()
    assert "revogada" in data["detail"].lower()


@pytest.mark.asyncio
async def test_validate_suspended_license(
    client: AsyncClient,
    suspended_license: License
):
    """Teste: Licença suspensa retorna 403"""
    response = await client.post(
        "/api/validate-license",
        json={"key": suspended_license.key}
    )
    
    assert response.status_code == 403
    data = response.json()
    assert "suspensa" in data["detail"].lower()


@pytest.mark.asyncio
async def test_validate_empty_key(client: AsyncClient):
    """Teste: Chave vazia retorna erro de validação"""
    response = await client.post(
        "/api/validate-license",
        json={"key": ""}
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_validate_missing_key(client: AsyncClient):
    """Teste: Requisição sem chave retorna erro"""
    response = await client.post(
        "/api/validate-license",
        json={}
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_machine_id_binding_first_activation(
    client: AsyncClient,
    sample_license: License
):
    """Teste: Primeira ativação vincula machine_id"""
    response = await client.post(
        "/api/validate-license",
        json={
            "key": sample_license.key,
            "machine_id": "first-machine-id"
        }
    )
    
    assert response.status_code == 200
    assert response.json()["valid"] is True


@pytest.mark.asyncio
async def test_machine_id_binding_second_machine_blocked(
    client: AsyncClient,
    license_with_machine: License
):
    """Teste: Segunda máquina bloqueada se limite atingido"""
    response = await client.post(
        "/api/validate-license",
        json={
            "key": license_with_machine.key,
            "machine_id": "different-machine-id"
        }
    )
    
    assert response.status_code == 403
    data = response.json()
    assert "ativações" in data["detail"].lower() or "dispositivo" in data["detail"].lower()


# ============================================================
# Testes de Verificação de Token
# ============================================================

@pytest.mark.asyncio
async def test_check_license_valid_token(
    client: AsyncClient,
    sample_license: License,
    valid_token: str
):
    """Teste: Token válido retorna status da licença"""
    response = await client.post(
        "/api/check-license",
        headers={"Authorization": f"Bearer {valid_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_check_license_no_token(client: AsyncClient):
    """Teste: Requisição sem token retorna 401"""
    response = await client.post("/api/check-license")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_check_license_invalid_token(
    client: AsyncClient,
    invalid_token: str
):
    """Teste: Token inválido retorna 401"""
    response = await client.post(
        "/api/check-license",
        headers={"Authorization": f"Bearer {invalid_token}"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_check_license_expired_token(
    client: AsyncClient,
    sample_license: License,
    expired_token: str
):
    """Teste: Token expirado retorna 401"""
    response = await client.post(
        "/api/check-license",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    
    assert response.status_code == 401


# ============================================================
# Testes de Features por Tipo de Licença
# ============================================================

@pytest.mark.asyncio
async def test_license_features_returned(
    client: AsyncClient,
    sample_license: License
):
    """Teste: Features são retornadas na validação"""
    response = await client.post(
        "/api/validate-license",
        json={"key": sample_license.key}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    features = data["data"]["features"]
    assert "max_contracts" in features
    assert "export_excel" in features
    assert "export_csv" in features
    assert "support" in features
    
    # PRO license should have export_excel and support
    assert features["export_excel"] is True
    assert features["support"] is True

