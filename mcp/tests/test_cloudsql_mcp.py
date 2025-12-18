"""
Testes para Cloud SQL MCP Server
================================

Testes completos de todas as funcionalidades do servidor MCP Cloud SQL.
Usa mocks para não depender de conexão real com banco.
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

class TestCloudSQLServerInit:
    """Testes de inicialização do servidor Cloud SQL"""
    
    def test_init_with_connection_string(self):
        """Deve inicializar com connection string"""
        from cloudsql_mcp_server import CloudSQLMCPServer
        
        server = CloudSQLMCPServer(
            connection_string="postgresql://user:pass@localhost:5432/db"
        )
        
        assert server is not None
        assert "postgresql://" in server.connection_string
    
    def test_init_with_individual_params(self):
        """Deve inicializar com parâmetros individuais"""
        from cloudsql_mcp_server import CloudSQLMCPServer
        
        server = CloudSQLMCPServer(
            host="localhost",
            port=5432,
            user="postgres",
            password="password",
            database="ifrs16_licenses"
        )
        
        assert server is not None
        assert "localhost" in server.connection_string
    
    @patch.dict(os.environ, {"DATABASE_URL": "postgresql://env:pass@envhost:5432/envdb"})
    def test_init_with_env_var(self):
        """Deve inicializar com variável de ambiente"""
        from cloudsql_mcp_server import CloudSQLMCPServer
        
        server = CloudSQLMCPServer()
        
        assert "envhost" in server.connection_string


# =============================================================================
# TESTES DE QUERIES
# =============================================================================

@pytest.mark.cloudsql
class TestCloudSQLQueries:
    """Testes de execução de queries"""
    
    @pytest.fixture
    def server(self):
        from cloudsql_mcp_server import CloudSQLMCPServer
        return CloudSQLMCPServer(
            connection_string="postgresql://test:test@localhost:5432/test"
        )
    
    @pytest.mark.asyncio
    async def test_execute_query_fetch(self, server, mock_asyncpg_pool):
        """Deve executar query com fetch"""
        pool, conn = mock_asyncpg_pool
        
        mock_row = {"id": 1, "name": "Test"}
        conn.fetch = AsyncMock(return_value=[mock_row])
        
        async def mock_get_pool():
            return pool
        
        with patch.object(server, '_get_pool', mock_get_pool):
            result = await server.execute_query("SELECT * FROM users")
        
        assert result["success"] is True
        assert result["row_count"] == 1
        assert result["rows"][0]["name"] == "Test"
    
    @pytest.mark.asyncio
    async def test_execute_query_with_params(self, server, mock_asyncpg_pool):
        """Deve executar query com parâmetros"""
        pool, conn = mock_asyncpg_pool
        
        mock_row = {"id": 1, "email": "test@example.com"}
        conn.fetch = AsyncMock(return_value=[mock_row])
        
        async def mock_get_pool():
            return pool
        
        with patch.object(server, '_get_pool', mock_get_pool):
            result = await server.execute_query(
                "SELECT * FROM users WHERE email = $1",
                ["test@example.com"]
            )
        
        assert result["success"] is True
        conn.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_query_no_fetch(self, server, mock_asyncpg_pool):
        """Deve executar query sem fetch (INSERT/UPDATE/DELETE)"""
        pool, conn = mock_asyncpg_pool
        
        conn.execute = AsyncMock(return_value="INSERT 0 1")
        
        async def mock_get_pool():
            return pool
        
        with patch.object(server, '_get_pool', mock_get_pool):
            result = await server.execute_query(
                "INSERT INTO users (name) VALUES ($1)",
                ["Test"],
                fetch=False
            )
        
        assert result["success"] is True
        assert result["status"] == "INSERT 0 1"
    
    @pytest.mark.asyncio
    async def test_execute_query_error(self, server, mock_asyncpg_pool):
        """Deve tratar erros de query"""
        pool, conn = mock_asyncpg_pool
        
        conn.fetch = AsyncMock(side_effect=Exception("Database error"))
        
        async def mock_get_pool():
            return pool
        
        with patch.object(server, '_get_pool', mock_get_pool):
            result = await server.execute_query("SELECT * FROM invalid_table")
        
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_execute_many(self, server, mock_asyncpg_pool):
        """Deve executar múltiplas queries"""
        pool, conn = mock_asyncpg_pool
        
        conn.executemany = AsyncMock(return_value=None)
        
        async def mock_get_pool():
            return pool
        
        with patch.object(server, '_get_pool', mock_get_pool):
            result = await server.execute_many(
                "INSERT INTO users (name) VALUES ($1)",
                [["User1"], ["User2"], ["User3"]]
            )
        
        assert result["success"] is True
        assert result["executed_count"] == 3


# =============================================================================
# TESTES DE SCHEMA
# =============================================================================

@pytest.mark.cloudsql
class TestCloudSQLSchema:
    """Testes de operações de schema"""
    
    @pytest.fixture
    def server(self):
        from cloudsql_mcp_server import CloudSQLMCPServer
        return CloudSQLMCPServer(
            connection_string="postgresql://test:test@localhost:5432/test"
        )
    
    @pytest.mark.asyncio
    async def test_list_tables(self, server, mock_db_tables):
        """Deve listar tabelas"""
        with patch.object(server, 'execute_query') as mock_query:
            mock_query.return_value = {"success": True, "rows": mock_db_tables}
            
            result = await server.list_tables()
        
        assert len(result) == 5
        assert any(t["table_name"] == "users" for t in result)
        assert any(t["table_name"] == "licenses" for t in result)
    
    @pytest.mark.asyncio
    async def test_describe_table(self, server):
        """Deve descrever estrutura da tabela"""
        mock_columns = [
            {"column_name": "id", "data_type": "uuid", "is_nullable": "NO"},
            {"column_name": "email", "data_type": "varchar", "is_nullable": "NO"},
            {"column_name": "name", "data_type": "varchar", "is_nullable": "YES"},
        ]
        mock_indexes = [
            {"indexname": "users_pkey", "indexdef": "CREATE UNIQUE INDEX..."},
        ]
        mock_constraints = [
            {"constraint_name": "users_pkey", "constraint_type": "PRIMARY KEY"},
        ]
        mock_count = [{"count": 100}]
        
        with patch.object(server, 'execute_query') as mock_query:
            mock_query.side_effect = [
                {"success": True, "rows": mock_columns},
                {"success": True, "rows": mock_indexes},
                {"success": True, "rows": mock_constraints},
                {"success": True, "rows": mock_count},
            ]
            
            result = await server.describe_table("users")
        
        assert result["table_name"] == "users"
        assert len(result["columns"]) == 3
        assert len(result["indexes"]) == 1
        assert result["row_count"] == 100
    
    @pytest.mark.asyncio
    async def test_get_table_stats(self, server):
        """Deve retornar estatísticas da tabela"""
        mock_stats = [{
            "table_name": "users",
            "live_rows": 100,
            "dead_rows": 5,
            "last_vacuum": datetime.now(),
            "last_autovacuum": None,
            "last_analyze": datetime.now(),
            "last_autoanalyze": None,
        }]
        
        with patch.object(server, 'execute_query') as mock_query:
            mock_query.return_value = {"success": True, "rows": mock_stats}
            
            result = await server.get_table_stats("users")
        
        assert result["table_name"] == "users"
        assert result["live_rows"] == 100


# =============================================================================
# TESTES DE CRUD
# =============================================================================

@pytest.mark.cloudsql
class TestCloudSQLCRUD:
    """Testes de operações CRUD"""
    
    @pytest.fixture
    def server(self):
        from cloudsql_mcp_server import CloudSQLMCPServer
        return CloudSQLMCPServer(
            connection_string="postgresql://test:test@localhost:5432/test"
        )
    
    @pytest.mark.asyncio
    async def test_select_all(self, server, mock_db_user):
        """Deve fazer SELECT de todos os registros"""
        with patch.object(server, 'execute_query') as mock_query:
            mock_query.return_value = {"success": True, "rows": [mock_db_user]}
            
            result = await server.select("users")
        
        assert len(result) == 1
        assert result[0]["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_select_with_columns(self, server):
        """Deve fazer SELECT com colunas específicas"""
        mock_result = [{"id": "123", "email": "test@example.com"}]
        
        with patch.object(server, 'execute_query') as mock_query:
            mock_query.return_value = {"success": True, "rows": mock_result}
            
            result = await server.select("users", columns=["id", "email"])
        
        # Verificar que a query foi construída corretamente
        call_args = mock_query.call_args[0][0]
        assert "id" in call_args
        assert "email" in call_args
    
    @pytest.mark.asyncio
    async def test_select_with_where(self, server, mock_db_user):
        """Deve fazer SELECT com WHERE"""
        with patch.object(server, 'execute_query') as mock_query:
            mock_query.return_value = {"success": True, "rows": [mock_db_user]}
            
            result = await server.select(
                "users",
                where={"email": "test@example.com"}
            )
        
        assert len(result) == 1
        # Verificar que WHERE foi incluído
        call_args = mock_query.call_args[0][0]
        assert "WHERE" in call_args
    
    @pytest.mark.asyncio
    async def test_select_with_order_and_limit(self, server, mock_db_user):
        """Deve fazer SELECT com ORDER BY e LIMIT"""
        with patch.object(server, 'execute_query') as mock_query:
            mock_query.return_value = {"success": True, "rows": [mock_db_user]}
            
            result = await server.select(
                "users",
                order_by="created_at",
                limit=10,
                offset=5
            )
        
        call_args = mock_query.call_args[0][0]
        assert "ORDER BY" in call_args
        assert "LIMIT 10" in call_args
        assert "OFFSET 5" in call_args
    
    @pytest.mark.asyncio
    async def test_insert(self, server):
        """Deve fazer INSERT"""
        with patch.object(server, 'execute_query') as mock_query:
            mock_query.return_value = {"success": True, "status": "INSERT 0 1"}
            
            result = await server.insert(
                "users",
                {"email": "new@example.com", "name": "New User"}
            )
        
        assert result["success"] is True
        call_args = mock_query.call_args[0][0]
        assert "INSERT INTO" in call_args
    
    @pytest.mark.asyncio
    async def test_insert_with_returning(self, server):
        """Deve fazer INSERT com RETURNING"""
        mock_inserted = {"id": str(uuid4()), "email": "new@example.com"}
        
        with patch.object(server, 'execute_query') as mock_query:
            mock_query.return_value = {"success": True, "rows": [mock_inserted]}
            
            result = await server.insert(
                "users",
                {"email": "new@example.com", "name": "New User"},
                returning=["id", "email"]
            )
        
        assert result["success"] is True
        assert "inserted" in result
        call_args = mock_query.call_args[0][0]
        assert "RETURNING" in call_args
    
    @pytest.mark.asyncio
    async def test_update(self, server):
        """Deve fazer UPDATE"""
        with patch.object(server, 'execute_query') as mock_query:
            mock_query.return_value = {"success": True, "status": "UPDATE 1"}
            
            result = await server.update(
                "users",
                {"name": "Updated Name"},
                {"email": "test@example.com"}
            )
        
        assert result["success"] is True
        call_args = mock_query.call_args[0][0]
        assert "UPDATE" in call_args
        assert "SET" in call_args
        assert "WHERE" in call_args
    
    @pytest.mark.asyncio
    async def test_delete(self, server):
        """Deve fazer DELETE"""
        with patch.object(server, 'execute_query') as mock_query:
            mock_query.return_value = {"success": True, "status": "DELETE 1"}
            
            result = await server.delete(
                "users",
                {"email": "test@example.com"}
            )
        
        assert result["success"] is True
        call_args = mock_query.call_args[0][0]
        assert "DELETE FROM" in call_args
        assert "WHERE" in call_args


# =============================================================================
# TESTES ESPECÍFICOS IFRS 16
# =============================================================================

@pytest.mark.cloudsql
class TestCloudSQLIFRS16:
    """Testes de funções específicas do IFRS 16"""
    
    @pytest.fixture
    def server(self):
        from cloudsql_mcp_server import CloudSQLMCPServer
        return CloudSQLMCPServer(
            connection_string="postgresql://test:test@localhost:5432/test"
        )
    
    @pytest.mark.asyncio
    async def test_get_licenses(self, server, mock_db_license):
        """Deve listar licenças"""
        with patch.object(server, 'select') as mock_select:
            mock_select.return_value = [mock_db_license]
            
            result = await server.get_licenses()
        
        assert len(result) == 1
        assert result[0]["key"].startswith("FX")
    
    @pytest.mark.asyncio
    async def test_get_licenses_by_status(self, server, mock_db_license):
        """Deve filtrar licenças por status"""
        with patch.object(server, 'select') as mock_select:
            mock_select.return_value = [mock_db_license]
            
            result = await server.get_licenses(status="active")
        
        mock_select.assert_called_once()
        call_kwargs = mock_select.call_args[1]
        assert call_kwargs["where"]["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_get_license_by_key(self, server, mock_db_license):
        """Deve buscar licença por chave"""
        with patch.object(server, 'select') as mock_select:
            mock_select.return_value = [mock_db_license]
            
            result = await server.get_license_by_key("FX20251217-IFRS16-ABCD1234")
        
        assert result is not None
        assert result["key"] == "FX20251217-IFRS16-ABCD1234"
    
    @pytest.mark.asyncio
    async def test_get_license_by_key_not_found(self, server):
        """Deve retornar None se licença não existir"""
        with patch.object(server, 'select') as mock_select:
            mock_select.return_value = []
            
            result = await server.get_license_by_key("INVALID-KEY")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_users(self, server, mock_db_user):
        """Deve listar usuários"""
        with patch.object(server, 'select') as mock_select:
            mock_select.return_value = [mock_db_user]
            
            result = await server.get_users()
        
        assert len(result) == 1
        assert result[0]["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_user_by_email(self, server, mock_db_user):
        """Deve buscar usuário por email"""
        with patch.object(server, 'select') as mock_select:
            mock_select.return_value = [mock_db_user]
            
            result = await server.get_user_by_email("test@example.com")
        
        assert result is not None
        assert result["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_get_subscriptions(self, server, mock_db_subscription):
        """Deve listar assinaturas"""
        with patch.object(server, 'select') as mock_select:
            mock_select.return_value = [mock_db_subscription]
            
            result = await server.get_subscriptions()
        
        assert len(result) == 1
        assert result[0]["status"] == "active"
    
    @pytest.mark.asyncio
    async def test_get_subscriptions_by_user(self, server, mock_db_subscription):
        """Deve filtrar assinaturas por usuário"""
        user_id = str(uuid4())
        
        with patch.object(server, 'select') as mock_select:
            mock_select.return_value = [mock_db_subscription]
            
            result = await server.get_subscriptions(user_id=user_id)
        
        call_kwargs = mock_select.call_args[1]
        assert call_kwargs["where"]["user_id"] == user_id
    
    @pytest.mark.asyncio
    async def test_get_admin_users(self, server):
        """Deve listar administradores"""
        mock_admin = {
            "id": str(uuid4()),
            "username": "admin",
            "email": "admin@example.com",
            "role": "superadmin",
            "is_active": True,
        }
        
        with patch.object(server, 'select') as mock_select:
            mock_select.return_value = [mock_admin]
            
            result = await server.get_admin_users()
        
        assert len(result) == 1
        assert result[0]["role"] == "superadmin"
    
    @pytest.mark.asyncio
    async def test_get_validation_logs(self, server):
        """Deve listar logs de validação"""
        mock_log = {
            "id": str(uuid4()),
            "license_key": "FX20251217-IFRS16-ABCD1234",
            "timestamp": datetime.now(),
            "success": True,
            "ip_address": "192.168.1.1",
        }
        
        with patch.object(server, 'select') as mock_select:
            mock_select.return_value = [mock_log]
            
            result = await server.get_validation_logs(
                license_key="FX20251217-IFRS16-ABCD1234"
            )
        
        assert len(result) == 1
        assert result[0]["success"] is True


# =============================================================================
# TESTES DE MONITORAMENTO
# =============================================================================

@pytest.mark.cloudsql
class TestCloudSQLMonitoring:
    """Testes de funções de monitoramento"""
    
    @pytest.fixture
    def server(self):
        from cloudsql_mcp_server import CloudSQLMCPServer
        return CloudSQLMCPServer(
            connection_string="postgresql://test:test@localhost:5432/test"
        )
    
    @pytest.mark.asyncio
    async def test_get_database_size(self, server):
        """Deve retornar tamanho do banco"""
        mock_size = [{
            "database": "ifrs16_licenses",
            "size": "50 MB",
            "size_bytes": 52428800,
        }]
        
        with patch.object(server, 'execute_query') as mock_query:
            mock_query.return_value = {"success": True, "rows": mock_size}
            
            result = await server.get_database_size()
        
        assert result["database"] == "ifrs16_licenses"
        assert result["size"] == "50 MB"
    
    @pytest.mark.asyncio
    async def test_get_active_connections(self, server):
        """Deve listar conexões ativas"""
        mock_connections = [{
            "pid": 12345,
            "username": "postgres",
            "application_name": "ifrs16-backend",
            "client_addr": "192.168.1.100",
            "state": "active",
            "query_start": datetime.now(),
            "state_change": datetime.now(),
        }]
        
        with patch.object(server, 'execute_query') as mock_query:
            mock_query.return_value = {"success": True, "rows": mock_connections}
            
            result = await server.get_active_connections()
        
        assert len(result) == 1
        assert result[0]["pid"] == 12345
        assert result[0]["state"] == "active"
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, server):
        """Deve retornar healthy quando conexão OK"""
        mock_result = [{"ok": 1, "timestamp": datetime.now()}]
        
        with patch.object(server, 'execute_query') as mock_query:
            mock_query.return_value = {"success": True, "rows": mock_result}
            
            result = await server.health_check()
        
        assert result["status"] == "healthy"
        assert result["connection"] == "ok"
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, server):
        """Deve retornar unhealthy quando conexão falha"""
        with patch.object(server, 'execute_query') as mock_query:
            mock_query.side_effect = Exception("Connection refused")
            
            result = await server.health_check()
        
        assert result["status"] == "unhealthy"
        assert "error" in result


# =============================================================================
# TESTES DE CONEXÃO
# =============================================================================

@pytest.mark.cloudsql
class TestCloudSQLConnection:
    """Testes de gerenciamento de conexão"""
    
    @pytest.fixture
    def server(self):
        from cloudsql_mcp_server import CloudSQLMCPServer
        return CloudSQLMCPServer(
            connection_string="postgresql://test:test@localhost:5432/test"
        )
    
    @pytest.mark.asyncio
    async def test_close_connection(self, server):
        """Deve fechar conexões corretamente"""
        mock_pool = AsyncMock()
        server._pool = mock_pool
        
        await server.close()
        
        mock_pool.close.assert_called_once()
        assert server._pool is None
    
    @pytest.mark.asyncio
    async def test_close_when_no_pool(self, server):
        """Deve lidar com close quando não há pool"""
        server._pool = None
        
        # Não deve lançar exceção
        await server.close()
        
        assert server._pool is None


# =============================================================================
# TESTES DE MCP TOOLS
# =============================================================================

@pytest.mark.cloudsql
class TestCloudSQLMCPTools:
    """Testes da definição de tools MCP"""
    
    def test_mcp_tools_defined(self):
        """Deve ter todas as tools definidas"""
        from cloudsql_mcp_server import MCP_TOOLS
        
        expected_tools = [
            "cloudsql_execute_query",
            "cloudsql_list_tables",
            "cloudsql_describe_table",
            "cloudsql_select",
            "cloudsql_insert",
            "cloudsql_update",
            "cloudsql_delete",
            "cloudsql_get_licenses",
            "cloudsql_get_users",
            "cloudsql_get_subscriptions",
            "cloudsql_health_check",
            "cloudsql_get_database_size",
            "cloudsql_get_active_connections",
        ]
        
        for tool in expected_tools:
            assert tool in MCP_TOOLS, f"Tool {tool} não encontrada"
    
    def test_mcp_tools_have_description(self):
        """Todas as tools devem ter descrição"""
        from cloudsql_mcp_server import MCP_TOOLS
        
        for name, tool in MCP_TOOLS.items():
            assert "description" in tool, f"Tool {name} sem descrição"
            assert len(tool["description"]) > 0
    
    def test_mcp_tools_have_parameters(self):
        """Todas as tools devem ter parâmetros definidos"""
        from cloudsql_mcp_server import MCP_TOOLS
        
        for name, tool in MCP_TOOLS.items():
            assert "parameters" in tool, f"Tool {name} sem parâmetros"
