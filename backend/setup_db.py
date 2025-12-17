"""
Script para configurar e inicializar o banco de dados
"""
import asyncio
import os
from pathlib import Path

# Configurar SQLite como padrão se não houver PostgreSQL
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./ifrs16_licenses.db"
    print("📝 Usando SQLite para desenvolvimento")

async def init_database():
    """Inicializa o banco de dados"""
    from app.database import init_db
    
    print("🔄 Inicializando banco de dados...")
    await init_db()
    print("✅ Banco de dados inicializado com sucesso!")
    
    # Verificar se arquivo foi criado (SQLite)
    db_file = Path("ifrs16_licenses.db")
    if db_file.exists():
        print(f"📁 Arquivo criado: {db_file.absolute()}")

if __name__ == "__main__":
    asyncio.run(init_database())

