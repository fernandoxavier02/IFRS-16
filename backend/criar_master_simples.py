"""Script simples para criar usuario master - apenas bcrypt"""
import asyncio
import asyncpg
import bcrypt

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
        # Verificar se existe
        existing = await conn.fetchrow(
            "SELECT id, username FROM admin_users WHERE username = $1 OR email = $2",
            "master", "fernandocostaxavier@gmail.com"
        )
        
        if existing:
            print("Usuario ja existe, atualizando...")
            await conn.execute(
                """UPDATE admin_users 
                   SET password_hash = $1, email = $2, role = $3, is_active = true 
                   WHERE id = $4""",
                password_hash, "fernandocostaxavier@gmail.com", "superadmin", existing['id']
            )
            print("OK: Usuario atualizado!")
        else:
            print("Criando novo usuario...")
            await conn.execute(
                """INSERT INTO admin_users (username, email, password_hash, role, is_active)
                   VALUES ($1, $2, $3, $4, $5)""",
                "master", "fernandocostaxavier@gmail.com", password_hash, "superadmin", True
            )
            print("OK: Usuario criado!")
        
        print("\nCredenciais:")
        print("  Username: master")
        print("  Email: fernandocostaxavier@gmail.com")
        print("  Senha: Master@2025!")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(criar_master())
