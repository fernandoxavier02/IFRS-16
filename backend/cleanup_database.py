"""
Script para Limpar Banco de Dados - IFRS 16

Este script remove todos os registros de teste/desenvolvimento do banco de dados:
- Subscriptions
- Licenses
- Users (exceto admin se existir)
- Validation logs
- Contracts

CUIDADO: Use apenas em ambiente de desenvolvimento/teste!

Data: 31/12/2025
"""

import asyncio
import sys
from pathlib import Path

# Adicionar backend ao PYTHONPATH
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database import AsyncSessionLocal
from sqlalchemy import text


async def cleanup_database():
    """Limpa todos os dados de teste do banco"""

    print("="*70)
    print("LIMPEZA DO BANCO DE DADOS - IFRS 16")
    print("="*70)
    print()

    # Confirmação
    print("[AVISO] Este script irá DELETAR todos os dados do banco:")
    print("  - Subscriptions")
    print("  - Licenses")
    print("  - Users (exceto admin)")
    print("  - Validation logs")
    print("  - Contracts")
    print()

    confirm = input("Tem certeza que deseja continuar? Digite 'SIM' para confirmar: ")

    if confirm.strip().upper() != 'SIM':
        print("[CANCELADO] Operação cancelada pelo usuário")
        return

    print()
    print("[INFO] Iniciando limpeza do banco de dados...")
    print()

    async with AsyncSessionLocal() as db:
        try:
            # 1. Deletar validation_logs
            print("[1/5] Deletando validation_logs...")
            result = await db.execute(text("DELETE FROM validation_logs"))
            print(f"  -> {result.rowcount} registros deletados")

            # 2. Deletar contracts
            print("[2/5] Deletando contracts...")
            result = await db.execute(text("DELETE FROM contracts"))
            print(f"  -> {result.rowcount} registros deletados")

            # 3. Deletar subscriptions
            print("[3/5] Deletando subscriptions...")
            result = await db.execute(text("DELETE FROM subscriptions"))
            print(f"  -> {result.rowcount} registros deletados")

            # 4. Deletar licenses
            print("[4/5] Deletando licenses...")
            result = await db.execute(text("DELETE FROM licenses"))
            print(f"  -> {result.rowcount} registros deletados")

            # 5. Deletar users (exceto admin)
            print("[5/5] Deletando users (exceto admin)...")
            # Manter usuários admin se existirem
            result = await db.execute(text("""
                DELETE FROM users
                WHERE email NOT LIKE '%admin%'
                AND id NOT IN (SELECT id FROM admin_users)
            """))
            print(f"  -> {result.rowcount} registros deletados")

            # Commit
            await db.commit()

            print()
            print("="*70)
            print("[OK] BANCO DE DADOS LIMPO COM SUCESSO!")
            print("="*70)
            print()
            print("Você pode agora:")
            print("  1. Fazer uma nova assinatura via Stripe")
            print("  2. Testar o fluxo completo end-to-end")
            print("  3. Verificar o dashboard com dados reais")
            print()

        except Exception as e:
            await db.rollback()
            print()
            print("="*70)
            print(f"[ERRO] Falha ao limpar banco de dados: {e}")
            print("="*70)
            raise
        finally:
            await db.close()


async def show_current_stats():
    """Mostra estatísticas atuais do banco"""
    async with AsyncSessionLocal() as db:
        try:
            print()
            print("="*70)
            print("ESTATÍSTICAS ATUAIS DO BANCO")
            print("="*70)

            # Users
            result = await db.execute(text("SELECT COUNT(*) FROM users"))
            users_count = result.scalar()
            print(f"Users: {users_count}")

            # Licenses
            result = await db.execute(text("SELECT COUNT(*) FROM licenses"))
            licenses_count = result.scalar()
            print(f"Licenses: {licenses_count}")

            # Subscriptions
            result = await db.execute(text("SELECT COUNT(*) FROM subscriptions"))
            subscriptions_count = result.scalar()
            print(f"Subscriptions: {subscriptions_count}")

            # Contracts
            result = await db.execute(text("SELECT COUNT(*) FROM contracts"))
            contracts_count = result.scalar()
            print(f"Contracts: {contracts_count}")

            # Validation logs
            result = await db.execute(text("SELECT COUNT(*) FROM validation_logs"))
            validation_logs_count = result.scalar()
            print(f"Validation Logs: {validation_logs_count}")

            print("="*70)
            print()

        except Exception as e:
            print(f"[ERRO] Falha ao obter estatísticas: {e}")
        finally:
            await db.close()


async def main():
    """Função principal"""
    # Mostrar estatísticas antes
    print()
    print("ANTES DA LIMPEZA:")
    await show_current_stats()

    # Limpar banco
    await cleanup_database()

    # Mostrar estatísticas depois
    print()
    print("DEPOIS DA LIMPEZA:")
    await show_current_stats()


if __name__ == "__main__":
    asyncio.run(main())
