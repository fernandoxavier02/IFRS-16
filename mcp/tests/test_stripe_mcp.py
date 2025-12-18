"""
Testes para Stripe MCP Server
=============================

Testes completos de todas as funcionalidades do servidor MCP Stripe.
Usa mocks para não depender de credenciais reais.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# TESTES DE INICIALIZAÇÃO
# =============================================================================

class TestStripeServerInit:
    """Testes de inicialização do servidor Stripe"""
    
    @patch('stripe.api_key', 'sk_test_mock')
    def test_init_with_api_key(self):
        """Deve inicializar com API key fornecida"""
        from stripe_mcp_server import StripeMCPServer
        
        server = StripeMCPServer(api_key="sk_test_123")
        assert server is not None
    
    @patch.dict(os.environ, {"STRIPE_SECRET_KEY": "sk_test_env"})
    @patch('stripe.api_key', 'sk_test_env')
    def test_init_with_env_var(self):
        """Deve inicializar com variável de ambiente"""
        from stripe_mcp_server import StripeMCPServer
        
        server = StripeMCPServer()
        assert server is not None


# =============================================================================
# TESTES DE CLIENTES
# =============================================================================

@pytest.mark.stripe
class TestStripeCustomers:
    """Testes de operações com clientes"""
    
    @pytest.fixture
    def server(self):
        """Fixture do servidor com mock"""
        with patch('stripe.api_key', 'sk_test_mock'):
            from stripe_mcp_server import StripeMCPServer
            return StripeMCPServer(api_key="sk_test_mock")
    
    @pytest.mark.asyncio
    @patch('stripe.Customer.list')
    async def test_list_customers(self, mock_list, server, mock_stripe_customer):
        """Deve listar clientes corretamente"""
        mock_list.return_value = MagicMock(data=[mock_stripe_customer])
        
        result = await server.list_customers(limit=10)
        
        assert len(result) == 1
        assert result[0]["id"] == "cus_test123456"
        assert result[0]["email"] == "test@example.com"
        mock_list.assert_called_once_with(limit=10)
    
    @pytest.mark.asyncio
    @patch('stripe.Customer.list')
    async def test_list_customers_with_email_filter(self, mock_list, server, mock_stripe_customer):
        """Deve filtrar clientes por email"""
        mock_list.return_value = MagicMock(data=[mock_stripe_customer])
        
        result = await server.list_customers(email="test@example.com")
        
        mock_list.assert_called_once()
        call_kwargs = mock_list.call_args[1]
        assert call_kwargs.get("email") == "test@example.com"
    
    @pytest.mark.asyncio
    @patch('stripe.Customer.retrieve')
    async def test_get_customer(self, mock_retrieve, server, mock_stripe_customer):
        """Deve buscar cliente por ID"""
        mock_retrieve.return_value = mock_stripe_customer
        
        result = await server.get_customer("cus_test123456")
        
        assert result["id"] == "cus_test123456"
        assert result["email"] == "test@example.com"
        mock_retrieve.assert_called_once_with("cus_test123456")
    
    @pytest.mark.asyncio
    @patch('stripe.Customer.create')
    async def test_create_customer(self, mock_create, server, mock_stripe_customer):
        """Deve criar novo cliente"""
        mock_create.return_value = mock_stripe_customer
        
        result = await server.create_customer(
            email="test@example.com",
            name="Test User"
        )
        
        assert result["id"] == "cus_test123456"
        mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('stripe.Customer.modify')
    async def test_update_customer(self, mock_modify, server, mock_stripe_customer):
        """Deve atualizar cliente existente"""
        mock_modify.return_value = mock_stripe_customer
        
        result = await server.update_customer(
            "cus_test123456",
            name="Updated Name"
        )
        
        assert result["id"] == "cus_test123456"
        mock_modify.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('stripe.Customer.delete')
    async def test_delete_customer(self, mock_delete, server):
        """Deve deletar cliente"""
        mock_delete.return_value = MagicMock(deleted=True, id="cus_test123456")
        
        result = await server.delete_customer("cus_test123456")
        
        assert result["deleted"] is True
        assert result["id"] == "cus_test123456"


# =============================================================================
# TESTES DE ASSINATURAS
# =============================================================================

@pytest.mark.stripe
class TestStripeSubscriptions:
    """Testes de operações com assinaturas"""
    
    @pytest.fixture
    def server(self):
        with patch('stripe.api_key', 'sk_test_mock'):
            from stripe_mcp_server import StripeMCPServer
            return StripeMCPServer(api_key="sk_test_mock")
    
    @pytest.mark.asyncio
    @patch('stripe.Subscription.list')
    async def test_list_subscriptions(self, mock_list, server, mock_stripe_subscription):
        """Deve listar assinaturas"""
        mock_list.return_value = MagicMock(data=[mock_stripe_subscription])
        
        result = await server.list_subscriptions(limit=10)
        
        assert len(result) == 1
        assert result[0]["id"] == "sub_test123456"
        assert result[0]["status"] == "active"
    
    @pytest.mark.asyncio
    @patch('stripe.Subscription.list')
    async def test_list_subscriptions_by_customer(self, mock_list, server, mock_stripe_subscription):
        """Deve filtrar assinaturas por cliente"""
        mock_list.return_value = MagicMock(data=[mock_stripe_subscription])
        
        result = await server.list_subscriptions(customer_id="cus_test123456")
        
        call_kwargs = mock_list.call_args[1]
        assert call_kwargs.get("customer") == "cus_test123456"
    
    @pytest.mark.asyncio
    @patch('stripe.Subscription.retrieve')
    async def test_get_subscription(self, mock_retrieve, server, mock_stripe_subscription):
        """Deve buscar assinatura por ID"""
        mock_retrieve.return_value = mock_stripe_subscription
        
        result = await server.get_subscription("sub_test123456")
        
        assert result["id"] == "sub_test123456"
        mock_retrieve.assert_called_once_with("sub_test123456")
    
    @pytest.mark.asyncio
    @patch('stripe.Subscription.create')
    async def test_create_subscription(self, mock_create, server, mock_stripe_subscription):
        """Deve criar nova assinatura"""
        mock_create.return_value = mock_stripe_subscription
        
        result = await server.create_subscription(
            customer_id="cus_test123456",
            price_id="price_test123"
        )
        
        assert result["id"] == "sub_test123456"
        mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('stripe.Subscription.modify')
    async def test_cancel_subscription_at_period_end(self, mock_modify, server, mock_stripe_subscription):
        """Deve cancelar assinatura no fim do período"""
        mock_stripe_subscription.cancel_at_period_end = True
        mock_modify.return_value = mock_stripe_subscription
        
        result = await server.cancel_subscription("sub_test123456", immediately=False)
        
        assert result["cancel_at_period_end"] is True
        mock_modify.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('stripe.Subscription.delete')
    async def test_cancel_subscription_immediately(self, mock_delete, server, mock_stripe_subscription):
        """Deve cancelar assinatura imediatamente"""
        mock_stripe_subscription.status = "canceled"
        mock_delete.return_value = mock_stripe_subscription
        
        result = await server.cancel_subscription("sub_test123456", immediately=True)
        
        mock_delete.assert_called_once_with("sub_test123456")


# =============================================================================
# TESTES DE FATURAS
# =============================================================================

@pytest.mark.stripe
class TestStripeInvoices:
    """Testes de operações com faturas"""
    
    @pytest.fixture
    def server(self):
        with patch('stripe.api_key', 'sk_test_mock'):
            from stripe_mcp_server import StripeMCPServer
            return StripeMCPServer(api_key="sk_test_mock")
    
    @pytest.mark.asyncio
    @patch('stripe.Invoice.list')
    async def test_list_invoices(self, mock_list, server, mock_stripe_invoice):
        """Deve listar faturas"""
        mock_list.return_value = MagicMock(data=[mock_stripe_invoice])
        
        result = await server.list_invoices(limit=10)
        
        assert len(result) == 1
        assert result[0]["id"] == "in_test123456"
        assert result[0]["status"] == "paid"
    
    @pytest.mark.asyncio
    @patch('stripe.Invoice.retrieve')
    async def test_get_invoice(self, mock_retrieve, server, mock_stripe_invoice):
        """Deve buscar fatura por ID"""
        mock_retrieve.return_value = mock_stripe_invoice
        
        result = await server.get_invoice("in_test123456")
        
        assert result["id"] == "in_test123456"
        assert result["amount_paid"] == 299.0  # 29900 / 100


# =============================================================================
# TESTES DE PRODUTOS E PREÇOS
# =============================================================================

@pytest.mark.stripe
class TestStripeProducts:
    """Testes de operações com produtos e preços"""
    
    @pytest.fixture
    def server(self):
        with patch('stripe.api_key', 'sk_test_mock'):
            from stripe_mcp_server import StripeMCPServer
            return StripeMCPServer(api_key="sk_test_mock")
    
    @pytest.mark.asyncio
    @patch('stripe.Product.list')
    async def test_list_products(self, mock_list, server):
        """Deve listar produtos"""
        mock_product = MagicMock()
        mock_product.id = "prod_test123456"
        mock_product.name = "Plano Básico"
        mock_product.description = "Plano básico IFRS 16"
        mock_product.active = True
        mock_product.created = int(datetime.now().timestamp())
        mock_product.metadata = {}
        
        mock_list.return_value = MagicMock(data=[mock_product])
        
        result = await server.list_products()
        
        assert len(result) == 1
        assert result[0]["id"] == "prod_test123456"
        assert result[0]["name"] == "Plano Básico"
    
    @pytest.mark.asyncio
    @patch('stripe.Product.retrieve')
    async def test_get_product(self, mock_retrieve, server, mock_stripe_product):
        """Deve buscar produto por ID"""
        mock_retrieve.return_value = mock_stripe_product
        
        result = await server.get_product("prod_test123456")
        
        assert result["id"] == "prod_test123456"
    
    @pytest.mark.asyncio
    @patch('stripe.Price.list')
    async def test_list_prices(self, mock_list, server, mock_stripe_price):
        """Deve listar preços"""
        mock_list.return_value = MagicMock(data=[mock_stripe_price])
        
        result = await server.list_prices()
        
        assert len(result) == 1
        assert result[0]["id"] == "price_test123456"
        assert result[0]["unit_amount"] == 299.0
    
    @pytest.mark.asyncio
    @patch('stripe.Price.retrieve')
    async def test_get_price(self, mock_retrieve, server, mock_stripe_price):
        """Deve buscar preço por ID"""
        mock_retrieve.return_value = mock_stripe_price
        
        result = await server.get_price("price_test123456")
        
        assert result["id"] == "price_test123456"


# =============================================================================
# TESTES DE CHECKOUT
# =============================================================================

@pytest.mark.stripe
class TestStripeCheckout:
    """Testes de operações de checkout"""
    
    @pytest.fixture
    def server(self):
        with patch('stripe.api_key', 'sk_test_mock'):
            from stripe_mcp_server import StripeMCPServer
            return StripeMCPServer(api_key="sk_test_mock")
    
    @pytest.mark.asyncio
    @patch('stripe.checkout.Session.create')
    async def test_create_checkout_session(self, mock_create, server, mock_stripe_checkout_session):
        """Deve criar sessão de checkout"""
        mock_create.return_value = mock_stripe_checkout_session
        
        result = await server.create_checkout_session(
            price_id="price_test123",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel"
        )
        
        assert result["id"] == "cs_test123456"
        assert result["url"] == "https://checkout.stripe.com/test"
        mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('stripe.checkout.Session.retrieve')
    async def test_get_checkout_session(self, mock_retrieve, server, mock_stripe_checkout_session):
        """Deve buscar sessão de checkout"""
        mock_retrieve.return_value = mock_stripe_checkout_session
        
        result = await server.get_checkout_session("cs_test123456")
        
        assert result["id"] == "cs_test123456"
        assert result["status"] == "open"


# =============================================================================
# TESTES DE SALDO
# =============================================================================

@pytest.mark.stripe
class TestStripeBalance:
    """Testes de operações de saldo"""
    
    @pytest.fixture
    def server(self):
        with patch('stripe.api_key', 'sk_test_mock'):
            from stripe_mcp_server import StripeMCPServer
            return StripeMCPServer(api_key="sk_test_mock")
    
    @pytest.mark.asyncio
    @patch('stripe.Balance.retrieve')
    async def test_get_balance(self, mock_retrieve, server, mock_stripe_balance):
        """Deve retornar saldo da conta"""
        mock_retrieve.return_value = mock_stripe_balance
        
        result = await server.get_balance()
        
        assert "available" in result
        assert "pending" in result
        assert result["available"][0]["amount"] == 1000.0  # 100000 / 100
    
    @pytest.mark.asyncio
    @patch('stripe.BalanceTransaction.list')
    async def test_list_balance_transactions(self, mock_list, server):
        """Deve listar transações do saldo"""
        mock_transaction = MagicMock(
            id="txn_test123",
            amount=10000,
            currency="brl",
            type="charge",
            status="available",
            created=int(datetime.now().timestamp()),
            description="Test transaction"
        )
        mock_list.return_value = MagicMock(data=[mock_transaction])
        
        result = await server.list_balance_transactions(limit=5)
        
        assert len(result) == 1
        assert result[0]["id"] == "txn_test123"
        assert result[0]["amount"] == 100.0


# =============================================================================
# TESTES DE WEBHOOKS
# =============================================================================

@pytest.mark.stripe
class TestStripeWebhooks:
    """Testes de operações com webhooks"""
    
    @pytest.fixture
    def server(self):
        with patch('stripe.api_key', 'sk_test_mock'):
            from stripe_mcp_server import StripeMCPServer
            return StripeMCPServer(api_key="sk_test_mock")
    
    @pytest.mark.asyncio
    @patch('stripe.WebhookEndpoint.list')
    async def test_list_webhook_endpoints(self, mock_list, server):
        """Deve listar webhooks configurados"""
        mock_webhook = MagicMock(
            id="we_test123",
            url="https://example.com/webhook",
            status="enabled",
            enabled_events=["checkout.session.completed"],
            created=int(datetime.now().timestamp())
        )
        mock_list.return_value = MagicMock(data=[mock_webhook])
        
        result = await server.list_webhook_endpoints()
        
        assert len(result) == 1
        assert result[0]["id"] == "we_test123"
        assert result[0]["status"] == "enabled"
    
    @pytest.mark.asyncio
    @patch('stripe.WebhookEndpoint.create')
    async def test_create_webhook_endpoint(self, mock_create, server):
        """Deve criar webhook endpoint"""
        mock_webhook = MagicMock(
            id="we_test123",
            url="https://example.com/webhook",
            secret="whsec_test123",
            status="enabled",
            enabled_events=["checkout.session.completed"]
        )
        mock_create.return_value = mock_webhook
        
        result = await server.create_webhook_endpoint(
            url="https://example.com/webhook",
            events=["checkout.session.completed"]
        )
        
        assert result["id"] == "we_test123"
        assert result["secret"] == "whsec_test123"


# =============================================================================
# TESTES DE FORMATADORES
# =============================================================================

@pytest.mark.stripe
class TestStripeFormatters:
    """Testes dos métodos de formatação"""
    
    @pytest.fixture
    def server(self):
        with patch('stripe.api_key', 'sk_test_mock'):
            from stripe_mcp_server import StripeMCPServer
            return StripeMCPServer(api_key="sk_test_mock")
    
    def test_format_customer(self, server, mock_stripe_customer):
        """Deve formatar cliente corretamente"""
        result = server._format_customer(mock_stripe_customer)
        
        assert "id" in result
        assert "email" in result
        assert "name" in result
        assert "created" in result
        assert isinstance(result["created"], str)  # ISO format
    
    def test_format_subscription(self, server, mock_stripe_subscription):
        """Deve formatar assinatura corretamente"""
        result = server._format_subscription(mock_stripe_subscription)
        
        assert "id" in result
        assert "customer" in result
        assert "status" in result
        assert "current_period_start" in result
        assert "items" in result
    
    def test_format_invoice(self, server, mock_stripe_invoice):
        """Deve formatar fatura corretamente"""
        result = server._format_invoice(mock_stripe_invoice)
        
        assert "id" in result
        assert "amount_due" in result
        assert "amount_paid" in result
        assert result["amount_paid"] == 299.0  # Convertido de centavos
    
    def test_format_product(self, server, mock_stripe_product):
        """Deve formatar produto corretamente"""
        result = server._format_product(mock_stripe_product)
        
        assert "id" in result
        assert "name" in result
        assert "active" in result
    
    def test_format_price(self, server, mock_stripe_price):
        """Deve formatar preço corretamente"""
        result = server._format_price(mock_stripe_price)
        
        assert "id" in result
        assert "unit_amount" in result
        assert result["unit_amount"] == 299.0  # Convertido de centavos
        assert "recurring" in result


# =============================================================================
# TESTES DE MCP TOOLS
# =============================================================================

@pytest.mark.stripe
class TestStripeMCPTools:
    """Testes da definição de tools MCP"""
    
    def test_mcp_tools_defined(self):
        """Deve ter todas as tools definidas"""
        from stripe_mcp_server import MCP_TOOLS
        
        expected_tools = [
            "stripe_list_customers",
            "stripe_get_customer",
            "stripe_create_customer",
            "stripe_list_subscriptions",
            "stripe_cancel_subscription",
            "stripe_list_invoices",
            "stripe_list_products",
            "stripe_list_prices",
            "stripe_get_balance",
            "stripe_create_checkout_session",
        ]
        
        for tool in expected_tools:
            assert tool in MCP_TOOLS, f"Tool {tool} não encontrada"
    
    def test_mcp_tools_have_description(self):
        """Todas as tools devem ter descrição"""
        from stripe_mcp_server import MCP_TOOLS
        
        for name, tool in MCP_TOOLS.items():
            assert "description" in tool, f"Tool {name} sem descrição"
            assert len(tool["description"]) > 0
    
    def test_mcp_tools_have_parameters(self):
        """Todas as tools devem ter parâmetros definidos"""
        from stripe_mcp_server import MCP_TOOLS
        
        for name, tool in MCP_TOOLS.items():
            assert "parameters" in tool, f"Tool {name} sem parâmetros"
