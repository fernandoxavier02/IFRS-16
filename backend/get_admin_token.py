"""
Script para obter o token JWT do administrador
"""

import asyncio
import sys
import httpx
sys.path.insert(0, '.')

from app.config import get_settings

settings = get_settings()


async def get_admin_token():
    print("=" * 50)
    print("🔑 Obter Token de Administrador - IFRS 16")
    print("=" * 50)
    print()
    
    # Credenciais
    email = "fernandocostaxavier@gmail.com"
    password = "Admin123!"
    
    print(f"📧 Email: {email}")
    print(f"🔐 Fazendo login...")
    print()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.API_URL}/api/auth/admin/login",
                json={
                    "email": email,
                    "password": password
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                
                print("=" * 50)
                print("✅ Login realizado com sucesso!")
                print("=" * 50)
                print()
                print("🔑 TOKEN JWT:")
                print("-" * 50)
                print(token)
                print("-" * 50)
                print()
                print("📋 Como usar:")
                print("   Adicione no header das requisições:")
                print(f'   Authorization: Bearer {token}')
                print()
                print("💡 Exemplo com curl:")
                print(f'   curl -H "Authorization: Bearer {token}" \\')
                print(f'        http://localhost:8000/api/admin/licenses')
                print()
            else:
                print(f"❌ Erro ao fazer login: {response.status_code}")
                print(f"   Resposta: {response.text}")
                
        except httpx.ConnectError:
            print("❌ Erro: Não foi possível conectar ao servidor")
            print("   Certifique-se de que o servidor está rodando em http://localhost:8000")
        except Exception as e:
            print(f"❌ Erro: {str(e)}")


if __name__ == "__main__":
    asyncio.run(get_admin_token())

