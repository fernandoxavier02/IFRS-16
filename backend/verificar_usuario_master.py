"""Verificar e corrigir usuario master no Cloud SQL"""
import asyncio
import asyncpg
import bcrypt

DATABASE_URL = "postgresql://ifrs16_user:ihU40nPKL38tCzTFvfNM@136.112.221.225:5432/ifrs16_licenses"

async def verificar_e_corrigir():
    conn = await asyncpg.connect(DATABASE_URL, ssl="require")
    
    try:
        # Verificar usuarios existentes
        print("=" * 60)
        print("VERIFICANDO USUARIOS NO BANCO")
        print("=" * 60)
        
        users = await conn.fetch("""
            SELECT id, username, email, role, is_active, created_at 
            FROM admin_users 
            ORDER BY created_at DESC
        """)
        
        if not users:
            print("\nNENHUM USUARIO ENCONTRADO!")
        else:
            print(f"\nTotal de usuarios: {len(users)}")
            for user in users:
                print(f"\n  Username: {user['username']}")
                print(f"  Email: {user['email']}")
                print(f"  Role: {user['role']}")
                print(f"  Ativo: {user['is_active']}")
                print(f"  Criado em: {user['created_at']}")
        
        # Verificar usuario master especifico
        print("\n" + "=" * 60)
        print("VERIFICANDO USUARIO MASTER")
        print("=" * 60)
        
        master = await conn.fetchrow("""
            SELECT * FROM admin_users 
            WHERE username = $1 OR email = $2
        """, "master", "fernandocostaxavier@gmail.com")
        
        if not master:
            print("\n❌ USUARIO MASTER NAO ENCONTRADO!")
            print("Criando usuario master...")
            
            # Criar usuario
            password = "Master@2025!"
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            
            import uuid
            from datetime import datetime
            
            user_id = uuid.uuid4()
            created_at = datetime.utcnow()
            
            await conn.execute("""
                INSERT INTO admin_users (id, username, email, password_hash, role, is_active, created_at)
                VALUES ($1, $2, $3, $4, $5::adminrole, $6, $7)
            """, user_id, "master", "fernandocostaxavier@gmail.com", password_hash, "SUPERADMIN", True, created_at)
            
            print("✅ Usuario master criado!")
        else:
            print(f"\n✅ Usuario encontrado:")
            print(f"   Username: {master['username']}")
            print(f"   Email: {master['email']}")
            print(f"   Role: {master['role']}")
            print(f"   Ativo: {master['is_active']}")
            
            # Testar hash da senha
            print("\nTestando senha...")
            password = "Master@2025!"
            test_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Verificar se precisa atualizar senha
            print("Atualizando senha para garantir...")
            salt = bcrypt.gensalt()
            new_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            
            await conn.execute("""
                UPDATE admin_users 
                SET password_hash = $1, is_active = true, role = 'SUPERADMIN'::adminrole
                WHERE id = $2
            """, new_hash, master['id'])
            
            print("✅ Senha atualizada!")
        
        # Verificar novamente
        print("\n" + "=" * 60)
        print("VERIFICACAO FINAL")
        print("=" * 60)
        
        final = await conn.fetchrow("""
            SELECT username, email, role, is_active 
            FROM admin_users 
            WHERE email = $1
        """, "fernandocostaxavier@gmail.com")
        
        if final:
            print(f"\n✅ Usuario confirmado:")
            print(f"   Username: {final['username']}")
            print(f"   Email: {final['email']}")
            print(f"   Role: {final['role']}")
            print(f"   Ativo: {final['is_active']}")
            print(f"\n📋 Credenciais:")
            print(f"   Email: fernandocostaxavier@gmail.com")
            print(f"   Senha: Master@2025!")
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(verificar_e_corrigir())
