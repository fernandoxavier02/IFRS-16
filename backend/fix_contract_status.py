"""
Script para corrigir status dos contratos de minúsculo para maiúsculo
"""
import asyncio
import asyncpg

async def fix_status():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='ifrs16_user',
        password='bBMOLk2HURjQAvDiPNYE',
        database='ifrs16_licenses'
    )
    
    try:
        # Verificar contratos com status em minúsculo
        result = await conn.fetch("""
            SELECT id, status FROM contracts WHERE status = 'active';
        """)
        
        print(f"📊 Encontrados {len(result)} contratos com status 'active' (minúsculo)")
        
        if result:
            # Atualizar para maiúsculo
            updated = await conn.execute("""
                UPDATE contracts 
                SET status = 'ACTIVE' 
                WHERE status = 'active';
            """)
            print(f"✅ Atualizados: {updated}")
        
        # Verificar resultado
        result_after = await conn.fetch("""
            SELECT status, COUNT(*) as count 
            FROM contracts 
            GROUP BY status;
        """)
        
        print("\n📊 Status dos contratos após correção:")
        for row in result_after:
            print(f"  - {row['status']}: {row['count']} contratos")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_status())
