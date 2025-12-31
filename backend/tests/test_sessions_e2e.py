"""
Testes End-to-End para sistema de sessões simultâneas
Simula cenários reais de uso
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserSession, Subscription, SubscriptionStatus, PlanType
from app.auth import hash_password


# =============================================================================
# FIXTURES DE CENÁRIOS
# =============================================================================

@pytest.fixture
async def familia_compartilhando_conta(db_session: AsyncSession):
    """
    Cenário: Família tentando compartilhar uma conta Basic
    - Pai no PC
    - Mãe no laptop
    - Filho no celular
    Resultado esperado: Apenas 1 dispositivo ativo por vez
    """
    user = User(
        email="familia@test.com",
        name="Conta Família",
        password_hash=hash_password("Familia123!"),
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    subscription = Subscription(
        user_id=user.id,
        plan_type=PlanType.BASIC_MONTHLY,
        status=SubscriptionStatus.ACTIVE
    )
    db_session.add(subscription)
    await db_session.commit()

    return user


@pytest.fixture
async def empresa_com_pro(db_session: AsyncSession):
    """
    Cenário: Empresa pequena com plano Pro
    - Desktop no escritório
    - Notebook em home office
    Resultado esperado: 2 dispositivos simultâneos OK
    """
    user = User(
        email="empresa@test.com",
        name="Empresa Ltda",
        password_hash=hash_password("Empresa123!"),
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    subscription = Subscription(
        user_id=user.id,
        plan_type=PlanType.PRO_MONTHLY,
        status=SubscriptionStatus.ACTIVE
    )
    db_session.add(subscription)
    await db_session.commit()

    return user


# =============================================================================
# CENÁRIO 1: TENTATIVA DE COMPARTILHAMENTO
# =============================================================================

@pytest.mark.asyncio
async def test_cenario_familia_compartilhando(
    client: AsyncClient,
    familia_compartilhando_conta: User,
    db_session: AsyncSession
):
    """
    História: Família tenta compartilhar conta Basic

    1. Pai faz login no PC Windows
    2. 30 minutos depois, mãe faz login no MacBook
    3. Pai é desconectado (sessão invalidada)
    4. 1 hora depois, filho faz login no iPhone
    5. Mãe é desconectada
    6. Pai tenta fazer heartbeat → erro 404
    """
    # 1. Pai faz login no PC
    pai_login = await client.post(
        "/api/auth/login",
        json={"email": "familia@test.com", "password": "Familia123!"},
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    assert pai_login.status_code == 200
    pai_token = pai_login.json()["session_token"]
    pai_auth = pai_login.json()["access_token"]

    # Verificar que pai está ativo
    result = await db_session.execute(
        select(UserSession).where(
            UserSession.session_token == pai_token,
            UserSession.is_active == True
        )
    )
    assert result.scalar_one_or_none() is not None

    # 2. Mãe faz login no MacBook (invalida pai)
    mae_login = await client.post(
        "/api/auth/login",
        json={"email": "familia@test.com", "password": "Familia123!"},
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
    )
    assert mae_login.status_code == 200
    mae_token = mae_login.json()["session_token"]
    mae_auth = mae_login.json()["access_token"]

    # Verificar que sessão do pai foi invalidada
    await db_session.commit()
    result = await db_session.execute(
        select(UserSession).where(UserSession.session_token == pai_token)
    )
    pai_session = result.scalar_one()
    assert pai_session.is_active == False

    # Verificar que mãe está ativa
    result = await db_session.execute(
        select(UserSession).where(
            UserSession.session_token == mae_token,
            UserSession.is_active == True
        )
    )
    assert result.scalar_one_or_none() is not None

    # 3. Filho faz login no iPhone (invalida mãe)
    filho_login = await client.post(
        "/api/auth/login",
        json={"email": "familia@test.com", "password": "Familia123!"},
        headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)"}
    )
    assert filho_login.status_code == 200
    filho_token = filho_login.json()["session_token"]

    # Verificar que apenas filho está ativo
    await db_session.commit()
    result = await db_session.execute(
        select(UserSession).where(
            UserSession.user_id == familia_compartilhando_conta.id,
            UserSession.is_active == True
        )
    )
    active_sessions = result.scalars().all()
    assert len(active_sessions) == 1
    assert active_sessions[0].session_token == filho_token

    # 4. Pai tenta fazer heartbeat → falha
    heartbeat_response = await client.post(
        f"/api/auth/sessions/heartbeat?session_token={pai_token}",
        headers={"Authorization": f"Bearer {pai_auth}"}
    )
    assert heartbeat_response.status_code == 404  # Sessão não encontrada ou inativa


# =============================================================================
# CENÁRIO 2: USO LEGÍTIMO COM PRO
# =============================================================================

@pytest.mark.asyncio
async def test_cenario_empresa_uso_legitimo(
    client: AsyncClient,
    empresa_com_pro: User,
    db_session: AsyncSession
):
    """
    História: Empresa usa plano Pro legitimamente

    1. Funcionário faz login no desktop do escritório
    2. Mesmo funcionário faz login no notebook para trabalhar em casa
    3. Ambas as sessões coexistem (Pro permite 2)
    4. Heartbeat funciona em ambos os dispositivos
    5. Funcionário tenta logar em 3º dispositivo → primeira sessão é invalidada
    """
    # 1. Login no desktop
    desktop_login = await client.post(
        "/api/auth/login",
        json={"email": "empresa@test.com", "password": "Empresa123!"},
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    desktop_token = desktop_login.json()["session_token"]
    desktop_auth = desktop_login.json()["access_token"]

    # 2. Login no notebook
    notebook_login = await client.post(
        "/api/auth/login",
        json={"email": "empresa@test.com", "password": "Empresa123!"},
        headers={"User-Agent": "Mozilla/5.0 (Macintosh)"}
    )
    notebook_token = notebook_login.json()["session_token"]
    notebook_auth = notebook_login.json()["access_token"]

    # 3. Verificar que ambas as sessões estão ativas
    result = await db_session.execute(
        select(UserSession).where(
            UserSession.user_id == empresa_com_pro.id,
            UserSession.is_active == True
        )
    )
    active_sessions = result.scalars().all()
    assert len(active_sessions) == 2

    # 4. Heartbeat funciona em ambos
    heartbeat1 = await client.post(
        f"/api/auth/sessions/heartbeat?session_token={desktop_token}",
        headers={"Authorization": f"Bearer {desktop_auth}"}
    )
    assert heartbeat1.status_code == 200

    heartbeat2 = await client.post(
        f"/api/auth/sessions/heartbeat?session_token={notebook_token}",
        headers={"Authorization": f"Bearer {notebook_auth}"}
    )
    assert heartbeat2.status_code == 200

    # 5. Login em tablet (3º dispositivo) → invalida desktop
    tablet_login = await client.post(
        "/api/auth/login",
        json={"email": "empresa@test.com", "password": "Empresa123!"},
        headers={"User-Agent": "Mozilla/5.0 (iPad)"}
    )
    tablet_token = tablet_login.json()["session_token"]

    # Verificar que desktop foi invalidado
    await db_session.commit()
    result = await db_session.execute(
        select(UserSession).where(UserSession.session_token == desktop_token)
    )
    desktop_session = result.scalar_one()
    assert desktop_session.is_active == False

    # Verificar que notebook e tablet estão ativos
    result = await db_session.execute(
        select(UserSession).where(
            UserSession.user_id == empresa_com_pro.id,
            UserSession.is_active == True
        )
    )
    active_sessions = result.scalars().all()
    assert len(active_sessions) == 2
    active_tokens = [s.session_token for s in active_sessions]
    assert notebook_token in active_tokens
    assert tablet_token in active_tokens


# =============================================================================
# CENÁRIO 3: SESSÃO EXPIRADA POR INATIVIDADE
# =============================================================================

@pytest.mark.asyncio
async def test_cenario_usuario_esqueceu_aba_aberta(
    client: AsyncClient,
    familia_compartilhando_conta: User,
    db_session: AsyncSession
):
    """
    História: Usuário deixou aba aberta mas computador dormiu

    1. Usuário faz login
    2. Computador entra em modo sleep por 25 horas
    3. Sessão expira (24h de inatividade)
    4. Usuário volta e tenta fazer heartbeat → erro 401
    5. Frontend detecta e redireciona para login
    """
    # 1. Login
    login_response = await client.post(
        "/api/auth/login",
        json={"email": "familia@test.com", "password": "Familia123!"}
    )
    session_token = login_response.json()["session_token"]
    auth_token = login_response.json()["access_token"]

    # 2. Simular passagem de 25 horas (expirar manualmente)
    result = await db_session.execute(
        select(UserSession).where(UserSession.session_token == session_token)
    )
    session = result.scalar_one()
    session.expires_at = datetime.utcnow() - timedelta(hours=1)  # Expirou há 1 hora
    await db_session.commit()

    # 3. Tentar heartbeat → falha com 401
    heartbeat_response = await client.post(
        f"/api/auth/sessions/heartbeat?session_token={session_token}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert heartbeat_response.status_code == 401
    assert "expirada" in heartbeat_response.json()["detail"].lower()

    # Verificar que sessão foi marcada como inativa
    await db_session.commit()
    result = await db_session.execute(
        select(UserSession).where(UserSession.session_token == session_token)
    )
    session = result.scalar_one()
    assert session.is_active == False


# =============================================================================
# CENÁRIO 4: UPGRADE DE PLANO
# =============================================================================

@pytest.mark.asyncio
async def test_cenario_upgrade_de_plano(
    client: AsyncClient,
    db_session: AsyncSession
):
    """
    História: Usuário faz upgrade de Basic para Pro

    1. Usuário Basic está usando 1 dispositivo
    2. Tenta logar em 2º dispositivo → 1º é desconectado
    3. Faz upgrade para Pro
    4. Agora pode usar 2 dispositivos simultaneamente
    """
    # Criar usuário Basic
    user = User(
        email="upgrade@test.com",
        name="Upgrade User",
        password_hash=hash_password("Test123!"),
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    subscription = Subscription(
        user_id=user.id,
        plan_type=PlanType.BASIC_MONTHLY,
        status=SubscriptionStatus.ACTIVE
    )
    db_session.add(subscription)
    await db_session.commit()

    # 1. Login no dispositivo 1
    login1 = await client.post(
        "/api/auth/login",
        json={"email": "upgrade@test.com", "password": "Test123!"}
    )
    token1 = login1.json()["session_token"]

    # 2. Login no dispositivo 2 (invalida dispositivo 1)
    login2 = await client.post(
        "/api/auth/login",
        json={"email": "upgrade@test.com", "password": "Test123!"}
    )
    token2 = login2.json()["session_token"]

    # Verificar que apenas 1 sessão está ativa
    result = await db_session.execute(
        select(UserSession).where(
            UserSession.user_id == user.id,
            UserSession.is_active == True
        )
    )
    assert len(result.scalars().all()) == 1

    # 3. Fazer upgrade para Pro
    result = await db_session.execute(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    sub = result.scalar_one()
    sub.plan_type = PlanType.PRO_MONTHLY
    await db_session.commit()

    # 4. Fazer login em ambos os dispositivos novamente
    login3 = await client.post(
        "/api/auth/login",
        json={"email": "upgrade@test.com", "password": "Test123!"}
    )

    login4 = await client.post(
        "/api/auth/login",
        json={"email": "upgrade@test.com", "password": "Test123!"}
    )

    # Verificar que agora 2 sessões estão ativas
    await db_session.commit()
    result = await db_session.execute(
        select(UserSession).where(
            UserSession.user_id == user.id,
            UserSession.is_active == True
        )
    )
    active_sessions = result.scalars().all()
    assert len(active_sessions) == 2


# =============================================================================
# CENÁRIO 5: DETECÇÃO DE COMPARTILHAMENTO SUSPEITO
# =============================================================================

@pytest.mark.asyncio
async def test_cenario_deteccao_compartilhamento_suspeito(
    client: AsyncClient,
    familia_compartilhando_conta: User,
    db_session: AsyncSession
):
    """
    História: Sistema detecta padrão suspeito de compartilhamento

    1. Login em São Paulo (IP brasileiro)
    2. 5 minutos depois, login em Nova York (IP americano)
    3. Ambos os logins são registrados com IPs e dispositivos diferentes
    4. Sistema invalida sessão antiga mas registra histórico
    5. Admin pode auditar comportamento suspeito
    """
    # 1. Login em São Paulo
    sp_login = await client.post(
        "/api/auth/login",
        json={"email": "familia@test.com", "password": "Familia123!"},
        headers={"User-Agent": "Mozilla/5.0 (Windows)"}
    )
    sp_token = sp_login.json()["session_token"]

    # Simular IP brasileiro
    result = await db_session.execute(
        select(UserSession).where(UserSession.session_token == sp_token)
    )
    sp_session = result.scalar_one()
    sp_session.ip_address = "200.150.100.50"  # IP BR
    await db_session.commit()

    # 2. Login em Nova York (5 minutos depois)
    await asyncio.sleep(0.1)  # Simular pequeno delay

    ny_login = await client.post(
        "/api/auth/login",
        json={"email": "familia@test.com", "password": "Familia123!"},
        headers={"User-Agent": "Mozilla/5.0 (Macintosh)"}
    )
    ny_token = ny_login.json()["session_token"]

    # Simular IP americano
    await db_session.commit()
    result = await db_session.execute(
        select(UserSession).where(UserSession.session_token == ny_token)
    )
    ny_session = result.scalar_one()
    ny_session.ip_address = "216.58.194.174"  # IP US
    await db_session.commit()

    # 3. Verificar que histórico completo foi registrado
    result = await db_session.execute(
        select(UserSession).where(
            UserSession.user_id == familia_compartilhando_conta.id
        ).order_by(UserSession.created_at)
    )
    all_sessions = result.scalars().all()

    assert len(all_sessions) == 2
    assert all_sessions[0].ip_address == "200.150.100.50"
    assert all_sessions[1].ip_address == "216.58.194.174"
    assert all_sessions[0].is_active == False  # SP foi invalidado
    assert all_sessions[1].is_active == True   # NY está ativo


# =============================================================================
# CENÁRIO 6: LOGOUT EXPLÍCITO
# =============================================================================

@pytest.mark.asyncio
async def test_cenario_logout_explicito(
    client: AsyncClient,
    empresa_com_pro: User,
    db_session: AsyncSession
):
    """
    História: Usuário faz logout explícito

    1. Usuário faz login no escritório
    2. Ao sair, clica em "Sair" (logout)
    3. Sessão é encerrada explicitamente
    4. Heartbeat subsequente falha
    5. Usuário pode fazer novo login
    """
    # 1. Login
    login_response = await client.post(
        "/api/auth/login",
        json={"email": "empresa@test.com", "password": "Empresa123!"}
    )
    session_token = login_response.json()["session_token"]
    auth_token = login_response.json()["access_token"]

    # Verificar sessão ativa
    result = await db_session.execute(
        select(UserSession).where(
            UserSession.session_token == session_token,
            UserSession.is_active == True
        )
    )
    assert result.scalar_one_or_none() is not None

    # 2. Logout explícito
    logout_response = await client.post(
        f"/api/auth/sessions/terminate?session_token={session_token}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert logout_response.status_code == 200

    # 3. Verificar que sessão foi encerrada
    await db_session.commit()
    result = await db_session.execute(
        select(UserSession).where(UserSession.session_token == session_token)
    )
    session = result.scalar_one()
    assert session.is_active == False

    # 4. Heartbeat falha
    heartbeat_response = await client.post(
        f"/api/auth/sessions/heartbeat?session_token={session_token}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert heartbeat_response.status_code == 404

    # 5. Novo login funciona
    new_login = await client.post(
        "/api/auth/login",
        json={"email": "empresa@test.com", "password": "Empresa123!"}
    )
    assert new_login.status_code == 200


# =============================================================================
# CENÁRIO 7: PERFORMANCE COM MÚLTIPLOS USUÁRIOS
# =============================================================================

@pytest.mark.asyncio
async def test_cenario_multiplos_usuarios_simultaneos(
    client: AsyncClient,
    db_session: AsyncSession
):
    """
    História: Sistema lida com múltiplos usuários fazendo login simultaneamente

    Criar 50 usuários diferentes
    Cada um faz login simultaneamente
    Verificar que sistema não trava e cada um tem sua sessão
    """
    # Criar 50 usuários
    users = []
    for i in range(50):
        user = User(
            email=f"user{i}@test.com",
            name=f"User {i}",
            password_hash=hash_password("Test123!"),
            is_active=True
        )
        db_session.add(user)
        users.append(user)

    await db_session.commit()

    # Fazer 50 logins sequenciais (simula carga sem race conditions do SQLite)
    responses = []
    for i in range(50):
        response = await client.post(
            "/api/auth/login",
            json={"email": f"user{i}@test.com", "password": "Test123!"}
        )
        responses.append(response)

    # Verificar que todos tiveram sucesso
    for response in responses:
        assert response.status_code == 200
        assert "session_token" in response.json()

    # Verificar que 50 sessões foram criadas
    await db_session.commit()
    result = await db_session.execute(
        select(UserSession).where(UserSession.is_active == True)
    )
    active_sessions = result.scalars().all()
    assert len(active_sessions) >= 50  # >= porque podem existir sessões de outros testes
