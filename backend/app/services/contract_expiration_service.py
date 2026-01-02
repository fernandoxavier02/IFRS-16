"""
Serviço para verificar contratos próximos do vencimento
"""

import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Contract, User, NotificationType
from sqlalchemy import text
from .notification_service import NotificationService

logger = logging.getLogger(__name__)


class ContractExpirationService:
    """Serviço para verificar contratos próximos do vencimento"""

    @staticmethod
    async def get_contracts_expiring_soon(
        db: AsyncSession,
        days_ahead: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Busca contratos que vencem nos próximos X dias.

        Args:
            db: Sessão do banco de dados
            days_ahead: Quantos dias à frente verificar (padrão: 30)

        Returns:
            Lista de dicionários com informações dos contratos vencendo
        """
        from dateutil.relativedelta import relativedelta

        today = date.today()
        future_date = today + timedelta(days=days_ahead)

        # Buscar contratos ativos
        contracts_query = select(Contract).where(
            and_(
                Contract.status == "active",
                Contract.is_deleted == False
            )
        )
        contracts_result = await db.execute(contracts_query)
        contracts = contracts_result.scalars().all()

        expiring_contracts = []

        for contract in contracts:
            # Buscar versão mais recente do contrato usando SQL direto
            version_query = text("""
                SELECT data_inicio, prazo_meses, version_number
                FROM contract_versions
                WHERE contract_id = :contract_id
                ORDER BY version_number DESC
                LIMIT 1
            """)
            version_result = await db.execute(version_query, {"contract_id": str(contract.id)})
            version_row = version_result.first()

            if not version_row or not version_row.data_inicio or not version_row.prazo_meses:
                continue

            # Calcular data de vencimento
            if isinstance(version_row.data_inicio, date):
                start_date = version_row.data_inicio
            elif isinstance(version_row.data_inicio, datetime):
                start_date = version_row.data_inicio.date()
            else:
                continue

            # Calcular data de vencimento (data_inicio + prazo_meses)
            end_date = start_date + relativedelta(months=version_row.prazo_meses)

            # Verificar se está no período de alerta
            if today <= end_date <= future_date:
                days_until_expiry = (end_date - today).days

                # Buscar dados do usuário
                user_result = await db.execute(
                    select(User).where(User.id == contract.user_id)
                )
                user = user_result.scalar_one_or_none()

                if user:
                    expiring_contracts.append({
                        "contract_id": contract.id,
                        "contract_name": contract.name,
                        "user_id": contract.user_id,
                        "user_email": user.email,
                        "user_name": user.name,
                        "end_date": end_date,
                        "days_until_expiry": days_until_expiry,
                        "version_number": version_row.version_number
                    })

        return expiring_contracts

    @staticmethod
    async def check_and_notify_expiring_contracts(
        db: AsyncSession,
        days_ahead: int = 30
    ) -> Dict[str, Any]:
        """
        Verifica contratos vencendo e cria notificações.

        Args:
            db: Sessão do banco de dados
            days_ahead: Quantos dias à frente verificar (padrão: 30)

        Returns:
            Dicionário com estatísticas do processamento
        """
        logger.info(f"Iniciando verificação de contratos vencendo (próximos {days_ahead} dias)")

        expiring_contracts = await ContractExpirationService.get_contracts_expiring_soon(
            db, days_ahead
        )

        notifications_created = 0
        errors = []

        for contract_info in expiring_contracts:
            try:
                # Verificar se já existe notificação recente para este contrato
                # (evitar spam de notificações - verificar últimos 7 dias)
                from ..models import Notification
                cutoff_date = datetime.utcnow() - timedelta(days=7)

                existing_query = select(func.count(Notification.id)).where(
                    and_(
                        Notification.user_id == contract_info["user_id"],
                        Notification.notification_type == NotificationType.CONTRACT_EXPIRING,
                        Notification.entity_id == contract_info["contract_id"],
                        Notification.created_at >= cutoff_date
                    )
                )
                existing_count = await db.scalar(existing_query) or 0

                # Se já existe notificação recente, pular
                if existing_count > 0:
                    logger.debug(
                        f"Notificação já existe para contrato {contract_info['contract_name']} "
                        f"(últimos 7 dias), pulando..."
                    )
                    continue

                # Criar notificação
                await NotificationService.notify_contract_expiring(
                    db=db,
                    user_id=contract_info["user_id"],
                    contract_id=contract_info["contract_id"],
                    contract_name=contract_info["contract_name"],
                    days_until_expiry=contract_info["days_until_expiry"]
                )

                notifications_created += 1
                logger.info(
                    f"Notificação criada para contrato {contract_info['contract_name']} "
                    f"(vence em {contract_info['days_until_expiry']} dias)"
                )

            except Exception as e:
                error_msg = f"Erro ao criar notificação para contrato {contract_info['contract_id']}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        result = {
            "contracts_checked": len(expiring_contracts),
            "notifications_created": notifications_created,
            "errors": errors
        }

        logger.info(
            f"Verificação concluída: {notifications_created} notificações criadas, "
            f"{len(errors)} erros"
        )

        return result
