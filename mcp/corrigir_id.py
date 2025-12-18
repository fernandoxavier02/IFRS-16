import asyncio
import asyncpg

async def fix_id():
    conn = await asyncpg.connect(
        host='136.112.221.225',
        port=5432,
        user='ifrs16_user',
        password='bBMOLk2HURjQAvDiPNYE',
        database='ifrs16_licenses'
    )
    
    print("Verificando coluna id da tabela contracts...")
    
    # Verificar o default da coluna id
    col_info = await conn.fetch("""
        SELECT column_name, column_default, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'contracts' AND column_name = 'id'
    """)
    
    for c in col_info:
        print(f"  Coluna: {c['column_name']}")
        print(f"  Default: {c['column_default']}")
        print(f"  Nullable: {c['is_nullable']}")
    
    # Corrigir o default para gerar UUID automaticamente
    print("\nCorrigindo default da coluna id...")
    try:
        await conn.execute('''
            ALTER TABLE contracts 
            ALTER COLUMN id SET DEFAULT gen_random_uuid()
        ''')
        print("✅ Default da coluna id corrigido!")
    except Exception as e:
        print(f"Erro: {e}")
    
    # Verificar novamente
    col_info = await conn.fetch("""
        SELECT column_name, column_default
        FROM information_schema.columns 
        WHERE table_name = 'contracts' AND column_name = 'id'
    """)
    
    print("\nApós correção:")
    for c in col_info:
        print(f"  Default: {c['column_default']}")
    
    await conn.close()
    print("\n✅ Correção concluída!")

asyncio.run(fix_id())
