"""
Endpoints de autenticação para Admin e Usuários
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..database import get_db
from ..models import AdminUser, User, AdminRole, License, LicenseStatus
from ..schemas import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
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

    # Enviar email de confirmação de cadastro
    from ..services.email_service import EmailService
    try:
        await EmailService.send_registration_confirmation_email(
            to_email=user.email,
            user_name=user.name
        )
        print(f"[OK] Email de confirmação de cadastro enviado para: {user.email}")
    except Exception as e:
        print(f"[WARN] Erro ao enviar email de confirmação: {e}")
        # Não falha o registro se email falhar

    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login de Usuário",
    description="Autentica um usuário e retorna token JWT"
)
async def user_login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login de usuário com email e senha.
    
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

    # Gerar token
    token = create_user_token(user.id, user.email)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_type="user"
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

