import asyncio
import asyncpg

async def fix_archived_at():
    conn = await asyncpg.connect(
        host='136.112.221.225',
        port=5432,
        user='ifrs16_user',
        password='bBMOLk2HURjQAvDiPNYE',
        database='ifrs16_licenses'
    )
    
    print("Corrigindo coluna archived_at em contract_versions...")
    
    # Permitir NULL na coluna archived_at
    await conn.execute('''
        ALTER TABLE contract_versions 
        ALTER COLUMN archived_at DROP NOT NULL
    ''')
    print("✅ archived_at agora permite NULL")
    
    # Verificar e corrigir outras colunas que podem ter o mesmo problema
    print("\nVerificando outras colunas...")
    
    # created_by_user_id também pode precisar de correção
    try:
        await conn.execute('''
            ALTER TABLE contract_versions 
            ALTER COLUMN created_by_user_id DROP NOT NULL
        ''')
        print("✅ created_by_user_id agora permite NULL")
    except Exception as e:
        print(f"  created_by_user_id já permite NULL ou não existe: {e}")
    
    # Verificar estrutura final
    cols = await conn.fetch("""
        SELECT column_name, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'contract_versions'
        ORDER BY ordinal_position
    """)
    
    print("\nEstrutura final de contract_versions:")
    for c in cols:
        print(f"  {c['column_name']:25} | Nullable: {c['is_nullable']:5} | Default: {c['column_default']}")
    
    await conn.close()
    print("\n✅ Correções aplicadas!")

asyncio.run(fix_archived_at())
