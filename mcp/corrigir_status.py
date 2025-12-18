import asyncio
import asyncpg

async def fix_status():
    conn = await asyncpg.connect(
        host='136.112.221.225',
        port=5432,
        user='ifrs16_user',
        password='bBMOLk2HURjQAvDiPNYE',
        database='ifrs16_licenses'
    )
    
    # Verificar o tipo da coluna status
    print("Verificando tipo da coluna status...")
    col_info = await conn.fetch("""
        SELECT column_name, data_type, udt_name 
        FROM information_schema.columns 
        WHERE table_name = 'contracts' AND column_name = 'status'
    """)
    
    for c in col_info:
        print(f"  Coluna: {c['column_name']}, Tipo: {c['data_type']}, UDT: {c['udt_name']}")
    
    # Se for ENUM, precisamos alterar para VARCHAR
    if col_info and col_info[0]['data_type'] == 'USER-DEFINED':
        print("\n⚠️ Coluna status é um ENUM. Alterando para VARCHAR...")
        
        try:
            await conn.execute('''
                ALTER TABLE contracts 
                ALTER COLUMN status TYPE VARCHAR(50) USING status::text
            ''')
            print("✅ Coluna status alterada para VARCHAR(50)!")
        except Exception as e:
            print(f"Erro ao alterar coluna: {e}")
    else:
        print("✅ Coluna status já é VARCHAR ou outro tipo compatível")
    
    await conn.close()
    print("\n✅ Correção concluída!")

asyncio.run(fix_status())
