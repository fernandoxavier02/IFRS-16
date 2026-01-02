"""
Endpoints para gerenciamento de notificações
"""

from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..auth import get_current_user_with_session
from ..models import User, NotificationType
from ..services.notification_service import NotificationService
from ..schemas import (
    NotificationResponse,
    NotificationListResponse,
    NotificationMarkReadRequest,
    NotificationMarkReadResponse,
    NotificationCountResponse,
    NotificationTypeEnum
)

router = APIRouter(prefix="/api/notifications", tags=["Notificações"])


def serialize_notification(notification) -> dict:
    """Converte notificação ORM em dict serializável"""
    return {
        "id": str(notification.id),
        "user_id": str(notification.user_id),
        "notification_type": notification.notification_type.value,
        "title": notification.title,
        "message": notification.message,
        "entity_type": notification.entity_type,
        "entity_id": str(notification.entity_id) if notification.entity_id else None,
        "metadata": notification.extra_data,
        "read": notification.read,
        "read_at": notification.read_at.isoformat() if notification.read_at else None,
        "created_at": notification.created_at.isoformat() if notification.created_at else None
    }


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="Listar Notificações",
    description="Lista todas as notificações do usuário autenticado"
)
async def list_notifications(
    unread_only: bool = Query(False, description="Retornar apenas não lidas"),
    notification_type: Optional[str] = Query(None, description="Filtrar por tipo"),
    limit: int = Query(50, ge=1, le=100, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    user_data: dict = Depends(get_current_user_with_session),
    db: AsyncSession = Depends(get_db)
):
    """Lista notificações do usuário"""
    user = user_data["user"]

    # Converter tipo se fornecido
    notif_type = None
    if notification_type:
        try:
            notif_type = NotificationType(notification_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de notificação inválido: {notification_type}"
            )

    notifications, total, unread_count = await NotificationService.get_user_notifications(
        db=db,
        user_id=user.id,
        unread_only=unread_only,
        notification_type=notif_type,
        limit=limit,
        offset=offset
    )

    return {
        "notifications": [serialize_notification(n) for n in notifications],
        "total": total,
        "unread_count": unread_count
    }


@router.get(
    "/count",
    response_model=NotificationCountResponse,
    summary="Contagem de Não Lidas",
    description="Retorna a contagem de notificações não lidas"
)
async def get_unread_count(
    user_data: dict = Depends(get_current_user_with_session),
    db: AsyncSession = Depends(get_db)
):
    """Retorna contagem de notificações não lidas"""
    user = user_data["user"]

    count = await NotificationService.get_unread_count(db, user.id)

    return {"unread_count": count}


@router.post(
    "/mark-read",
    response_model=NotificationMarkReadResponse,
    summary="Marcar como Lidas",
    description="Marca notificações específicas como lidas"
)
async def mark_as_read(
    request: NotificationMarkReadRequest,
    user_data: dict = Depends(get_current_user_with_session),
    db: AsyncSession = Depends(get_db)
):
    """Marca notificações como lidas"""
    user = user_data["user"]

    count = await NotificationService.mark_as_read(
        db=db,
        user_id=user.id,
        notification_ids=request.notification_ids
    )

    return {
        "success": True,
        "marked_count": count
    }


@router.post(
    "/mark-all-read",
    response_model=NotificationMarkReadResponse,
    summary="Marcar Todas como Lidas",
    description="Marca todas as notificações do usuário como lidas"
)
async def mark_all_as_read(
    user_data: dict = Depends(get_current_user_with_session),
    db: AsyncSession = Depends(get_db)
):
    """Marca todas as notificações como lidas"""
    user = user_data["user"]

    count = await NotificationService.mark_all_as_read(db, user.id)

    return {
        "success": True,
        "marked_count": count
    }


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir Notificação",
    description="Exclui uma notificação específica"
)
async def delete_notification(
    notification_id: UUID,
    user_data: dict = Depends(get_current_user_with_session),
    db: AsyncSession = Depends(get_db)
):
    """Exclui uma notificação"""
    user = user_data["user"]

    deleted = await NotificationService.delete_notification(
        db=db,
        user_id=user.id,
        notification_id=notification_id
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificação não encontrada"
        )

    return None
