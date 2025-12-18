"""
Testes para Firebase MCP Server
===============================

Testes completos de todas as funcionalidades do servidor MCP Firebase.
Usa mocks para não depender de credenciais reais.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# TESTES DE INICIALIZAÇÃO
# =============================================================================

class TestFirebaseServerInit:
    """Testes de inicialização do servidor Firebase"""
    
    @patch('firebase_admin._apps', {})
    @patch('firebase_admin.initialize_app')
    @patch('firebase_admin.credentials.ApplicationDefault')
    @patch('firebase_admin.firestore.client')
    @patch('firebase_admin.storage.bucket')
    def test_init_with_default_credentials(
        self, mock_bucket, mock_firestore, mock_cred, mock_init
    ):
        """Deve inicializar com credenciais padrão"""
        mock_firestore.return_value = MagicMock()
        mock_bucket.return_value = MagicMock()
        
        from firebase_mcp_server import FirebaseMCPServer
        server = FirebaseMCPServer(project_id="test-project")
        
        assert server is not None
        assert server.project_id == "test-project"
    
    @patch('firebase_admin._apps', {'[DEFAULT]': MagicMock()})
    @patch('firebase_admin.firestore.client')
    @patch('firebase_admin.storage.bucket')
    def test_init_with_existing_app(self, mock_bucket, mock_firestore):
        """Deve usar app existente se já inicializado"""
        mock_firestore.return_value = MagicMock()
        mock_bucket.return_value = MagicMock()
        
        from firebase_mcp_server import FirebaseMCPServer
        server = FirebaseMCPServer(project_id="test-project")
        
        assert server is not None


# =============================================================================
# TESTES DE FIRESTORE
# =============================================================================

@pytest.mark.firebase
class TestFirestoreOperations:
    """Testes de operações Firestore"""
    
    @pytest.fixture
    def server(self):
        """Fixture do servidor com mocks"""
        with patch('firebase_admin._apps', {'[DEFAULT]': MagicMock()}):
            with patch('firebase_admin.firestore.client') as mock_firestore:
                with patch('firebase_admin.storage.bucket') as mock_bucket:
                    mock_db = MagicMock()
                    mock_firestore.return_value = mock_db
                    mock_bucket.return_value = MagicMock()
                    
                    from firebase_mcp_server import FirebaseMCPServer
                    server = FirebaseMCPServer(project_id="test-project")
                    server.db = mock_db
                    return server
    
    @pytest.mark.asyncio
    async def test_list_collections(self, server):
        """Deve listar coleções"""
        mock_col1 = MagicMock()
        mock_col1.id = "users"
        mock_col2 = MagicMock()
        mock_col2.id = "licenses"
        
        server.db.collections.return_value = [mock_col1, mock_col2]
        
        result = await server.firestore_list_collections()
        
        assert len(result) == 2
        assert "users" in result
        assert "licenses" in result
    
    @pytest.mark.asyncio
    async def test_get_documents(self, server, mock_firestore_document):
        """Deve listar documentos de uma coleção"""
        mock_query = MagicMock()
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = [mock_firestore_document]
        
        server.db.collection.return_value = mock_query
        
        result = await server.firestore_get_documents("users", limit=10)
        
        assert len(result) == 1
        assert result[0]["id"] == "doc_123"
        assert "data" in result[0]
    
    @pytest.mark.asyncio
    async def test_get_documents_with_where(self, server, mock_firestore_document):
        """Deve filtrar documentos com where"""
        mock_query = MagicMock()
        mock_query.where.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.stream.return_value = [mock_firestore_document]
        
        server.db.collection.return_value = mock_query
        
        result = await server.firestore_get_documents(
            "users",
            where_field="email",
            where_op="==",
            where_value="test@example.com"
        )
        
        mock_query.where.assert_called_once()
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_document(self, server, mock_firestore_document):
        """Deve buscar documento específico"""
        mock_doc_ref = MagicMock()
        mock_doc_ref.get.return_value = mock_firestore_document
        
        server.db.collection.return_value.document.return_value = mock_doc_ref
        
        result = await server.firestore_get_document("users", "doc_123")
        
        assert result is not None
        assert result["id"] == "doc_123"
    
    @pytest.mark.asyncio
    async def test_get_document_not_found(self, server):
        """Deve retornar None se documento não existir"""
        mock_doc = MagicMock()
        mock_doc.exists = False
        
        mock_doc_ref = MagicMock()
        mock_doc_ref.get.return_value = mock_doc
        
        server.db.collection.return_value.document.return_value = mock_doc_ref
        
        result = await server.firestore_get_document("users", "nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_document_with_id(self, server):
        """Deve criar documento com ID específico"""
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "new_doc_123"
        mock_doc_ref.path = "users/new_doc_123"
        
        server.db.collection.return_value.document.return_value = mock_doc_ref
        
        result = await server.firestore_create_document(
            "users",
            {"name": "Test", "email": "test@example.com"},
            document_id="new_doc_123"
        )
        
        assert result["id"] == "new_doc_123"
        assert result["created"] is True
        mock_doc_ref.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_document_auto_id(self, server):
        """Deve criar documento com ID automático"""
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "auto_generated_id"
        mock_doc_ref.path = "users/auto_generated_id"
        
        server.db.collection.return_value.add.return_value = (None, mock_doc_ref)
        
        result = await server.firestore_create_document(
            "users",
            {"name": "Test", "email": "test@example.com"}
        )
        
        assert result["id"] == "auto_generated_id"
        assert result["created"] is True
    
    @pytest.mark.asyncio
    async def test_update_document(self, server):
        """Deve atualizar documento existente"""
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "doc_123"
        mock_doc_ref.path = "users/doc_123"
        
        server.db.collection.return_value.document.return_value = mock_doc_ref
        
        result = await server.firestore_update_document(
            "users",
            "doc_123",
            {"name": "Updated Name"}
        )
        
        assert result["id"] == "doc_123"
        assert result["updated"] is True
        mock_doc_ref.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_document(self, server):
        """Deve deletar documento"""
        mock_doc_ref = MagicMock()
        
        server.db.collection.return_value.document.return_value = mock_doc_ref
        
        result = await server.firestore_delete_document("users", "doc_123")
        
        assert result["id"] == "doc_123"
        assert result["deleted"] is True
        mock_doc_ref.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_write(self, server):
        """Deve executar operações em batch"""
        mock_batch = MagicMock()
        server.db.batch.return_value = mock_batch
        
        mock_doc_ref = MagicMock()
        server.db.collection.return_value.document.return_value = mock_doc_ref
        
        operations = [
            {"type": "create", "collection": "users", "document_id": "doc1", "data": {"name": "User 1"}},
            {"type": "update", "collection": "users", "document_id": "doc2", "data": {"name": "Updated"}},
            {"type": "delete", "collection": "users", "document_id": "doc3", "data": None},
        ]
        
        result = await server.firestore_batch_write(operations)
        
        assert result["success"] is True
        assert result["operations_count"] == 3
        mock_batch.commit.assert_called_once()


# =============================================================================
# TESTES DE AUTHENTICATION
# =============================================================================

@pytest.mark.firebase
class TestFirebaseAuth:
    """Testes de operações de autenticação"""
    
    @pytest.fixture
    def server(self):
        with patch('firebase_admin._apps', {'[DEFAULT]': MagicMock()}):
            with patch('firebase_admin.firestore.client') as mock_firestore:
                with patch('firebase_admin.storage.bucket') as mock_bucket:
                    mock_firestore.return_value = MagicMock()
                    mock_bucket.return_value = MagicMock()
                    
                    from firebase_mcp_server import FirebaseMCPServer
                    return FirebaseMCPServer(project_id="test-project")
    
    @pytest.mark.asyncio
    @patch('firebase_admin.auth.list_users')
    async def test_list_users(self, mock_list, server, mock_firebase_user):
        """Deve listar usuários"""
        mock_result = MagicMock()
        mock_result.users = [mock_firebase_user]
        mock_result.next_page_token = None
        mock_list.return_value = mock_result
        
        result = await server.auth_list_users(limit=10)
        
        assert "users" in result
        assert len(result["users"]) == 1
        assert result["users"][0]["uid"] == "firebase_uid_123"
    
    @pytest.mark.asyncio
    @patch('firebase_admin.auth.get_user')
    async def test_get_user(self, mock_get, server, mock_firebase_user):
        """Deve buscar usuário por UID"""
        mock_get.return_value = mock_firebase_user
        
        result = await server.auth_get_user("firebase_uid_123")
        
        assert result is not None
        assert result["uid"] == "firebase_uid_123"
        assert result["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    @patch('firebase_admin.auth.get_user')
    async def test_get_user_not_found(self, mock_get, server):
        """Deve retornar None se usuário não existir"""
        from firebase_admin import auth
        mock_get.side_effect = auth.UserNotFoundError("User not found")
        
        result = await server.auth_get_user("nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    @patch('firebase_admin.auth.get_user_by_email')
    @patch('firebase_admin.auth.get_user')
    async def test_get_user_by_email(self, mock_get, mock_get_by_email, server, mock_firebase_user):
        """Deve buscar usuário por email"""
        mock_get_by_email.return_value = mock_firebase_user
        mock_get.return_value = mock_firebase_user
        
        result = await server.auth_get_user_by_email("test@example.com")
        
        assert result is not None
        assert result["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    @patch('firebase_admin.auth.create_user')
    async def test_create_user(self, mock_create, server, mock_firebase_user):
        """Deve criar novo usuário"""
        mock_create.return_value = mock_firebase_user
        
        result = await server.auth_create_user(
            email="test@example.com",
            password="password123",
            display_name="Test User"
        )
        
        assert result["uid"] == "firebase_uid_123"
        assert result["created"] is True
        mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('firebase_admin.auth.update_user')
    async def test_update_user(self, mock_update, server, mock_firebase_user):
        """Deve atualizar usuário"""
        mock_update.return_value = mock_firebase_user
        
        result = await server.auth_update_user(
            "firebase_uid_123",
            display_name="Updated Name"
        )
        
        assert result["uid"] == "firebase_uid_123"
        assert result["updated"] is True
    
    @pytest.mark.asyncio
    @patch('firebase_admin.auth.delete_user')
    async def test_delete_user(self, mock_delete, server):
        """Deve deletar usuário"""
        mock_delete.return_value = None
        
        result = await server.auth_delete_user("firebase_uid_123")
        
        assert result["uid"] == "firebase_uid_123"
        assert result["deleted"] is True
    
    @pytest.mark.asyncio
    @patch('firebase_admin.auth.set_custom_user_claims')
    async def test_set_custom_claims(self, mock_set_claims, server):
        """Deve definir custom claims"""
        mock_set_claims.return_value = None
        
        claims = {"admin": True, "role": "superadmin"}
        result = await server.auth_set_custom_claims("firebase_uid_123", claims)
        
        assert result["uid"] == "firebase_uid_123"
        assert result["claims"] == claims
        assert result["updated"] is True
    
    @pytest.mark.asyncio
    @patch('firebase_admin.auth.generate_password_reset_link')
    async def test_generate_password_reset_link(self, mock_generate, server):
        """Deve gerar link de reset de senha"""
        mock_generate.return_value = "https://firebase.com/reset?token=abc123"
        
        result = await server.auth_generate_password_reset_link("test@example.com")
        
        assert "https://firebase.com/reset" in result
    
    @pytest.mark.asyncio
    @patch('firebase_admin.auth.generate_email_verification_link')
    async def test_generate_email_verification_link(self, mock_generate, server):
        """Deve gerar link de verificação de email"""
        mock_generate.return_value = "https://firebase.com/verify?token=abc123"
        
        result = await server.auth_generate_email_verification_link("test@example.com")
        
        assert "https://firebase.com/verify" in result


# =============================================================================
# TESTES DE STORAGE
# =============================================================================

@pytest.mark.firebase
class TestFirebaseStorage:
    """Testes de operações de Storage"""
    
    @pytest.fixture
    def server(self):
        with patch('firebase_admin._apps', {'[DEFAULT]': MagicMock()}):
            with patch('firebase_admin.firestore.client') as mock_firestore:
                with patch('firebase_admin.storage.bucket') as mock_bucket:
                    mock_firestore.return_value = MagicMock()
                    mock_storage = MagicMock()
                    mock_bucket.return_value = mock_storage
                    
                    from firebase_mcp_server import FirebaseMCPServer
                    server = FirebaseMCPServer(project_id="test-project")
                    server.bucket = mock_storage
                    return server
    
    @pytest.mark.asyncio
    async def test_list_files(self, server):
        """Deve listar arquivos"""
        mock_blob = MagicMock()
        mock_blob.name = "test/file.txt"
        mock_blob.size = 1024
        mock_blob.content_type = "text/plain"
        mock_blob.time_created = datetime.now()
        mock_blob.updated = datetime.now()
        mock_blob.public_url = "https://storage.googleapis.com/bucket/test/file.txt"
        
        server.bucket.list_blobs.return_value = [mock_blob]
        
        result = await server.storage_list_files(prefix="test/")
        
        assert len(result) == 1
        assert result[0]["name"] == "test/file.txt"
        assert result[0]["size"] == 1024
    
    @pytest.mark.asyncio
    async def test_get_file_url(self, server):
        """Deve gerar URL assinada"""
        mock_blob = MagicMock()
        mock_blob.generate_signed_url.return_value = "https://storage.googleapis.com/signed-url"
        
        server.bucket.blob.return_value = mock_blob
        
        result = await server.storage_get_file_url("test/file.txt", expiration_minutes=60)
        
        assert "https://storage.googleapis.com" in result
        mock_blob.generate_signed_url.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_file(self, server):
        """Deve fazer upload de arquivo"""
        mock_blob = MagicMock()
        mock_blob.name = "uploaded/file.txt"
        mock_blob.size = 2048
        mock_blob.public_url = "https://storage.googleapis.com/bucket/uploaded/file.txt"
        
        server.bucket.blob.return_value = mock_blob
        
        result = await server.storage_upload_file(
            "/local/path/file.txt",
            "uploaded/file.txt"
        )
        
        assert result["name"] == "uploaded/file.txt"
        assert result["uploaded"] is True
        mock_blob.upload_from_filename.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_file(self, server):
        """Deve deletar arquivo"""
        mock_blob = MagicMock()
        server.bucket.blob.return_value = mock_blob
        
        result = await server.storage_delete_file("test/file.txt")
        
        assert result["name"] == "test/file.txt"
        assert result["deleted"] is True
        mock_blob.delete.assert_called_once()


# =============================================================================
# TESTES DE PROJECT INFO
# =============================================================================

@pytest.mark.firebase
class TestFirebaseProjectInfo:
    """Testes de informações do projeto"""
    
    @pytest.fixture
    def server(self):
        with patch('firebase_admin._apps', {'[DEFAULT]': MagicMock()}):
            with patch('firebase_admin.firestore.client') as mock_firestore:
                with patch('firebase_admin.storage.bucket') as mock_bucket:
                    mock_firestore.return_value = MagicMock()
                    mock_bucket.return_value = MagicMock()
                    
                    from firebase_mcp_server import FirebaseMCPServer
                    return FirebaseMCPServer(project_id="ifrs16-app")
    
    @pytest.mark.asyncio
    async def test_get_project_info(self, server):
        """Deve retornar informações do projeto"""
        result = await server.get_project_info()
        
        assert result["project_id"] == "ifrs16-app"
        assert "storage_bucket" in result
        assert "hosting_url" in result
        assert "ifrs16-app.web.app" in result["hosting_url"]


# =============================================================================
# TESTES DE MCP TOOLS
# =============================================================================

@pytest.mark.firebase
class TestFirebaseMCPTools:
    """Testes da definição de tools MCP"""
    
    def test_mcp_tools_defined(self):
        """Deve ter todas as tools definidas"""
        from firebase_mcp_server import MCP_TOOLS
        
        expected_tools = [
            "firebase_list_collections",
            "firebase_get_documents",
            "firebase_get_document",
            "firebase_create_document",
            "firebase_update_document",
            "firebase_delete_document",
            "firebase_list_users",
            "firebase_get_user",
            "firebase_get_user_by_email",
            "firebase_create_user",
            "firebase_delete_user",
            "firebase_list_files",
            "firebase_get_file_url",
            "firebase_get_project_info",
        ]
        
        for tool in expected_tools:
            assert tool in MCP_TOOLS, f"Tool {tool} não encontrada"
    
    def test_mcp_tools_have_description(self):
        """Todas as tools devem ter descrição"""
        from firebase_mcp_server import MCP_TOOLS
        
        for name, tool in MCP_TOOLS.items():
            assert "description" in tool, f"Tool {name} sem descrição"
            assert len(tool["description"]) > 0
    
    def test_mcp_tools_have_parameters(self):
        """Todas as tools devem ter parâmetros definidos"""
        from firebase_mcp_server import MCP_TOOLS
        
        for name, tool in MCP_TOOLS.items():
            assert "parameters" in tool, f"Tool {name} sem parâmetros"
