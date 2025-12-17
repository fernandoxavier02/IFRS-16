"""
Script para verificar conectividade de todos os componentes do sistema:
- Backend API
- Frontend
- Banco de dados PostgreSQL
- Stripe API
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any
import json

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Adicionar backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("❌ Instalando requests...")
    os.system("pip install requests")
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

try:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
except ImportError:
    print("❌ Instalando sqlalchemy...")
    os.system("pip install sqlalchemy asyncpg")
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

from backend.app.config import get_settings

# Configurações
BACKEND_URL = "https://ifrs16-backend-fbbm.onrender.com"
FRONTEND_URL = "https://ifrs-16-1.onrender.com"
ALTERNATIVE_BACKEND_URL = "https://ifrs-16.onrender.com"

# Configurar retry para requests
def get_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# Resultados
results = {
    "timestamp": datetime.now().isoformat(),
    "backend": {},
    "frontend": {},
    "database": {},
    "stripe": {}
}

def print_header(text: str):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_result(component: str, status: str, details: Dict[str, Any] = None):
    status_icon = "✅" if status == "OK" else "❌" if status == "ERRO" else "⚠️"
    print(f"\n{status_icon} {component}: {status}")
    if details:
        for key, value in details.items():
            print(f"   {key}: {value}")

# ============================================================================
# VERIFICAÇÃO DO BACKEND
# ============================================================================

def verificar_backend():
    print_header("VERIFICANDO BACKEND API")
    
    session = get_session()
    backend_urls = [BACKEND_URL, ALTERNATIVE_BACKEND_URL]
    
    backend_ok = False
    backend_details = {}
    
    for url in backend_urls:
        try:
            print(f"\n🔍 Testando: {url}")
            
            # Teste 1: Health check
            print("   → Health check...")
            health_response = session.get(f"{url}/health", timeout=10)
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"      ✅ Health: {health_data}")
                backend_details["health"] = health_data
            else:
                print(f"      ⚠️ Health retornou: {health_response.status_code}")
            
            # Teste 2: Root endpoint
            print("   → Root endpoint...")
            root_response = session.get(f"{url}/", timeout=10)
            if root_response.status_code == 200:
                root_data = root_response.json()
                print(f"      ✅ Root: {root_data.get('name', 'N/A')}")
                backend_details["root"] = root_data
            else:
                print(f"      ⚠️ Root retornou: {root_response.status_code}")
            
            # Teste 3: Docs endpoint
            print("   → Docs endpoint...")
            docs_response = session.get(f"{url}/docs", timeout=10)
            if docs_response.status_code == 200:
                print(f"      ✅ Docs acessível")
                backend_details["docs"] = True
            else:
                print(f"      ⚠️ Docs retornou: {docs_response.status_code}")
            
            # Teste 4: API de autenticação (sem autenticação, deve retornar erro específico)
            print("   → API Auth endpoint...")
            auth_response = session.post(f"{url}/api/auth/login", 
                                       json={"email": "test@test.com", "password": "test"},
                                       timeout=10)
            if auth_response.status_code in [400, 401, 422]:
                print(f"      ✅ Auth endpoint responde (esperado erro de credenciais)")
                backend_details["auth_endpoint"] = "OK"
            else:
                print(f"      ⚠️ Auth retornou: {auth_response.status_code}")
            
            backend_ok = True
            backend_details["url"] = url
            backend_details["status_code"] = health_response.status_code
            results["backend"] = {
                "status": "OK",
                "url": url,
                "details": backend_details
            }
            print_result("Backend", "OK", {"URL": url})
            break
            
        except requests.exceptions.Timeout:
            print(f"      ❌ Timeout ao conectar em {url}")
        except requests.exceptions.ConnectionError:
            print(f"      ❌ Erro de conexão em {url}")
        except Exception as e:
            print(f"      ❌ Erro: {str(e)}")
    
    if not backend_ok:
        results["backend"] = {
            "status": "ERRO",
            "details": "Não foi possível conectar a nenhum backend"
        }
        print_result("Backend", "ERRO", {"Erro": "Não foi possível conectar"})

# ============================================================================
# VERIFICAÇÃO DO FRONTEND
# ============================================================================

def verificar_frontend():
    print_header("VERIFICANDO FRONTEND")
    
    session = get_session()
    frontend_pages = [
        ("Calculadora", f"{FRONTEND_URL}/Calculadora_IFRS16_Deploy.html"),
        ("Login", f"{FRONTEND_URL}/login.html"),
        ("Admin", f"{FRONTEND_URL}/admin.html"),
        ("Pricing", f"{FRONTEND_URL}/pricing.html"),
    ]
    
    frontend_ok = True
    frontend_details = {}
    
    for page_name, url in frontend_pages:
        try:
            print(f"\n🔍 Testando: {page_name} ({url})")
            response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                content_length = len(response.content)
                print(f"   ✅ {page_name}: OK ({content_length} bytes)")
                frontend_details[page_name] = {
                    "status": "OK",
                    "size": content_length,
                    "url": url
                }
            else:
                print(f"   ⚠️ {page_name}: Status {response.status_code}")
                frontend_details[page_name] = {
                    "status": "WARNING",
                    "status_code": response.status_code,
                    "url": url
                }
                frontend_ok = False
                
        except requests.exceptions.Timeout:
            print(f"   ❌ {page_name}: Timeout")
            frontend_details[page_name] = {"status": "ERRO", "erro": "Timeout"}
            frontend_ok = False
        except Exception as e:
            print(f"   ❌ {page_name}: {str(e)}")
            frontend_details[page_name] = {"status": "ERRO", "erro": str(e)}
            frontend_ok = False
    
    results["frontend"] = {
        "status": "OK" if frontend_ok else "ERRO",
        "base_url": FRONTEND_URL,
        "pages": frontend_details
    }
    print_result("Frontend", "OK" if frontend_ok else "ERRO", 
                {"Páginas testadas": len(frontend_pages)})

# ============================================================================
# VERIFICAÇÃO DO BANCO DE DADOS
# ============================================================================

async def verificar_database():
    print_header("VERIFICANDO BANCO DE DADOS")
    
    try:
        settings = get_settings()
        database_url = settings.async_database_url
        
        # Não mostrar a URL completa por segurança
        db_host = database_url.split("@")[1].split("/")[0] if "@" in database_url else "N/A"
        print(f"\n🔍 Conectando ao banco: {db_host}")
        
        # Criar engine
        engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            connect_args={
                "ssl": True if "postgresql" in database_url else False,
                "command_timeout": 30,
                "timeout": 30,
            },
        )
        
        # Teste de conexão
        print("   → Testando conexão...")
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version(), current_database(), current_user"))
            row = result.fetchone()
            
            if row:
                db_version = row[0]
                db_name = row[1]
                db_user = row[2]
                print(f"      ✅ Conectado!")
                print(f"      📊 Database: {db_name}")
                print(f"      👤 User: {db_user}")
                print(f"      🔧 PostgreSQL: {db_version.split(',')[0]}")
                
                # Verificar tabelas
                print("   → Verificando tabelas...")
                tables_result = await conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """))
                tables = [row[0] for row in tables_result.fetchall()]
                print(f"      ✅ Tabelas encontradas: {len(tables)}")
                for table in tables[:10]:  # Mostrar primeiras 10
                    print(f"         - {table}")
                if len(tables) > 10:
                    print(f"         ... e mais {len(tables) - 10}")
                
                # Verificar contagem de registros em tabelas principais
                print("   → Verificando registros...")
                main_tables = ["users", "licenses", "subscriptions"]
                counts = {}
                for table in main_tables:
                    if table in tables:
                        try:
                            count_result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                            count = count_result.scalar()
                            counts[table] = count
                            print(f"      📊 {table}: {count} registros")
                        except:
                            pass
                
                results["database"] = {
                    "status": "OK",
                    "host": db_host,
                    "database": db_name,
                    "user": db_user,
                    "version": db_version.split(',')[0],
                    "tables_count": len(tables),
                    "tables": tables,
                    "counts": counts
                }
                print_result("Database", "OK", {
                    "Database": db_name,
                    "Tabelas": len(tables),
                    "Registros": counts
                })
        
        await engine.dispose()
        
    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ Erro ao conectar: {error_msg}")
        results["database"] = {
            "status": "ERRO",
            "erro": error_msg
        }
        print_result("Database", "ERRO", {"Erro": error_msg[:100]})

