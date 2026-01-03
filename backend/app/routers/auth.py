"""
Endpoints de autenticação para Admin e Usuários
"""

from datetime import datetime, timedelta
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..database import get_db
from ..models import AdminUser, User, AdminRole, License, LicenseStatus, UserSession
from ..schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    ResendVerificationRequest,
    VerifyEmailResponse,
    AdminUserResponse,
    UserResponse,
    UserLicenseResponse,
    LicenseFeatures,
    LicenseTypeEnum,
    LicenseStatusEnum,
)
from ..auth import (
    hash_password,
    verify_password,
    create_admin_token,
    create_user_token,
    create_access_token,
    get_current_admin,
    get_current_user,
)
from ..config import get_settings

settings = get_settings()

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])
limiter = Limiter(key_func=get_remote_address)


# =============================================================================
# ADMIN AUTHENTICATION
# =============================================================================

@router.post(
    "/admin/login",
    response_model=TokenResponse,
    summary="Login de Administrador",
    description="Autentica um administrador e retorna token JWT"
)
@limiter.limit("5/minute")  # Rate limit: 5 tentativas por minuto por IP
async def admin_login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Login de administrador com email e senha.
    
    - **email**: Email do administrador
    - **password**: Senha do administrador
    """
    # Buscar admin por email
    result = await db.execute(
        select(AdminUser).where(AdminUser.email == body.email.lower())
    )
    admin = result.scalar_one_or_none()
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Conta de administrador desativada"
        )
    
    # Verificar senha
    if not verify_password(body.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )
    
    # Atualizar último login
    admin.last_login = datetime.utcnow()
    await db.commit()
    
    # Gerar token
    token = create_admin_token(admin.id, admin.username, admin.role.value)
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_type="admin"
    )


@router.get(
    "/admin/me",
    response_model=AdminUserResponse,
    summary="Dados do Admin Logado",
    description="Retorna dados do administrador autenticado"
)
async def admin_me(
    admin_data: dict = Depends(get_current_admin)
):
    """
    Retorna os dados do administrador autenticado.
    
    Requer: Bearer Token de admin
    """
    admin = admin_data["admin"]
    return AdminUserResponse.model_validate(admin)


@router.post(
    "/admin/logout",
    summary="Logout de Admin",
    description="Invalida a sessão do administrador"
)
async def admin_logout(
    admin_data: dict = Depends(get_current_admin)
):
    """
    Logout do administrador.
    
    Nota: Como usamos JWT stateless, o logout é feito no cliente
    removendo o token. Este endpoint serve para registro de auditoria.
    """
    return {
        "success": True,
        "message": "Logout realizado com sucesso"
    }


@router.post(
    "/admin/change-password",
    summary="Alterar Senha do Admin",
    description="Altera a senha do administrador autenticado"
)
async def admin_change_password(
    body: ChangePasswordRequest,
    admin_data: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Altera a senha do administrador.
    
    - **current_password**: Senha atual
    - **new_password**: Nova senha (mínimo 8 caracteres)
    """
    admin = admin_data["admin"]
    
    # Verificar senha atual
    if not verify_password(body.current_password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta"
        )
    
    # Atualizar senha
    admin.password_hash = hash_password(body.new_password)
    await db.commit()
    
    return {
        "success": True,
        "message": "Senha alterada com sucesso"
    }


