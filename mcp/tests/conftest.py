"""
Configuração de fixtures para testes dos MCPs
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

# Adicionar diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# FIXTURES STRIPE
# =============================================================================

@pytest.fixture
def mock_stripe_customer():
    """Mock de um cliente Stripe"""
    return MagicMock(
        id="cus_test123456",
        email="test@example.com",
        name="Test User",
        created=int(datetime.now().timestamp()),
        metadata={},
        default_source=None,
        currency="brl"
    )


@pytest.fixture
def mock_stripe_subscription():
    """Mock de uma assinatura Stripe"""
    now = datetime.now()
    return MagicMock(
        id="sub_test123456",
        customer="cus_test123456",
        status="active",
        current_period_start=int(now.timestamp()),
        current_period_end=int((now + timedelta(days=30)).timestamp()),
        cancel_at_period_end=False,
        items=MagicMock(data=[
            MagicMock(
                id="si_test123",
                price=MagicMock(id="price_test123", product="prod_test123")
            )
        ]),
        metadata={}
    )


@pytest.fixture
def mock_stripe_invoice():
    """Mock de uma fatura Stripe"""
    return MagicMock(
        id="in_test123456",
        customer="cus_test123456",
        status="paid",
        amount_due=29900,
        amount_paid=29900,
        currency="brl",
        created=int(datetime.now().timestamp()),
        invoice_pdf="https://stripe.com/invoice.pdf",
        hosted_invoice_url="https://stripe.com/invoice"
    )


@pytest.fixture
def mock_stripe_product():
    """Mock de um produto Stripe"""
    return MagicMock(
        id="prod_test123456",
        name="Plano Básico",
        description="Plano básico IFRS 16",
        active=True,
        created=int(datetime.now().timestamp()),
        metadata={}
    )


@pytest.fixture
def mock_stripe_price():
    """Mock de um preço Stripe"""
    return MagicMock(
        id="price_test123456",
        product="prod_test123456",
        active=True,
        currency="brl",
        unit_amount=29900,
        recurring=MagicMock(interval="month", interval_count=1),
        type="recurring"
    )


@pytest.fixture
def mock_stripe_balance():
    """Mock do saldo Stripe"""
    return MagicMock(
        available=[MagicMock(amount=100000, currency="brl")],
        pending=[MagicMock(amount=50000, currency="brl")]
    )


@pytest.fixture
def mock_stripe_checkout_session():
    """Mock de sessão de checkout"""
    return MagicMock(
        id="cs_test123456",
        url="https://checkout.stripe.com/test",
        status="open",
        customer="cus_test123456",
        subscription="sub_test123456",
        payment_status="unpaid",
        amount_total=29900
    )


# =============================================================================
# FIXTURES FIREBASE
# =============================================================================

@pytest.fixture
def mock_firebase_user():
    """Mock de um usuário Firebase Auth"""
    return MagicMock(
        uid="firebase_uid_123",
        email="test@example.com",
        display_name="Test User",
        phone_number=None,
        photo_url=None,
        disabled=False,
        email_verified=True,
        custom_claims=None,
        provider_data=[
            MagicMock(provider_id="password", uid="test@example.com", email="test@example.com")
        ],
        user_metadata=MagicMock(
            creation_timestamp=int(datetime.now().timestamp() * 1000),
            last_sign_in_timestamp=int(datetime.now().timestamp() * 1000)
        )
    )


@pytest.fixture
def mock_firestore_document():
    """Mock de um documento Firestore"""
    return MagicMock(
        id="doc_123",
        exists=True,
        to_dict=lambda: {"field1": "value1", "field2": 123},
        create_time=datetime.now(),
        update_time=datetime.now()
    )


@pytest.fixture
def mock_storage_blob():
    """Mock de um blob do Storage"""
    return MagicMock(
        name="test/file.txt",
        size=1024,
        content_type="text/plain",
        time_created=datetime.now(),
        updated=datetime.now(),
        public_url="https://storage.googleapis.com/bucket/test/file.txt"
    )


# =============================================================================
# FIXTURES CLOUD SQL
# =============================================================================

@pytest.fixture
def mock_db_user():
    """Mock de um usuário do banco"""
    return {
        "id": str(uuid4()),
        "email": "test@example.com",
        "name": "Test User",
        "password_hash": "hashed_password",
        "is_active": True,
        "email_verified": False,
        "stripe_customer_id": "cus_test123456",
        "created_at": datetime.now(),
        "last_login": datetime.now()
    }


@pytest.fixture
def mock_db_license():
    """Mock de uma licença do banco"""
    return {
        "id": str(uuid4()),
        "key": "FX20251217-IFRS16-ABCD1234",
        "user_id": str(uuid4()),
        "customer_name": "Test User",
        "email": "test@example.com",
        "license_type": "basic",
        "status": "active",
        "expires_at": datetime.now() + timedelta(days=365),
        "revoked": False,
        "revoked_at": None,
        "revoke_reason": None,
        "max_activations": 3,
        "current_activations": 1,
        "created_at": datetime.now(),
        "last_validation": datetime.now()
    }


@pytest.fixture
def mock_db_subscription():
    """Mock de uma assinatura do banco"""
    return {
        "id": str(uuid4()),
        "user_id": str(uuid4()),
        "license_id": str(uuid4()),
        "stripe_subscription_id": "sub_test123456",
        "stripe_price_id": "price_test123456",
        "plan_type": "monthly",
        "status": "active",
        "current_period_start": datetime.now(),
        "current_period_end": datetime.now() + timedelta(days=30),
        "cancel_at_period_end": False,
        "created_at": datetime.now(),
        "cancelled_at": None
    }


@pytest.fixture
def mock_db_tables():
    """Mock da lista de tabelas"""
    return [
        {"table_name": "users", "table_type": "BASE TABLE", "column_count": 10},
        {"table_name": "licenses", "table_type": "BASE TABLE", "column_count": 15},
        {"table_name": "subscriptions", "table_type": "BASE TABLE", "column_count": 12},
        {"table_name": "admin_users", "table_type": "BASE TABLE", "column_count": 8},
        {"table_name": "validation_logs", "table_type": "BASE TABLE", "column_count": 9},
    ]


# =============================================================================
# FIXTURES ASYNCPG
# =============================================================================

@pytest.fixture
def mock_asyncpg_pool():
    """Mock do pool de conexões asyncpg"""
    conn = AsyncMock()
    
    # Criar um context manager mock adequado
    class MockContextManager:
        async def __aenter__(self):
            return conn
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None
    
    pool = MagicMock()  # Usar MagicMock, não AsyncMock
    pool.acquire.return_value = MockContextManager()
    pool.close = AsyncMock()
    
    return pool, conn


# =============================================================================
# CONFIGURAÇÃO PYTEST
# =============================================================================

def pytest_configure(config):
    """Configuração do pytest"""
    config.addinivalue_line(
        "markers", "stripe: testes relacionados ao Stripe MCP"
    )
    config.addinivalue_line(
        "markers", "firebase: testes relacionados ao Firebase MCP"
    )
    config.addinivalue_line(
        "markers", "cloudsql: testes relacionados ao Cloud SQL MCP"
    )
    config.addinivalue_line(
        "markers", "unified: testes relacionados ao Unified MCP"
    )
    config.addinivalue_line(
        "markers", "integration: testes de integração"
    )
