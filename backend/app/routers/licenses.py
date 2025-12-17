"""
Endpoints públicos de licença
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import LicenseStatus
from ..schemas import (
    LicenseValidateRequest,
    ValidationSuccessResponse,
    ValidationErrorResponse,
    CheckLicenseResponse,
    LicenseData,
    LicenseFeatures,
    LicenseTypeEnum,
)
from ..auth import create_access_token, get_current_license
from .. import crud

router = APIRouter(prefix="/api", tags=["Licenses"])


def get_client_ip(request: Request) -> str:
    """Obtém o IP do cliente da requisição"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post(
    "/validate-license",
    response_model=ValidationSuccessResponse,
    responses={
        400: {"model": ValidationErrorResponse},
        403: {"model": ValidationErrorResponse},
        404: {"model": ValidationErrorResponse},
    },
    summary="Validar chave de licença",
    description="Valida uma chave de licença e retorna um token JWT para autenticação"
)
async def validate_license(
    request: Request,
    body: LicenseValidateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Valida uma chave de licença.
    
    - **key**: Chave da licença (obrigatório)
    - **machine_id**: ID único da máquina (opcional, usado para controle de ativações)
    - **app_version**: Versão da aplicação (opcional, para logs)
    
    Retorna um token JWT se a licença for válida.
    """
    key = body.key.upper().strip()
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")[:500]
    
    # Buscar licença
    license = await crud.get_license_by_key(db, key)
    
    if not license:
        # Log de tentativa com chave inválida
        await crud.log_validation(
            db,
            license_key=key,
            success=False,
            message="Chave não encontrada",
            machine_id=body.machine_id,
            ip_address=ip_address,
            user_agent=user_agent,
            app_version=body.app_version
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chave de licença não encontrada"
        )
    
    # Verificar se está revogada
    if license.revoked:
        await crud.log_validation(
            db,
            license_key=key,
            success=False,
            message="Licença revogada",
            machine_id=body.machine_id,
            ip_address=ip_address,
            user_agent=user_agent,
            app_version=body.app_version
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta licença foi revogada. Entre em contato com o suporte."
        )
    
    # Verificar status
    if license.status != LicenseStatus.ACTIVE:
        await crud.log_validation(
            db,
            license_key=key,
            success=False,
            message=f"Status: {license.status.value}",
            machine_id=body.machine_id,
            ip_address=ip_address,
            user_agent=user_agent,
            app_version=body.app_version
        )
        status_messages = {
            LicenseStatus.SUSPENDED: "Licença suspensa. Verifique seu pagamento.",
            LicenseStatus.EXPIRED: "Licença expirada. Renove sua assinatura.",
            LicenseStatus.CANCELLED: "Licença cancelada. Entre em contato com o suporte.",
        }
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=status_messages.get(license.status, "Licença inválida")
        )
    
    # Verificar expiração
    if license.expires_at and datetime.utcnow() > license.expires_at:
        # Atualizar status para expirado
        await crud.update_license_status(db, key, LicenseStatus.EXPIRED)
        
        await crud.log_validation(
            db,
            license_key=key,
            success=False,
            message="Licença expirada",
            machine_id=body.machine_id,
            ip_address=ip_address,
            user_agent=user_agent,
            app_version=body.app_version
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Licença expirada em {license.expires_at.strftime('%d/%m/%Y')}. Renove sua assinatura."
        )
    
    # Verificar limite de ativações por machine_id
    if body.machine_id:
        if license.machine_id and license.machine_id != body.machine_id:
            if license.current_activations >= license.max_activations:
                await crud.log_validation(
                    db,
                    license_key=key,
                    success=False,
                    message="Limite de ativações excedido",
                    machine_id=body.machine_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    app_version=body.app_version
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Esta licença já está em uso em outro dispositivo. Máximo de ativações atingido."
                )
    
    # Atualizar informações de validação
    await crud.update_license_validation(
        db,
        key=key,
        machine_id=body.machine_id,
        ip_address=ip_address
    )
    
    # Log de sucesso
    await crud.log_validation(
        db,
        license_key=key,
        success=True,
        message="Validação bem-sucedida",
        machine_id=body.machine_id,
        ip_address=ip_address,
        user_agent=user_agent,
        app_version=body.app_version
    )
    
    # Gerar token JWT
    token_data = {
        "key": license.key,
        "customer_name": license.customer_name,
        "license_type": license.license_type.value,
    }
    token = create_access_token(token_data)
    
    # Preparar features
    features = license.features
    license_features = LicenseFeatures(
        max_contracts=features["max_contracts"],
        export_excel=features["export_excel"],
        export_csv=features["export_csv"],
        support=features["support"],
        multi_user=features["multi_user"]
    )
    
    # Preparar resposta
    license_data = LicenseData(
        customer_name=license.customer_name,
        license_type=LicenseTypeEnum(license.license_type.value),
        expires_at=license.expires_at,
        features=license_features
    )
    
    return ValidationSuccessResponse(
        valid=True,
        token=token,
        data=license_data
    )


@router.post(
    "/check-license",
    response_model=CheckLicenseResponse,
    summary="Verificar status do token",
    description="Verifica se o token JWT ainda é válido e retorna o status da licença"
)
async def check_license(
    license_data: dict = Depends(get_current_license),
    db: AsyncSession = Depends(get_db)
):
    """
    Verifica o status de uma licença usando o token JWT.
    
    Requer header: `Authorization: Bearer <token>`
    
    Retorna o status atual da licença.
    """
    key = license_data.get("key")
    
    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    
    # Buscar licença
    license = await crud.get_license_by_key(db, key)
    
    if not license:
        return CheckLicenseResponse(
            valid=False,
            message="Licença não encontrada"
        )
    
    # Verificar se ainda está válida
    if license.revoked or license.status != LicenseStatus.ACTIVE:
        return CheckLicenseResponse(
            valid=False,
            status=license.status,
            message="Licença revogada ou inativa"
        )
    
    # Verificar expiração
    if license.expires_at and datetime.utcnow() > license.expires_at:
        await crud.update_license_status(db, key, LicenseStatus.EXPIRED)
        return CheckLicenseResponse(
            valid=False,
            status=LicenseStatus.EXPIRED,
            expires_at=license.expires_at,
            message="Licença expirada"
        )
    
    return CheckLicenseResponse(
        valid=True,
        status=license.status,
        expires_at=license.expires_at
    )

