"""
Testes unitários para o serviço de notificações
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from app.models import Notification, NotificationType, User
from app.services.notification_service import NotificationService
from app.services.email_service import EmailService


@pytest.mark.asyncio
class TestNotificationService:
    """Testes para NotificationService"""

    async def test_create_notification(self, db_session, test_user):
        """Testa criação de notificação básica"""
        notification = await NotificationService.create_notification(
            db=db_session,
            user_id=test_user.id,
            notification_type=NotificationType.SYSTEM_ALERT,
            title="Teste",
            message="Mensagem de teste",
            send_email=False  # Não enviar email nos testes
        )

        assert notification is not None
        assert notification.user_id == test_user.id
        assert notification.notification_type == NotificationType.SYSTEM_ALERT
        assert notification.title == "Teste"
        assert notification.message == "Mensagem de teste"
        assert notification.read is False

    async def test_create_notification_with_email(self, db_session, test_user):
        """Testa criação de notificação com envio de email"""
        with patch.object(EmailService, 'send_email', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            notification = await NotificationService.create_notification(
                db=db_session,
                user_id=test_user.id,
                notification_type=NotificationType.SYSTEM_ALERT,
                title="Teste Email",
                message="Mensagem de teste com email",
                send_email=True
            )

            assert notification is not None
            # Verificar se email foi chamado
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[1]['to_email'] == test_user.email
            assert call_args[1]['subject'] == "Teste Email"

    async def test_get_user_notifications(self, db_session, test_user):
        """Testa listagem de notificações do usuário"""
        # Criar algumas notificações
        for i in range(5):
            await NotificationService.create_notification(
                db=db_session,
                user_id=test_user.id,
                notification_type=NotificationType.SYSTEM_ALERT,
                title=f"Notificação {i}",
                message=f"Mensagem {i}",
                send_email=False
            )

        notifications, total, unread = await NotificationService.get_user_notifications(
            db=db_session,
            user_id=test_user.id
        )

        assert len(notifications) == 5
        assert total == 5
        assert unread == 5

    async def test_mark_as_read(self, db_session, test_user):
        """Testa marcação de notificações como lidas"""
        # Criar notificações
        notification1 = await NotificationService.create_notification(
            db=db_session,
            user_id=test_user.id,
            notification_type=NotificationType.SYSTEM_ALERT,
            title="Teste 1",
            message="Mensagem 1",
            send_email=False
        )

        notification2 = await NotificationService.create_notification(
            db=db_session,
            user_id=test_user.id,
            notification_type=NotificationType.SYSTEM_ALERT,
            title="Teste 2",
            message="Mensagem 2",
            send_email=False
        )

        # Marcar como lidas
        count = await NotificationService.mark_as_read(
            db=db_session,
            user_id=test_user.id,
            notification_ids=[notification1.id, notification2.id]
        )

        assert count == 2

        # Verificar se foram marcadas
        notifications, _, unread = await NotificationService.get_user_notifications(
            db=db_session,
            user_id=test_user.id,
            unread_only=True
        )
        assert unread == 0

    async def test_get_unread_count(self, db_session, test_user):
        """Testa contagem de notificações não lidas"""
        # Criar 3 notificações
        for i in range(3):
            await NotificationService.create_notification(
                db=db_session,
                user_id=test_user.id,
                notification_type=NotificationType.SYSTEM_ALERT,
                title=f"Teste {i}",
                message=f"Mensagem {i}",
                send_email=False
            )

        count = await NotificationService.get_unread_count(
            db=db_session,
            user_id=test_user.id
        )

        assert count == 3

    async def test_notify_contract_expiring(self, db_session, test_user):
        """Testa criação de notificação de contrato vencendo"""
        contract_id = uuid4()
        notification = await NotificationService.notify_contract_expiring(
            db=db_session,
            user_id=test_user.id,
            contract_id=contract_id,
            contract_name="Contrato Teste",
            days_until_expiry=15
        )

        assert notification is not None
        assert notification.notification_type == NotificationType.CONTRACT_EXPIRING
        assert notification.entity_type == "contract"
        assert notification.entity_id == contract_id

    async def test_notify_remeasurement_done(self, db_session, test_user):
        """Testa criação de notificação de remensuração"""
        contract_id = uuid4()
        notification = await NotificationService.notify_remeasurement_done(
            db=db_session,
            user_id=test_user.id,
            contract_id=contract_id,
            contract_name="Contrato Teste",
            version_number=2,
            index_type="IGPM",
            old_value=5.5,
            new_value=6.0
        )

        assert notification is not None
        assert notification.notification_type == NotificationType.REMEASUREMENT_DONE
        assert notification.entity_type == "contract"
        assert notification.entity_id == contract_id

    async def test_delete_old_notifications(self, db_session, test_user):
        """Testa deleção de notificações antigas"""
        # Criar notificação antiga (lida)
        old_notification = Notification(
            id=uuid4(),
            user_id=test_user.id,
            notification_type=NotificationType.SYSTEM_ALERT,
            title="Antiga",
            message="Mensagem antiga",
            read=True,
            created_at=datetime.utcnow() - timedelta(days=100)
        )
        db_session.add(old_notification)
        await db_session.commit()

        # Criar notificação recente (lida)
        recent_notification = Notification(
            id=uuid4(),
            user_id=test_user.id,
            notification_type=NotificationType.SYSTEM_ALERT,
            title="Recente",
            message="Mensagem recente",
            read=True,
            created_at=datetime.utcnow() - timedelta(days=10)
        )
        db_session.add(recent_notification)
        await db_session.commit()

        # Deletar notificações antigas (> 90 dias)
        deleted_count = await NotificationService.delete_old_notifications(
            db=db_session,
            days_old=90
        )

        assert deleted_count >= 1

    async def test_email_template_generation(self):
        """Testa geração de templates de email"""
        html, text = NotificationService._generate_email_template(
            notification_type=NotificationType.CONTRACT_EXPIRING,
            title="Contrato Vencendo",
            message="Seu contrato vence em 15 dias",
            metadata={"days_until_expiry": 15},
            entity_type="contract",
            entity_id=uuid4()
        )

        assert html is not None
        assert text is not None
        assert "Contrato Vencendo" in html
        assert "15 dias" in html
        assert "Contrato Vencendo" in text
