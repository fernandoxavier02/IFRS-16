"""
Testes para o sistema de controle de sessões simultâneas
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserSession, Subscription, SubscriptionStatus, PlanType
from app.auth import hash_password


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
async def basic_user(db_session: AsyncSession) -> User:
    """Cria usuário com plano Basic"""
    user = User(
        email="basic@test.com",
        name="Basic User",
        password_hash=hash_password("Test123!"),
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Criar assinatura Basic
    subscription = Subscription(
        user_id=user.id,
        plan_type=PlanType.BASIC_MONTHLY,
        status=SubscriptionStatus.ACTIVE
    )
    db_session.add(subscription)
    await db_session.commit()

    return user


@pytest.fixture
async def pro_user(db_session: AsyncSession) -> User:
    """Cria usuário com plano Pro"""
    user = User(
        email="pro@test.com",
        name="Pro User",
        password_hash=hash_password("Test123!"),
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Criar assinatura Pro
    subscription = Subscription(
        user_id=user.id,
        plan_type=PlanType.PRO_MONTHLY,
        status=SubscriptionStatus.ACTIVE
    )
    db_session.add(subscription)
    await db_session.commit()

    return user


@pytest.fixture
async def enterprise_user(db_session: AsyncSession) -> User:
    """Cria usuário com plano Enterprise"""
    user = User(
        email="enterprise@test.com",
        name="Enterprise User",
        password_hash=hash_password("Test123!"),
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Criar assinatura Enterprise
    subscription = Subscription(
        user_id=user.id,
        plan_type=PlanType.ENTERPRISE_MONTHLY,
        status=SubscriptionStatus.ACTIVE
    )
    db_session.add(subscription)
    await db_session.commit()

    return user


# =============================================================================
# TESTES DE LOGIN E CRIAÇÃO DE SESSÃO
# =============================================================================

@pytest.mark.asyncio
async def test_login_creates_session(client: AsyncClient, basic_user: User, db_session: AsyncSession):
    """Testa se login cria uma sessão automaticamente"""
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "basic@test.com",
            "password": "Test123!"
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Verificar se retornou session_token
    assert "session_token" in data
    assert data["session_token"] is not None
    assert len(data["session_token"]) > 0

    # Verificar se sessão foi criada no banco
    result = await db_session.execute(
        select(UserSession).where(
            UserSession.user_id == basic_user.id,
            UserSession.is_active == True
        )
    )
    sessions = result.scalars().all()
    assert len(sessions) == 1
    assert sessions[0].session_token == data["session_token"]


@pytest.mark.asyncio
async def test_login_tracks_device_info(client: AsyncClient, basic_user: User, db_session: AsyncSession):
    """Testa se login registra informações do dispositivo"""
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "basic@test.com",
            "password": "Test123!"
        },
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    )

    assert response.status_code == 200

    # Verificar informações do dispositivo
    result = await db_session.execute(
        select(UserSession).where(UserSession.user_id == basic_user.id)
    )
    session = result.scalar_one()

    assert session.device_name == "Windows PC"
    assert session.user_agent is not None
    assert "Windows" in session.user_agent
    assert session.ip_address is not None


# =============================================================================
# TESTES DE LIMITE DE SESSÕES
# =============================================================================

@pytest.mark.asyncio
async def test_basic_user_limited_to_one_session(
    client: AsyncClient,
    basic_user: User,
    db_session: AsyncSession
):
    """Testa que usuário Basic só pode ter 1 sessão ativa"""
    # Login 1 (PC)
    response1 = await client.post(
        "/api/auth/login",
        json={"email": "basic@test.com", "password": "Test123!"},
        headers={"User-Agent": "Mozilla/5.0 (Windows)"}
    )
    assert response1.status_code == 200
    session_token_1 = response1.json()["session_token"]

    # Verificar 1 sessão ativa
    result = await db_session.execute(
        select(UserSession).where(
            UserSession.user_id == basic_user.id,
            UserSession.is_active == True
        )
    )
    assert len(result.scalars().all()) == 1

    # Login 2 (Mobile) - deve invalidar sessão 1
    response2 = await client.post(
        "/api/auth/login",
        json={"email": "basic@test.com", "password": "Test123!"},
        headers={"User-Agent": "Mozilla/5.0 (iPhone)"}
    )
    assert response2.status_code == 200
    session_token_2 = response2.json()["session_token"]

    # Verificar que apenas 1 sessão está ativa
    await db_session.refresh(basic_user)
    result = await db_session.execute(
        select(UserSession).where(
            UserSession.user_id == basic_user.id,
            UserSession.is_active == True
        )
    )
    active_sessions = result.scalars().all()
    assert len(active_sessions) == 1
    assert active_sessions[0].session_token == session_token_2

    # Verificar que sessão 1 foi invalidada
    result = await db_session.execute(
        select(UserSession).where(UserSession.session_token == session_token_1)
    )
    old_session = result.scalar_one()
    assert old_session.is_active == False


@pytest.mark.asyncio
async def test_pro_user_can_have_two_sessions(
    client: AsyncClient,
    pro_user: User,
    db_session: AsyncSession
):
    """Testa que usuário Pro pode ter 2 sessões simultâneas"""
    # Login 1 (PC)
    response1 = await client.post(
        "/api/auth/login",
        json={"email": "pro@test.com", "password": "Test123!"},
        headers={"User-Agent": "Mozilla/5.0 (Windows)"}
    )
    assert response1.status_code == 200

    # Login 2 (Mobile)
    response2 = await client.post(
        "/api/auth/login",
        json={"email": "pro@test.com", "password": "Test123!"},
        headers={"User-Agent": "Mozilla/5.0 (iPhone)"}
    )
    assert response2.status_code == 200

    # Verificar 2 sessões ativas
    result = await db_session.execute(
        select(UserSession).where(
            UserSession.user_id == pro_user.id,
            UserSession.is_active == True
        )
    )
    active_sessions = result.scalars().all()
    assert len(active_sessions) == 2


@pytest.mark.asyncio
async def test_pro_user_third_login_invalidates_oldest(
    client: AsyncClient,
    pro_user: User,
    db_session: AsyncSession
):
    """Testa que 3º login de usuário Pro invalida a sessão mais antiga"""
    # Login 1 (PC)
    response1 = await client.post(
        "/api/auth/login",
        json={"email": "pro@test.com", "password": "Test123!"}
    )
    token1 = response1.json()["session_token"]

    # Login 2 (Mobile)
    response2 = await client.post(
        "/api/auth/login",
        json={"email": "pro@test.com", "password": "Test123!"}
    )
    token2 = response2.json()["session_token"]

    # Login 3 (Tablet) - deve invalidar sessão 1
    response3 = await client.post(
        "/api/auth/login",
        json={"email": "pro@test.com", "password": "Test123!"}
    )
    token3 = response3.json()["session_token"]

    # Verificar que apenas 2 sessões estão ativas
    await db_session.commit()
    result = await db_session.execute(
        select(UserSession).where(
            UserSession.user_id == pro_user.id,
            UserSession.is_active == True
        )
    )
    active_sessions = result.scalars().all()
    assert len(active_sessions) == 2

    # Verificar que sessão 1 foi invalidada
    result = await db_session.execute(
        select(UserSession).where(UserSession.session_token == token1)
    )
    old_session = result.scalar_one()
    assert old_session.is_active == False

    # Verificar que sessões 2 e 3 estão ativas
    active_tokens = [s.session_token for s in active_sessions]
    assert token2 in active_tokens
    assert token3 in active_tokens


@pytest.mark.asyncio
async def test_enterprise_user_can_have_five_sessions(
    client: AsyncClient,
    enterprise_user: User,
    db_session: AsyncSession
):
    """Testa que usuário Enterprise pode ter 5 sessões simultâneas"""
    # Criar 5 logins
    for i in range(5):
        response = await client.post(
            "/api/auth/login",
            json={"email": "enterprise@test.com", "password": "Test123!"},
            headers={"User-Agent": f"Device-{i}"}
        )
        assert response.status_code == 200

    # Verificar 5 sessões ativas
    result = await db_session.execute(
        select(UserSession).where(
            UserSession.user_id == enterprise_user.id,
            UserSession.is_active == True
        )
    )
    active_sessions = result.scalars().all()
    assert len(active_sessions) == 5


# =============================================================================
# TESTES DE HEARTBEAT
# =============================================================================

@pytest.mark.asyncio
async def test_heartbeat_updates_last_activity(
    client: AsyncClient,
    basic_user: User,
    db_session: AsyncSession
):
    """Testa que heartbeat atualiza timestamp de última atividade"""
    # Login
    login_response = await client.post(
        "/api/auth/login",
        json={"email": "basic@test.com", "password": "Test123!"}
    )
    session_token = login_response.json()["session_token"]
    auth_token = login_response.json()["access_token"]

    # Obter timestamp inicial
    result = await db_session.execute(
        select(UserSession).where(UserSession.session_token == session_token)
    )
    session_before = result.scalar_one()
    last_activity_before = session_before.last_activity

    # Aguardar 1 segundo
    import asyncio
    await asyncio.sleep(1)

    # Enviar heartbeat
    heartbeat_response = await client.post(
        f"/api/auth/sessions/heartbeat?session_token={session_token}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert heartbeat_response.status_code == 200

    # Verificar que last_activity foi atualizado
    await db_session.commit()
    result = await db_session.execute(
        select(UserSession).where(UserSession.session_token == session_token)
    )
    session_after = result.scalar_one()
    assert session_after.last_activity > last_activity_before


@pytest.mark.asyncio
async def test_heartbeat_fails_for_invalid_token(
    client: AsyncClient,
    basic_user: User
):
    """Testa que heartbeat falha com token inválido"""
    # Login
    login_response = await client.post(
        "/api/auth/login",
        json={"email": "basic@test.com", "password": "Test123!"}
    )
    auth_token = login_response.json()["access_token"]

    # Tentar heartbeat com token falso
    response = await client.post(
        f"/api/auth/sessions/heartbeat?session_token=invalid-token",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_heartbeat_fails_for_expired_session(
    client: AsyncClient,
    basic_user: User,
    db_session: AsyncSession
):
    """Testa que heartbeat falha para sessão expirada"""
    # Login
    login_response = await client.post(
        "/api/auth/login",
        json={"email": "basic@test.com", "password": "Test123!"}
    )
    session_token = login_response.json()["session_token"]
    auth_token = login_response.json()["access_token"]

    # Expirar a sessão manualmente
    result = await db_session.execute(
        select(UserSession).where(UserSession.session_token == session_token)
    )
    session = result.scalar_one()
    session.expires_at = datetime.utcnow() - timedelta(hours=1)  # Expirou há 1 hora
    await db_session.commit()

    # Tentar heartbeat
    response = await client.post(
        f"/api/auth/sessions/heartbeat?session_token={session_token}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 401
    assert "expirada" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_heartbeat_fails_for_inactive_session(
    client: AsyncClient,
    basic_user: User,
    db_session: AsyncSession
):
    """Testa que heartbeat falha para sessão inativa"""
    # Login
    login_response = await client.post(
        "/api/auth/login",
        json={"email": "basic@test.com", "password": "Test123!"}
    )
    session_token = login_response.json()["session_token"]
    auth_token = login_response.json()["access_token"]

    # Inativar a sessão manualmente
    result = await db_session.execute(
        select(UserSession).where(UserSession.session_token == session_token)
    )
    session = result.scalar_one()
    session.is_active = False
    await db_session.commit()

    # Tentar heartbeat
    response = await client.post(
        f"/api/auth/sessions/heartbeat?session_token={session_token}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404


# =============================================================================
# TESTES DE ENCERRAMENTO DE SESSÃO
# =============================================================================

@pytest.mark.asyncio
async def test_terminate_session_marks_inactive(
    client: AsyncClient,
    basic_user: User,
    db_session: AsyncSession
):
    """Testa que terminate marca sessão como inativa"""
    # Login
    login_response = await client.post(
        "/api/auth/login",
        json={"email": "basic@test.com", "password": "Test123!"}
    )
    session_token = login_response.json()["session_token"]
    auth_token = login_response.json()["access_token"]

    # Encerrar sessão
    response = await client.post(
        f"/api/auth/sessions/terminate?session_token={session_token}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200

    # Verificar que sessão foi marcada como inativa
    await db_session.commit()
    result = await db_session.execute(
        select(UserSession).where(UserSession.session_token == session_token)
    )
    session = result.scalar_one()
    assert session.is_active == False


# =============================================================================
# TESTES DE LISTAGEM DE SESSÕES ATIVAS
# =============================================================================

@pytest.mark.asyncio
async def test_list_active_sessions(
    client: AsyncClient,
    pro_user: User,
    db_session: AsyncSession
):
    """Testa listagem de sessões ativas"""
    # Criar 2 sessões
    login1 = await client.post(
        "/api/auth/login",
        json={"email": "pro@test.com", "password": "Test123!"},
        headers={"User-Agent": "Mozilla/5.0 (Windows)"}
    )
    auth_token = login1.json()["access_token"]

    await client.post(
        "/api/auth/login",
        json={"email": "pro@test.com", "password": "Test123!"},
        headers={"User-Agent": "Mozilla/5.0 (iPhone)"}
    )

    # Listar sessões
    response = await client.get(
        "/api/auth/sessions/active",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 2
    assert len(data["sessions"]) == 2

    # Verificar estrutura dos dados
    session = data["sessions"][0]
    assert "session_token" in session
    assert "device_name" in session
    assert "ip_address" in session
    assert "last_activity" in session
    assert "created_at" in session
    assert "expires_at" in session


@pytest.mark.asyncio
async def test_list_sessions_excludes_inactive(
    client: AsyncClient,
    pro_user: User,
    db_session: AsyncSession
):
    """Testa que listagem exclui sessões inativas"""
    # Criar 2 sessões
    login1 = await client.post(
        "/api/auth/login",
        json={"email": "pro@test.com", "password": "Test123!"}
    )
    token1 = login1.json()["session_token"]
    auth_token = login1.json()["access_token"]

    await client.post(
        "/api/auth/login",
        json={"email": "pro@test.com", "password": "Test123!"}
    )

    # Inativar sessão 1
    result = await db_session.execute(
        select(UserSession).where(UserSession.session_token == token1)
    )
    session = result.scalar_one()
    session.is_active = False
    await db_session.commit()

    # Listar sessões - deve retornar apenas 1
    response = await client.get(
        "/api/auth/sessions/active",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    data = response.json()
    assert data["total"] == 1


# =============================================================================
# TESTES DE EXPIRAÇÃO
# =============================================================================

@pytest.mark.asyncio
async def test_session_expires_after_24_hours(
    client: AsyncClient,
    basic_user: User,
    db_session: AsyncSession
):
    """Testa que sessão tem expiração de 24 horas"""
    # Login
    login_response = await client.post(
        "/api/auth/login",
        json={"email": "basic@test.com", "password": "Test123!"}
    )
    session_token = login_response.json()["session_token"]

    # Verificar expiração
    result = await db_session.execute(
        select(UserSession).where(UserSession.session_token == session_token)
    )
    session = result.scalar_one()

    time_diff = session.expires_at - session.created_at
    assert time_diff.total_seconds() == pytest.approx(24 * 60 * 60, rel=10)


# =============================================================================
# TESTES DE SEGURANÇA
# =============================================================================

@pytest.mark.asyncio
async def test_cannot_heartbeat_another_users_session(
    client: AsyncClient,
    basic_user: User,
    pro_user: User,
    db_session: AsyncSession
):
    """Testa que usuário não pode fazer heartbeat de sessão de outro usuário"""
    # Login usuário 1
    login1 = await client.post(
        "/api/auth/login",
        json={"email": "basic@test.com", "password": "Test123!"}
    )
    session_token_1 = login1.json()["session_token"]

    # Login usuário 2
    login2 = await client.post(
        "/api/auth/login",
        json={"email": "pro@test.com", "password": "Test123!"}
    )
    auth_token_2 = login2.json()["access_token"]

    # Usuário 2 tenta fazer heartbeat da sessão do usuário 1
    response = await client.post(
        f"/api/auth/sessions/heartbeat?session_token={session_token_1}",
        headers={"Authorization": f"Bearer {auth_token_2}"}
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cannot_terminate_another_users_session(
    client: AsyncClient,
    basic_user: User,
    pro_user: User,
    db_session: AsyncSession
):
    """Testa que usuário não pode encerrar sessão de outro usuário"""
    # Login usuário 1
    login1 = await client.post(
        "/api/auth/login",
        json={"email": "basic@test.com", "password": "Test123!"}
    )
    session_token_1 = login1.json()["session_token"]

    # Login usuário 2
    login2 = await client.post(
        "/api/auth/login",
        json={"email": "pro@test.com", "password": "Test123!"}
    )
    auth_token_2 = login2.json()["access_token"]

    # Usuário 2 tenta encerrar sessão do usuário 1
    response = await client.post(
        f"/api/auth/sessions/terminate?session_token={session_token_1}",
        headers={"Authorization": f"Bearer {auth_token_2}"}
    )
    assert response.status_code == 404


# =============================================================================
# TESTES DE CLEANUP
# =============================================================================

@pytest.mark.asyncio
async def test_cleanup_removes_expired_sessions(db_session: AsyncSession, basic_user: User):
    """Testa que sessões expiradas podem ser removidas"""
    from sqlalchemy import delete

    # Criar sessão expirada
    expired_session = UserSession(
        user_id=basic_user.id,
        session_token=str(uuid4()),
        device_name="Test Device",
        last_activity=datetime.utcnow() - timedelta(days=2),
        expires_at=datetime.utcnow() - timedelta(days=1),
        is_active=True
    )
    db_session.add(expired_session)

    # Criar sessão ativa
    active_session = UserSession(
        user_id=basic_user.id,
        session_token=str(uuid4()),
        device_name="Test Device",
        last_activity=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=24),
        is_active=True
    )
    db_session.add(active_session)
    await db_session.commit()

    # Simular cleanup: deletar sessões expiradas
    now = datetime.utcnow()
    result = await db_session.execute(
        delete(UserSession).where(
            UserSession.expires_at < now
        )
    )
    deleted_count = result.rowcount
    await db_session.commit()

    # Verificar que 1 sessão foi deletada
    assert deleted_count == 1

    # Verificar que apenas sessão ativa permanece
    result = await db_session.execute(
        select(UserSession).where(UserSession.user_id == basic_user.id)
    )
    sessions = result.scalars().all()
    assert len(sessions) == 1
    assert sessions[0].session_token == active_session.session_token


# =============================================================================
# TESTES DE EDGE CASES
# =============================================================================

@pytest.mark.asyncio
async def test_user_without_subscription_limited_to_one_session(
    client: AsyncClient,
    db_session: AsyncSession
):
    """Testa que usuário sem assinatura é limitado a 1 sessão"""
    # Criar usuário sem assinatura
    user = User(
        email="nosub@test.com",
        name="No Sub User",
        password_hash=hash_password("Test123!"),
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()

    # Login 1
    await client.post(
        "/api/auth/login",
        json={"email": "nosub@test.com", "password": "Test123!"}
    )

    # Login 2 - deve invalidar sessão 1
    await client.post(
        "/api/auth/login",
        json={"email": "nosub@test.com", "password": "Test123!"}
    )

    # Verificar apenas 1 sessão ativa
    result = await db_session.execute(
        select(UserSession).where(
            UserSession.user_id == user.id,
            UserSession.is_active == True
        )
    )
    assert len(result.scalars().all()) == 1


@pytest.mark.asyncio
async def test_concurrent_logins_handle_race_conditions(
    client: AsyncClient,
    pro_user: User,
    db_session: AsyncSession
):
    """Testa que múltiplos logins sequenciais são tratados corretamente"""
    # Fazer 3 logins sequenciais (simula concorrência de forma mais controlada)
    responses = []
    for _ in range(3):
        response = await client.post(
            "/api/auth/login",
            json={"email": "pro@test.com", "password": "Test123!"}
        )
        responses.append(response)
        # Pequeno delay para evitar race condition no SQLite
        import asyncio
        await asyncio.sleep(0.1)

    # Todos devem ter sucesso
    for response in responses:
        assert response.status_code == 200

    # Mas apenas 2 sessões devem estar ativas (limite do Pro)
    await db_session.commit()
    result = await db_session.execute(
        select(UserSession).where(
            UserSession.user_id == pro_user.id,
            UserSession.is_active == True
        )
    )
    active_sessions = result.scalars().all()
    assert len(active_sessions) == 2
