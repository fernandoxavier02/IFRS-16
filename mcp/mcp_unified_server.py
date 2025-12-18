"""
MCP Unified Server - Servidor unificado para Stripe, Firebase e Cloud SQL
=========================================================================

Este servidor combina todos os MCPs em uma única interface,
permitindo operações coordenadas entre os serviços.
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any

from stripe_mcp_server import StripeMCPServer
from firebase_mcp_server import FirebaseMCPServer
from cloudsql_mcp_server import CloudSQLMCPServer


class UnifiedMCPServer:
    """
    Servidor MCP unificado que coordena operações entre:
    - Stripe (pagamentos)
    - Firebase (auth, firestore)
    - Cloud SQL (banco de dados principal)
    """
    
    def __init__(
        self,
        stripe_api_key: str = None,
        firebase_project_id: str = None,
        firebase_credentials_path: str = None,
        database_url: str = None
    ):
        """
        Inicializa todos os servidores MCP.
        
        Args:
            stripe_api_key: Chave secreta do Stripe
            firebase_project_id: ID do projeto Firebase
            firebase_credentials_path: Caminho para o arquivo de credenciais Firebase
            database_url: URL de conexão com o Cloud SQL
        """
        # Stripe
        self.stripe = StripeMCPServer(
            api_key=stripe_api_key or os.getenv("STRIPE_SECRET_KEY")
        )
        
        # Firebase
        self.firebase = FirebaseMCPServer(
            credentials_path=firebase_credentials_path,
            project_id=firebase_project_id or os.getenv("FIREBASE_PROJECT_ID", "ifrs16-app")
        )
        
        # Cloud SQL
        self.cloudsql = CloudSQLMCPServer(
            connection_string=database_url or os.getenv("DATABASE_URL")
        )
    
    async def close(self):
        """Fecha todas as conexões"""
        await self.cloudsql.close()
    
    # =========================================================================
    # OPERAÇÕES COORDENADAS
    # =========================================================================
    
    async def sync_stripe_customer_to_db(self, stripe_customer_id: str) -> Dict:
        """
        Sincroniza dados de um cliente Stripe com o banco de dados.
        """
        # Buscar cliente no Stripe
        customer = await self.stripe.get_customer(stripe_customer_id)
        
        if not customer:
            return {"success": False, "error": "Cliente não encontrado no Stripe"}
        
        # Verificar se existe no banco
        db_user = await self.cloudsql.get_user_by_email(customer["email"])
        
        if db_user:
            # Atualizar stripe_customer_id se necessário
            if not db_user.get("stripe_customer_id"):
                await self.cloudsql.update(
                    "users",
                    {"stripe_customer_id": stripe_customer_id},
                    {"id": db_user["id"]}
                )
                return {
                    "success": True,
                    "action": "updated",
                    "user_id": str(db_user["id"])
                }
            return {
                "success": True,
                "action": "already_synced",
                "user_id": str(db_user["id"])
            }
        
        return {
            "success": False,
            "error": "Usuário não encontrado no banco de dados",
            "stripe_email": customer["email"]
        }
    
    async def get_user_full_profile(self, email: str) -> Dict:
        """
        Retorna perfil completo do usuário de todas as fontes.
        """
        result = {
            "email": email,
            "database": None,
            "stripe": None,
            "firebase_auth": None,
            "licenses": [],
            "subscriptions": []
        }
        
        # Dados do banco
        db_user = await self.cloudsql.get_user_by_email(email)
        if db_user:
            result["database"] = db_user
            
            # Licenças
            licenses = await self.cloudsql.select(
                "licenses",
                where={"user_id": db_user["id"]}
            )
            result["licenses"] = licenses
            
            # Assinaturas
            subscriptions = await self.cloudsql.select(
                "subscriptions",
                where={"user_id": db_user["id"]}
            )
            result["subscriptions"] = subscriptions
            
            # Dados do Stripe
            if db_user.get("stripe_customer_id"):
                try:
                    stripe_customer = await self.stripe.get_customer(
                        db_user["stripe_customer_id"]
                    )
                    result["stripe"] = stripe_customer
                except:
                    pass
        
        # Dados do Firebase Auth
        try:
            firebase_user = await self.firebase.auth_get_user_by_email(email)
            result["firebase_auth"] = firebase_user
        except:
            pass
        
        return result
    
    async def revoke_user_access(self, email: str, reason: str = None) -> Dict:
        """
        Revoga acesso de um usuário em todos os sistemas.
        """
        results = {
            "email": email,
            "database": None,
            "stripe": None,
            "firebase": None
        }
        
        # 1. Revogar licenças no banco
        db_user = await self.cloudsql.get_user_by_email(email)
        if db_user:
            # Revogar todas as licenças
            await self.cloudsql.execute_query(
                """
                UPDATE licenses 
                SET status = 'cancelled', revoked = true, 
                    revoked_at = NOW(), revoke_reason = $1
                WHERE user_id = $2
                """,
                [reason or "Acesso revogado", db_user["id"]],
                fetch=False
            )
            
            # Cancelar assinaturas no banco
            await self.cloudsql.execute_query(
                """
                UPDATE subscriptions 
                SET status = 'cancelled', cancelled_at = NOW()
                WHERE user_id = $1
                """,
                [db_user["id"]],
                fetch=False
            )
            
            results["database"] = {"success": True, "user_id": str(db_user["id"])}
            
            # 2. Cancelar assinatura no Stripe
            if db_user.get("stripe_customer_id"):
                try:
                    subscriptions = await self.stripe.list_subscriptions(
                        customer_id=db_user["stripe_customer_id"],
                        status="active"
                    )
                    for sub in subscriptions:
                        await self.stripe.cancel_subscription(sub["id"], immediately=True)
                    results["stripe"] = {"success": True, "cancelled": len(subscriptions)}
                except Exception as e:
                    results["stripe"] = {"success": False, "error": str(e)}
        
        # 3. Desativar no Firebase Auth
        try:
            firebase_user = await self.firebase.auth_get_user_by_email(email)
            if firebase_user:
                await self.firebase.auth_update_user(
                    firebase_user["uid"],
                    disabled=True
                )
                results["firebase"] = {"success": True, "uid": firebase_user["uid"]}
        except Exception as e:
            results["firebase"] = {"success": False, "error": str(e)}
        
        return results
    
    async def create_manual_license(
        self,
        email: str,
        name: str,
        license_type: str = "basic",
        duration_months: int = 12
    ) -> Dict:
        """
        Cria uma licença manual (sem pagamento Stripe).
        Útil para parceiros, testes, etc.
        """
        import secrets
        import string
        from datetime import timedelta
        
        # Gerar chave de licença
        chars = string.ascii_uppercase + string.digits
        date_part = datetime.now().strftime("%Y%m%d")
        random_part = ''.join(secrets.choice(chars) for _ in range(8))
        license_key = f"FX{date_part}-IFRS16-{random_part}"
        
        # Verificar/criar usuário
        db_user = await self.cloudsql.get_user_by_email(email)
        
        if not db_user:
            # Criar usuário
            import bcrypt
            temp_password = secrets.token_hex(4)
            password_hash = bcrypt.hashpw(
                temp_password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            
            result = await self.cloudsql.insert(
                "users",
                {
                    "email": email,
                    "name": name,
                    "password_hash": password_hash,
                    "is_active": True,
                    "email_verified": False
                },
                returning=["id"]
            )
            user_id = result["inserted"]["id"]
            created_user = True
            user_password = temp_password
        else:
            user_id = db_user["id"]
            created_user = False
            user_password = None
        
        # Calcular expiração
        expires_at = datetime.utcnow() + timedelta(days=duration_months * 30)
        
        # Criar licença
        await self.cloudsql.insert(
            "licenses",
            {
                "key": license_key,
                "user_id": user_id,
                "customer_name": name,
                "email": email,
                "license_type": license_type,
                "status": "active",
                "expires_at": expires_at,
                "max_activations": 3,
                "current_activations": 0,
                "revoked": False
            }
        )
        
        return {
            "success": True,
            "license_key": license_key,
            "user_id": str(user_id),
            "email": email,
            "license_type": license_type,
            "expires_at": expires_at.isoformat(),
            "created_user": created_user,
            "temp_password": user_password
        }
    
    async def get_system_stats(self) -> Dict:
        """
        Retorna estatísticas gerais do sistema.
        """
        stats = {
            "timestamp": datetime.utcnow().isoformat(),
            "database": {},
            "stripe": {},
            "firebase": {}
        }
        
        # Stats do banco
        try:
            # Total de usuários
            users_result = await self.cloudsql.execute_query(
                "SELECT COUNT(*) as total FROM users"
            )
            stats["database"]["total_users"] = users_result["rows"][0]["total"]
            
            # Licenças por status
            licenses_result = await self.cloudsql.execute_query(
                """
                SELECT status, COUNT(*) as count 
                FROM licenses 
                GROUP BY status
                """
            )
            stats["database"]["licenses_by_status"] = {
                row["status"]: row["count"] 
                for row in licenses_result["rows"]
            }
            
            # Assinaturas ativas
            subs_result = await self.cloudsql.execute_query(
                """
                SELECT status, COUNT(*) as count 
                FROM subscriptions 
                GROUP BY status
                """
            )
            stats["database"]["subscriptions_by_status"] = {
                row["status"]: row["count"] 
                for row in subs_result["rows"]
            }
            
            # Tamanho do banco
            db_size = await self.cloudsql.get_database_size()
            stats["database"]["size"] = db_size.get("size", "N/A")
        except Exception as e:
            stats["database"]["error"] = str(e)
        
        # Stats do Stripe
        try:
            balance = await self.stripe.get_balance()
            stats["stripe"]["balance"] = balance
            
            # Últimas transações
            transactions = await self.stripe.list_balance_transactions(limit=5)
            stats["stripe"]["recent_transactions"] = len(transactions)
        except Exception as e:
            stats["stripe"]["error"] = str(e)
        
        # Stats do Firebase
        try:
            project_info = await self.firebase.get_project_info()
            stats["firebase"]["project"] = project_info
        except Exception as e:
            stats["firebase"]["error"] = str(e)
        
        return stats
    
    async def health_check_all(self) -> Dict:
        """
        Verifica saúde de todos os serviços.
        """
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {}
        }
        
        # Cloud SQL
        try:
            db_health = await self.cloudsql.health_check()
            results["services"]["cloudsql"] = db_health
        except Exception as e:
            results["services"]["cloudsql"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Stripe
        try:
            balance = await self.stripe.get_balance()
            results["services"]["stripe"] = {
                "status": "healthy",
                "balance_available": len(balance.get("available", [])) > 0
            }
        except Exception as e:
            results["services"]["stripe"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Firebase
        try:
            info = await self.firebase.get_project_info()
            results["services"]["firebase"] = {
                "status": "healthy",
                "project_id": info.get("project_id")
            }
        except Exception as e:
            results["services"]["firebase"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Status geral
        all_healthy = all(
            s.get("status") == "healthy" 
            for s in results["services"].values()
        )
        results["overall_status"] = "healthy" if all_healthy else "degraded"
        
        return results


# =========================================================================
# CLI para testes
# =========================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Unified Server CLI")
    parser.add_argument("command", choices=[
        "health", "stats", "user-profile", "create-license", "revoke-user"
    ])
    parser.add_argument("--email", help="Email do usuário")
    parser.add_argument("--name", help="Nome do usuário")
    parser.add_argument("--type", default="basic", help="Tipo de licença")
    parser.add_argument("--months", type=int, default=12, help="Duração em meses")
    parser.add_argument("--reason", help="Motivo da revogação")
    
    args = parser.parse_args()
    
    async def main():
        server = UnifiedMCPServer()
        
        try:
            if args.command == "health":
                result = await server.health_check_all()
                print(json.dumps(result, indent=2, default=str))
            
            elif args.command == "stats":
                result = await server.get_system_stats()
                print(json.dumps(result, indent=2, default=str))
            
            elif args.command == "user-profile":
                if not args.email:
                    print("Erro: --email é obrigatório")
                    return
                result = await server.get_user_full_profile(args.email)
                print(json.dumps(result, indent=2, default=str))
            
            elif args.command == "create-license":
                if not args.email or not args.name:
                    print("Erro: --email e --name são obrigatórios")
                    return
                result = await server.create_manual_license(
                    args.email, args.name, args.type, args.months
                )
                print(json.dumps(result, indent=2, default=str))
            
            elif args.command == "revoke-user":
                if not args.email:
                    print("Erro: --email é obrigatório")
                    return
                result = await server.revoke_user_access(args.email, args.reason)
                print(json.dumps(result, indent=2, default=str))
        
        finally:
            await server.close()
    
    asyncio.run(main())
