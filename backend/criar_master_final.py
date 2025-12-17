"""Script final para criar usuario master - verifica enum e cria corretamente"""
import asyncio
import asyncpg
import bcrypt
import uuid
from datetime import datetime

DATABASE_URL = "postgresql://ifrs16_user:ihU40nPKL38tCzTFvfNM@136.112.221.225:5432/ifrs16_licenses"

async def criar_master():
    # Gerar hash
    password = "Master@2025!"
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    print(f"Hash gerado: {password_hash[:30]}...")
    
    # Conectar
    conn = await asyncpg.connect(DATABASE_URL, ssl="require")
    
    try:
        # Primeiro, verificar valores do enum
        print("Verificando valores do enum adminrole...")
        enumValues = await conn.fetch("""
            SELECT unnest(enum_range(NULL::adminrole))::text as value;
        """)
        
        print("Valores do enum encontrados:")
        validValues = []
        for row in enumValues:
            value = row['value']
            print(f"  - {value}")
            validValues.append(value)
        
        # Usar o primeiro valor válido (geralmente 'superadmin' ou 'SUPERADMIN')
        roleValue = validValues[0] if validValues else "superadmin"
        print(f"\nUsando role: {roleValue}")
        
        # Verificar se existe
        existing = await conn.fetchrow(
            "SELECT id, username, role FROM admin_users WHERE username = $1 OR email = $2",
            "master", "fernandocostaxavier@gmail.com"
        )
        
        if existing:
            print(f"\nUsuario ja existe: {existing['username']} (role: {existing['role']})")
            print("Atualizando senha e role...")
            await conn.execute(
                """UPDATE admin_users 
                   SET password_hash = $1, email = $2, role = $3::adminrole, is_active = true 
                   WHERE id = $4""",
                password_hash, "fernandocostaxavier@gmail.com", roleValue, existing['id']
            )
            print("OK: Usuario atualizado!")
        else:
            print("\nCriando novo usuario...")
            user_id = uuid.uuid4()
            created_at = datetime.utcnow()
            await conn.execute(
                """INSERT INTO admin_users (id, username, email, password_hash, role, is_active, created_at)
                   VALUES ($1, $2, $3, $4, $5::adminrole, $6, $7)""",
                user_id, "master", "fernandocostaxavier@gmail.com", password_hash, roleValue, True, created_at
            )
            print("OK: Usuario criado!")
        
        # Verificar criação
        user = await conn.fetchrow(
            "SELECT username, email, role, is_active FROM admin_users WHERE username = $1",
            "master"
        )
        
        print("\n" + "="*50)
        print("CREDENCIAIS DO USUARIO MASTER")
        print("="*50)
        print(f"  Username: {user['username']}")
        print(f"  Email: {user['email']}")
        print(f"  Role: {user['role']}")
        print(f"  Ativo: {user['is_active']}")
        print(f"  Senha: {password}")
        print("="*50)
        
    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(criar_master())
