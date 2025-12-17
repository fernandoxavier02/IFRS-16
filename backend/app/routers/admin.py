"""
Endpoints administrativos para gerenciamento de licenças e usuários
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import LicenseStatus
from ..schemas import (
    LicenseCreateRequest,
    LicenseRevokeRequest,
    LicenseReactivateRequest,
    LicenseFullResponse,
    LicenseListResponse,
    AdminActionResponse,
    GenerateLicenseResponse,
    LicenseStatusEnum,
)
from ..auth import get_current_admin, get_superadmin
from .. import crud

# Router com autenticação JWT
router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"]
)


@router.get(
    "/licenses",
    response_model=LicenseListResponse,
    summary="Listar todas as licenças",
    description="Lista todas as licenças com paginação e filtro opcional por status"
)
async def list_licenses(
    skip: int = Query(0, ge=0, description="Registros para pular"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
    status_filter: Optional[LicenseStatusEnum] = Query(None, description="Filtrar por status"),
    admin_data: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todas as licenças cadastradas.
    
    Requer: Token JWT de administrador (Bearer token)
    
    - **skip**: Quantos registros pular (paginação)
    - **limit**: Máximo de registros a retornar
    - **status_filter**: Filtrar por status (active, suspended, expired, cancelled)
    """
    # Converter enum do schema para enum do modelo
    model_status = None
    if status_filter:
        model_status = LicenseStatus(status_filter.value)
    
    licenses = await crud.get_all_licenses(
        db,
        skip=skip,
        limit=limit,
        status_filter=model_status
    )
    
    total = await crud.count_licenses(db, status_filter=model_status)
    
    return LicenseListResponse(
        total=total,
        licenses=[LicenseFullResponse.model_validate(lic) for lic in licenses]
    )


@router.post(
    "/generate-license",
    response_model=GenerateLicenseResponse,
    summary="Gerar nova licença",
    description="Cria uma nova licença para um cliente"
)
async def generate_license(
    body: LicenseCreateRequest,
    admin_data: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Gera uma nova licença.
    
    Requer: Token JWT de administrador (Bearer token)
    
    - **customer_name**: Nome do cliente
    - **email**: Email do cliente
    - **license_type**: Tipo da licença (trial, basic, pro, enterprise)
    - **duration_months**: Duração em meses (null = permanente)
    - **max_activations**: Máximo de ativações permitidas
    """
    try:
        license = await crud.create_license(db, body)
        
        return GenerateLicenseResponse(
            success=True,
            message=f"Licença gerada com sucesso: {license.key}",
            license=LicenseFullResponse.model_validate(license)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar licença: {str(e)}"
        )


@router.post(
    "/revoke-license",
    response_model=AdminActionResponse,
    summary="Revogar licença",
    description="Revoga uma licença existente"
)
async def revoke_license(
    body: LicenseRevokeRequest,
    admin_data: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoga uma licença.
    
    Requer: Token JWT de administrador (Bearer token)
    
    - **key**: Chave da licença a revogar
    - **reason**: Motivo da revogação (opcional)
    
    Após revogada, a licença não poderá mais ser usada até ser reativada.
    """
    license = await crud.revoke_license(db, body.key, body.reason)
    
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Licença não encontrada"
        )
    
    return AdminActionResponse(
        success=True,
        message=f"Licença {body.key} revogada com sucesso",
        key=body.key
    )


@router.post(
    "/reactivate-license",
    response_model=AdminActionResponse,
    summary="Reativar licença",
    description="Reativa uma licença revogada"
)
async def reactivate_license(
    body: LicenseReactivateRequest,
    admin_data: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Reativa uma licença revogada.
    
    Requer: Token JWT de administrador (Bearer token)
    
    - **key**: Chave da licença a reativar
    
    A licença voltará ao status 'active'.
    """
    license = await crud.reactivate_license(db, body.key)
    
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Licença não encontrada"
        )
    
    return AdminActionResponse(
        success=True,
        message=f"Licença {body.key} reativada com sucesso",
        key=body.key
    )


@router.get(
    "/license/{key}",
    response_model=LicenseFullResponse,
    summary="Buscar licença por chave",
    description="Retorna detalhes completos de uma licença"
)
async def get_license(
    key: str,
    admin_data: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Busca uma licença pela chave.
    
    Requer: Token JWT de administrador (Bearer token)
    """
    license = await crud.get_license_by_key(db, key)
    
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Licença não encontrada"
        )
    
    return LicenseFullResponse.model_validate(license)


