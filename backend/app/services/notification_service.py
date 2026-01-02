"""
Serviço de Notificações
Gerencia criação, listagem e marcação de notificações para usuários
"""

import json
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Notification, NotificationType, User
from .email_service import EmailService

logger = logging.getLogger(__name__)


class NotificationService:
    """Serviço para gerenciar notificações de usuários"""

    @staticmethod
    async def create_notification(
        db: AsyncSession,
        user_id: UUID,
        notification_type: NotificationType,
        title: str,
        message: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        metadata: Optional[dict] = None,
        send_email: bool = True,
    ) -> Notification:
        """
        Cria uma nova notificação para um usuário.

        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário destinatário
            notification_type: Tipo da notificação
            title: Título da notificação
            message: Mensagem detalhada
            entity_type: Tipo da entidade relacionada (opcional)
            entity_id: ID da entidade relacionada (opcional)
            metadata: Metadados adicionais em JSON (opcional)
            send_email: Se True, envia email ao usuário (padrão: True)

        Returns:
            Notification: Notificação criada
        """
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
            extra_data=json.dumps(metadata) if metadata else None,
            read=False,
        )

        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        logger.info(
            f"Notificação criada: user_id={user_id}, type={notification_type.value}"
        )

        # Enviar email se solicitado
        if send_email:
            try:
                # Buscar usuário para obter email
                user_result = await db.execute(select(User).where(User.id == user_id))
                user = user_result.scalar_one_or_none()

                if user and user.email:
                    # Gerar template de email baseado no tipo
                    html_content, text_content = (
                        NotificationService._generate_email_template(
                            notification_type=notification_type,
                            title=title,
                            message=message,
                            metadata=metadata,
                            entity_type=entity_type,
                            entity_id=entity_id,
                        )
                    )

                    subject = title
                    await EmailService.send_email(
                        to_email=user.email,
                        subject=subject,
                        html_content=html_content,
                        text_content=text_content,
                    )
                    logger.info(
                        f"Email enviado para {user.email} sobre notificação {notification.id}"
                    )
            except Exception as e:
                # Não falhar a criação da notificação se o email falhar
                logger.error(
                    f"Erro ao enviar email para notificação {notification.id}: {e}"
                )

        return notification

    @staticmethod
    async def get_user_notifications(
        db: AsyncSession,
        user_id: UUID,
        unread_only: bool = False,
        notification_type: Optional[NotificationType] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[Notification], int, int]:
        """
        Lista notificações do usuário.

        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            unread_only: Se True, retorna apenas não lidas
            notification_type: Filtrar por tipo (opcional)
            limit: Limite de resultados
            offset: Offset para paginação

        Returns:
            tuple: (lista de notificações, total, não lidas)
        """
        # Query base
        query = select(Notification).where(Notification.user_id == user_id)

        # Filtros opcionais
        if unread_only:
            query = query.where(Notification.read == False)  # noqa: E712

        if notification_type:
            query = query.where(Notification.notification_type == notification_type)

        # Ordenar por data de criação (mais recentes primeiro)
        query = query.order_by(Notification.created_at.desc())

        # Aplicar paginação
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        notifications = list(result.scalars().all())

        # Contar total
        count_query = select(func.count(Notification.id)).where(
            Notification.user_id == user_id
        )
        if notification_type:
            count_query = count_query.where(
                Notification.notification_type == notification_type
            )

        total = await db.scalar(count_query) or 0

        # Contar não lidas
        unread_count = (
            await db.scalar(
                select(func.count(Notification.id)).where(
                    Notification.user_id == user_id,
                    Notification.read == False,  # noqa: E712
                )
            )
            or 0
        )

        return notifications, total, unread_count

    @staticmethod
    async def mark_as_read(
        db: AsyncSession, user_id: UUID, notification_ids: List[UUID]
    ) -> int:
        """
        Marca notificações como lidas.

        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário (para segurança)
            notification_ids: Lista de IDs das notificações

        Returns:
            int: Quantidade de notificações atualizadas
        """
        result = await db.execute(
            update(Notification)
            .where(
                Notification.id.in_(notification_ids),
                Notification.user_id == user_id,
                Notification.read == False,  # noqa: E712
            )
            .values(read=True, read_at=datetime.utcnow())
        )

        await db.commit()

        count = result.rowcount
        logger.info(f"Marcadas {count} notificações como lidas para user_id={user_id}")
        return count

    @staticmethod
    async def mark_all_as_read(db: AsyncSession, user_id: UUID) -> int:
        """
        Marca todas as notificações do usuário como lidas.

        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário

        Returns:
            int: Quantidade de notificações atualizadas
        """
        result = await db.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.read == False,  # noqa: E712
            )
            .values(read=True, read_at=datetime.utcnow())
        )

        await db.commit()

        count = result.rowcount
        logger.info(f"Marcadas {count} notificações como lidas para user_id={user_id}")
        return count

    @staticmethod
    async def get_unread_count(db: AsyncSession, user_id: UUID) -> int:
        """
        Retorna contagem de notificações não lidas.

        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário

        Returns:
            int: Quantidade de notificações não lidas
        """
        count = await db.scalar(
            select(func.count(Notification.id)).where(
                Notification.user_id == user_id,
                Notification.read == False,  # noqa: E712
            )
        )
        return count or 0

    @staticmethod
    async def delete_notification(
        db: AsyncSession, user_id: UUID, notification_id: UUID
    ) -> bool:
        """
        Deleta uma notificação.

        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário (para segurança)
            notification_id: ID da notificação

        Returns:
            bool: True se deletou, False se não encontrou
        """
        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id, Notification.user_id == user_id
            )
        )
        notification = result.scalar_one_or_none()

        if notification:
            await db.delete(notification)
            await db.commit()
            logger.info(
                f"Notificação {notification_id} deletada para user_id={user_id}"
            )
            return True

        return False

    @staticmethod
    async def delete_old_notifications(db: AsyncSession, days_old: int = 90) -> int:
        """
        Deleta notificações antigas (lidas) para limpeza.

        Args:
            db: Sessão do banco de dados
            days_old: Deletar notificações mais antigas que X dias

        Returns:
            int: Quantidade de notificações deletadas
        """
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        result = await db.execute(
            select(Notification).where(
                Notification.read == True,  # noqa: E712
                Notification.created_at < cutoff_date,
            )
        )
        old_notifications = result.scalars().all()

        count = len(old_notifications)
        for notification in old_notifications:
            await db.delete(notification)

        await db.commit()

        logger.info(f"Deletadas {count} notificações antigas (>{days_old} dias)")
        return count

    # ==========================================================================
    # Métodos de conveniência para tipos específicos de notificações
    # ==========================================================================

    @staticmethod
    async def notify_contract_expiring(
        db: AsyncSession,
        user_id: UUID,
        contract_id: UUID,
        contract_name: str,
        days_until_expiry: int,
    ) -> Notification:
        """Cria notificação de contrato próximo do vencimento"""
        return await NotificationService.create_notification(
            db=db,
            user_id=user_id,
            notification_type=NotificationType.CONTRACT_EXPIRING,
            title=f"Contrato '{contract_name}' próximo do vencimento",
            message=f"O contrato '{contract_name}' vence em {days_until_expiry} dias. Verifique se é necessário renovar ou encerrar o contrato.",
            entity_type="contract",
            entity_id=contract_id,
            metadata={"days_until_expiry": days_until_expiry},
        )

    @staticmethod
    async def notify_remeasurement_done(
        db: AsyncSession,
        user_id: UUID,
        contract_id: UUID,
        contract_name: str,
        version_number: int,
        index_type: str,
        old_value: float,
        new_value: float,
    ) -> Notification:
        """Cria notificação de remensuração automática realizada"""
        return await NotificationService.create_notification(
            db=db,
            user_id=user_id,
            notification_type=NotificationType.REMEASUREMENT_DONE,
            title=f"Remensuração automática: {contract_name}",
            message=f"O contrato '{contract_name}' foi remensurado automaticamente com base na variação do índice {index_type.upper()}. Nova versão #{version_number} criada.",
            entity_type="contract",
            entity_id=contract_id,
            metadata={
                "version_number": version_number,
                "index_type": index_type,
                "old_value": old_value,
                "new_value": new_value,
            },
        )

    @staticmethod
    async def notify_index_updated(
        db: AsyncSession,
        user_id: UUID,
        index_type: str,
        reference_date: str,
        value: str,
    ) -> Notification:
        """Cria notificação de índice econômico atualizado"""
        return await NotificationService.create_notification(
            db=db,
            user_id=user_id,
            notification_type=NotificationType.INDEX_UPDATED,
            title=f"Índice {index_type.upper()} atualizado",
            message=f"O índice {index_type.upper()} de {reference_date} foi atualizado para {value}%.",
            metadata={
                "index_type": index_type,
                "reference_date": reference_date,
                "value": value,
            },
        )

    @staticmethod
    async def notify_license_expiring(
        db: AsyncSession, user_id: UUID, license_id: UUID, days_until_expiry: int
    ) -> Notification:
        """Cria notificação de licença próxima do vencimento"""
        return await NotificationService.create_notification(
            db=db,
            user_id=user_id,
            notification_type=NotificationType.LICENSE_EXPIRING,
            title="Sua licença está próxima do vencimento",
            message=f"Sua licença expira em {days_until_expiry} dias. Renove para continuar tendo acesso ao sistema.",
            entity_type="license",
            entity_id=license_id,
            metadata={"days_until_expiry": days_until_expiry},
        )

    @staticmethod
    async def notify_system_alert(
        db: AsyncSession, user_id: UUID, title: str, message: str
    ) -> Notification:
        """Cria notificação de alerta do sistema"""
        return await NotificationService.create_notification(
            db=db,
            user_id=user_id,
            notification_type=NotificationType.SYSTEM_ALERT,
            title=title,
            message=message,
        )

    # ==========================================================================
    # Métodos auxiliares para templates de email
    # ==========================================================================

    @staticmethod
    def _generate_email_template(
        notification_type: NotificationType,
        title: str,
        message: str,
        metadata: Optional[dict] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
    ) -> tuple[str, str]:
        """
        Gera template de email HTML e texto baseado no tipo de notificação.

        Returns:
            tuple: (html_content, text_content)
        """
        from ..config import get_settings

        settings = get_settings()
        frontend_url = settings.FRONTEND_URL

        # URL base para links
        if entity_type == "contract" and entity_id:
            # Se for remensuração, adicionar parâmetro de versão
            if notification_type == NotificationType.REMEASUREMENT_DONE and metadata:
                version_number = metadata.get("version_number")
                if version_number:
                    contract_url = f"{frontend_url}/contracts.html?contract_id={entity_id}&version={version_number}"
                else:
                    contract_url = (
                        f"{frontend_url}/contracts.html?contract_id={entity_id}"
                    )
            else:
                contract_url = f"{frontend_url}/contracts.html?contract_id={entity_id}"
        else:
            contract_url = f"{frontend_url}/notifications.html"

        # Template base HTML
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7fa;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 600px; border-collapse: collapse; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); padding: 40px; border-radius: 12px 12px 0 0; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600;">
                                IFRS 16
                            </h1>
                            <p style="color: #a8c5e2; margin: 10px 0 0 0; font-size: 14px;">
                                Sistema de Gestão de Arrendamentos
                            </p>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <h2 style="color: #1e3a5f; margin: 0 0 20px 0; font-size: 22px;">
                                {title}
                            </h2>
                            <p style="color: #4a5568; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                {message}
                            </p>
                            {{extra_content}}
                            <!-- CTA Button -->
                            <table role="presentation" style="width: 100%; margin: 30px 0;">
                                <tr>
                                    <td align="center">
                                        <a href="{contract_url}"
                                           style="display: inline-block; background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 8px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 6px rgba(30, 58, 95, 0.3);">
                                            Ver Detalhes
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8fafc; padding: 30px 40px; border-radius: 0 0 12px 12px; text-align: center;">
                            <p style="color: #718096; font-size: 14px; margin: 0 0 10px 0;">
                                Precisa de ajuda? Entre em contato conosco.
                            </p>
                            <p style="color: #a0aec0; font-size: 12px; margin: 0;">
                                © 2025 IFRS 16 - Sistema de Gestão de Arrendamentos
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """

        # Conteúdo extra baseado no tipo
        extra_content = ""
        if notification_type == NotificationType.CONTRACT_EXPIRING and metadata:
            days = metadata.get("days_until_expiry", 0)
            extra_content = f"""
                            <table role="presentation" style="width: 100%; background-color: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 0 8px 8px 0; margin: 20px 0;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="color: #92400e; font-size: 14px; margin: 0;">
                                            <strong>⚠️ Atenção:</strong> Este contrato vence em <strong>{days} dias</strong>. 
                                            Verifique se é necessário renovar ou encerrar o contrato.
                                        </p>
                                    </td>
                                </tr>
                            </table>
            """
        elif notification_type == NotificationType.REMEASUREMENT_DONE and metadata:
            index_type = metadata.get("index_type", "").upper()
            old_value = metadata.get("old_value", 0)
            new_value = metadata.get("new_value", 0)
            version = metadata.get("version_number", 0)
            extra_content = f"""
                            <table role="presentation" style="width: 100%; background-color: #dbeafe; border-left: 4px solid #3b82f6; border-radius: 0 8px 8px 0; margin: 20px 0;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="color: #1e40af; font-size: 14px; margin: 0 0 10px 0;">
                                            <strong>📊 Detalhes da Remensuração:</strong>
                                        </p>
                                        <p style="color: #1e40af; font-size: 14px; margin: 5px 0;">
                                            <strong>Índice:</strong> {index_type}
                                        </p>
                                        <p style="color: #1e40af; font-size: 14px; margin: 5px 0;">
                                            <strong>Valor Anterior:</strong> {old_value:.4f}%
                                        </p>
                                        <p style="color: #1e40af; font-size: 14px; margin: 5px 0;">
                                            <strong>Novo Valor:</strong> {new_value:.4f}%
                                        </p>
                                        <p style="color: #1e40af; font-size: 14px; margin: 5px 0;">
                                            <strong>Nova Versão:</strong> #{version}
                                        </p>
                                    </td>
                                </tr>
                            </table>
            """
        elif notification_type == NotificationType.INDEX_UPDATED and metadata:
            index_type = metadata.get("index_type", "").upper()
            reference_date = metadata.get("reference_date", "")
            value = metadata.get("value", "")
            extra_content = f"""
                            <table role="presentation" style="width: 100%; background-color: #dbeafe; border-left: 4px solid #3b82f6; border-radius: 0 8px 8px 0; margin: 20px 0;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="color: #1e40af; font-size: 14px; margin: 0 0 10px 0;">
                                            <strong>📈 Índice Atualizado:</strong>
                                        </p>
                                        <p style="color: #1e40af; font-size: 14px; margin: 5px 0;">
                                            <strong>Tipo:</strong> {index_type}
                                        </p>
                                        <p style="color: #1e40af; font-size: 14px; margin: 5px 0;">
                                            <strong>Data de Referência:</strong> {reference_date}
                                        </p>
                                        <p style="color: #1e40af; font-size: 14px; margin: 5px 0;">
                                            <strong>Valor:</strong> {value}%
                                        </p>
                                    </td>
                                </tr>
                            </table>
            """
        elif notification_type == NotificationType.LICENSE_EXPIRING and metadata:
            days = metadata.get("days_until_expiry", 0)
            extra_content = f"""
                            <table role="presentation" style="width: 100%; background-color: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 0 8px 8px 0; margin: 20px 0;">
                                <tr>
                                    <td style="padding: 20px;">
                                        <p style="color: #92400e; font-size: 14px; margin: 0;">
                                            <strong>⚠️ Atenção:</strong> Sua licença expira em <strong>{days} dias</strong>. 
                                            Renove para continuar tendo acesso ao sistema.
                                        </p>
                                    </td>
                                </tr>
                            </table>
            """

        html_content = html_template.replace("{extra_content}", extra_content)

        # Template texto simples
        text_content = f"""
{title}

{message}

{extra_content.replace('<p style="color: #92400e; font-size: 14px; margin: 0;">', '').replace('</p>', '').replace('<strong>', '').replace('</strong>', '').replace('<table role="presentation" style="width: 100%; background-color: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 0 8px 8px 0; margin: 20px 0;">', '').replace('</table>', '').replace('<tr>', '').replace('</tr>', '').replace('<td style="padding: 20px;">', '').replace('</td>', '') if extra_content else ''}

Ver detalhes: {contract_url}

© 2025 IFRS 16 - Sistema de Gestão de Arrendamentos
        """

        return html_content, text_content
