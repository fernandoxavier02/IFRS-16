"""
Teste de Conectividade em Produção - MCPs IFRS 16
=================================================

Este script testa a conectividade REAL com os serviços em produção:
- Stripe
- Firebase
- Google Cloud SQL

IMPORTANTE: Apenas operações de LEITURA são executadas.
Nenhum dado é criado, modificado ou deletado.
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import Dict, Any

# Adicionar diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ProductionConnectivityTest:
    """Testa conectividade com serviços de produção"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0
            }
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log formatado"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        icons = {"INFO": "ℹ️", "OK": "✅", "FAIL": "❌", "WARN": "⚠️", "SKIP": "⏭️"}
        icon = icons.get(level, "•")
        print(f"[{timestamp}] {icon} {message}")
    
    def record_result(self, test_name: str, success: bool, details: Dict = None, skipped: bool = False):
        """Registra resultado do teste"""
        self.results["tests"][test_name] = {
            "success": success,
            "skipped": skipped,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.results["summary"]["total"] += 1
        if skipped:
            self.results["summary"]["skipped"] += 1
        elif success:
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
    
    # =========================================================================
    # STRIPE
    # =========================================================================
    
    async def test_stripe_connection(self) -> bool:
        """Testa conexão com Stripe - SOMENTE LEITURA"""
        self.log("Testando conexão com Stripe...", "INFO")
        
        try:
            import stripe
            
            # Verificar se há API key configurada
            api_key = os.getenv("STRIPE_SECRET_KEY")
            if not api_key:
                self.log("STRIPE_SECRET_KEY não configurada", "SKIP")
                self.record_result("stripe_connection", False, 
                    {"error": "API key não configurada"}, skipped=True)
                return False
            
            stripe.api_key = api_key
            
            # Teste 1: Listar produtos (somente leitura)
            self.log("  → Listando produtos...", "INFO")
            products = stripe.Product.list(limit=5, active=True)
            product_count = len(products.data)
            self.log(f"  → {product_count} produtos encontrados", "OK")
            
            # Teste 2: Listar preços (somente leitura)
            self.log("  → Listando preços...", "INFO")
            prices = stripe.Price.list(limit=10, active=True)
            price_count = len(prices.data)
            self.log(f"  → {price_count} preços encontrados", "OK")
            
            # Teste 3: Verificar saldo (somente leitura)
            self.log("  → Verificando saldo...", "INFO")
            balance = stripe.Balance.retrieve()
            available = sum(b.amount for b in balance.available) / 100
            pending = sum(b.amount for b in balance.pending) / 100
            self.log(f"  → Saldo disponível: R$ {available:.2f}", "OK")
            self.log(f"  → Saldo pendente: R$ {pending:.2f}", "OK")
            
            # Teste 4: Listar webhooks configurados (somente leitura)
            self.log("  → Listando webhooks...", "INFO")
            webhooks = stripe.WebhookEndpoint.list(limit=5)
            webhook_count = len(webhooks.data)
            self.log(f"  → {webhook_count} webhooks configurados", "OK")
            
            self.log("Stripe: Conexão OK!", "OK")
            self.record_result("stripe_connection", True, {
                "products": product_count,
                "prices": price_count,
                "balance_available": available,
                "balance_pending": pending,
                "webhooks": webhook_count,
                "products_list": [{"id": p.id, "name": p.name} for p in products.data],
                "prices_list": [{"id": p.id, "amount": p.unit_amount/100 if p.unit_amount else 0} for p in prices.data]
            })
            return True
            
        except Exception as e:
            self.log(f"Stripe: ERRO - {str(e)}", "FAIL")
            self.record_result("stripe_connection", False, {"error": str(e)})
            return False
    
    # =========================================================================
    # FIREBASE
    # =========================================================================
    
    async def test_firebase_connection(self) -> bool:
        """Testa conexão com Firebase - SOMENTE LEITURA"""
        self.log("Testando conexão com Firebase...", "INFO")
        
        try:
            import firebase_admin
            from firebase_admin import credentials, auth
            
            # Verificar credenciais
            cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            project_id = os.getenv("FIREBASE_PROJECT_ID", "ifrs16-app")
            
            if not cred_path and not firebase_admin._apps:
                self.log("GOOGLE_APPLICATION_CREDENTIALS não configurada", "SKIP")
                self.record_result("firebase_connection", False,
                    {"error": "Credenciais não configuradas"}, skipped=True)
                return False
            
            # Inicializar se necessário
            if not firebase_admin._apps:
                if cred_path and os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred, {"projectId": project_id})
                else:
                    # Tentar Application Default Credentials
                    cred = credentials.ApplicationDefault()
                    firebase_admin.initialize_app(cred, {"projectId": project_id})
            
            # Teste 1: Listar usuários do Auth (somente leitura)
            self.log("  → Conectando ao Firebase Auth...", "INFO")
            users_page = auth.list_users(max_results=5)
            user_count = len(users_page.users)
            self.log(f"  → {user_count} usuários encontrados no Auth", "OK")
            
            # Mostrar emails (parcialmente ocultos)
            for user in users_page.users:
                email = user.email or "N/A"
                if "@" in email:
                    parts = email.split("@")
                    masked = parts[0][:3] + "***@" + parts[1]
                else:
                    masked = email
                self.log(f"    • {masked} (uid: {user.uid[:8]}...)", "INFO")
            
            self.log("Firebase Auth: Conexão OK!", "OK")
            self.record_result("firebase_connection", True, {
                "project_id": project_id,
                "auth_users_count": user_count,
                "users_list": [{"uid": u.uid, "email": u.email} for u in users_page.users]
            })
            return True
            
        except Exception as e:
            self.log(f"Firebase: ERRO - {str(e)}", "FAIL")
            self.record_result("firebase_connection", False, {"error": str(e)})
            return False
    
    # =========================================================================
    # CLOUD SQL
    # =========================================================================
    
    async def test_cloudsql_connection(self) -> bool:
        """Testa conexão com Cloud SQL - SOMENTE LEITURA"""
        self.log("Testando conexão com Cloud SQL...", "INFO")
        
        try:
            import asyncpg
            
            # Verificar connection string
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                self.log("DATABASE_URL não configurada", "SKIP")
                self.record_result("cloudsql_connection", False,
                    {"error": "DATABASE_URL não configurada"}, skipped=True)
                return False
            
            # Extrair parâmetros da URL
            import urllib.parse
            parsed = urllib.parse.urlparse(db_url.replace("+asyncpg", ""))
            
            self.log(f"  → Conectando a {parsed.hostname}...", "INFO")
            
            # Conectar
            conn = await asyncpg.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip('/'),
                ssl='require' if 'sslmode=require' in db_url else None
            )
            
            try:
                # Teste 1: Health check
                self.log("  → Executando health check...", "INFO")
                result = await conn.fetchrow("SELECT 1 as ok, NOW() as timestamp, version() as version")
                self.log(f"  → Banco respondendo: {result['timestamp']}", "OK")
                
                # Teste 2: Listar tabelas (somente leitura)
                self.log("  → Listando tabelas...", "INFO")
                tables = await conn.fetch("""
                    SELECT table_name, 
                           (SELECT COUNT(*) FROM information_schema.columns 
                            WHERE table_name = t.table_name AND table_schema = 'public') as columns
                    FROM information_schema.tables t
                    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
                table_names = [t['table_name'] for t in tables]
                self.log(f"  → {len(table_names)} tabelas encontradas", "OK")
                
                # Teste 3: Contar registros em tabelas principais (somente leitura)
                self.log("  → Contando registros...", "INFO")
                counts = {}
                for table in ['users', 'licenses', 'subscriptions', 'admin_users']:
                    if table in table_names:
                        count = await conn.fetchval(f'SELECT COUNT(*) FROM "{table}"')
                        counts[table] = count
                        self.log(f"    • {table}: {count} registros", "INFO")
                
                # Teste 4: Verificar tamanho do banco (somente leitura)
                self.log("  → Verificando tamanho do banco...", "INFO")
                size = await conn.fetchrow("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size,
                           pg_database_size(current_database()) as size_bytes
                """)
                self.log(f"  → Tamanho do banco: {size['size']}", "OK")
                
                # Teste 5: Verificar conexões ativas (somente leitura)
                self.log("  → Verificando conexões ativas...", "INFO")
                connections = await conn.fetchval("""
                    SELECT COUNT(*) FROM pg_stat_activity 
                    WHERE datname = current_database()
                """)
                self.log(f"  → {connections} conexões ativas", "OK")
                
                self.log("Cloud SQL: Conexão OK!", "OK")
                self.record_result("cloudsql_connection", True, {
                    "host": parsed.hostname,
                    "database": parsed.path.lstrip('/'),
                    "tables": table_names,
                    "record_counts": counts,
                    "database_size": size['size'],
                    "active_connections": connections,
                    "postgres_version": result['version'][:50] + "..."
                })
                return True
                
            finally:
                await conn.close()
            
        except Exception as e:
            self.log(f"Cloud SQL: ERRO - {str(e)}", "FAIL")
            self.record_result("cloudsql_connection", False, {"error": str(e)})
            return False
    
    # =========================================================================
    # TESTE INTEGRADO
    # =========================================================================
    
    async def test_api_backend(self) -> bool:
        """Testa API do backend IFRS 16 - SOMENTE LEITURA"""
        self.log("Testando API do Backend...", "INFO")
        
        try:
            import aiohttp
            
            api_url = os.getenv("API_URL", "https://ifrs16-backend-1051753255664.us-central1.run.app")
            
            async with aiohttp.ClientSession() as session:
                # Teste 1: Health check
                self.log(f"  → Testando {api_url}/health...", "INFO")
                async with session.get(f"{api_url}/health", timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.log(f"  → Health: {data.get('status', 'ok')}", "OK")
                    else:
                        self.log(f"  → Health: Status {resp.status}", "WARN")
                
                # Teste 2: Root endpoint
                self.log(f"  → Testando {api_url}/...", "INFO")
                async with session.get(f"{api_url}/", timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.log(f"  → API: {data.get('message', 'ok')}", "OK")
                
                # Teste 3: Preços públicos
                self.log(f"  → Testando {api_url}/api/payments/prices...", "INFO")
                async with session.get(f"{api_url}/api/payments/prices", timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.log(f"  → Preços: {len(data.get('prices', []))} planos", "OK")
            
            self.log("API Backend: Conexão OK!", "OK")
            self.record_result("api_backend", True, {"api_url": api_url})
            return True
            
        except Exception as e:
            self.log(f"API Backend: ERRO - {str(e)}", "FAIL")
            self.record_result("api_backend", False, {"error": str(e)})
            return False
    
    # =========================================================================
    # EXECUTAR TODOS OS TESTES
    # =========================================================================
    
    async def run_all_tests(self):
        """Executa todos os testes de conectividade"""
        print("\n" + "="*60)
        print("  TESTE DE CONECTIVIDADE - PRODUÇÃO")
        print("  IFRS 16 - MCPs (Stripe, Firebase, Cloud SQL)")
        print("="*60 + "\n")
        
        self.log("Iniciando testes de conectividade...", "INFO")
        self.log("MODO: Somente leitura (dados não serão modificados)\n", "WARN")
        
        # Executar testes
        await self.test_stripe_connection()
        print()
        await self.test_firebase_connection()
        print()
        await self.test_cloudsql_connection()
        print()
        await self.test_api_backend()
        
        # Resumo
        print("\n" + "="*60)
        print("  RESUMO DOS TESTES")
        print("="*60)
        
        summary = self.results["summary"]
        print(f"\n  Total de testes: {summary['total']}")
        print(f"  ✅ Aprovados:    {summary['passed']}")
        print(f"  ❌ Falhos:       {summary['failed']}")
        print(f"  ⏭️  Pulados:      {summary['skipped']}")
        
        # Status por serviço
        print("\n  Status por serviço:")
        for test_name, result in self.results["tests"].items():
            if result["skipped"]:
                status = "⏭️  PULADO"
            elif result["success"]:
                status = "✅ OK"
            else:
                status = "❌ FALHOU"
            print(f"    • {test_name}: {status}")
        
        print("\n" + "="*60 + "\n")
        
        return self.results
    
    def save_report(self, filepath: str = None):
        """Salva relatório em JSON"""
        if filepath is None:
            filepath = f"connectivity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        self.log(f"Relatório salvo em: {filepath}", "OK")
        return filepath


async def main():
    """Função principal"""
    tester = ProductionConnectivityTest()
    results = await tester.run_all_tests()
    
    # Salvar relatório
    report_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        f"connectivity_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    tester.save_report(report_path)
    
    # Retornar código de saída
    if results["summary"]["failed"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
