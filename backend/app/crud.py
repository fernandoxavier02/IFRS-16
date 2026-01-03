"""
Operações CRUD para o banco de dados
"""

import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import License, ValidationLog, LicenseStatus, LicenseType, EmailVerificationToken
from .schemas import LicenseCreateRequest


def generate_license_key(license_type: LicenseType) -> str:
    """
    Gera uma chave de licença única.
    
    Formato: FX2025-IFRS16-{TYPE}-{RANDOM}
    Exemplo: FX2025-IFRS16-PRO-A1B2C3D4
    
    Args:
        license_type: Tipo da licença
    
    Returns:
        Chave de licença gerada
    """
    type_code = license_type.value[:3].upper()
    random_part = ''.join(
        secrets.choice(string.ascii_uppercase + string.digits)
        for _ in range(8)
    )
    return f"FX2025-IFRS16-{type_code}-{random_part}"


# ============================================================
# Operações de Licença
# ============================================================

async def get_license_by_key(
    db: AsyncSession,
    key: str
) -> Optional[License]:
    """
    Busca uma licença pela chave.
    
    Args:
        db: Sessão do banco de dados
        key: Chave da licença
    
    Returns:
        Licença encontrada ou None
    """
    result = await db.execute(
        select(License).where(License.key == key.upper())
    )
    return result.scalar_one_or_none()


async def get_license_by_id(
    db: AsyncSession,
    license_id: UUID
) -> Optional[License]:
    """
    Busca uma licença pelo ID.
    
    Args:
        db: Sessão do banco de dados
        license_id: UUID da licença
    
    Returns:
        Licença encontrada ou None
    """
    result = await db.execute(
        select(License).where(License.id == license_id)
    )
    return result.scalar_one_or_none()


async def get_all_licenses(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[LicenseStatus] = None
) -> List[License]:
    """
    Lista todas as licenças com paginação opcional.
    
    Args:
        db: Sessão do banco de dados
        skip: Quantos registros pular
        limit: Máximo de registros a retornar
        status_filter: Filtrar por status (opcional)
    
    Returns:
        Lista de licenças
    """
    query = select(License).order_by(License.created_at.desc())
    
    if status_filter:
        query = query.where(License.status == status_filter)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def count_licenses(
    db: AsyncSession,
    status_filter: Optional[LicenseStatus] = None
) -> int:
    """
    Conta o total de licenças.
    
    Args:
        db: Sessão do banco de dados
        status_filter: Filtrar por status (opcional)
    
    Returns:
        Total de licenças
    """
    query = select(func.count(License.id))
    
    if status_filter:
        query = query.where(License.status == status_filter)
    
    result = await db.execute(query)
    return result.scalar() or 0


async def create_license(
    db: AsyncSession,
    license_data: LicenseCreateRequest
) -> License:
    """
    Cria uma nova licença.
    
    Args:
        db: Sessão do banco de dados
        license_data: Dados da licença a criar
    
    Returns:
        Licença criada
    """
    # Gerar chave única
    key = generate_license_key(license_data.license_type)
    
    # Garantir que a chave é única
    while await get_license_by_key(db, key):
        key = generate_license_key(license_data.license_type)
    
    # Calcular data de expiração
    expires_at = None
    if license_data.duration_months:
        expires_at = datetime.now(timezone.utc) + timedelta(days=30 * license_data.duration_months)
    
    # Criar licença
    license = License(
        key=key,
        customer_name=license_data.customer_name,
        email=license_data.email,
        license_type=LicenseType(license_data.license_type.value),
        status=LicenseStatus.ACTIVE,
        expires_at=expires_at,
        max_activations=license_data.max_activations,
    )
    
    db.add(license)
    await db.flush()
    await db.refresh(license)
    
    return license


async def update_license_status(
    db: AsyncSession,
    key: str,
    status: LicenseStatus
) -> Optional[License]:
    """
    Atualiza o status de uma licença.
    
    Args:
        db: Sessão do banco de dados
        key: Chave da licença
        status: Novo status
    
    Returns:
        Licença atualizada ou None se não encontrada
    """
    license = await get_license_by_key(db, key)
    
    if not license:
        return None
    
    license.status = status
    await db.flush()
    await db.refresh(license)
    
    return license


async def revoke_license(
    db: AsyncSession,
    key: str,
    reason: Optional[str] = None
) -> Optional[License]:
    """
    Revoga uma licença.
    
    Args:
        db: Sessão do banco de dados
        key: Chave da licença
        reason: Motivo da revogação
    
    Returns:
        Licença revogada ou None se não encontrada
    """
    license = await get_license_by_key(db, key)
    
    if not license:
        return None
    
    license.revoked = True
    license.revoked_at = datetime.now(timezone.utc)
    license.revoke_reason = reason or "Revogada pelo administrador"
    license.status = LicenseStatus.CANCELLED
    
    await db.flush()
    await db.refresh(license)
    
    return license


async def reactivate_license(
    db: AsyncSession,
    key: str
) -> Optional[License]:
    """
    Reativa uma licença revogada.
    
    Args:
        db: Sessão do banco de dados
        key: Chave da licença
    
    Returns:
        Licença reativada ou None se não encontrada
    """
    license = await get_license_by_key(db, key)
    
    if not license:
        return None
    
    license.revoked = False
    license.revoked_at = None
    license.revoke_reason = None
    license.status = LicenseStatus.ACTIVE
    
    await db.flush()
    await db.refresh(license)
    
    return license


