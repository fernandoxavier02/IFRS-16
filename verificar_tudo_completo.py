"""
Script completo de verificação de conectividade
Inclui verificação do Stripe via API direta (não MCP)
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

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("Instalando requests...")
    os.system("pip install requests")
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

try:
    import stripe
except ImportError:
    print("Instalando stripe...")
    os.system("pip install stripe")
    import stripe

from backend.app.config import get_settings

# URLs
BACKEND_URLS = [
    "https://ifrs16-backend-fbbm.onrender.com",
    "https://ifrs-16.onrender.com"
]
FRONTEND_URL = "https://ifrs-16-1.onrender.com"

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
# BACKEND
# ============================================================================

def verificar_backend():
    print_header("VERIFICANDO BACKEND API")
    
    session = get_session()
    backend_ok = False
    
    for url in BACKEND_URLS:
        try:
            print(f"\n🔍 Testando: {url}")
            
            # Health check com timeout maior (serviço pode estar dormindo)
            print("   → Health check (aguardando serviço acordar...)")
            try:
                health_response = session.get(f"{url}/health", timeout=60)
                if health_response.status_code == 200:
                    health_data = health_response.json()
                    print(f"      ✅ Health: {health_data}")
                    backend_ok = True
                    results["backend"] = {
                        "status": "OK",
                        "url": url,
                        "health": health_data
                    }
                    break
                else:
                    print(f"      ⚠️ Health retornou: {health_response.status_code}")
            except requests.exceptions.Timeout:
                print(f"      ⚠️ Timeout (serviço pode estar dormindo)")
            
            # Root endpoint
            print("   → Root endpoint...")
            try:
                root_response = session.get(f"{url}/", timeout=30)
                if root_response.status_code == 200:
                    root_data = root_response.json()
                    print(f"      ✅ Root: {root_data.get('name', 'N/A')}")
                    if not backend_ok:
                        backend_ok = True
                        results["backend"] = {
                            "status": "OK",
                            "url": url,
                            "root": root_data
                        }
                        break
            except:
                pass
                
        except Exception as e:
            print(f"      ❌ Erro: {str(e)[:100]}")
    
    if not backend_ok:
        results["backend"] = {
            "status": "WARNING",
            "details": "Serviço pode estar dormindo (Render free tier)"
        }
        print_result("Backend", "WARNING", {"Nota": "Serviço pode estar dormindo"})

# ============================================================================
# FRONTEND
# ============================================================================

def verificar_frontend():
    print_header("VERIFICANDO FRONTEND")
    
    session = get_session()
    pages = [
        ("Calculadora", f"{FRONTEND_URL}/Calculadora_IFRS16_Deploy.html"),
        ("Login", f"{FRONTEND_URL}/login.html"),
        ("Admin", f"{FRONTEND_URL}/admin.html"),
        ("Pricing", f"{FRONTEND_URL}/pricing.html"),
    ]
    
    frontend_ok = True
    frontend_details = {}
    
    for page_name, url in pages:
        try:
            print(f"\n🔍 {page_name}...")
            response = session.get(url, timeout=10)
            if response.status_code == 200:
                size = len(response.content)
                print(f"   ✅ OK ({size:,} bytes)")
                frontend_details[page_name] = {"status": "OK", "size": size}
            else:
                print(f"   ⚠️ Status {response.status_code}")
                frontend_details[page_name] = {"status": "WARNING", "code": response.status_code}
                frontend_ok = False
        except Exception as e:
            print(f"   ❌ Erro: {str(e)[:50]}")
            frontend_details[page_name] = {"status": "ERRO", "erro": str(e)[:100]}
            frontend_ok = False
    
    results["frontend"] = {
        "status": "OK" if frontend_ok else "ERRO",
        "pages": frontend_details
    }
    print_result("Frontend", "OK" if frontend_ok else "ERRO")

# ============================================================================
# DATABASE
# ============================================================================

async def verificar_database():
    print_header("VERIFICANDO BANCO DE DADOS")
    
    try:
        settings = get_settings()
        database_url = settings.async_database_url
        
        # Verificar se é localhost (não vai funcionar)
        if "localhost" in database_url or "127.0.0.1" in database_url:
            print("\n⚠️  DATABASE_URL aponta para localhost")
            print("   Para testar, configure as variáveis de ambiente do Render")
            results["database"] = {
                "status": "SKIP",
                "reason": "Localhost - requer variáveis de ambiente do Render"
            }
            return
        
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import create_async_engine
        
        db_host = database_url.split("@")[1].split("/")[0] if "@" in database_url else "N/A"
        print(f"\n🔍 Conectando: {db_host}")
        
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
        
        print("   → Testando conexão...")
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version(), current_database(), current_user"))
            row = result.fetchone()
            
            if row:
                print(f"      ✅ Conectado!")
                print(f"      📊 Database: {row[1]}")
                print(f"      👤 User: {row[2]}")
                
                # Tabelas
                tables_result = await conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """))
                tables = [r[0] for r in tables_result.fetchall()]
                print(f"      ✅ Tabelas: {len(tables)}")
                
                results["database"] = {
                    "status": "OK",
                    "database": row[1],
                    "user": row[2],
                    "tables_count": len(tables),
                    "tables": tables
                }
                print_result("Database", "OK", {"Tabelas": len(tables)})
        
        await engine.dispose()
        
    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ Erro: {error_msg[:100]}")
        results["database"] = {
            "status": "ERRO",
            "erro": error_msg[:200]
        }
        print_result("Database", "ERRO")

