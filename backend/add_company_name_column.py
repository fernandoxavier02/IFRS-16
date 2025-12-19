"""
Script para adicionar coluna company_name na tabela users em produção
"""
import asyncio
import asyncpg

async def add_column():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='ifrs16_user',
        password='bBMOLk2HURjQAvDiPNYE',
        database='ifrs16_licenses'
    )
    
    try:
        # Adicionar coluna company_name
        await conn.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS company_name VARCHAR(255);
        """)
        print("✅ Coluna company_name adicionada com sucesso!")
        
        # Verificar se a coluna existe
        result = await conn.fetch("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'company_name';
        """)
        
        if result:
            print(f"✅ Verificação: {result[0]['column_name']} ({result[0]['data_type']})")
        else:
            print("❌ Coluna não encontrada após criação")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(add_column())
