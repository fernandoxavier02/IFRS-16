"""
Debug completo do login admin
"""

import asyncio
import httpx
import bcrypt
import asyncpg

API_URL = "https://ifrs-16.onrender.com"
DATABASE_URL = "postgresql://ifrs16_database_ycs3_user:WUhx3D36NZVEytmT3a90c6ZWNog2pGEZ@dpg-d4r4lrmr433s738i13u0-a.virginia-postgres.render.com:5432/ifrs16_database_ycs3"

async def debug_completo():
    print("=" * 70)
    print("🔍 DEBUG COMPLETO DO LOGIN ADMIN")
    print("=" * 70)
    print()
    
    # Credenciais
    email = "fernandocostaxavier@gmail.com"
    password = "Master@2025!"
    
    print("📋 PASSO 1: VERIFICAR DADOS NO BANCO")
    print("-" * 70)
    
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        result = await conn.fetchrow(
            "SELECT id, username, email, password_hash, role, is_active FROM admin_users WHERE email = $1",
            email.lower()
        )
        
        if result:
            print(f"✅ Usuário encontrado no banco:")
            print(f"   ID: {result['id']}")
            print(f"   Username: {result['username']}")
            print(f"   Email: {result['email']}")
            print(f"   Role: {result['role']}")
            print(f"   Ativo: {result['is_active']}")
            print(f"   Hash: {result['password_hash'][:50]}...")
            print()
            
            # Verificar senha
            print("🔑 PASSO 2: VERIFICAR SENHA")
            print("-" * 70)
            password_hash = result['password_hash']
            senha_valida = bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
            print(f"   Senha testada: '{password}'")
            print(f"   Senha válida: {senha_valida}")
            
            if not senha_valida:
                print("   ❌ SENHA INVÁLIDA NO BANCO!")
                print("   Vou resetar a senha...")
                
                # Resetar senha
                salt = bcrypt.gensalt()
                new_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
                
                await conn.execute(
                    "UPDATE admin_users SET password_hash = $1 WHERE id = $2",
                    new_hash, result['id']
                )
                print(f"   ✅ Senha resetada para: {password}")
            else:
                print("   ✅ Senha válida no banco")
            print()
        else:
            print(f"❌ Usuário não encontrado com email: {email}")
            print()
            return
            
    finally:
        await conn.close()
    
    # Testar API
    print("🌐 PASSO 3: TESTAR LOGIN VIA API")
    print("-" * 70)
    
    async with httpx.AsyncClient() as client:
        try:
            print(f"   URL: {API_URL}/api/auth/admin/login")
            print(f"   Email: {email}")
            print(f"   Senha: {password}")
            print()
            
            response = await client.post(
                f"{API_URL}/api/auth/admin/login",
                json={"email": email, "password": password},
                timeout=30.0
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("   ✅ LOGIN BEM-SUCEDIDO!")
                print(f"   Token: {data.get('access_token', 'N/A')[:50]}...")
                print(f"   Tipo: {data.get('user_type', 'N/A')}")
            else:
                print("   ❌ LOGIN FALHOU!")
                try:
                    error_data = response.json()
                    print(f"   Erro: {error_data.get('detail', 'Desconhecido')}")
                except:
                    print(f"   Resposta: {response.text}")
            print()
                    
        except Exception as e:
            print(f"   ❌ ERRO: {e}")
            print()
    
    # Verificar frontend
    print("🖥️  PASSO 4: VERIFICAR FRONTEND")
    print("-" * 70)
    
    async with httpx.AsyncClient() as client:
        try:
            # Verificar se login.html existe
            response = await client.get(f"https://ifrs-16-1.onrender.com/login.html", timeout=10.0)
            print(f"   login.html: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Página de login existe")
                
                # Verificar se está apontando para a API correta
                content = response.text
                if "ifrs-16.onrender.com" in content:
                    print("   ✅ Frontend aponta para API correta")
                else:
                    print("   ⚠️  Frontend pode estar apontando para API errada")
            else:
                print("   ❌ Página de login não encontrada")
                
        except Exception as e:
            print(f"   ❌ Erro ao verificar frontend: {e}")
    
    print()
    print("=" * 70)
    print("📊 RESUMO")
    print("=" * 70)
    print()
    print("Para fazer login:")
    print(f"1. Acesse: https://ifrs-16-1.onrender.com/login.html")
    print(f"2. Clique na aba 'Administrador'")
    print(f"3. Email: {email}")
    print(f"4. Senha: {password}")
    print()
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(debug_completo())

