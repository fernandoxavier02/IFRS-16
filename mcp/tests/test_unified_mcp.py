"""
Testes para Unified MCP Server
==============================

Testes completos do servidor MCP unificado que coordena
operações entre Stripe, Firebase e Cloud SQL.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from uuid import uuid4
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# TESTES DE INICIALIZAÇÃO
# =============================================================================

class TestUnifiedServerInit:
    """Testes de inicialização do servidor unificado"""
    
    @patch('mcp_unified_server.StripeMCPServer')
    @patch('mcp_unified_server.FirebaseMCPServer')
    @patch('mcp_unified_server.CloudSQLMCPServer')
    def test_init_all_servers(self, mock_cloudsql, mock_firebase, mock_stripe):
        """Deve inicializar todos os servidores"""
        mock_stripe.return_value = MagicMock()
        mock_firebase.return_value = MagicMock()
        mock_cloudsql.return_value = MagicMock()
        
        from mcp_unified_server import UnifiedMCPServer
        
        server = UnifiedMCPServer(
            stripe_api_key="sk_test_123",
            firebase_project_id="test-project",
            database_url="postgresql://test:test@localhost/db"
        )
        
        assert server is not None
        assert server.stripe is not None
        assert server.firebase is not None
        assert server.cloudsql is not None


# =============================================================================
# TESTES DE OPERAÇÕES COORDENADAS
# =============================================================================

@pytest.mark.unified
class TestUnifiedOperations:
    """Testes de operações coordenadas entre serviços"""
    
    @pytest.fixture
    def server(self):
        """Fixture do servidor com mocks"""
        with patch('mcp_unified_server.StripeMCPServer') as mock_stripe:
            with patch('mcp_unified_server.FirebaseMCPServer') as mock_firebase:
                with patch('mcp_unified_server.CloudSQLMCPServer') as mock_cloudsql:
                    mock_stripe_instance = MagicMock()
                    mock_firebase_instance = MagicMock()
                    mock_cloudsql_instance = MagicMock()
                    
                    mock_stripe.return_value = mock_stripe_instance
                    mock_firebase.return_value = mock_firebase_instance
                    mock_cloudsql.return_value = mock_cloudsql_instance
                    
                    from mcp_unified_server import UnifiedMCPServer
                    server = UnifiedMCPServer()
                    
                    # Substituir por mocks
                    server.stripe = mock_stripe_instance
                    server.firebase = mock_firebase_instance
                    server.cloudsql = mock_cloudsql_instance
                    
                    return server
    
    @pytest.mark.asyncio
    async def test_sync_stripe_customer_to_db_existing_user(self, server, mock_db_user):
        """Deve sincronizar cliente Stripe com usuário existente"""
        # Mock Stripe
        server.stripe.get_customer = AsyncMock(return_value={
            "id": "cus_test123",
            "email": "test@example.com",
            "name": "Test User"
        })
        
        # Mock Cloud SQL - usuário existe mas sem stripe_customer_id
        mock_db_user["stripe_customer_id"] = None
        server.cloudsql.get_user_by_email = AsyncMock(return_value=mock_db_user)
        server.cloudsql.update = AsyncMock(return_value={"success": True})
        
        result = await server.sync_stripe_customer_to_db("cus_test123")
        
        assert result["success"] is True
        assert result["action"] == "updated"
    
    @pytest.mark.asyncio
    async def test_sync_stripe_customer_already_synced(self, server, mock_db_user):
        """Deve retornar already_synced se já sincronizado"""
        server.stripe.get_customer = AsyncMock(return_value={
            "id": "cus_test123",
            "email": "test@example.com"
        })
        
        # Usuário já tem stripe_customer_id
        server.cloudsql.get_user_by_email = AsyncMock(return_value=mock_db_user)
        
        result = await server.sync_stripe_customer_to_db("cus_test123")
        
        assert result["success"] is True
        assert result["action"] == "already_synced"
    
    @pytest.mark.asyncio
    async def test_sync_stripe_customer_not_found(self, server):
        """Deve retornar erro se cliente não encontrado no Stripe"""
        server.stripe.get_customer = AsyncMock(return_value=None)
        
        result = await server.sync_stripe_customer_to_db("cus_invalid")
        
        assert result["success"] is False
        assert "não encontrado" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_user_full_profile(self, server, mock_db_user, mock_db_license, mock_db_subscription):
        """Deve retornar perfil completo do usuário"""
        # Mock Cloud SQL
        server.cloudsql.get_user_by_email = AsyncMock(return_value=mock_db_user)
        server.cloudsql.select = AsyncMock(side_effect=[
            [mock_db_license],  # licenses
            [mock_db_subscription],  # subscriptions
        ])
        
        # Mock Stripe
        server.stripe.get_customer = AsyncMock(return_value={
            "id": "cus_test123",
            "email": "test@example.com"
        })
        
        # Mock Firebase
        server.firebase.auth_get_user_by_email = AsyncMock(return_value={
            "uid": "firebase_uid_123",
            "email": "test@example.com"
        })
        
        result = await server.get_user_full_profile("test@example.com")
        
        assert result["email"] == "test@example.com"
        assert result["database"] is not None
        assert len(result["licenses"]) == 1
        assert len(result["subscriptions"]) == 1
        assert result["stripe"] is not None
        assert result["firebase_auth"] is not None
    
    @pytest.mark.asyncio
    async def test_get_user_full_profile_not_found(self, server):
        """Deve retornar perfil vazio se usuário não encontrado"""
        server.cloudsql.get_user_by_email = AsyncMock(return_value=None)
        server.firebase.auth_get_user_by_email = AsyncMock(side_effect=Exception("Not found"))
        
        result = await server.get_user_full_profile("nonexistent@example.com")
        
        assert result["email"] == "nonexistent@example.com"
        assert result["database"] is None
        assert result["licenses"] == []


# =============================================================================
# TESTES DE REVOGAÇÃO DE ACESSO
# =============================================================================

@pytest.mark.unified
class TestUnifiedRevokeAccess:
    """Testes de revogação de acesso"""
    
    @pytest.fixture
    def server(self):
        with patch('mcp_unified_server.StripeMCPServer') as mock_stripe:
            with patch('mcp_unified_server.FirebaseMCPServer') as mock_firebase:
                with patch('mcp_unified_server.CloudSQLMCPServer') as mock_cloudsql:
                    from mcp_unified_server import UnifiedMCPServer
                    server = UnifiedMCPServer()
                    
                    server.stripe = MagicMock()
                    server.firebase = MagicMock()
                    server.cloudsql = MagicMock()
                    
                    return server
    
    @pytest.mark.asyncio
    async def test_revoke_user_access_full(self, server, mock_db_user):
        """Deve revogar acesso em todos os sistemas"""
        # Mock Cloud SQL
        server.cloudsql.get_user_by_email = AsyncMock(return_value=mock_db_user)
        server.cloudsql.execute_query = AsyncMock(return_value={"success": True})
        
        # Mock Stripe
        server.stripe.list_subscriptions = AsyncMock(return_value=[
            {"id": "sub_test123"}
        ])
        server.stripe.cancel_subscription = AsyncMock(return_value={"id": "sub_test123"})
        
        # Mock Firebase
        server.firebase.auth_get_user_by_email = AsyncMock(return_value={
            "uid": "firebase_uid_123"
        })
        server.firebase.auth_update_user = AsyncMock(return_value={"updated": True})
        
        result = await server.revoke_user_access("test@example.com", reason="Teste")
        
        assert result["database"]["success"] is True
        assert result["stripe"]["success"] is True
        assert result["stripe"]["cancelled"] == 1
        assert result["firebase"]["success"] is True
    
    @pytest.mark.asyncio
    async def test_revoke_user_access_partial_failure(self, server, mock_db_user):
        """Deve continuar mesmo com falhas parciais"""
        # Mock Cloud SQL - sucesso
        server.cloudsql.get_user_by_email = AsyncMock(return_value=mock_db_user)
        server.cloudsql.execute_query = AsyncMock(return_value={"success": True})
        
        # Mock Stripe - falha
        server.stripe.list_subscriptions = AsyncMock(side_effect=Exception("Stripe error"))
        
        # Mock Firebase - sucesso
        server.firebase.auth_get_user_by_email = AsyncMock(return_value={
            "uid": "firebase_uid_123"
        })
        server.firebase.auth_update_user = AsyncMock(return_value={"updated": True})
        
        result = await server.revoke_user_access("test@example.com")
        
        assert result["database"]["success"] is True
        assert result["stripe"]["success"] is False
        assert result["firebase"]["success"] is True


# =============================================================================
# TESTES DE CRIAÇÃO DE LICENÇA MANUAL
# =============================================================================

@pytest.mark.unified
class TestUnifiedCreateLicense:
    """Testes de criação de licença manual"""
    
    @pytest.fixture
    def server(self):
        with patch('mcp_unified_server.StripeMCPServer') as mock_stripe:
            with patch('mcp_unified_server.FirebaseMCPServer') as mock_firebase:
                with patch('mcp_unified_server.CloudSQLMCPServer') as mock_cloudsql:
                    from mcp_unified_server import UnifiedMCPServer
                    server = UnifiedMCPServer()
                    
                    server.stripe = MagicMock()
                    server.firebase = MagicMock()
                    server.cloudsql = MagicMock()
                    
                    return server
    
    @pytest.mark.asyncio
    async def test_create_manual_license_new_user(self, server):
        """Deve criar licença para novo usuário"""
        # Mock - usuário não existe
        server.cloudsql.get_user_by_email = AsyncMock(return_value=None)
        
        # Mock - criar usuário
        new_user_id = str(uuid4())
        server.cloudsql.insert = AsyncMock(side_effect=[
            {"success": True, "inserted": {"id": new_user_id}},  # users
            {"success": True},  # licenses
        ])
        
        result = await server.create_manual_license(
            email="new@example.com",
            name="New User",
            license_type="basic",
            duration_months=12
        )
        
        assert result["success"] is True
        assert result["license_key"].startswith("FX")
        assert result["created_user"] is True
        assert result["temp_password"] is not None
    
    @pytest.mark.asyncio
    async def test_create_manual_license_existing_user(self, server, mock_db_user):
        """Deve criar licença para usuário existente"""
        # Mock - usuário existe
        server.cloudsql.get_user_by_email = AsyncMock(return_value=mock_db_user)
        
        # Mock - criar licença
        server.cloudsql.insert = AsyncMock(return_value={"success": True})
        
        result = await server.create_manual_license(
            email="test@example.com",
            name="Test User",
            license_type="pro",
            duration_months=6
        )
        
        assert result["success"] is True
        assert result["license_key"].startswith("FX")
        assert result["created_user"] is False
        assert result["temp_password"] is None
    
    @pytest.mark.asyncio
    async def test_create_manual_license_types(self, server, mock_db_user):
        """Deve criar licenças de diferentes tipos"""
        server.cloudsql.get_user_by_email = AsyncMock(return_value=mock_db_user)
        server.cloudsql.insert = AsyncMock(return_value={"success": True})
        
        for license_type in ["trial", "basic", "pro", "enterprise"]:
            result = await server.create_manual_license(
                email="test@example.com",
                name="Test User",
                license_type=license_type
            )
            
            assert result["success"] is True
            assert result["license_type"] == license_type


# =============================================================================
# TESTES DE ESTATÍSTICAS
# =============================================================================

@pytest.mark.unified
class TestUnifiedStats:
    """Testes de estatísticas do sistema"""
    
    @pytest.fixture
    def server(self):
        with patch('mcp_unified_server.StripeMCPServer') as mock_stripe:
            with patch('mcp_unified_server.FirebaseMCPServer') as mock_firebase:
                with patch('mcp_unified_server.CloudSQLMCPServer') as mock_cloudsql:
                    from mcp_unified_server import UnifiedMCPServer
                    server = UnifiedMCPServer()
                    
                    server.stripe = MagicMock()
                    server.firebase = MagicMock()
                    server.cloudsql = MagicMock()
                    
                    return server
    
    @pytest.mark.asyncio
    async def test_get_system_stats(self, server):
        """Deve retornar estatísticas do sistema"""
        # Mock Cloud SQL
        server.cloudsql.execute_query = AsyncMock(side_effect=[
            {"success": True, "rows": [{"total": 100}]},  # users count
            {"success": True, "rows": [
                {"status": "active", "count": 80},
                {"status": "expired", "count": 20},
            ]},  # licenses by status
            {"success": True, "rows": [
                {"status": "active", "count": 75},
                {"status": "cancelled", "count": 25},
            ]},  # subscriptions by status
        ])
        server.cloudsql.get_database_size = AsyncMock(return_value={"size": "50 MB"})
        
        # Mock Stripe
        server.stripe.get_balance = AsyncMock(return_value={
            "available": [{"amount": 1000, "currency": "brl"}]
        })
        server.stripe.list_balance_transactions = AsyncMock(return_value=[
            {"id": "txn_1"}, {"id": "txn_2"}
        ])
        
        # Mock Firebase
        server.firebase.get_project_info = AsyncMock(return_value={
            "project_id": "ifrs16-app"
        })
        
        result = await server.get_system_stats()
        
        assert "timestamp" in result
        assert result["database"]["total_users"] == 100
        assert result["database"]["licenses_by_status"]["active"] == 80
        assert result["stripe"]["recent_transactions"] == 2
        assert result["firebase"]["project"]["project_id"] == "ifrs16-app"
    
    @pytest.mark.asyncio
    async def test_get_system_stats_with_errors(self, server):
        """Deve lidar com erros em serviços individuais"""
        # Mock Cloud SQL - erro
        server.cloudsql.execute_query = AsyncMock(side_effect=Exception("DB error"))
        
        # Mock Stripe - sucesso
        server.stripe.get_balance = AsyncMock(return_value={"available": []})
        server.stripe.list_balance_transactions = AsyncMock(return_value=[])
        
        # Mock Firebase - erro
        server.firebase.get_project_info = AsyncMock(side_effect=Exception("Firebase error"))
        
        result = await server.get_system_stats()
        
        assert "error" in result["database"]
        assert "error" in result["firebase"]


# =============================================================================
# TESTES DE HEALTH CHECK
# =============================================================================

@pytest.mark.unified
class TestUnifiedHealthCheck:
    """Testes de health check"""
    
    @pytest.fixture
    def server(self):
        with patch('mcp_unified_server.StripeMCPServer') as mock_stripe:
            with patch('mcp_unified_server.FirebaseMCPServer') as mock_firebase:
                with patch('mcp_unified_server.CloudSQLMCPServer') as mock_cloudsql:
                    from mcp_unified_server import UnifiedMCPServer
                    server = UnifiedMCPServer()
                    
                    server.stripe = MagicMock()
                    server.firebase = MagicMock()
                    server.cloudsql = MagicMock()
                    
                    return server
    
    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self, server):
        """Deve retornar healthy quando todos os serviços OK"""
        server.cloudsql.health_check = AsyncMock(return_value={
            "status": "healthy",
            "connection": "ok"
        })
        server.stripe.get_balance = AsyncMock(return_value={
            "available": [{"amount": 100}]
        })
        server.firebase.get_project_info = AsyncMock(return_value={
            "project_id": "ifrs16-app"
        })
        
        result = await server.health_check_all()
        
        assert result["overall_status"] == "healthy"
        assert result["services"]["cloudsql"]["status"] == "healthy"
        assert result["services"]["stripe"]["status"] == "healthy"
        assert result["services"]["firebase"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_check_degraded(self, server):
        """Deve retornar degraded quando algum serviço falha"""
        server.cloudsql.health_check = AsyncMock(return_value={
            "status": "healthy"
        })
        server.stripe.get_balance = AsyncMock(side_effect=Exception("Stripe down"))
        server.firebase.get_project_info = AsyncMock(return_value={
            "project_id": "ifrs16-app"
        })
        
        result = await server.health_check_all()
        
        assert result["overall_status"] == "degraded"
        assert result["services"]["stripe"]["status"] == "unhealthy"
    
    @pytest.mark.asyncio
    async def test_health_check_all_unhealthy(self, server):
        """Deve retornar degraded quando todos os serviços falham"""
        server.cloudsql.health_check = AsyncMock(side_effect=Exception("DB down"))
        server.stripe.get_balance = AsyncMock(side_effect=Exception("Stripe down"))
        server.firebase.get_project_info = AsyncMock(side_effect=Exception("Firebase down"))
        
        result = await server.health_check_all()
        
        assert result["overall_status"] == "degraded"
        assert all(
            s["status"] == "unhealthy" 
            for s in result["services"].values()
        )


# =============================================================================
# TESTES DE CLOSE
# =============================================================================

@pytest.mark.unified
class TestUnifiedClose:
    """Testes de fechamento de conexões"""
    
    @pytest.fixture
    def server(self):
        with patch('mcp_unified_server.StripeMCPServer') as mock_stripe:
            with patch('mcp_unified_server.FirebaseMCPServer') as mock_firebase:
                with patch('mcp_unified_server.CloudSQLMCPServer') as mock_cloudsql:
                    from mcp_unified_server import UnifiedMCPServer
                    server = UnifiedMCPServer()
                    
                    server.stripe = MagicMock()
                    server.firebase = MagicMock()
                    server.cloudsql = MagicMock()
                    
                    return server
    
    @pytest.mark.asyncio
    async def test_close(self, server):
        """Deve fechar conexões do Cloud SQL"""
        server.cloudsql.close = AsyncMock()
        
        await server.close()
        
        server.cloudsql.close.assert_called_once()