@router.get(
    "/license/{key}/logs",
    summary="Buscar logs de validação",
    description="Retorna histórico de validações de uma licença"
)
async def get_license_logs(
    key: str,
    limit: int = Query(100, ge=1, le=1000),
    admin_data: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Busca logs de validação de uma licença.
    
    Requer: Token JWT de administrador (Bearer token)
    """
    # Verificar se licença existe
    license = await crud.get_license_by_key(db, key)
    
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Licença não encontrada"
        )
    
    logs = await crud.get_validation_logs(db, key, limit)
    
    return {
        "license_key": key,
        "total": len(logs),
        "logs": [
            {
                "id": str(log.id),
                "timestamp": log.timestamp.isoformat(),
                "success": log.success,
                "message": log.message,
                "machine_id": log.machine_id,
                "ip_address": log.ip_address,
            }
            for log in logs
        ]
    }


@router.delete(
    "/license/{key}",
    response_model=AdminActionResponse,
    summary="Excluir licença",
    description="Remove permanentemente uma licença do sistema"
)
async def delete_license(
    key: str,
    admin_data: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Exclui uma licença permanentemente.
    
    Requer: Token JWT de administrador (Bearer token)
    
    ATENÇÃO: Esta ação não pode ser desfeita!
    """
    license = await crud.get_license_by_key(db, key)
    
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Licença não encontrada"
        )
    
    await db.delete(license)
    await db.flush()
    
    return AdminActionResponse(
        success=True,
        message=f"Licença {key} excluída permanentemente",
        key=key
    )


# =============================================================================
# CRUD DE USUÁRIOS CLIENTES
# =============================================================================

from sqlalchemy import select, func
from ..models import User, AdminUser, Subscription
from ..schemas import (
    UserResponse,
    UserListResponse,
    AdminUserCreate,
    AdminUserUpdate,
    AdminUserResponse,
)
from ..auth import hash_password, get_current_admin, get_superadmin


@router.get(
    "/users",
    response_model=UserListResponse,
    summary="Listar usuários",
    description="Lista todos os usuários clientes"
)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    admin_data: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todos os usuários clientes.
    
    - **skip**: Paginação - registros a pular
    - **limit**: Máximo de registros
    - **is_active**: Filtrar por status ativo
    """
    query = select(User)
    
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    # Contar total
    count_query = select(func.count()).select_from(User)
    if is_active is not None:
        count_query = count_query.where(User.is_active == is_active)
    
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    return UserListResponse(
        total=total,
        users=[UserResponse.model_validate(u) for u in users]
    )


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Detalhes do usuário",
    description="Retorna detalhes de um usuário específico"
)
async def get_user(
    user_id: str,
    admin_data: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna detalhes de um usuário pelo ID.
    """
    from uuid import UUID
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuário inválido"
        )
    
    result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    return UserResponse.model_validate(user)


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Atualizar usuário",
    description="Atualiza dados de um usuário"
)
async def update_user(
    user_id: str,
    is_active: Optional[bool] = Query(None),
    email_verified: Optional[bool] = Query(None),
    admin_data: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza status de um usuário.
    
    - **is_active**: Ativar/desativar usuário
    - **email_verified**: Marcar email como verificado
    """
    from uuid import UUID
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuário inválido"
        )
    
    result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    if is_active is not None:
        user.is_active = is_active
    
    if email_verified is not None:
        user.email_verified = email_verified
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.delete(
    "/users/{user_id}",
    response_model=AdminActionResponse,
    summary="Excluir usuário",
    description="Remove um usuário permanentemente"
)
async def delete_user(
    user_id: str,
    admin_data: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Exclui um usuário permanentemente.
    
    ATENÇÃO: Isto também exclui as licenças e assinaturas do usuário!
    """
    from uuid import UUID
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de usuário inválido"
        )
    
    result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    email = user.email
    await db.delete(user)
    await db.commit()
    
    return AdminActionResponse(
        success=True,
        message=f"Usuário {email} excluído permanentemente"
    )


