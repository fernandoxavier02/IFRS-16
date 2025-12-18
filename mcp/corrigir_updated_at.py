import asyncio
import asyncpg

async def fix_updated_at():
    conn = await asyncpg.connect(
        host='136.112.221.225',
        port=5432,
        user='ifrs16_user',
        password='bBMOLk2HURjQAvDiPNYE',
        database='ifrs16_licenses'
    )
    
    print("Corrigindo coluna updated_at...")
    
    # Permitir NULL na coluna updated_at
    await conn.execute('''
        ALTER TABLE contracts 
        ALTER COLUMN updated_at DROP NOT NULL
    ''')
    print("✅ updated_at agora permite NULL")
    
    # Também corrigir created_at para ter default
    await conn.execute('''
        ALTER TABLE contracts 
        ALTER COLUMN created_at SET DEFAULT NOW()
    ''')
    print("✅ created_at tem default NOW()")
    
    # Corrigir contract_versions também
    print("\nCorrigindo contract_versions...")
    
    await conn.execute('''
        ALTER TABLE contract_versions 
        ALTER COLUMN id SET DEFAULT gen_random_uuid()
    ''')
    print("✅ contract_versions.id tem default gen_random_uuid()")
    
    await conn.execute('''
        ALTER TABLE contract_versions 
        ALTER COLUMN created_at SET DEFAULT NOW()
    ''')
    print("✅ contract_versions.created_at tem default NOW()")
    
    # Testar inserção novamente
    print("\n🧪 Testando inserção...")
    user = await conn.fetchrow("SELECT id FROM users LIMIT 1")
    if user:
        user_id = user['id']
        
        result = await conn.fetchrow("""
            INSERT INTO contracts (user_id, name, description, contract_code, status, is_deleted)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, name, status, created_at
        """, user_id, "Teste Final", "Descrição teste", "TEST-FINAL", "draft", False)
        
        print(f"✅ Contrato criado com sucesso!")
        print(f"   ID: {result['id']}")
        print(f"   Nome: {result['name']}")
        print(f"   Status: {result['status']}")
        print(f"   Created: {result['created_at']}")
        
        # Deletar o contrato de teste
        await conn.execute("DELETE FROM contracts WHERE id = $1", result['id'])
        print("🗑️ Contrato de teste removido")
    
    await conn.close()
    print("\n✅ Todas as correções aplicadas!")

asyncio.run(fix_updated_at())