# ============================================================================
# VERIFICAÇÃO DO STRIPE (via MCP será feito separadamente)
# ============================================================================

def verificar_stripe_config():
    print_header("VERIFICANDO CONFIGURAÇÃO STRIPE")
    
    try:
        settings = get_settings()
        
        stripe_config = {
            "secret_key": "✅ Configurado" if settings.STRIPE_SECRET_KEY and settings.STRIPE_SECRET_KEY != "sk_test_..." else "❌ Não configurado",
            "publishable_key": "✅ Configurado" if settings.STRIPE_PUBLISHABLE_KEY and settings.STRIPE_PUBLISHABLE_KEY != "pk_test_..." else "❌ Não configurado",
            "webhook_secret": "✅ Configurado" if settings.STRIPE_WEBHOOK_SECRET and settings.STRIPE_WEBHOOK_SECRET != "whsec_..." else "❌ Não configurado",
        }
        
        # Verificar preços
        prices = {}
        price_keys = [
            "STRIPE_PRICE_BASIC_MONTHLY",
            "STRIPE_PRICE_BASIC_YEARLY",
            "STRIPE_PRICE_PRO_MONTHLY",
            "STRIPE_PRICE_PRO_YEARLY",
            "STRIPE_PRICE_ENTERPRISE_MONTHLY",
            "STRIPE_PRICE_ENTERPRISE_YEARLY",
        ]
        
        for key in price_keys:
            value = getattr(settings, key, None)
            prices[key] = "✅ Configurado" if value else "❌ Não configurado"
        
        print("\n📋 Configurações Stripe:")
        for key, value in stripe_config.items():
            print(f"   {key}: {value}")
        
        print("\n💰 Preços configurados:")
        for key, value in prices.items():
            print(f"   {key}: {value}")
        
        all_configured = (
            stripe_config["secret_key"].startswith("✅") and
            stripe_config["publishable_key"].startswith("✅") and
            all(v.startswith("✅") for v in prices.values())
        )
        
        results["stripe"] = {
            "status": "OK" if all_configured else "WARNING",
            "config": stripe_config,
            "prices": prices
        }
        
        print_result("Stripe Config", "OK" if all_configured else "WARNING", 
                    {"Configurado": "Sim" if all_configured else "Parcial"})
        
    except Exception as e:
        print(f"   ❌ Erro ao verificar configuração: {str(e)}")
        results["stripe"] = {
            "status": "ERRO",
            "erro": str(e)
        }
        print_result("Stripe Config", "ERRO", {"Erro": str(e)})