@router.post(
    "/users/{user_id}/grant-license",
    summary="Conceder licença manual",
    description="Concede uma licença manualmente a um usuário"
)
async def grant_license_to_user(
    user_id: str,
    license_type: LicenseStatusEnum = Query(LicenseStatusEnum.ACTIVE),
    duration_months: Optional[int] = Query(None, ge=1, le=120),
    admin_data: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Concede uma licença manualmente a um usuário.
    
    - **license_type**: Tipo da licença (trial, basic, pro, enterprise)
    - **duration_months**: Duração em meses (null = permanente)
    """
    from datetime import datetime, timedelta
    from ..models import License, LicenseType, LicenseStatus
    import secrets
    import string
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Gerar chave
    chars = string.ascii_uppercase + string.digits
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = ''.join(secrets.choice(chars) for _ in range(8))
    key = f"FX{date_part}-IFRS16-{random_part}"
    
    # Calcular expiração
    expires_at = None
    if duration_months:
        expires_at = datetime.utcnow() + timedelta(days=duration_months * 30)
    
    # Criar licença
    license = License(
        key=key,
        user_id=user.id,
        customer_name=user.name,
        email=user.email,
        license_type=LicenseType.PRO,  # Licenças manuais são PRO por padrão
        status=LicenseStatus.ACTIVE,
        expires_at=expires_at,
        max_activations=3,
    )
    
    db.add(license)
    await db.commit()
    
    return {
        "success": True,
        "message": f"Licença concedida ao usuário {user.email}",
        "license_key": key,
        "expires_at": expires_at.isoformat() if expires_at else None
    }


# =============================================================================
# CRUD DE ADMINISTRADORES
# =============================================================================

@router.get(
    "/admins",
    response_model=list[AdminUserResponse],
    summary="Listar administradores",
    description="Lista todos os administradores (requer superadmin)"
)
async def list_admins(
    admin_data: dict = Depends(get_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista todos os administradores.
    
    Requer: Token JWT de superadmin
    """
    result = await db.execute(
        select(AdminUser).order_by(AdminUser.created_at.desc())
    )
    admins = result.scalars().all()
    
    return [AdminUserResponse.model_validate(a) for a in admins]


@router.post(
    "/admins",
    response_model=AdminUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar administrador",
    description="Cria um novo administrador (requer superadmin)"
)
async def create_admin(
    body: AdminUserCreate,
    admin_data: dict = Depends(get_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """
    Cria um novo administrador.
    
    Requer: Token JWT de superadmin
    """
    from ..models import AdminRole
    
    # Verificar se username já existe
    result = await db.execute(
        select(AdminUser).where(AdminUser.username == body.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username já existe"
        )
    
    # Verificar se email já existe
    result = await db.execute(
        select(AdminUser).where(AdminUser.email == body.email.lower())
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já existe"
        )
    
    admin = AdminUser(
        username=body.username,
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        role=AdminRole(body.role.value),
        is_active=True
    )
    
    db.add(admin)
    await db.commit()
    await db.refresh(admin)
    
    return AdminUserResponse.model_validate(admin)


@router.put(
    "/admins/{admin_id}",
    response_model=AdminUserResponse,
    summary="Atualizar administrador",
    description="Atualiza um administrador (requer superadmin)"
)
async def update_admin(
    admin_id: str,
    body: AdminUserUpdate,
    admin_data: dict = Depends(get_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """
    Atualiza um administrador.
    
    Requer: Token JWT de superadmin
    """
    from ..models import AdminRole
    
    result = await db.execute(
        select(AdminUser).where(AdminUser.id == admin_id)
    )
    admin = result.scalar_one_or_none()
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Administrador não encontrado"
        )
    
    if body.username:
        # Verificar unicidade
        result = await db.execute(
            select(AdminUser).where(
                AdminUser.username == body.username,
                AdminUser.id != admin_id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username já existe"
            )
        admin.username = body.username
    
    if body.email:
        result = await db.execute(
            select(AdminUser).where(
                AdminUser.email == body.email.lower(),
                AdminUser.id != admin_id
            )
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já existe"
            )
        admin.email = body.email.lower()
    
    if body.role:
        admin.role = AdminRole(body.role.value)
    
    if body.is_active is not None:
        admin.is_active = body.is_active
    
    await db.commit()
    await db.refresh(admin)
    
    return AdminUserResponse.model_validate(admin)


@router.delete(
    "/admins/{admin_id}",
    response_model=AdminActionResponse,
    summary="Excluir administrador",
    description="Exclui um administrador (requer superadmin)"
)
async def delete_admin(
    admin_id: str,
    admin_data: dict = Depends(get_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """
    Exclui um administrador.
    
    Requer: Token JWT de superadmin
    """
    # Não permitir excluir a si mesmo
    if admin_data["id"] == admin_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível excluir a si mesmo"
        )
    
    result = await db.execute(
        select(AdminUser).where(AdminUser.id == admin_id)
    )
    admin = result.scalar_one_or_none()
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Administrador não encontrado"
        )
    
    username = admin.username
    await db.delete(admin)
    await db.commit()
    
    return AdminActionResponse(
        success=True,
        message=f"Administrador {username} excluído"
    )

