"""
Script para adicionar a coluna user_id à tabela licenses
"""

import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy import text
from app.database import AsyncSessionLocal, init_db


async def add_user_id_column():
    print("=" * 50)
    print("🔧 Adicionar coluna user_id à tabela licenses")
    print("=" * 50)
    print()
    
    await init_db()
    
    async with AsyncSessionLocal() as db:
        try:
            # Verificar se a coluna já existe
            result = await db.execute(
                text("PRAGMA table_info(licenses)")
            )
            columns = result.fetchall()
            column_names = [col[1] for col in columns]
            
            if 'user_id' in column_names:
                print("✅ Coluna user_id já existe!")
                return
            
            print("📝 Adicionando coluna user_id...")
            
            # Adicionar coluna user_id
            await db.execute(
                text("ALTER TABLE licenses ADD COLUMN user_id TEXT")
            )
            await db.commit()
            
            print("✅ Coluna user_id adicionada com sucesso!")
            print()
            print("💡 Nota: A coluna foi criada como TEXT para SQLite.")
            print("   O SQLAlchemy fará a conversão para UUID automaticamente.")
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(add_user_id_column())

