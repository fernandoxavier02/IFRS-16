import asyncio
import asyncpg

async def check_structure():
    conn = await asyncpg.connect(
        host='136.112.221.225',
        port=5432,
        user='ifrs16_user',
        password='bBMOLk2HURjQAvDiPNYE',
        database='ifrs16_licenses'
    )
    
    print("=" * 60)
    print("📋 ESTRUTURA DA TABELA CONTRACTS")
    print("=" * 60)
    
    cols = await conn.fetch("""
        SELECT column_name, data_type, column_default, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'contracts'
        ORDER BY ordinal_position
    """)
    
    for c in cols:
        default = c['column_default'][:40] + "..." if c['column_default'] and len(c['column_default']) > 40 else c['column_default']
        print(f"  {c['column_name']:20} | {c['data_type']:20} | Default: {default}")
    
    print("\n" + "=" * 60)
    print("📋 ESTRUTURA DA TABELA CONTRACT_VERSIONS")
    print("=" * 60)
    
    cols = await conn.fetch("""
        SELECT column_name, data_type, column_default, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'contract_versions'
        ORDER BY ordinal_position
    """)
    
    if cols:
        for c in cols:
            default = c['column_default'][:40] + "..." if c['column_default'] and len(c['column_default']) > 40 else c['column_default']
            print(f"  {c['column_name']:20} | {c['data_type']:20} | Default: {default}")
    else:
        print("  ⚠️ Tabela não existe!")
    
    # Testar inserção direta
    print("\n" + "=" * 60)
    print("🧪 TESTE DE INSERÇÃO DIRETA")
    print("=" * 60)
    
    try:
        # Buscar um user_id válido
        user = await conn.fetchrow("SELECT id FROM users LIMIT 1")
        if user:
            user_id = user['id']
            print(f"  User ID para teste: {user_id}")
            
            # Tentar inserir um contrato
            result = await conn.fetchrow("""
                INSERT INTO contracts (user_id, name, description, contract_code, status, is_deleted, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                RETURNING id, name, status
            """, user_id, "Teste Direto", "Descrição teste", "TEST-DIRECT", "draft", False)
            
            print(f"  ✅ Contrato criado com sucesso!")
            print(f"     ID: {result['id']}")
            print(f"     Nome: {result['name']}")
            print(f"     Status: {result['status']}")
            
            # Deletar o contrato de teste
            await conn.execute("DELETE FROM contracts WHERE id = $1", result['id'])
            print(f"  🗑️ Contrato de teste removido")
        else:
            print("  ⚠️ Nenhum usuário encontrado para teste")
    except Exception as e:
        print(f"  ❌ Erro: {e}")
    
    await conn.close()
    print("\n✅ Verificação concluída!")

asyncio.run(check_structure())