async def update_license_validation(
    db: AsyncSession,
    key: str,
    machine_id: Optional[str] = None,
    ip_address: Optional[str] = None
) -> Optional[License]:
    """
    Atualiza informações de última validação.
    
    Args:
        db: Sessão do banco de dados
        key: Chave da licença
        machine_id: ID da máquina
        ip_address: Endereço IP
    
    Returns:
        Licença atualizada ou None se não encontrada
    """
    license = await get_license_by_key(db, key)
    
    if not license:
        return None
    
    license.last_validation = datetime.utcnow()
    license.last_validation_ip = ip_address
    
    # Controle de ativações por dispositivo
    if machine_id:
        # Primeira ativação
        if not license.machine_id:
            license.machine_id = machine_id
            license.current_activations = 1
        # Nova máquina diferente da registrada - incrementar contador
        elif license.machine_id != machine_id:
            # Verificar se ainda há slots disponíveis antes de incrementar
            if license.max_activations is None or license.current_activations < license.max_activations:
                license.current_activations = (license.current_activations or 0) + 1
                license.machine_id = machine_id  # Atualizar para última máquina ativa
    
    await db.flush()
    await db.refresh(license)
    
    return license


# ============================================================
# Operações de Log de Validação
# ============================================================

async def log_validation(
    db: AsyncSession,
    license_key: str,
    success: bool,
    message: Optional[str] = None,
    machine_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    app_version: Optional[str] = None
) -> ValidationLog:
    """
    Registra um log de validação.
    
    Args:
        db: Sessão do banco de dados
        license_key: Chave da licença
        success: Se a validação foi bem-sucedida
        message: Mensagem descritiva
        machine_id: ID da máquina
        ip_address: Endereço IP
        user_agent: User agent do cliente
        app_version: Versão da aplicação
    
    Returns:
        Log criado
    """
    log = ValidationLog(
        license_key=license_key.upper(),
        success=success,
        message=message,
        machine_id=machine_id,
        ip_address=ip_address,
        user_agent=user_agent,
        app_version=app_version,
    )
    
    db.add(log)
    await db.flush()
    await db.refresh(log)
    
    return log


async def get_validation_logs(
    db: AsyncSession,
    license_key: str,
    limit: int = 100
) -> List[ValidationLog]:
    """
    Busca logs de validação de uma licença.
    
    Args:
        db: Sessão do banco de dados
        license_key: Chave da licença
        limit: Máximo de registros
    
    Returns:
        Lista de logs
    """
    result = await db.execute(
        select(ValidationLog)
        .where(ValidationLog.license_key == license_key.upper())
        .order_by(ValidationLog.timestamp.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_recent_validations(
    db: AsyncSession,
    hours: int = 24,
    limit: int = 100
) -> List[ValidationLog]:
    """
    Busca validações recentes.
    
    Args:
        db: Sessão do banco de dados
        hours: Últimas N horas
        limit: Máximo de registros
    
    Returns:
        Lista de logs
    """
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    result = await db.execute(
        select(ValidationLog)
        .where(ValidationLog.timestamp >= since)
        .order_by(ValidationLog.timestamp.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


# ============================================================
# Operações de Email Verification
# ============================================================

async def create_verification_token(
    db: AsyncSession,
    user_id: UUID
) -> EmailVerificationToken:
    """
    Cria um novo token de verificação de email.
    
    Args:
        db: Sessão do banco de dados
        user_id: ID do usuário
    
    Returns:
        Token criado
    """
    import uuid
    
    # Gerar token único
    token = str(uuid.uuid4())
    
    # Expiração: 24 horas
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    # Criar token
    verification_token = EmailVerificationToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at
    )
    
    db.add(verification_token)
    await db.flush()
    
    return verification_token


async def get_verification_token(
    db: AsyncSession,
    token: str
) -> Optional[EmailVerificationToken]:
    """
    Busca um token de verificação.
    
    Args:
        db: Sessão do banco de dados
        token: Token de verificação
    
    Returns:
        Token encontrado ou None
    """
    result = await db.execute(
        select(EmailVerificationToken).where(EmailVerificationToken.token == token)
    )
    return result.scalar_one_or_none()


async def mark_token_as_used(
    db: AsyncSession,
    token: str
) -> bool:
    """
    Marca um token como usado.
    
    Args:
        db: Sessão do banco de dados
        token: Token de verificação
    
    Returns:
        True se marcado com sucesso
    """
    result = await db.execute(
        update(EmailVerificationToken)
        .where(EmailVerificationToken.token == token)
        .values(used_at=datetime.utcnow())
    )
    await db.flush()
    return result.rowcount > 0


async def invalidate_old_tokens(
    db: AsyncSession,
    user_id: UUID
) -> int:
    """
    Invalida todos os tokens antigos de um usuário.
    
    Args:
        db: Sessão do banco de dados
        user_id: ID do usuário
    
    Returns:
        Número de tokens invalidados
    """
    result = await db.execute(
        update(EmailVerificationToken)
        .where(
            EmailVerificationToken.user_id == user_id,
            EmailVerificationToken.used_at.is_(None)
        )
        .values(used_at=datetime.utcnow())
    )
    await db.flush()
    return result.rowcount