# ============================================================================
# STRIPE
# ============================================================================

def verificar_stripe():
    print_header("VERIFICANDO STRIPE")
    
    try:
        settings = get_settings()
        
        if not settings.STRIPE_SECRET_KEY or settings.STRIPE_SECRET_KEY == "sk_test_...":
            print("\n⚠️  STRIPE_SECRET_KEY não configurada localmente")
            print("   (Configuração existe no Render, mas não localmente)")
            results["stripe"] = {
                "status": "SKIP",
                "reason": "Chaves não configuradas localmente"
            }
            return
        
        # Configurar Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        print("\n🔍 Testando API Stripe...")
        
        # 1. Verificar saldo
        print("   → Verificando saldo...")
        try:
            balance = stripe.Balance.retrieve()
            print(f"      ✅ Saldo disponível: R$ {balance.available[0].amount / 100:.2f} {balance.available[0].currency.upper()}")
            results["stripe"] = {
                "status": "OK",
                "balance": {
                    "amount": balance.available[0].amount / 100,
                    "currency": balance.available[0].currency
                }
            }
        except Exception as e:
            print(f"      ❌ Erro ao verificar saldo: {str(e)[:100]}")
            results["stripe"] = {"status": "ERRO", "erro": str(e)[:200]}
            return
        
        # 2. Listar produtos
        print("   → Listando produtos...")
        try:
            products = stripe.Product.list(limit=5)
            print(f"      ✅ Produtos encontrados: {len(products.data)}")
            for p in products.data[:3]:
                print(f"         - {p.name} ({p.id})")
        except Exception as e:
            print(f"      ⚠️ Erro ao listar produtos: {str(e)[:100]}")
        
        # 3. Listar preços
        print("   → Listando preços...")
        try:
            prices = stripe.Price.list(limit=10)
            print(f"      ✅ Preços encontrados: {len(prices.data)}")
            
            # Verificar se os preços configurados existem
            expected_prices = [
                settings.STRIPE_PRICE_BASIC_MONTHLY,
                settings.STRIPE_PRICE_BASIC_YEARLY,
                settings.STRIPE_PRICE_PRO_MONTHLY,
                settings.STRIPE_PRICE_PRO_YEARLY,
                settings.STRIPE_PRICE_ENTERPRISE_MONTHLY,
                settings.STRIPE_PRICE_ENTERPRISE_YEARLY,
            ]
            
            price_ids = {p.id for p in prices.data}
            found_prices = [p for p in expected_prices if p and p in price_ids]
            print(f"      ✅ Preços configurados encontrados: {len(found_prices)}/{len([p for p in expected_prices if p])}")
        except Exception as e:
            print(f"      ⚠️ Erro ao listar preços: {str(e)[:100]}")
        
        print_result("Stripe", "OK", {"API": "Funcionando"})
        
    except Exception as e:
        print(f"   ❌ Erro: {str(e)[:100]}")
        results["stripe"] = {"status": "ERRO", "erro": str(e)[:200]}
        print_result("Stripe", "ERRO")

# ============================================================================
# MAIN
# ============================================================================

async def main():
    print("\n" + "="*60)
    print("  🔍 VERIFICAÇÃO COMPLETA DE CONECTIVIDADE")
    print("="*60)
    print(f"  Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    verificar_backend()
    verificar_frontend()
    await verificar_database()
    verificar_stripe()
    
    # Resumo
    print_header("RESUMO FINAL")
    
    statuses = {
        "backend": results["backend"].get("status", "UNKNOWN"),
        "frontend": results["frontend"].get("status", "UNKNOWN"),
        "database": results["database"].get("status", "UNKNOWN"),
        "stripe": results["stripe"].get("status", "UNKNOWN"),
    }
    
    ok_count = sum(1 for s in statuses.values() if s == "OK")
    total = len([s for s in statuses.values() if s != "SKIP"])
    
    print(f"\n✅ Componentes OK: {ok_count}/{total}")
    print(f"⚠️  Componentes com aviso: {sum(1 for s in statuses.values() if s == 'WARNING')}")
    print(f"❌ Componentes com erro: {sum(1 for s in statuses.values() if s == 'ERRO')}")
    print(f"⏭️  Componentes pulados: {sum(1 for s in statuses.values() if s == 'SKIP')}")
    
    # Salvar resultados
    output_file = "conectividade_completo.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Resultados salvos em: {output_file}")
    
    return results

if __name__ == "__main__":
    try:
        results = asyncio.run(main())
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n⚠️ Verificação interrompida")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
