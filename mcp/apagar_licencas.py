"""
Script para apagar licenças específicas
"""
import asyncio
import asyncpg

async def delete_licenses():
    conn = await asyncpg.connect(
        host='136.112.221.225',
        port=5432,
        user='ifrs16_user',
        password='bBMOLk2HURjQAvDiPNYE',
        database='ifrs16_licenses'
    )
    
    licenses_to_delete = [
        'FX2025-IFRS16-PRO-LTUD3BTQ',
        'FX2025-IFRS16-TRI-WWDN6BMF'
    ]
    
    for key in licenses_to_delete:
        # Primeiro, deletar logs de validação associados
        await conn.execute('DELETE FROM validation_logs WHERE license_key = $1', key)
        
        # Deletar subscriptions associadas
        await conn.execute('''
            DELETE FROM subscriptions 
            WHERE license_id IN (SELECT id FROM licenses WHERE key = $1)
        ''', key)
        
        # Deletar a licença
        result = await conn.execute('DELETE FROM licenses WHERE key = $1', key)
        print(f"✅ Licença {key} deletada: {result}")
    
    print("\n" + "="*50)
    print("Licenças restantes:")
    print("="*50)
    
    licenses = await conn.fetch('SELECT key, customer_name, email, license_type, status FROM licenses ORDER BY created_at DESC')
    for lic in licenses:
        print(f"  {lic['key']} - {lic['customer_name']} ({lic['email']}) - {lic['license_type']}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(delete_licenses())
