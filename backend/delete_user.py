"""
Script para deletar usuário do banco de dados
"""
import asyncio
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models import User, UserSession, Subscription, Contract

settings = get_settings()


async def delete_user(email: str):
    """Deleta usuário e todos os dados relacionados"""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True,
        pool_pre_ping=True
    )

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as db:
        # Buscar usuário
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if not user:
            print(f"[X] Usuario {email} nao encontrado!")
            return

        print(f"[OK] Usuario encontrado: {user.name} ({user.email})")
        user_id = user.id

        # Deletar sessões
        result = await db.execute(
            delete(UserSession).where(UserSession.user_id == user_id)
        )
        print(f"[DELETE] Sessoes deletadas: {result.rowcount}")

        # Deletar assinaturas
        result = await db.execute(
            delete(Subscription).where(Subscription.user_id == user_id)
        )
        print(f"[DELETE] Assinaturas deletadas: {result.rowcount}")

        # Deletar contratos (se existir)
        try:
            result = await db.execute(
                delete(Contract).where(Contract.user_id == user_id)
            )
            print(f"[DELETE] Contratos deletados: {result.rowcount}")
        except Exception as e:
            print(f"[WARN] Tabela contracts nao existe ou erro: {e}")

        # Deletar usuário
        await db.delete(user)
        await db.commit()

        print(f"[SUCCESS] Usuario {email} deletado com sucesso!")

    await engine.dispose()


async def check_user(email: str):
    """Verifica se usuário existe no banco"""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as db:
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if user:
            print(f"[OK] Usuario encontrado!")
            print(f"    ID: {user.id}")
            print(f"    Email: {user.email}")
            print(f"    Nome: {user.name}")
            print(f"    Ativo: {user.is_active}")
            print(f"    Criado em: {user.created_at}")
            print(f"    Ultimo login: {user.last_login}")
        else:
            print(f"[X] Usuario {email} NAO EXISTE no banco!")

    await engine.dispose()


if __name__ == "__main__":
    import sys

    email = "fcxforextrader@gmail.com"

    # Se passar argumento "check", apenas verifica
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        print(f"\n{'='*60}")
        print(f"VERIFICANDO USUARIO: {email}")
        print(f"{'='*60}\n")
        asyncio.run(check_user(email))
    else:
        print(f"\n{'='*60}")
        print(f"DELETANDO USUARIO: {email}")
        print(f"{'='*60}\n")
        asyncio.run(delete_user(email))

    print(f"\n{'='*60}")
    print(f"PROCESSO CONCLUIDO!")
    print(f"{'='*60}\n")
