"""
Script para listar usuários do banco de dados
"""
import asyncio
import sys
from pathlib import Path

# Adicionar o diretório backend ao path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import User


async def listar_usuarios():
    """Lista todos os usuários cadastrados"""
    async with AsyncSessionLocal() as session:
        # Buscar todos os usuários
        result = await session.execute(
            select(User).order_by(User.created_at.desc())
        )
        usuarios = result.scalars().all()

        if not usuarios:
            print("[INFO] Nenhum usuário encontrado no banco de dados.")
            return

        print(f"\n{'='*80}")
        print(f"USUÁRIOS CADASTRADOS ({len(usuarios)})")
        print(f"{'='*80}\n")

        for i, user in enumerate(usuarios, 1):
            print(f"[{i}] {user.name}")
            print(f"    Email: {user.email}")
            print(f"    ID: {user.id}")
            print(f"    Empresa: {user.company_name or 'Não informada'}")
            print(f"    Ativo: {'Sim' if user.is_active else 'Não'}")
            print(f"    Email verificado: {'Sim' if user.email_verified else 'Não'}")
            print(f"    Precisa trocar senha: {'Sim' if user.password_must_change else 'Não'}")
            print(f"    Stripe Customer ID: {user.stripe_customer_id or 'Não tem'}")
            print(f"    Criado em: {user.created_at.strftime('%d/%m/%Y %H:%M:%S')}")

            if user.last_login:
                print(f"    Último login: {user.last_login.strftime('%d/%m/%Y %H:%M:%S')}")
            else:
                print(f"    Último login: Nunca fez login")

            if user.password_changed_at:
                print(f"    Senha alterada em: {user.password_changed_at.strftime('%d/%m/%Y %H:%M:%S')}")

            print()

        print(f"{'='*80}")
        print(f"Total: {len(usuarios)} usuário(s)")
        print(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(listar_usuarios())
