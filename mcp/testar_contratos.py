import asyncio
import aiohttp
import json

API_URL = "https://ifrs16-backend-1051753255664.us-central1.run.app"

async def test_contracts():
    """Testa os endpoints de contratos"""
    
    async with aiohttp.ClientSession() as session:
        print("=" * 60)
        print("🧪 TESTES DE ENDPOINTS DE CONTRATOS")
        print("=" * 60)
        
        # 1. Testar health check
        print("\n1️⃣ Testando health check...")
        async with session.get(f"{API_URL}/health") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"   ✅ Health: {data}")
            else:
                print(f"   ❌ Erro: {resp.status}")
        
        # 2. Testar endpoint sem token (deve retornar 401)
        print("\n2️⃣ Testando /api/contracts sem token (esperado: 401)...")
        async with session.get(f"{API_URL}/api/contracts") as resp:
            if resp.status == 401:
                print(f"   ✅ Retornou 401 como esperado")
            else:
                print(f"   ❌ Esperado 401, recebeu: {resp.status}")
        
        # 3. Testar CORS preflight
        print("\n3️⃣ Testando CORS preflight...")
        headers = {
            "Origin": "https://ifrs16-app.web.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type"
        }
        async with session.options(f"{API_URL}/api/contracts", headers=headers) as resp:
            if resp.status == 200:
                cors_origin = resp.headers.get("access-control-allow-origin", "")
                cors_methods = resp.headers.get("access-control-allow-methods", "")
                print(f"   ✅ CORS OK")
                print(f"      Allow-Origin: {cors_origin}")
                print(f"      Allow-Methods: {cors_methods}")
            else:
                print(f"   ❌ CORS falhou: {resp.status}")
        
        # 4. Obter um token válido para testes (login)
        print("\n4️⃣ Obtendo token de teste...")
        # Primeiro, vamos tentar fazer login com um usuário de teste
        login_data = {
            "email": "teste@teste.com",
            "password": "teste123"
        }
        async with session.post(
            f"{API_URL}/api/auth/login",
            json=login_data
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                token = data.get("access_token") or data.get("token")
                print(f"   ✅ Login OK, token obtido")
            else:
                # Tentar com outro usuário
                print(f"   ⚠️ Login falhou ({resp.status}), tentando outro método...")
                token = None
        
        if not token:
            # Tentar validar uma licença existente
            print("   Tentando obter token via licença...")
            # Vamos usar um token fake para testar a estrutura
            token = "fake_token_for_structure_test"
        
        # 5. Testar criação de contrato (com token)
        print("\n5️⃣ Testando POST /api/contracts...")
        contract_data = {
            "name": "Contrato de Teste",
            "description": "Teste automatizado",
            "contract_code": "TEST-001",
            "status": "draft"
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Origin": "https://ifrs16-app.web.app"
        }
        async with session.post(
            f"{API_URL}/api/contracts",
            json=contract_data,
            headers=headers
        ) as resp:
            response_text = await resp.text()
            print(f"   Status: {resp.status}")
            if resp.status in [200, 201]:
                print(f"   ✅ Contrato criado!")
                print(f"   Resposta: {response_text[:200]}")
            elif resp.status == 401:
                print(f"   ⚠️ Token inválido (esperado para token fake)")
            elif resp.status == 403:
                print(f"   ⚠️ Sem licença ativa")
            else:
                print(f"   ❌ Erro: {response_text[:300]}")
            
            # Verificar se CORS está presente na resposta
            cors_header = resp.headers.get("access-control-allow-origin", "")
            if cors_header:
                print(f"   ✅ CORS header presente: {cors_header}")
            else:
                print(f"   ⚠️ CORS header ausente na resposta")
        
        # 6. Testar listagem de contratos
        print("\n6️⃣ Testando GET /api/contracts...")
        async with session.get(
            f"{API_URL}/api/contracts",
            headers=headers
        ) as resp:
            print(f"   Status: {resp.status}")
            if resp.status == 200:
                data = await resp.json()
                print(f"   ✅ Listagem OK")
                print(f"   Contratos: {len(data.get('contracts', []))}")
            elif resp.status == 401:
                print(f"   ⚠️ Token inválido")
            else:
                response_text = await resp.text()
                print(f"   ❌ Erro: {response_text[:200]}")
        
        print("\n" + "=" * 60)
        print("🏁 TESTES CONCLUÍDOS")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_contracts())
