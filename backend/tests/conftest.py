"""
Configurações e fixtures do pytest para testes da API
"""

import asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.config import get_settings, Settings
from app.models import License, LicenseStatus, LicenseType, AdminUser, AdminRole, User
from app.auth import create_access_token, create_admin_token, create_user_token, hash_password


# ============================================================
# Configuração do banco de testes
# ============================================================

# Usar SQLite em memória para testes (mais rápido)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Engine de testes
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False}
)

# Session factory de testes
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ============================================================
# Fixtures de configuração
# ============================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Cria event loop para testes async"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def settings() -> Settings:
    """Retorna configurações para testes"""
    return get_settings()


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> AdminUser:
    """Cria um admin para testes"""
    admin = AdminUser(
        id=uuid4(),
        username="test_admin",
        email="admin@test.com",
        password_hash=hash_password("TestAdmin123!"),
        role=AdminRole.SUPERADMIN,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest.fixture
def admin_token(admin_user: AdminUser) -> str:
    """Retorna token JWT de admin para testes"""
    return create_admin_token(admin_user.id, admin_user.username, admin_user.role.value)


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Cria um usuário para testes"""
    user = User(
        id=uuid4(),
        email="user@test.com",
        name="Test User",
        password_hash=hash_password("TestUser123!"),
        is_active=True,
        email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def user_token(test_user: User) -> str:
    """Retorna token JWT de usuário para testes"""
    return create_user_token(test_user.id, test_user.email)


# ============================================================
# Fixtures de banco de dados
# ============================================================

@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Cria uma sessão de banco de dados isolada para cada teste.
    As tabelas são criadas antes e removidas após cada teste.
    """
    # Criar tabelas
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Criar sessão
    async with TestSessionLocal() as session:
        yield session
    
    # Limpar tabelas após teste
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Cliente HTTP assíncrono para testes de API.
    Substitui a dependência do banco pelo banco de testes.
    """
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# ============================================================
# Fixtures de dados de teste
# ============================================================

@pytest_asyncio.fixture
async def sample_license(db_session: AsyncSession) -> License:
    """
    Cria uma licença de teste válida no banco.
    """
    license = License(
        id=uuid4(),
        key="TEST-LICENSE-001",
        customer_name="Test User",
        email="test@example.com",
        status=LicenseStatus.ACTIVE,
        license_type=LicenseType.PRO,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=365),
        max_activations=1,
        current_activations=0,
    )
    db_session.add(license)
    await db_session.commit()
    await db_session.refresh(license)
    return license


@pytest_asyncio.fixture
async def expired_license(db_session: AsyncSession) -> License:
    """
    Cria uma licença expirada para testes.
    """
    license = License(
        id=uuid4(),
        key="TEST-EXPIRED-001",
        customer_name="Expired User",
        email="expired@example.com",
        status=LicenseStatus.ACTIVE,
        license_type=LicenseType.BASIC,
        created_at=datetime.utcnow() - timedelta(days=400),
        expires_at=datetime.utcnow() - timedelta(days=30),
        max_activations=1,
        current_activations=0,
    )
    db_session.add(license)
    await db_session.commit()
    await db_session.refresh(license)
    return license


@pytest_asyncio.fixture
async def revoked_license(db_session: AsyncSession) -> License:
    """
    Cria uma licença revogada para testes.
    """
    license = License(
        id=uuid4(),
        key="TEST-REVOKED-001",
        customer_name="Revoked User",
        email="revoked@example.com",
        status=LicenseStatus.CANCELLED,
        license_type=LicenseType.PRO,
        created_at=datetime.utcnow() - timedelta(days=30),
        revoked=True,
        revoked_at=datetime.utcnow() - timedelta(days=5),
        revoke_reason="Pagamento não realizado",
        max_activations=1,
        current_activations=0,
    )
    db_session.add(license)
    await db_session.commit()
    await db_session.refresh(license)
    return license


@pytest_asyncio.fixture
async def suspended_license(db_session: AsyncSession) -> License:
    """
    Cria uma licença suspensa para testes.
    """
    license = License(
        id=uuid4(),
        key="TEST-SUSPENDED-001",
        customer_name="Suspended User",
        email="suspended@example.com",
        status=LicenseStatus.SUSPENDED,
        license_type=LicenseType.BASIC,
        created_at=datetime.utcnow() - timedelta(days=60),
        max_activations=1,
        current_activations=0,
    )
    db_session.add(license)
    await db_session.commit()
    await db_session.refresh(license)
    return license


@pytest_asyncio.fixture
async def license_with_machine(db_session: AsyncSession) -> License:
    """
    Cria uma licença com machine_id vinculado.
    """
    license = License(
        id=uuid4(),
        key="TEST-MACHINE-001",
        customer_name="Machine User",
        email="machine@example.com",
        status=LicenseStatus.ACTIVE,
        license_type=LicenseType.PRO,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=365),
        machine_id="existing-machine-id-12345",
        max_activations=1,
        current_activations=1,
    )
    db_session.add(license)
    await db_session.commit()
    await db_session.refresh(license)
    return license


@pytest.fixture
def valid_token(sample_license) -> str:
    """
    Gera um token JWT válido para a licença de teste.
    """
    return create_access_token({
        "key": sample_license.key,
        "customer_name": sample_license.customer_name,
        "license_type": sample_license.license_type.value,
    })


@pytest.fixture
def expired_token() -> str:
    """
    Gera um token JWT expirado.
    """
    return create_access_token(
        {"key": "TEST-LICENSE-001"},
        expires_delta=timedelta(seconds=-1)
    )


@pytest.fixture
def invalid_token() -> str:
    """
    Retorna um token inválido.
    """
    return "invalid.token.here"


# ============================================================
# Fixtures adicionais para testes de validação
# ============================================================

@pytest_asyncio.fixture
async def trial_license(db_session: AsyncSession) -> License:
    """Cria uma licença Trial para testes"""
    license = License(
        id=uuid4(),
        key="TEST-TRIAL-001",
        customer_name="Trial User",
        email="trial@example.com",
        status=LicenseStatus.ACTIVE,
        license_type=LicenseType.TRIAL,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=7),
        max_activations=1,
        current_activations=0,
    )
    db_session.add(license)
    await db_session.commit()
    await db_session.refresh(license)
    return license


@pytest_asyncio.fixture
async def basic_license(db_session: AsyncSession) -> License:
    """Cria uma licença Basic para testes"""
    license = License(
        id=uuid4(),
        key="TEST-BASIC-001",
        customer_name="Basic User",
        email="basic@example.com",
        status=LicenseStatus.ACTIVE,
        license_type=LicenseType.BASIC,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30),
        max_activations=1,
        current_activations=0,
    )
    db_session.add(license)
    await db_session.commit()
    await db_session.refresh(license)
    return license


@pytest_asyncio.fixture
async def enterprise_license(db_session: AsyncSession) -> License:
    """Cria uma licença Enterprise para testes"""
    license = License(
        id=uuid4(),
        key="TEST-ENTERPRISE-001",
        customer_name="Enterprise Corp",
        email="enterprise@example.com",
        status=LicenseStatus.ACTIVE,
        license_type=LicenseType.ENTERPRISE,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=365),
        max_activations=10,
        current_activations=0,
    )
    db_session.add(license)
    await db_session.commit()
    await db_session.refresh(license)
    return license


@pytest_asyncio.fixture
async def permanent_license(db_session: AsyncSession) -> License:
    """Cria uma licença permanente (sem expiração) para testes"""
    license = License(
        id=uuid4(),
        key="TEST-PERMANENT-001",
        customer_name="Permanent User",
        email="permanent@example.com",
        status=LicenseStatus.ACTIVE,
        license_type=LicenseType.PRO,
        created_at=datetime.utcnow(),
        expires_at=None,
        max_activations=3,
        current_activations=0,
    )
    db_session.add(license)
    await db_session.commit()
    await db_session.refresh(license)
    return license


@pytest_asyncio.fixture
async def multi_activation_license(db_session: AsyncSession) -> License:
    """Cria uma licença com múltiplas ativações permitidas"""
    license = License(
        id=uuid4(),
        key="TEST-MULTI-001",
        customer_name="Multi User",
        email="multi@example.com",
        status=LicenseStatus.ACTIVE,
        license_type=LicenseType.PRO,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=365),
        max_activations=3,
        current_activations=0,
    )
    db_session.add(license)
    await db_session.commit()
    await db_session.refresh(license)
    return license


@pytest_asyncio.fixture
async def license_about_to_expire(db_session: AsyncSession) -> License:
    """Cria uma licença prestes a expirar (em 1 hora)"""
    license = License(
        id=uuid4(),
        key="TEST-EXPIRING-001",
        customer_name="Expiring User",
        email="expiring@example.com",
        status=LicenseStatus.ACTIVE,
        license_type=LicenseType.BASIC,
        created_at=datetime.utcnow() - timedelta(days=29),
        expires_at=datetime.utcnow() + timedelta(hours=1),
        max_activations=1,
        current_activations=0,
    )
    db_session.add(license)
    await db_session.commit()
    await db_session.refresh(license)
    return license

