"""
Testar login do admin via API
"""

import asyncio
import httpx

API_URL = "https://ifrs-16.onrender.com"

async def test_login():
    """Testa login do admin via API"""
    
    print("=" * 60)
    print("🔐 TESTE DE LOGIN VIA API")
    print("=" * 60)
    print()
    
    # Credenciais
    email = "fernandocostaxavier@gmail.com"
    password = "Master@2025!"
    
    print(f"📧 Email: {email}")
    print(f"🔑 Senha: {password}")
    print()
    
    # Fazer requisição
    async with httpx.AsyncClient() as client:
        try:
            print(f"🌐 URL: {API_URL}/api/auth/admin/login")
            print()
            
            response = await client.post(
                f"{API_URL}/api/auth/admin/login",
                json={
                    "email": email,
                    "password": password
                },
                timeout=30.0
            )
            
            print(f"📊 Status Code: {response.status_code}")
            print()
            
            if response.status_code == 200:
                data = response.json()
                print("✅ LOGIN BEM-SUCEDIDO!")
                print()
                print(f"🎫 Token: {data.get('access_token', 'N/A')[:50]}...")
                print(f"⏰ Expira em: {data.get('expires_in', 'N/A')} segundos")
                print(f"👤 Tipo: {data.get('user_type', 'N/A')}")
                print()
                
                # Testar endpoint /me
                token = data.get('access_token')
                if token:
                    print("🔍 Testando endpoint /api/auth/admin/me...")
                    me_response = await client.get(
                        f"{API_URL}/api/auth/admin/me",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    
                    if me_response.status_code == 200:
                        me_data = me_response.json()
                        print("✅ Dados do usuário obtidos:")
                        print(f"   Username: {me_data.get('username')}")
                        print(f"   Email: {me_data.get('email')}")
                        print(f"   Role: {me_data.get('role')}")
                        print(f"   Ativo: {me_data.get('is_active')}")
                    else:
                        print(f"❌ Erro ao obter dados: {me_response.status_code}")
                        print(f"   {me_response.text}")
            else:
                print("❌ LOGIN FALHOU!")
                print()
                try:
                    error_data = response.json()
                    print(f"📋 Detalhes: {error_data.get('detail', 'Erro desconhecido')}")
                except:
                    print(f"📋 Resposta: {response.text}")
                    
        except Exception as e:
            print(f"❌ ERRO: {e}")
            import traceback
            traceback.print_exc()
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_login())

