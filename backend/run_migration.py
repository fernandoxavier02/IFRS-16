#!/usr/bin/env python
"""
Script para executar migration manualmente no banco de produção.
Uso: python run_migration.py
"""
import asyncio
from sqlalchemy import text
from app.database import async_engine

async def run_migration():
    """Adiciona coluna stripe_session_id à tabela subscriptions"""
    async with async_engine.begin() as conn:
        # Verificar se coluna já existe
        result = await conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='subscriptions' AND column_name='stripe_session_id'
        """))
        exists = result.fetchone()

        if exists:
            print("[INFO] Coluna stripe_session_id já existe na tabela subscriptions")
            return

        print("[INFO] Adicionando coluna stripe_session_id...")

        # Adicionar coluna
        await conn.execute(text("""
            ALTER TABLE subscriptions
            ADD COLUMN stripe_session_id VARCHAR(100)
        """))

        print("[OK] Coluna stripe_session_id adicionada com sucesso!")

        # Criar índice único
        print("[INFO] Criando índice único...")
        await conn.execute(text("""
            CREATE UNIQUE INDEX ix_subscriptions_stripe_session_id
            ON subscriptions (stripe_session_id)
            WHERE stripe_session_id IS NOT NULL
        """))

        print("[OK] Índice criado com sucesso!")
        print("[OK] Migration concluída!")

if __name__ == "__main__":
    asyncio.run(run_migration())