# =============================================================================
# USER AUTHENTICATION
# =============================================================================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registro de Usuário",
    description="Cria uma nova conta de usuário"
)
async def register_user(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Registra um novo usuário.

    - **name**: Nome completo
    - **email**: Email (único)
    - **password**: Senha escolhida pelo usuário
    - **company_name**: Nome da empresa (opcional)

    O usuário receberá um email de confirmação de cadastro.
    O cadastro é criado sem assinatura - o usuário precisará assinar um plano
    para ter acesso à calculadora.
    """
    # Verificar se email já existe
    result = await db.execute(
        select(User).where(User.email == body.email.lower())
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este email já está cadastrado"
        )

    # Criar usuário com a senha fornecida
    user = User(
        email=body.email.lower(),
        name=body.name,
        password_hash=hash_password(body.password),
        company_name=body.company_name,
        is_active=True,
        email_verified=False,
        password_must_change=False,  # Usuário escolheu a senha
        password_changed_at=datetime.utcnow()
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Criar token de verificação de email
    from .. import crud
    from ..services.email_service import EmailService
    
    try:
        verification_token = await crud.create_verification_token(db, user.id)
        await db.commit()
        
        # Enviar email de verificação
        await EmailService.send_email_verification(
            to_email=user.email,
            user_name=user.name,
            verification_token=verification_token.token
        )
        print(f"[OK] Email de verificação enviado para: {user.email}")
    except Exception as e:
        print(f"[WARN] Erro ao enviar email de verificação: {e}")
        # Não falha o registro se email falhar

    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login de Usuário",
    description="Autentica um usuário e retorna token JWT"
)
async def user_login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login de usuário com email e senha.
    Registra automaticamente uma sessão para controle de acesso simultâneo.

    - **email**: Email do usuário
    - **password**: Senha do usuário
    """
    # Buscar usuário por email
    result = await db.execute(
        select(User).where(User.email == body.email.lower())
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Conta desativada. Entre em contato com o suporte."
        )
    
    # Verificar se email foi confirmado
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Por favor, confirme seu email antes de fazer login. Verifique sua caixa de entrada."
        )
    
    # Verificar senha
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )

    # SEGURANÇA: Verificar se precisa trocar senha
    if user.password_must_change:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você deve alterar sua senha temporária antes de continuar. "
                   "Use o endpoint /api/auth/change-password com sua senha atual."
        )

    # Atualizar último login
    user.last_login = datetime.utcnow()
    await db.commit()

    # ========== REGISTRO DE SESSÃO (Anti-compartilhamento) ==========
    # Definir limites de sessão por plano
    SESSION_LIMITS = {
        "basic_monthly": 1,
        "basic_yearly": 1,
        "pro_monthly": 2,
        "pro_yearly": 2,
        "enterprise_monthly": 5,
        "enterprise_yearly": 5,
    }

    # Buscar assinatura ativa do usuário para determinar o plano
    from ..models import Subscription, SubscriptionStatus
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.status == SubscriptionStatus.ACTIVE
        ).order_by(Subscription.created_at.desc())
    )
    subscription = result.scalar_one_or_none()

    # Determinar limite de sessões
    if not subscription:
        max_sessions = 1  # Padrão para usuários sem assinatura
    else:
        plan_type = subscription.plan_type.value
        max_sessions = SESSION_LIMITS.get(plan_type, 1)

    # Buscar sessões ativas atuais (não expiradas)
    now = datetime.utcnow()
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == user.id,
            UserSession.is_active == True,
            UserSession.expires_at > now
        ).order_by(UserSession.last_activity.desc())
    )
    active_sessions = result.scalars().all()

    # Verificar se atingiu o limite
    if len(active_sessions) >= max_sessions:
        # Invalidar a sessão mais antiga para permitir a nova
        oldest_session = active_sessions[-1]
        oldest_session.is_active = False
        print(f"[INFO] Sessão antiga invalidada para {user.email} (device: {oldest_session.device_name})")

    # Criar nova sessão
    session_token = str(uuid.uuid4())

    # Extrair informações do dispositivo
    user_agent = request.headers.get("user-agent", "Unknown")
    ip_address = request.client.host if request.client else "Unknown"

    # Criar device fingerprint básico
    device_fingerprint = f"{user_agent[:100]}-{ip_address}"

    # Determinar nome do dispositivo
    device_name = "Unknown Device"
    if "Windows" in user_agent:
        device_name = "Windows PC"
    elif "Macintosh" in user_agent or "Mac OS" in user_agent:
        device_name = "Mac"
    elif "Linux" in user_agent:
        device_name = "Linux PC"
    elif "iPhone" in user_agent or "iPad" in user_agent:
        device_name = "iOS Device"
    elif "Android" in user_agent:
        device_name = "Android Device"

    # Expiração em 24 horas
    expires_at = now + timedelta(hours=24)

    new_session = UserSession(
        user_id=user.id,
        session_token=session_token,
        device_fingerprint=device_fingerprint,
        ip_address=ip_address,
        user_agent=user_agent[:500],
        device_name=device_name,
        last_activity=now,
        expires_at=expires_at,
        is_active=True
    )

    db.add(new_session)
    await db.commit()

    # Gerar token JWT COM o session_token incluído
    token = create_user_token(user.id, user.email, session_token=session_token)

    print(f"[OK] Login bem-sucedido: {user.email} (device: {device_name}, IP: {ip_address})")
    # ===============================================================

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_type="user",
        session_token=session_token
    )


