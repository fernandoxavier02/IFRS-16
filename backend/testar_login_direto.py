"""Testar login diretamente no banco"""
import asyncio
import asyncpg
import bcrypt

DATABASE_URL = "postgresql://ifrs16_user:ihU40nPKL38tCzTFvfNM@136.112.221.225:5432/ifrs16_licenses"

async def testar_login():
    conn = await asyncpg.connect(DATABASE_URL, ssl="require")
    
    try:
        email = "fernandocostaxavier@gmail.com"
        password = "Master@2025!"
        
        print("=" * 60)
        print("TESTE DE LOGIN DIRETO")
        print("=" * 60)
        print(f"\nEmail: {email}")
        print(f"Senha: {password}")
        
        # Buscar usuario
        user = await conn.fetchrow("""
            SELECT id, username, email, password_hash, role, is_active 
            FROM admin_users 
            WHERE email = $1 OR email = LOWER($1)
        """, email)
        
        if not user:
            print("\nERRO: Usuario nao encontrado!")
            return
        
        print(f"\nUsuario encontrado:")
        print(f"  ID: {user['id']}")
        print(f"  Username: {user['username']}")
        print(f"  Email: {user['email']}")
        print(f"  Role: {user['role']}")
        print(f"  Ativo: {user['is_active']}")
        print(f"  Hash: {user['password_hash'][:30]}...")
        
        # Testar senha
        print("\nTestando senha...")
        stored_hash = user['password_hash']
        
        # Tentar verificar com bcrypt
        try:
            is_valid = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
            if is_valid:
                print("OK: Senha valida!")
            else:
                print("ERRO: Senha invalida!")
                print("\nGerando novo hash...")
                salt = bcrypt.gensalt()
                new_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
                
                print(f"Novo hash: {new_hash[:30]}...")
                print("Atualizando no banco...")
                
                await conn.execute("""
                    UPDATE admin_users 
                    SET password_hash = $1 
                    WHERE id = $2
                """, new_hash, user['id'])
                
                print("OK: Senha atualizada!")
                
                # Testar novamente
                is_valid = bcrypt.checkpw(password.encode('utf-8'), new_hash.encode('utf-8'))
                if is_valid:
                    print("OK: Nova senha validada com sucesso!")
                else:
                    print("ERRO: Problema ao validar nova senha!")
        except Exception as e:
            print(f"ERRO ao verificar senha: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(testar_login())
