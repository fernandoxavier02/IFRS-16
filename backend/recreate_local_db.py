"""
Script para recriar banco de dados SQLite local com schema atualizado

Este script deleta o banco SQLite local e recria com o schema correto
baseado nos modelos atuais (app/models.py)

Data: 31/12/2025
"""

import asyncio
import sys
from pathlib import Path

# Adicionar backend ao PYTHONPATH
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database import engine, Base
from app.models import User, License, Subscription  # Importar models para criar tabelas


async def recreate_database():
    """Recria banco de dados local"""
    db_file = backend_dir / "ifrs16_licenses.db"

    print(f"[INFO] Recreando banco de dados local: {db_file}")

    # Deletar banco existente
    if db_file.exists():
        db_file.unlink()
        print("[OK] Banco de dados antigo deletado")

    # Criar novo banco com schema atualizado
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("[OK] Banco de dados recriado com schema atualizado")
    print("[INFO] Tabelas criadas: users, licenses, subscriptions, contracts")

    # Fechar engine
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(recreate_database())
