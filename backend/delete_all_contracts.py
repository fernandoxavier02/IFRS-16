"""
Script para deletar todos os contratos do banco de dados
"""
import asyncio
import asyncpg

async def delete_contracts():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='ifrs16_user',
        password='bBMOLk2HURjQAvDiPNYE',
        database='ifrs16_licenses'
    )
    
    try:
        # Verificar quantos contratos existem
        result = await conn.fetchval("SELECT COUNT(*) FROM contracts;")
        print(f"📊 Total de contratos no banco: {result}")
        
        if result > 0:
            # Deletar todos os contratos
            deleted = await conn.execute("DELETE FROM contracts;")
            print(f"🗑️  Contratos deletados: {deleted}")
        else:
            print("ℹ️  Nenhum contrato para deletar")
        
        # Verificar resultado
        result_after = await conn.fetchval("SELECT COUNT(*) FROM contracts;")
        print(f"✅ Total de contratos após deleção: {result_after}")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(delete_contracts())
