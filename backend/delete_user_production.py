"""
Script para deletar um usuário específico do banco de dados de produção

IMPORTANTE: Este script se conecta ao banco PostgreSQL de PRODUÇÃO
Use com cuidado!

Data: 31/12/2025
"""

import asyncio
import sys
from pathlib import Path

# Adicionar backend ao PYTHONPATH
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# URL do banco de produção (PostgreSQL no Google Cloud)
PRODUCTION_DB_URL = "postgresql+asyncpg://ifrs16_user:1Fr$16#2024@/ifrs16_db?host=/cloudsql/ifrs16-backend:us-central1:ifrs16-db"

# Email do usuário a ser deletado
USER_EMAIL = "fcxforextrader@gmail.com"


async def delete_user():
    """Deleta um usuário específico e todos os seus dados relacionados"""

    print("="*70)
    print("DELETAR USUÁRIO DO BANCO DE PRODUÇÃO")
    print("="*70)
    print()
    print(f"[AVISO] Este script irá deletar o usuário: {USER_EMAIL}")
    print("        e todos os seus dados relacionados:")
    print("  - Subscriptions")
    print("  - Licenses")
    print("  - Contracts")
    print("  - Validation logs")
    print()

    confirm = input(f"Tem certeza que deseja deletar '{USER_EMAIL}'? Digite 'SIM' para confirmar: ")

    if confirm.strip().upper() != 'SIM':
        print("[CANCELADO] Operação cancelada pelo usuário")
        return

    print()
    print("[INFO] Conectando ao banco de produção...")

    # Criar engine para produção
    engine = create_async_engine(
        PRODUCTION_DB_URL,
        echo=False,
        pool_pre_ping=True
    )

    # Criar sessão
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as db:
        try:
            # 1. Buscar user_id
            print(f"[1/6] Buscando usuário '{USER_EMAIL}'...")
            result = await db.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": USER_EMAIL}
            )
            user_row = result.fetchone()

            if not user_row:
                print(f"[INFO] Usuário '{USER_EMAIL}' não encontrado no banco")
                return

            user_id = user_row[0]
            print(f"  -> User ID encontrado: {user_id}")

            # 2. Deletar validation_logs
            print("[2/6] Deletando validation_logs...")
            result = await db.execute(
                text("DELETE FROM validation_logs WHERE contract_id IN (SELECT id FROM contracts WHERE user_id = :user_id)"),
                {"user_id": user_id}
            )
            print(f"  -> {result.rowcount} registros deletados")

            # 3. Deletar contracts
            print("[3/6] Deletando contracts...")
            result = await db.execute(
                text("DELETE FROM contracts WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            print(f"  -> {result.rowcount} registros deletados")

            # 4. Deletar subscriptions
            print("[4/6] Deletando subscriptions...")
            result = await db.execute(
                text("DELETE FROM subscriptions WHERE license_id IN (SELECT id FROM licenses WHERE user_id = :user_id)"),
                {"user_id": user_id}
            )
            print(f"  -> {result.rowcount} registros deletados")

            # 5. Deletar licenses
            print("[5/6] Deletando licenses...")
            result = await db.execute(
                text("DELETE FROM licenses WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            print(f"  -> {result.rowcount} registros deletados")

            # 6. Deletar user
            print("[6/6] Deletando usuário...")
            result = await db.execute(
                text("DELETE FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            )
            print(f"  -> {result.rowcount} registro deletado")

            # Commit
            await db.commit()

            print()
            print("="*70)
            print(f"[OK] USUÁRIO '{USER_EMAIL}' DELETADO COM SUCESSO!")
            print("="*70)
            print()
            print("Você pode agora fazer um novo registro em:")
            print("  https://fxstudioai.com/register")
            print()

        except Exception as e:
            await db.rollback()
            print()
            print("="*70)
            print(f"[ERRO] Falha ao deletar usuário: {e}")
            print("="*70)
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(delete_user())
