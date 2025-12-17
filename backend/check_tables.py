"""Verificar tabelas no banco de producao"""
import asyncio
import os
os.environ['DATABASE_URL'] = 'postgresql://ifrs16_database_user:DmgbPA9jjyA587ot8Rc4Kt4fnAr0opM7@dpg-d4qvp9ggjchc73bk1rvg-a.virginia-postgres.render.com/ifrs16_database'

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def check():
    url = os.environ['DATABASE_URL'].replace('postgresql://', 'postgresql+asyncpg://')
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
        tables = [row[0] for row in result.fetchall()]
        print("Tabelas encontradas:", tables)
    await engine.dispose()

asyncio.run(check())