# ============================================================================
# MAIN
# ============================================================================

async def main():
    print("\n" + "="*60)
    print("  🔍 VERIFICAÇÃO DE CONECTIVIDADE - IFRS 16")
    print("="*60)
    print(f"  Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar Backend
    verificar_backend()
    
    # Verificar Frontend
    verificar_frontend()
    
    # Verificar Database
    await verificar_database()
    
    # Verificar Stripe Config
    verificar_stripe_config()
    
    # Resumo final
    print_header("RESUMO FINAL")
    
    total_checks = 4
    ok_count = sum([
        1 if results["backend"].get("status") == "OK" else 0,
        1 if results["frontend"].get("status") == "OK" else 0,
        1 if results["database"].get("status") == "OK" else 0,
        1 if results["stripe"].get("status") == "OK" else 0,
    ])
    
    print(f"\n✅ Componentes OK: {ok_count}/{total_checks}")
    print(f"❌ Componentes com erro: {total_checks - ok_count}/{total_checks}")
    
    # Salvar resultados em JSON
    output_file = "conectividade_resultado.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Resultados salvos em: {output_file}")
    
    return results

if __name__ == "__main__":
    try:
        results = asyncio.run(main())
        sys.exit(0 if all(r.get("status") == "OK" for r in results.values() if isinstance(r, dict) and "status" in r) else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Verificação interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