@router.post(
    "/verify-email",
    response_model=VerifyEmailResponse,
    summary="Verificar Email",
    description="Confirma o email do usuário usando o token enviado por email"
)
@limiter.limit("10/hour")
async def verify_email(
    request: Request,
    body: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verifica o email do usuário usando o token de verificação.
    
    - **token**: Token de verificação enviado por email
    """
    from .. import crud
    
    # Buscar token
    verification_token = await crud.get_verification_token(db, body.token)
    
    if not verification_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token de verificação inválido"
        )
    
    # Verificar se já foi usado
    if verification_token.is_used:
        return VerifyEmailResponse(
            success=True,
            message="Seu email já foi confirmado anteriormente. Você já pode fazer login."
        )
    
    # Verificar se expirou
    if verification_token.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de verificação expirado. Solicite um novo email de confirmação."
        )
    
    # Buscar usuário
    result = await db.execute(
        select(User).where(User.id == verification_token.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Marcar email como verificado
    user.email_verified = True
    
    # Marcar token como usado
    await crud.mark_token_as_used(db, body.token)
    
    await db.commit()
    
    print(f"[OK] Email verificado para usuário: {user.email}")
    
    return VerifyEmailResponse(
        success=True,
        message="Email confirmado com sucesso! Você já pode fazer login."
    )


@router.post(
    "/resend-verification",
    response_model=VerifyEmailResponse,
    summary="Reenviar Email de Verificação",
    description="Reenvia o email de verificação para o usuário"
)
@limiter.limit("3/hour")
async def resend_verification(
    request: Request,
    body: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reenvia o email de verificação para o usuário.
    
    - **email**: Email do usuário
    """
    from .. import crud
    from ..services.email_service import EmailService
    
    # Buscar usuário
    result = await db.execute(
        select(User).where(User.email == body.email.lower())
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Não revelar se o email existe ou não (segurança)
        return VerifyEmailResponse(
            success=True,
            message="Se o email estiver cadastrado, você receberá um novo link de confirmação."
        )
    
    # Verificar se já está verificado
    if user.email_verified:
        return VerifyEmailResponse(
            success=True,
            message="Seu email já está confirmado. Você já pode fazer login."
        )
    
    # Invalidar tokens antigos
    await crud.invalidate_old_tokens(db, user.id)
    
    # Criar novo token
    verification_token = await crud.create_verification_token(db, user.id)
    await db.commit()
    
    # Enviar email
    try:
        await EmailService.send_email_verification(
            to_email=user.email,
            user_name=user.name,
            verification_token=verification_token.token
        )
        print(f"[OK] Email de verificação reenviado para: {user.email}")
    except Exception as e:
        print(f"[ERROR] Erro ao reenviar email de verificação: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao enviar email. Tente novamente mais tarde."
        )
    
    return VerifyEmailResponse(
        success=True,
        message="Novo email de confirmação enviado! Verifique sua caixa de entrada."
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Dados do Usuário Logado",
    description="Retorna dados do usuário autenticado"
)
async def user_me(
    user_data: dict = Depends(get_current_user)
):
    """
    Retorna os dados do usuário autenticado.
    
    Requer: Bearer Token de usuário
    """
    user = user_data["user"]
    return UserResponse.model_validate(user)


@router.get(
    "/me/license",
    response_model=UserLicenseResponse,
    summary="Licença do Usuário Logado",
    description="Retorna a licença ativa do usuário autenticado"
)
async def user_license(
    user_data: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna a licença ativa do usuário autenticado.
    
    Requer: Bearer Token de usuário
    
    Retorna os dados da licença e um token JWT para validação.
    """
    user = user_data["user"]
    
    # Buscar licença ativa do usuário
    result = await db.execute(
        select(License).where(
            License.user_id == user.id,
            License.status == LicenseStatus.ACTIVE,
            License.revoked == False
        ).order_by(License.created_at.desc())
    )
    license = result.scalar_one_or_none()
    
    if not license:
        return UserLicenseResponse(
            has_license=False
        )
    
    # Verificar se expirou
    if license.expires_at and datetime.utcnow() > license.expires_at:
        return UserLicenseResponse(
            has_license=False
        )
    
    # Gerar token JWT para a licença
    token_data = {
        "key": license.key,
        "customer_name": license.customer_name,
        "license_type": license.license_type.value,
    }
    license_token = create_access_token(token_data)
    
    # Preparar features
    features = license.features
    license_features = LicenseFeatures(
        max_contracts=features["max_contracts"],
        export_excel=features["export_excel"],
        export_csv=features["export_csv"],
        support=features["support"],
        multi_user=features["multi_user"]
    )
    
    return UserLicenseResponse(
        has_license=True,
        license_key=license.key,
        customer_name=license.customer_name,
        license_type=LicenseTypeEnum(license.license_type.value),
        status=LicenseStatusEnum(license.status.value),
        expires_at=license.expires_at,
        features=license_features,
        token=license_token
    )


@router.post(
    "/me/validate-license-token",
    summary="Validar Licença pelo Token do Usuário",
    description="Valida a licença usando o token de autenticação do usuário"
)
async def validate_license_by_user_token(
    request: Request,
    user_data: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Valida a licença do usuário autenticado usando seu token de autenticação.

    Este endpoint permite que a calculadora valide a licença sem precisar
    de um token JWT separado da licença. A licença é vinculada exclusivamente
    ao usuário e só muda quando o plano é alterado.

    IMPORTANTE: Realiza validação anexa apenas na primeira vez (quando last_validation é NULL).
    Isso garante que a licença seja ativada corretamente no primeiro acesso após a compra.

    Requer: Bearer Token de usuário

    Retorna os dados da licença válida ou erro se não houver licença ativa.
    """
    import traceback
    from ..crud import update_license_validation, log_validation
    
    try:
        user = user_data["user"]
        print(f"[INFO] Validando licença para usuário: {user.email} (ID: {user.id})")
    except Exception as e:
        print(f"[ERROR] Erro ao obter dados do usuário: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação inválido ou expirado"
        )

    # Buscar licença ativa do usuário
    try:
        result = await db.execute(
            select(License).where(
                License.user_id == user.id,
                License.status == LicenseStatus.ACTIVE,
                License.revoked == False
            ).order_by(License.created_at.desc())
        )
        license = result.scalar_one_or_none()
        print(f"[INFO] Licença encontrada: {license.key if license else 'Nenhuma'}")
    except Exception as e:
        print(f"[ERROR] Erro ao buscar licença: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar licença: {str(e)}"
        )

    if not license:
        print(f"[WARN] Nenhuma licença ativa encontrada para usuário {user.email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma licença ativa encontrada para este usuário"
        )

    # Verificar se expirou
    if license.expires_at and datetime.utcnow() > license.expires_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Licença expirada. Renove sua assinatura para continuar."
        )

    # VALIDAÇÃO ANEXA: Realizar apenas na primeira vez (quando last_validation é NULL)
    # Isso garante que a licença seja ativada corretamente no primeiro acesso após compra
    if not license.last_validation:
        # Obter informações do cliente
        ip_address = None
        if request.client:
            ip_address = request.client.host
        # Verificar X-Forwarded-For para proxies
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
        
        user_agent = request.headers.get("User-Agent", "")[:500]
        machine_id = request.headers.get("X-Machine-ID")  # Opcional, pode ser None
        
        try:
            # Atualizar informações de validação (marca como validada pela primeira vez)
            await update_license_validation(
                db,
                key=license.key,
                machine_id=machine_id,
                ip_address=ip_address
            )
            
            # Criar log de validação
            await log_validation(
                db,
                license_key=license.key,
                success=True,
                message="Validação anexa inicial após compra (via validate-license-token)",
                machine_id=machine_id,
                ip_address=ip_address,
                user_agent=user_agent,
                app_version=None
            )
            
            await db.commit()
            print(f"[OK] Validação anexa realizada para licença {license.key} (primeiro acesso)")
            
            # Buscar licença novamente após commit para garantir dados atualizados
            result = await db.execute(
                select(License).where(License.key == license.key)
            )
            license = result.scalar_one_or_none()
            if not license:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Licença não encontrada após validação"
                )
            
            # CRÍTICO: Refresh para garantir que features seja carregado corretamente
            await db.refresh(license)
        except Exception as e:
            # Não bloquear o fluxo se houver erro na validação anexa
            print(f"[WARN] Erro ao realizar validação anexa: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()

    # Gerar token JWT para a licença (para compatibilidade com código existente)
    try:
        token_data = {
            "key": license.key,
            "customer_name": license.customer_name,
            "license_type": license.license_type.value,
        }
        license_token = create_access_token(token_data)
    except Exception as e:
        print(f"[ERROR] Erro ao gerar token JWT: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar token de licença: {str(e)}"
        )

    # Preparar features com tratamento de erro
    try:
        features = license.features
    except Exception as e:
        print(f"[WARN] Erro ao obter features da licença: {e}")
        # Fallback para features básicas
        from ..config import LICENSE_LIMITS
        features = LICENSE_LIMITS.get("basic", LICENSE_LIMITS.get("trial", {}))

    try:
        return {
            "valid": True,
            "key": license.key,
            "customer_name": license.customer_name,
            "license_type": license.license_type.value,
            "status": license.status.value,
            "expires_at": license.expires_at.isoformat() if license.expires_at else None,
            "features": features,
            "token": license_token,
            "message": "Licença válida e vinculada ao usuário"
        }
    except Exception as e:
        print(f"[ERROR] Erro ao preparar resposta: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar validação: {str(e)}"
        )


@router.post(
    "/logout",
    summary="Logout de Usuário",
    description="Invalida a sessão do usuário"
)
async def user_logout(
    user_data: dict = Depends(get_current_user)
):
    """
    Logout do usuário.
    """
    return {
        "success": True,
        "message": "Logout realizado com sucesso"
    }


@router.post(
    "/change-password",
    summary="Alterar Senha do Usuário",
    description="Altera a senha do usuário autenticado"
)
async def user_change_password(
    body: ChangePasswordRequest,
    user_data: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Altera a senha do usuário.
    """
    user = user_data["user"]
    
    # Verificar senha atual
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta"
        )

    # Validar força da nova senha
    if len(body.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A nova senha deve ter no mínimo 8 caracteres"
        )

    # Atualizar senha e limpar flag de troca obrigatória
    user.password_hash = hash_password(body.new_password)
    user.password_must_change = False  # Senha foi alterada, libera acesso
    user.password_changed_at = datetime.utcnow()  # Registra data da troca
    await db.commit()

    return {
        "success": True,
        "message": "Senha alterada com sucesso. Você já pode fazer login normalmente."
    }


@router.post(
    "/forgot-password",
    summary="Recuperar Senha",
    description="Envia email de recuperação de senha"
)
async def forgot_password(
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Solicita recuperação de senha.
    
    - **email**: Email do usuário
    
    Nota: Por segurança, sempre retorna sucesso mesmo se o email não existir.
    """
    # Buscar usuário
    result = await db.execute(
        select(User).where(User.email == body.email.lower())
    )
    user = result.scalar_one_or_none()
    
    if user:
        # Gerar token de reset
        from ..auth import create_reset_token
        reset_token = create_reset_token(user.id)

        # Enviar email
        from ..services.email_service import EmailService
        try:
            await EmailService.send_password_reset_email(
                to_email=user.email,
                user_name=user.name,
                reset_token=reset_token
            )
            print(f"[OK] Email de reset enviado para: {user.email}")
        except Exception as e:
            print(f"[WARN] Erro ao enviar email de reset: {e}")
            # Não falha a request se email falhar

    # Sempre retorna sucesso por segurança (não revela se email existe)
    return {
        "success": True,
        "message": "Se o email existir em nossa base, você receberá instruções de recuperação."
    }


@router.post(
    "/reset-password",
    summary="Resetar Senha",
    description="Reseta a senha usando o token recebido por email"
)
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reseta a senha do usuário.

    - **token**: Token recebido por email
    - **new_password**: Nova senha (mínimo 8 caracteres)

    Retorna erro se token for inválido ou expirado.
    """
    # Validar token
    from ..auth import verify_reset_token
    user_id = verify_reset_token(body.token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado. Solicite um novo link de recuperação."
        )

    # Buscar usuário
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )

    # Atualizar senha
    user.password_hash = hash_password(body.new_password)
    user.password_changed_at = datetime.utcnow()
    user.password_must_change = False  # Usuário já trocou a senha

    await db.commit()

    print(f"[OK] Senha resetada para usuário: {user.email}")

    return {
        "success": True,
        "message": "Senha redefinida com sucesso. Você já pode fazer login com a nova senha."
    }


# =============================================================================
# SESSION MANAGEMENT (CONTROLE DE SESSÕES SIMULTÂNEAS)
# =============================================================================

@router.post(
    "/sessions/register",
    summary="Registrar Nova Sessão",
    description="Registra uma nova sessão de usuário e valida limite de sessões simultâneas"
)
async def register_session(
    request: Request,
    user_data: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Registra uma nova sessão de usuário.
    Valida o limite de sessões simultâneas baseado no plano.

    Limites por plano:
    - basic_monthly/basic_yearly: 1 sessão simultânea
    - pro_monthly/pro_yearly: 2 sessões simultâneas
    - enterprise_monthly/enterprise_yearly: 5 sessões simultâneas
    """
    user = user_data["user"]

    # Definir limites de sessão por plano
    SESSION_LIMITS = {
        "basic_monthly": 1,
        "basic_yearly": 1,
        "pro_monthly": 2,
        "pro_yearly": 2,
        "enterprise_monthly": 5,
        "enterprise_yearly": 5,
    }

    # Buscar assinatura ativa do usuário para determinar o plano
    from ..models import Subscription, SubscriptionStatus
    result = await db.execute(
        select(Subscription).where(
            Subscription.user_id == user.id,
            Subscription.status == SubscriptionStatus.ACTIVE
        ).order_by(Subscription.created_at.desc())
    )
    subscription = result.scalar_one_or_none()

    # Determinar limite de sessões
    if not subscription:
        max_sessions = 1  # Padrão para usuários sem assinatura
    else:
        plan_type = subscription.plan_type.value
        max_sessions = SESSION_LIMITS.get(plan_type, 1)

    # Buscar sessões ativas atuais (não expiradas)
    now = datetime.utcnow()
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == user.id,
            UserSession.is_active == True,
            UserSession.expires_at > now
        ).order_by(UserSession.last_activity.desc())
    )
    active_sessions = result.scalars().all()

    # Verificar se atingiu o limite
    if len(active_sessions) >= max_sessions:
        # Invalidar a sessão mais antiga para permitir a nova
        oldest_session = active_sessions[-1]
        oldest_session.is_active = False
        await db.commit()

        print(f"[INFO] Sessão antiga invalidada para usuário {user.email} (device: {oldest_session.device_name})")

    # Criar nova sessão
    # Gerar token único para esta sessão
    session_token = str(uuid.uuid4())

    # Extrair informações do dispositivo
    user_agent = request.headers.get("user-agent", "Unknown")
    ip_address = request.client.host if request.client else "Unknown"

    # Criar device fingerprint básico (pode ser melhorado com hash de user-agent + outros dados)
    device_fingerprint = f"{user_agent[:100]}-{ip_address}"

    # Determinar nome do dispositivo baseado no user-agent
    device_name = "Unknown Device"
    if "Windows" in user_agent:
        device_name = "Windows PC"
    elif "Macintosh" in user_agent or "Mac OS" in user_agent:
        device_name = "Mac"
    elif "Linux" in user_agent:
        device_name = "Linux PC"
    elif "iPhone" in user_agent or "iPad" in user_agent:
        device_name = "iOS Device"
    elif "Android" in user_agent:
        device_name = "Android Device"

    # Expiração em 24 horas
    expires_at = now + timedelta(hours=24)

    new_session = UserSession(
        user_id=user.id,
        session_token=session_token,
        device_fingerprint=device_fingerprint,
        ip_address=ip_address,
        user_agent=user_agent[:500],  # Limitar tamanho
        device_name=device_name,
        last_activity=now,
        expires_at=expires_at,
        is_active=True
    )

    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    print(f"[OK] Nova sessão criada para {user.email} (device: {device_name}, IP: {ip_address})")

    return {
        "success": True,
        "session_token": session_token,
        "device_name": device_name,
        "expires_at": expires_at.isoformat(),
        "max_sessions": max_sessions,
        "active_sessions": len(active_sessions) + 1 if len(active_sessions) < max_sessions else max_sessions,
        "message": "Sessão registrada com sucesso"
    }


@router.post(
    "/sessions/heartbeat",
    summary="Atualizar Heartbeat da Sessão",
    description="Atualiza o timestamp de última atividade da sessão"
)
async def session_heartbeat(
    session_token: str,
    user_data: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza o heartbeat da sessão para manter ela ativa.
    Deve ser chamado periodicamente pelo frontend (ex: a cada 5 minutos).
    """
    try:
        user = user_data["user"]

        # Buscar sessão
        result = await db.execute(
            select(UserSession).where(
                UserSession.session_token == session_token,
                UserSession.user_id == user.id,
                UserSession.is_active == True
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sessão não encontrada ou inativa"
            )

        # Verificar se expirou (normalizando timezone para comparação segura)
        now = datetime.utcnow()

        # Normalizar expires_at para naive datetime (sem timezone)
        expires_at = session.expires_at
        if expires_at is not None:
            # Se tiver timezone, converter para naive
            if hasattr(expires_at, 'tzinfo') and expires_at.tzinfo is not None:
                # Converter para UTC e remover timezone
                try:
                    expires_at = expires_at.replace(tzinfo=None)
                except Exception:
                    # Fallback: usar timestamp
                    expires_at = datetime.utcfromtimestamp(expires_at.timestamp())

        if expires_at is None or expires_at < now:
            session.is_active = False
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sessão expirada. Faça login novamente."
            )

        # Atualizar última atividade
        session.last_activity = now
        await db.commit()

        return {
            "success": True,
            "last_activity": now.isoformat(),
            "expires_at": session.expires_at.isoformat() if session.expires_at else None
        }
    except HTTPException:
        # Re-raise HTTPException para manter status code correto
        raise
    except Exception as e:
        print(f"[ERROR] Erro no heartbeat de sessão: {type(e).__name__}: {e}")
        # Retornar sucesso silenciosamente para não interromper a UX
        # O heartbeat é um keep-alive, não crítico
        return {
            "success": True,
            "last_activity": datetime.utcnow().isoformat(),
            "warning": "Sessão não encontrada no banco, mas autenticação válida"
        }


@router.post(
    "/sessions/terminate",
    summary="Encerrar Sessão",
    description="Encerra uma sessão ativa"
)
async def terminate_session(
    session_token: str,
    user_data: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Encerra uma sessão específica (logout).
    """
    user = user_data["user"]

    # Buscar sessão
    result = await db.execute(
        select(UserSession).where(
            UserSession.session_token == session_token,
            UserSession.user_id == user.id
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sessão não encontrada"
        )

    # Marcar como inativa
    session.is_active = False
    await db.commit()

    print(f"[OK] Sessão encerrada para {user.email} (device: {session.device_name})")

    return {
        "success": True,
        "message": "Sessão encerrada com sucesso"
    }


@router.get(
    "/sessions/active",
    summary="Listar Sessões Ativas",
    description="Lista todas as sessões ativas do usuário"
)
async def list_active_sessions(
    user_data: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todas as sessões ativas do usuário.
    Útil para mostrar no dashboard quais dispositivos estão conectados.
    """
    user = user_data["user"]

    # Buscar sessões ativas não expiradas
    now = datetime.utcnow()
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == user.id,
            UserSession.is_active == True,
            UserSession.expires_at > now
        ).order_by(UserSession.last_activity.desc())
    )
    sessions = result.scalars().all()

    return {
        "sessions": [
            {
                "session_token": s.session_token,
                "device_name": s.device_name,
                "ip_address": s.ip_address,
                "last_activity": s.last_activity.isoformat(),
                "created_at": s.created_at.isoformat(),
                "expires_at": s.expires_at.isoformat()
            }
            for s in sessions
        ],
        "total": len(sessions)
    }


# =============================================================================
# UTILITÁRIOS
# =============================================================================

@router.get(
    "/verify-token",
    summary="Verificar Token",
    description="Verifica se um token JWT é válido"
)
async def verify_token_endpoint(
    token_data: dict = Depends(get_current_user)
):
    """
    Verifica se o token é válido e retorna informações básicas.
    """
    return {
        "valid": True,
        "user_type": "user",
        "email": token_data.get("email")
    }

