"""
Testes completos para o fluxo de validação de licenças

Este arquivo contém testes que cobrem todo o ciclo de vida das licenças:
- Validação inicial
- Controle de ativações
- Expiração automática
- Revogação e reativação
- Logs de validação
- Features por tipo de licença
- Fluxo completo de uso
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import License, LicenseStatus, LicenseType, ValidationLog
from app.auth import create_access_token


# ============================================================
# TESTES DE VALIDAÇÃO BÁSICA
# ============================================================

class TestBasicValidation:
    """Testes de validação básica de licenças"""

    @pytest.mark.asyncio
    async def test_validate_with_all_parameters(
        self, client: AsyncClient, sample_license: License
    ):
        """Teste: Validação com todos os parâmetros"""
        response = await client.post(
            "/api/validate-license",
            json={
                "key": sample_license.key,
                "machine_id": "machine-abc-123",
                "app_version": "1.0.5"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "token" in data
        assert len(data["token"]) > 50  # JWT é longo
        assert data["data"]["customer_name"] == sample_license.customer_name

    @pytest.mark.asyncio
    async def test_validate_without_optional_params(
        self, client: AsyncClient, sample_license: License
    ):
        """Teste: Validação sem parâmetros opcionais"""
        response = await client.post(
            "/api/validate-license",
            json={"key": sample_license.key}
        )
        
        assert response.status_code == 200
        assert response.json()["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_key_trimming(
        self, client: AsyncClient, sample_license: License
    ):
        """Teste: Espaços em branco são removidos da chave"""
        response = await client.post(
            "/api/validate-license",
            json={"key": f"  {sample_license.key}  "}
        )
        
        assert response.status_code == 200
        assert response.json()["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_key_case_insensitive(
        self, client: AsyncClient, sample_license: License
    ):
        """Teste: Validação é case-insensitive"""
        # Testar minúsculas
        response = await client.post(
            "/api/validate-license",
            json={"key": sample_license.key.lower()}
        )
        assert response.status_code == 200
        
        # Testar maiúsculas mistas
        mixed_case = sample_license.key[:4].lower() + sample_license.key[4:].upper()
        response = await client.post(
            "/api/validate-license",
            json={"key": mixed_case}
        )
        assert response.status_code == 200


# ============================================================
# TESTES DE STATUS DE LICENÇA
# ============================================================

class TestLicenseStatus:
    """Testes de diferentes status de licença"""

    @pytest.mark.asyncio
    async def test_active_license_validates(
        self, client: AsyncClient, sample_license: License
    ):
        """Teste: Licença ativa valida corretamente"""
        response = await client.post(
            "/api/validate-license",
            json={"key": sample_license.key}
        )
        
        assert response.status_code == 200
        assert response.json()["valid"] is True

    @pytest.mark.asyncio
    async def test_suspended_license_blocked(
        self, client: AsyncClient, suspended_license: License
    ):
        """Teste: Licença suspensa é bloqueada"""
        response = await client.post(
            "/api/validate-license",
            json={"key": suspended_license.key}
        )
        
        assert response.status_code == 403
        assert "suspensa" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_cancelled_license_blocked(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Teste: Licença cancelada é bloqueada"""
        license = License(
            id=uuid4(),
            key="TEST-CANCELLED-001",
            customer_name="Cancelled User",
            email="cancelled@example.com",
            status=LicenseStatus.CANCELLED,
            license_type=LicenseType.BASIC,
            created_at=datetime.utcnow() - timedelta(days=30),
            max_activations=1,
            current_activations=0,
        )
        db_session.add(license)
        await db_session.commit()
        
        response = await client.post(
            "/api/validate-license",
            json={"key": license.key}
        )
        
        assert response.status_code == 403
        assert "cancelada" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_revoked_license_blocked(
        self, client: AsyncClient, revoked_license: License
    ):
        """Teste: Licença revogada é bloqueada com mensagem específica"""
        response = await client.post(
            "/api/validate-license",
            json={"key": revoked_license.key}
        )
        
        assert response.status_code == 403
        data = response.json()
        assert "revogada" in data["detail"].lower()
        assert "suporte" in data["detail"].lower()


