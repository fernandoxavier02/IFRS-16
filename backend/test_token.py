"""
Script para testar o token JWT do administrador
"""

import asyncio
import sys
import httpx
sys.path.insert(0, '.')

from app.config import get_settings

settings = get_settings()


async def test_token():
    print("=" * 50)
    print("🧪 Testar Token de Administrador - IFRS 16")
    print("=" * 50)
    print()
    
    # Credenciais
    email = "fernandocostaxavier@gmail.com"
    password = "Admin123!"
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. Fazer login para obter token
            print("1️⃣ Fazendo login...")
            login_response = await client.post(
                f"{settings.API_URL}/api/auth/admin/login",
                json={
                    "email": email,
                    "password": password
                },
                timeout=10.0
            )
            
            if login_response.status_code != 200:
                print(f"❌ Erro no login: {login_response.status_code}")
                print(f"   Resposta: {login_response.text}")
                return
            
            token = login_response.json().get("access_token")
            print(f"✅ Token obtido: {token[:50]}...")
            print()
            
            # 2. Testar endpoint que requer admin
            print("2️⃣ Testando endpoint /api/admin/licenses...")
            headers = {
                "Authorization": f"Bearer {token}"
            }
            
            test_response = await client.get(
                f"{settings.API_URL}/api/admin/licenses",
                headers=headers,
                timeout=10.0
            )
            
            print(f"   Status Code: {test_response.status_code}")
            
            if test_response.status_code == 200:
                print("✅ Token funcionando corretamente!")
                data = test_response.json()
                print(f"   Licenças encontradas: {len(data)}")
            elif test_response.status_code == 401:
                print("❌ Token inválido ou expirado")
                print(f"   Resposta: {test_response.text}")
            elif test_response.status_code == 403:
                print("❌ Acesso negado (sem permissão)")
                print(f"   Resposta: {test_response.text}")
            else:
                print(f"❌ Erro inesperado: {test_response.status_code}")
                print(f"   Resposta: {test_response.text}")
            
            print()
            
            # 3. Testar endpoint /api/auth/admin/me
            print("3️⃣ Testando endpoint /api/auth/admin/me...")
            me_response = await client.get(
                f"{settings.API_URL}/api/auth/admin/me",
                headers=headers,
                timeout=10.0
            )
            
            print(f"   Status Code: {me_response.status_code}")
            
            if me_response.status_code == 200:
                data = me_response.json()
                print("✅ Token válido!")
                print(f"   Username: {data.get('username')}")
                print(f"   Email: {data.get('email')}")
                print(f"   Role: {data.get('role')}")
            else:
                print(f"❌ Erro: {me_response.status_code}")
                print(f"   Resposta: {me_response.text}")
                
        except httpx.ConnectError:
            print("❌ Erro: Não foi possível conectar ao servidor")
            print("   Certifique-se de que o servidor está rodando em http://localhost:8000")
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_token())

