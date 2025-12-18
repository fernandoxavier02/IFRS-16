import asyncio
import asyncpg

async def fix_table():
    conn = await asyncpg.connect(
        host='136.112.221.225',
        port=5432,
        user='ifrs16_user',
        password='bBMOLk2HURjQAvDiPNYE',
        database='ifrs16_licenses'
    )
    
    print("Adicionando coluna is_deleted à tabela contracts...")
    
    try:
        await conn.execute('''
            ALTER TABLE contracts 
            ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE
        ''')
        print("✅ Coluna is_deleted adicionada!")
    except Exception as e:
        print(f"Erro ao adicionar coluna: {e}")
    
    # Verificar colunas após correção
    cols = await conn.fetch("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'contracts'
        ORDER BY ordinal_position
    """)
    
    print("\nColunas em contracts após correção:")
    for c in cols:
        print(f"  - {c['column_name']}")
    
    await conn.close()
    print("\n✅ Correção concluída!")

asyncio.run(fix_table())