# ============================================================
# TESTES DE EXPIRAÇÃO
# ============================================================

class TestLicenseExpiration:
    """Testes de expiração de licenças"""

    @pytest.mark.asyncio
    async def test_expired_license_blocked(
        self, client: AsyncClient, expired_license: License
    ):
        """Teste: Licença expirada é bloqueada"""
        response = await client.post(
            "/api/validate-license",
            json={"key": expired_license.key}
        )
        
        assert response.status_code == 403
        data = response.json()
        assert "expirada" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_permanent_license_never_expires(
        self, client: AsyncClient, permanent_license: License
    ):
        """Teste: Licença permanente não expira"""
        response = await client.post(
            "/api/validate-license",
            json={"key": permanent_license.key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["data"]["expires_at"] is None

    @pytest.mark.asyncio
    async def test_license_about_to_expire_still_valid(
        self, client: AsyncClient, license_about_to_expire: License
    ):
        """Teste: Licença prestes a expirar ainda é válida"""
        response = await client.post(
            "/api/validate-license",
            json={"key": license_about_to_expire.key}
        )
        
        assert response.status_code == 200
        assert response.json()["valid"] is True

    @pytest.mark.asyncio
    async def test_expiration_date_returned_in_response(
        self, client: AsyncClient, sample_license: License
    ):
        """Teste: Data de expiração é retornada na resposta"""
        response = await client.post(
            "/api/validate-license",
            json={"key": sample_license.key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "expires_at" in data["data"]
        assert data["data"]["expires_at"] is not None


# ============================================================
# TESTES DE CONTROLE DE ATIVAÇÕES
# ============================================================

class TestActivationControl:
    """Testes de controle de ativações por machine_id"""

    @pytest.mark.asyncio
    async def test_first_activation_binds_machine_id(
        self, client: AsyncClient, sample_license: License, db_session: AsyncSession
    ):
        """Teste: Primeira ativação vincula machine_id"""
        machine_id = "first-machine-abc123"
        
        response = await client.post(
            "/api/validate-license",
            json={
                "key": sample_license.key,
                "machine_id": machine_id
            }
        )
        
        assert response.status_code == 200
        
        # Verificar que machine_id foi salvo
        await db_session.refresh(sample_license)
        assert sample_license.machine_id == machine_id

    @pytest.mark.asyncio
    async def test_same_machine_can_revalidate(
        self, client: AsyncClient, license_with_machine: License
    ):
        """Teste: Mesma máquina pode revalidar"""
        response = await client.post(
            "/api/validate-license",
            json={
                "key": license_with_machine.key,
                "machine_id": license_with_machine.machine_id
            }
        )
        
        assert response.status_code == 200
        assert response.json()["valid"] is True

    @pytest.mark.asyncio
    async def test_different_machine_blocked_when_limit_reached(
        self, client: AsyncClient, license_with_machine: License
    ):
        """Teste: Máquina diferente é bloqueada quando limite atingido"""
        response = await client.post(
            "/api/validate-license",
            json={
                "key": license_with_machine.key,
                "machine_id": "different-machine-xyz789"
            }
        )
        
        assert response.status_code == 403
        data = response.json()
        assert "ativações" in data["detail"].lower() or "dispositivo" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_multi_activation_allows_multiple_machines(
        self, client: AsyncClient, multi_activation_license: License
    ):
        """Teste: Licença multi-ativação permite múltiplas máquinas"""
        machines = ["machine-1", "machine-2", "machine-3"]
        
        for machine in machines:
            response = await client.post(
                "/api/validate-license",
                json={
                    "key": multi_activation_license.key,
                    "machine_id": machine
                }
            )
            assert response.status_code == 200, f"Falhou para {machine}"

    @pytest.mark.asyncio
    async def test_enterprise_license_allows_many_activations(
        self, client: AsyncClient, enterprise_license: License
    ):
        """Teste: Licença Enterprise permite até 10 ativações"""
        for i in range(5):  # Testar com 5 máquinas
            response = await client.post(
                "/api/validate-license",
                json={
                    "key": enterprise_license.key,
                    "machine_id": f"enterprise-machine-{i}"
                }
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_validation_without_machine_id_succeeds(
        self, client: AsyncClient, sample_license: License
    ):
        """Teste: Validação sem machine_id funciona"""
        response = await client.post(
            "/api/validate-license",
            json={"key": sample_license.key}
        )
        
        assert response.status_code == 200
        assert response.json()["valid"] is True


# ============================================================
# TESTES DE FEATURES POR TIPO DE LICENÇA
# ============================================================

class TestLicenseFeatures:
    """Testes de features por tipo de licença"""

    @pytest.mark.asyncio
    async def test_trial_license_features(
        self, client: AsyncClient, trial_license: License
    ):
        """Teste: Features da licença Trial"""
        response = await client.post(
            "/api/validate-license",
            json={"key": trial_license.key}
        )
        
        assert response.status_code == 200
        features = response.json()["data"]["features"]
        
        # Trial tem recursos limitados
        assert features["max_contracts"] <= 5
        assert features["export_excel"] is False
        assert features["support"] is False

    @pytest.mark.asyncio
    async def test_basic_license_features(
        self, client: AsyncClient, basic_license: License
    ):
        """Teste: Features da licença Basic"""
        response = await client.post(
            "/api/validate-license",
            json={"key": basic_license.key}
        )
        
        assert response.status_code == 200
        features = response.json()["data"]["features"]
        
        assert features["max_contracts"] >= 10
        assert features["export_csv"] is True

    @pytest.mark.asyncio
    async def test_pro_license_features(
        self, client: AsyncClient, sample_license: License
    ):
        """Teste: Features da licença Pro"""
        response = await client.post(
            "/api/validate-license",
            json={"key": sample_license.key}
        )
        
        assert response.status_code == 200
        features = response.json()["data"]["features"]
        
        assert features["max_contracts"] >= 50
        assert features["export_excel"] is True
        assert features["export_csv"] is True
        assert features["support"] is True

    @pytest.mark.asyncio
    async def test_enterprise_license_features(
        self, client: AsyncClient, enterprise_license: License
    ):
        """Teste: Features da licença Enterprise"""
        response = await client.post(
            "/api/validate-license",
            json={"key": enterprise_license.key}
        )
        
        assert response.status_code == 200
        features = response.json()["data"]["features"]
        
        # Enterprise tem todos os recursos
        assert features["max_contracts"] == -1  # Ilimitado
        assert features["export_excel"] is True
        assert features["export_csv"] is True
        assert features["support"] is True
        assert features["multi_user"] is True


# ============================================================
# TESTES DE VERIFICAÇÃO DE TOKEN (CHECK-LICENSE)
# ============================================================

class TestCheckLicense:
    """Testes do endpoint check-license"""

    @pytest.mark.asyncio
    async def test_check_valid_token(
        self, client: AsyncClient, sample_license: License
    ):
        """Teste: Token válido retorna status correto"""
        # Primeiro validar para obter token
        validate_response = await client.post(
            "/api/validate-license",
            json={"key": sample_license.key}
        )
        token = validate_response.json()["token"]
        
        # Depois verificar token
        check_response = await client.post(
            "/api/check-license",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert check_response.status_code == 200
        data = check_response.json()
        assert data["valid"] is True
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_check_without_token_fails(self, client: AsyncClient):
        """Teste: Requisição sem token falha"""
        response = await client.post("/api/check-license")
        
        assert response.status_code == 401
        assert "token" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_check_invalid_token_fails(self, client: AsyncClient):
        """Teste: Token inválido falha"""
        response = await client.post(
            "/api/check-license",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_check_expired_jwt_fails(self, client: AsyncClient):
        """Teste: JWT expirado falha"""
        expired_token = create_access_token(
            {"key": "TEST-LICENSE-001"},
            expires_delta=timedelta(seconds=-10)
        )
        
        response = await client.post(
            "/api/check-license",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_check_returns_expiration_date(
        self, client: AsyncClient, sample_license: License
    ):
        """Teste: Check retorna data de expiração"""
        # Validar para obter token
        validate_response = await client.post(
            "/api/validate-license",
            json={"key": sample_license.key}
        )
        token = validate_response.json()["token"]
        
        # Verificar
        check_response = await client.post(
            "/api/check-license",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert check_response.status_code == 200
        data = check_response.json()
        assert "expires_at" in data


# ============================================================
# TESTES DE LOGS DE VALIDAÇÃO
# ============================================================

class TestValidationLogs:
    """Testes de logs de validação"""

    @pytest.mark.asyncio
    async def test_successful_validation_creates_log(
        self, client: AsyncClient, sample_license: License, db_session: AsyncSession
    ):
        """Teste: Validação bem-sucedida cria log"""
        response = await client.post(
            "/api/validate-license",
            json={
                "key": sample_license.key,
                "machine_id": "test-machine-log",
                "app_version": "1.0.0"
            }
        )
        
        assert response.status_code == 200
        
        # Verificar log criado
        result = await db_session.execute(
            select(ValidationLog).where(ValidationLog.license_key == sample_license.key)
        )
        logs = result.scalars().all()
        
        assert len(logs) >= 1
        log = logs[-1]
        assert log.success is True
        assert log.machine_id == "test-machine-log"

    @pytest.mark.asyncio
    async def test_failed_validation_creates_log(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Teste: Validação falhada cria log"""
        invalid_key = "INVALID-KEY-12345"
        
        response = await client.post(
            "/api/validate-license",
            json={
                "key": invalid_key,
                "machine_id": "test-machine-failed"
            }
        )
        
        assert response.status_code == 404
        
        # Verificar log de falha
        result = await db_session.execute(
            select(ValidationLog).where(ValidationLog.license_key == invalid_key)
        )
        logs = result.scalars().all()
        
        assert len(logs) >= 1
        log = logs[-1]
        assert log.success is False
        assert "não encontrada" in log.message.lower()

    @pytest.mark.asyncio
    async def test_revoked_license_logs_attempt(
        self, client: AsyncClient, revoked_license: License, db_session: AsyncSession
    ):
        """Teste: Tentativa de usar licença revogada é logada"""
        response = await client.post(
            "/api/validate-license",
            json={"key": revoked_license.key}
        )
        
        assert response.status_code == 403
        
        # Verificar log
        result = await db_session.execute(
            select(ValidationLog).where(ValidationLog.license_key == revoked_license.key)
        )
        logs = result.scalars().all()
        
        assert len(logs) >= 1
        log = logs[-1]
        assert log.success is False
        assert "revogada" in log.message.lower()

    @pytest.mark.asyncio
    async def test_expired_license_logs_attempt(
        self, client: AsyncClient, expired_license: License, db_session: AsyncSession
    ):
        """Teste: Tentativa de usar licença expirada é logada"""
        response = await client.post(
            "/api/validate-license",
            json={"key": expired_license.key}
        )
        
        assert response.status_code == 403
        
        # Verificar log
        result = await db_session.execute(
            select(ValidationLog).where(ValidationLog.license_key == expired_license.key)
        )
        logs = result.scalars().all()
        
        assert len(logs) >= 1
        log = logs[-1]
        assert log.success is False
        assert "expirada" in log.message.lower()

    @pytest.mark.asyncio
    async def test_multiple_validations_create_multiple_logs(
        self, client: AsyncClient, sample_license: License, db_session: AsyncSession
    ):
        """Teste: Múltiplas validações criam múltiplos logs"""
        for i in range(3):
            await client.post(
                "/api/validate-license",
                json={
                    "key": sample_license.key,
                    "machine_id": f"machine-{i}"
                }
            )
        
        result = await db_session.execute(
            select(ValidationLog).where(ValidationLog.license_key == sample_license.key)
        )
        logs = result.scalars().all()
        
        assert len(logs) >= 3


# ============================================================
# TESTES DE FLUXO COMPLETO
# ============================================================

class TestCompleteFlow:
    """Testes de fluxo completo de uso da licença"""

    @pytest.mark.asyncio
    async def test_complete_validation_flow(
        self, client: AsyncClient, sample_license: License
    ):
        """Teste: Fluxo completo - validar → usar token → verificar"""
        # 1. Validar licença
        validate_response = await client.post(
            "/api/validate-license",
            json={
                "key": sample_license.key,
                "machine_id": "flow-test-machine"
            }
        )
        
        assert validate_response.status_code == 200
        validate_data = validate_response.json()
        assert validate_data["valid"] is True
        token = validate_data["token"]
        
        # 2. Verificar token
        check_response = await client.post(
            "/api/check-license",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert check_response.status_code == 200
        check_data = check_response.json()
        assert check_data["valid"] is True
        
        # 3. Revalidar com mesma máquina
        revalidate_response = await client.post(
            "/api/validate-license",
            json={
                "key": sample_license.key,
                "machine_id": "flow-test-machine"
            }
        )
        
        assert revalidate_response.status_code == 200
        assert revalidate_response.json()["valid"] is True

    @pytest.mark.asyncio
    async def test_flow_with_license_suspension(
        self, client: AsyncClient, sample_license: License, db_session: AsyncSession
    ):
        """Teste: Fluxo quando licença é suspensa durante uso"""
        # 1. Validar (sucesso)
        validate_response = await client.post(
            "/api/validate-license",
            json={"key": sample_license.key}
        )
        assert validate_response.status_code == 200
        token = validate_response.json()["token"]
        
        # 2. Suspender licença
        sample_license.status = LicenseStatus.SUSPENDED
        await db_session.commit()
        
        # 3. Verificar token (deve indicar problema)
        check_response = await client.post(
            "/api/check-license",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        data = check_response.json()
        assert data["valid"] is False

    @pytest.mark.asyncio
    async def test_flow_with_license_revocation(
        self, client: AsyncClient, sample_license: License, db_session: AsyncSession
    ):
        """Teste: Fluxo quando licença é revogada durante uso"""
        # 1. Validar (sucesso)
        validate_response = await client.post(
            "/api/validate-license",
            json={"key": sample_license.key}
        )
        assert validate_response.status_code == 200
        token = validate_response.json()["token"]
        
        # 2. Revogar licença
        sample_license.revoked = True
        sample_license.revoked_at = datetime.utcnow()
        sample_license.status = LicenseStatus.CANCELLED
        await db_session.commit()
        
        # 3. Tentar revalidar (deve falhar)
        revalidate_response = await client.post(
            "/api/validate-license",
            json={"key": sample_license.key}
        )
        
        assert revalidate_response.status_code == 403


# ============================================================
# TESTES DE EDGE CASES E ERROS
# ============================================================

class TestEdgeCases:
    """Testes de casos extremos e erros"""

    @pytest.mark.asyncio
    async def test_empty_key_returns_validation_error(self, client: AsyncClient):
        """Teste: Chave vazia retorna erro de validação"""
        response = await client.post(
            "/api/validate-license",
            json={"key": ""}
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_null_key_returns_validation_error(self, client: AsyncClient):
        """Teste: Chave nula retorna erro de validação"""
        response = await client.post(
            "/api/validate-license",
            json={"key": None}
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_key_returns_validation_error(self, client: AsyncClient):
        """Teste: Requisição sem chave retorna erro"""
        response = await client.post(
            "/api/validate-license",
            json={}
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_very_long_key_handled(self, client: AsyncClient):
        """Teste: Chave muito longa é tratada"""
        long_key = "A" * 1000
        
        response = await client.post(
            "/api/validate-license",
            json={"key": long_key}
        )
        
        # Deve retornar 404 (não encontrada) ou 422 (validação)
        assert response.status_code in [404, 422]

    @pytest.mark.asyncio
    async def test_special_characters_in_key(self, client: AsyncClient):
        """Teste: Caracteres especiais na chave são tratados"""
        special_key = "TEST<>\"';--INJECT"
        
        response = await client.post(
            "/api/validate-license",
            json={"key": special_key}
        )
        
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_unicode_in_machine_id(
        self, client: AsyncClient, sample_license: License
    ):
        """Teste: Unicode no machine_id é tratado"""
        response = await client.post(
            "/api/validate-license",
            json={
                "key": sample_license.key,
                "machine_id": "máquina-açúcar-ñ-日本語"
            }
        )
        
        assert response.status_code == 200


# ============================================================
# TESTES DE MÚLTIPLAS VALIDAÇÕES
# ============================================================

class TestMultipleValidations:
    """Testes de múltiplas validações sequenciais"""

    @pytest.mark.asyncio
    async def test_sequential_validations_same_license(
        self, client: AsyncClient, sample_license: License
    ):
        """Teste: Múltiplas validações sequenciais da mesma licença"""
        for i in range(5):
            response = await client.post(
                "/api/validate-license",
                json={
                    "key": sample_license.key,
                    "machine_id": "sequential-machine"
                }
            )
            assert response.status_code == 200
            assert response.json()["valid"] is True

    @pytest.mark.asyncio
    async def test_rapid_fire_validations(
        self, client: AsyncClient, sample_license: License
    ):
        """Teste: Muitas validações em sequência rápida"""
        for i in range(10):
            response = await client.post(
                "/api/validate-license",
                json={
                    "key": sample_license.key,
                    "machine_id": f"rapid-machine-{i % 3}"
                }
            )
            # Pode ser 200 ou 403 dependendo do controle de ativações
            assert response.status_code in [200, 403]


# ============================================================
# TESTES DE DADOS RETORNADOS
# ============================================================

class TestResponseData:
    """Testes dos dados retornados nas respostas"""

    @pytest.mark.asyncio
    async def test_validation_response_structure(
        self, client: AsyncClient, sample_license: License
    ):
        """Teste: Estrutura completa da resposta de validação"""
        response = await client.post(
            "/api/validate-license",
            json={"key": sample_license.key}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar campos obrigatórios
        assert "valid" in data
        assert "token" in data
        assert "data" in data
        
        # Verificar dados da licença
        license_data = data["data"]
        assert "customer_name" in license_data
        assert "license_type" in license_data
        assert "expires_at" in license_data
        assert "features" in license_data
        
        # Verificar features
        features = license_data["features"]
        assert "max_contracts" in features
        assert "export_excel" in features
        assert "export_csv" in features
        assert "support" in features
        assert "multi_user" in features

    @pytest.mark.asyncio
    async def test_check_response_structure(
        self, client: AsyncClient, sample_license: License
    ):
        """Teste: Estrutura da resposta de check"""
        # Validar primeiro
        validate_response = await client.post(
            "/api/validate-license",
            json={"key": sample_license.key}
        )
        token = validate_response.json()["token"]
        
        # Verificar
        check_response = await client.post(
            "/api/check-license",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert check_response.status_code == 200
        data = check_response.json()
        
        assert "valid" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_error_response_structure(self, client: AsyncClient):
        """Teste: Estrutura da resposta de erro"""
        response = await client.post(
            "/api/validate-license",
            json={"key": "INVALID-KEY"}
        )
        
        assert response.status_code == 404
        data = response.json()
        
        assert "detail" in data
        assert isinstance(data["detail"], str)

