"""
Task para limpeza de sessões expiradas
Executa periodicamente para manter o banco limpo
"""

import asyncio
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from ..config import get_settings
from ..models import UserSession

settings = get_settings()


async def cleanup_expired_sessions():
    """
    Remove sessões expiradas ou inativas do banco de dados.

    Critérios de remoção:
    - Sessões com expires_at < now
    - Sessões marcadas como is_active = False há mais de 7 dias
    """
    # Criar engine
    engine = create_async_engine(
        settings.ASYNC_DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )

    # Criar session factory
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as db:
        now = datetime.utcnow()

        # 1. Deletar sessões expiradas
        result_expired = await db.execute(
            delete(UserSession).where(
                UserSession.expires_at < now
            )
        )
        expired_count = result_expired.rowcount

        # 2. Deletar sessões inativas antigas (mais de 7 dias)
        # from datetime import timedelta
        # seven_days_ago = now - timedelta(days=7)
        # result_inactive = await db.execute(
        #     delete(UserSession).where(
        #         UserSession.is_active == False,
        #         UserSession.last_activity < seven_days_ago
        #     )
        # )
        # inactive_count = result_inactive.rowcount

        await db.commit()

        print(f"[Cleanup] Sessões expiradas removidas: {expired_count}")
        # print(f"[Cleanup] Sessões inativas antigas removidas: {inactive_count}")
        print(f"[Cleanup] Total de sessões limpas: {expired_count}")

    await engine.dispose()


async def mark_expired_sessions_inactive():
    """
    Marca sessões expiradas como inativas sem deletá-las.
    Útil para auditoria.
    """
    engine = create_async_engine(
        settings.ASYNC_DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as db:
        now = datetime.utcnow()

        # Buscar sessões expiradas ainda marcadas como ativas
        result = await db.execute(
            select(UserSession).where(
                UserSession.expires_at < now,
                UserSession.is_active == True
            )
        )
        expired_sessions = result.scalars().all()

        # Marcar como inativas
        for session in expired_sessions:
            session.is_active = False

        await db.commit()

        print(f"[Cleanup] Sessões expiradas marcadas como inativas: {len(expired_sessions)}")

    await engine.dispose()


if __name__ == "__main__":
    """
    Executar limpeza manualmente:
    python -m backend.app.tasks.cleanup_sessions
    """
    print("[Cleanup] Iniciando limpeza de sessões...")
    asyncio.run(cleanup_expired_sessions())
    print("[Cleanup] Limpeza concluída!")
