"""
Script para listar usuários ativos, licenças e administradores
"""
import asyncio
import asyncpg

async def get_users():
    conn = await asyncpg.connect(
        host='136.112.221.225',
        port=5432,
        user='ifrs16_user',
        password='bBMOLk2HURjQAvDiPNYE',
        database='ifrs16_licenses'
    )
    
    # Usuarios
    print('='*70)
    print('USUARIOS ATIVOS')
    print('='*70)
    users = await conn.fetch('''
        SELECT id, email, name, is_active, stripe_customer_id, created_at, last_login
        FROM users
        WHERE is_active = true
        ORDER BY created_at DESC
    ''')
    for u in users:
        print(f"Email: {u['email']}")
        print(f"  Nome: {u['name']}")
        print(f"  ID: {u['id']}")
        print(f"  Stripe: {u['stripe_customer_id']}")
        print(f"  Criado: {u['created_at']}")
        print(f"  Ultimo login: {u['last_login']}")
        print()
    
    # Licencas
    print('='*70)
    print('LICENCAS')
    print('='*70)
    licenses = await conn.fetch('''
        SELECT l.id, l.key, l.customer_name, l.email, l.license_type, l.status, 
               l.expires_at, l.revoked, l.max_activations, l.current_activations
        FROM licenses l
        ORDER BY l.created_at DESC
    ''')
    for lic in licenses:
        print(f"Chave: {lic['key']}")
        print(f"  Cliente: {lic['customer_name']} ({lic['email']})")
        print(f"  Tipo: {lic['license_type']}")
        print(f"  Status: {lic['status']}")
        print(f"  Expira: {lic['expires_at']}")
        print(f"  Revogada: {lic['revoked']}")
        print(f"  Ativacoes: {lic['current_activations']}/{lic['max_activations']}")
        print()
    
    # Admin users
    print('='*70)
    print('ADMINISTRADORES')
    print('='*70)
    admins = await conn.fetch('''
        SELECT id, username, email, role, is_active, created_at
        FROM admin_users
        WHERE is_active = true
    ''')
    for a in admins:
        print(f"Username: {a['username']}")
        print(f"  Email: {a['email']}")
        print(f"  Role: {a['role']}")
        print(f"  Criado: {a['created_at']}")
        print()
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(get_users())
