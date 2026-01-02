"""
Endpoints para Jobs Internos (Cloud Run Jobs)
Estes endpoints são protegidos por token interno e não devem ser expostos publicamente
"""

import os
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..services.remeasurement_service import RemeasurementService
from ..services.contract_expiration_service import ContractExpirationService
from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/internal/jobs", tags=["Jobs Internos"])


def verify_internal_token(x_internal_token: str = Header(...)):
    """
    Verifica o token interno para autorização de jobs.
    O token deve ser configurado como variável de ambiente.
    """
    expected_token = os.getenv("INTERNAL_JOB_TOKEN", settings.ADMIN_TOKEN)

    if not expected_token:
        logger.error("INTERNAL_JOB_TOKEN não configurado")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token interno não configurado"
        )

    if x_internal_token != expected_token:
        logger.warning("Tentativa de acesso a job com token inválido")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

    return True


@router.post(
    "/remeasurement",
    summary="Executar Remensuração Automática",
    description="Executa o job de remensuração automática para todos os contratos elegíveis"
)
async def run_remeasurement_job(
    _: bool = Depends(verify_internal_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint para execução do job de remensuração automática.

    Este endpoint é chamado pelo Cloud Run Job agendado mensalmente.
    Protegido por token interno.
    """
    logger.info("Iniciando job de remensuração via endpoint")

    try:
        result = await RemeasurementService.run_remeasurement_job(db)

        logger.info(
            f"Job finalizado: {result['contracts_remeasured']} contratos remensurados"
        )

        return {
            "success": True,
            "message": "Job de remensuração executado com sucesso",
            "result": result
        }

    except Exception as e:
        logger.error(f"Erro no job de remensuração: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao executar job: {str(e)}"
        )


@router.get(
    "/health",
    summary="Health Check do Job",
    description="Verifica se o serviço de jobs está funcionando"
)
async def jobs_health():
    """Health check simples para verificar se o endpoint está acessível"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "jobs"
    }


@router.post(
    "/cleanup-notifications",
    summary="Limpar Notificações Antigas",
    description="Remove notificações lidas com mais de 90 dias"
)
async def cleanup_old_notifications(
    days: int = 90,
    _: bool = Depends(verify_internal_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Limpa notificações antigas do banco de dados.

    Args:
        days: Notificações lidas mais antigas que X dias serão deletadas
    """
    from ..services.notification_service import NotificationService

    logger.info(f"Iniciando limpeza de notificações antigas (>{days} dias)")

    try:
        deleted_count = await NotificationService.delete_old_notifications(db, days)

        return {
            "success": True,
            "message": f"Limpeza concluída: {deleted_count} notificações removidas",
            "deleted_count": deleted_count
        }

    except Exception as e:
        logger.error(f"Erro na limpeza de notificações: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na limpeza: {str(e)}"
        )


@router.post(
    "/check-expiring-contracts",
    summary="Verificar Contratos Vencendo",
    description="Verifica contratos próximos do vencimento e cria notificações"
)
async def check_expiring_contracts(
    days_ahead: int = 30,
    _: bool = Depends(verify_internal_token),
    db: AsyncSession = Depends(get_db)
):
    """
    Verifica contratos que vencem nos próximos X dias e cria notificações.

    Args:
        days_ahead: Quantos dias à frente verificar (padrão: 30)
    """
    logger.info(f"Iniciando verificação de contratos vencendo (próximos {days_ahead} dias)")

    try:
        result = await ContractExpirationService.check_and_notify_expiring_contracts(
            db, days_ahead
        )

        return {
            "success": True,
            "message": "Verificação de contratos vencendo concluída",
            "result": result
        }

    except Exception as e:
        logger.error(f"Erro na verificação de contratos vencendo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao verificar contratos: {str(e)}"
        )
