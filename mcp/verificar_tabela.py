import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect(
        host='136.112.221.225',
        port=5432,
        user='ifrs16_user',
        password='bBMOLk2HURjQAvDiPNYE',
        database='ifrs16_licenses'
    )
    
    # Verificar colunas da tabela contracts
    cols = await conn.fetch("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'contracts'
    """)
    
    print("Colunas em contracts:")
    for c in cols:
        print(f"  - {c['column_name']}")
    
    if not cols:
        print("  TABELA NÃO EXISTE!")
    
    await conn.close()

asyncio.run(check())
