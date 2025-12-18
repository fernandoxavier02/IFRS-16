import asyncio
import asyncpg

async def add_category_and_version_id():
    conn = await asyncpg.connect(
        host='136.112.221.225',
        port=5432,
        user='ifrs16_user',
        password='bBMOLk2HURjQAvDiPNYE',
        database='ifrs16_licenses'
    )
    
    print("=" * 60)
    print("Adicionando campos de categoria e ID de versão")
    print("=" * 60)
    
    # 1. Adicionar campo categoria na tabela contracts
    print("\n1. Adicionando campo 'categoria' em contracts...")
    try:
        await conn.execute('''
            ALTER TABLE contracts 
            ADD COLUMN IF NOT EXISTS categoria VARCHAR(2) DEFAULT 'OT'
        ''')
        print("   ✅ Campo 'categoria' adicionado (IM, VE, EQ, PC, OT)")
    except Exception as e:
        print(f"   ⚠️ Erro: {e}")
    
    # 2. Adicionar campo numero_sequencial na tabela contracts (para gerar o número único por categoria)
    print("\n2. Adicionando campo 'numero_sequencial' em contracts...")
    try:
        await conn.execute('''
            ALTER TABLE contracts 
            ADD COLUMN IF NOT EXISTS numero_sequencial INTEGER
        ''')
        print("   ✅ Campo 'numero_sequencial' adicionado")
    except Exception as e:
        print(f"   ⚠️ Erro: {e}")
    
    # 3. Adicionar campo version_id na tabela contract_versions
    print("\n3. Adicionando campo 'version_id' em contract_versions...")
    try:
        await conn.execute('''
            ALTER TABLE contract_versions 
            ADD COLUMN IF NOT EXISTS version_id VARCHAR(20)
        ''')
        print("   ✅ Campo 'version_id' adicionado (ex: IDVE2-0001)")
    except Exception as e:
        print(f"   ⚠️ Erro: {e}")
    
    # 4. Criar sequência para cada categoria (para gerar números únicos)
    print("\n4. Criando sequências para cada categoria...")
    categorias = ['IM', 'VE', 'EQ', 'PC', 'OT']
    for cat in categorias:
        try:
            await conn.execute(f'''
                CREATE SEQUENCE IF NOT EXISTS seq_contrato_{cat.lower()}
                START WITH 1 INCREMENT BY 1
            ''')
            print(f"   ✅ Sequência seq_contrato_{cat.lower()} criada")
        except Exception as e:
            print(f"   ⚠️ Erro ao criar sequência {cat}: {e}")
    
    # 5. Verificar estrutura final
    print("\n5. Verificando estrutura final...")
    
    print("\n   Tabela contracts:")
    cols = await conn.fetch("""
        SELECT column_name, data_type, column_default
        FROM information_schema.columns 
        WHERE table_name = 'contracts'
        ORDER BY ordinal_position
    """)
    for c in cols:
        print(f"      {c['column_name']:25} | {c['data_type']:15} | {c['column_default']}")
    
    print("\n   Tabela contract_versions:")
    cols = await conn.fetch("""
        SELECT column_name, data_type, column_default
        FROM information_schema.columns 
        WHERE table_name = 'contract_versions'
        ORDER BY ordinal_position
    """)
    for c in cols:
        print(f"      {c['column_name']:25} | {c['data_type']:15} | {c['column_default']}")
    
    await conn.close()
    print("\n" + "=" * 60)
    print("✅ Alterações concluídas!")
    print("=" * 60)

asyncio.run(add_category_and_version_id())
