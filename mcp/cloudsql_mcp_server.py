"""
MCP Server para Google Cloud SQL - Conexão direta com PostgreSQL
Permite executar queries, gerenciar tabelas e fazer operações CRUD
"""

import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from contextlib import asynccontextmanager

# Async PostgreSQL
try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    print("⚠️ asyncpg não instalado. Execute: pip install asyncpg")

# SQLAlchemy para operações mais complexas
try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import text
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False


class CloudSQLMCPServer:
    """
    Servidor MCP para integração direta com Banco de Dados (PostgreSQL ou SQLite).
    """
    
    def __init__(
        self,
        host: str = None,
        port: int = 5432,
        user: str = None,
        password: str = None,
        database: str = None,
        connection_string: str = None
    ):
        """
        Inicializa conexão com Banco de Dados.
        """
        # Carregar .env se existir na pasta mcp
        from dotenv import load_dotenv
        mcp_env = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(mcp_env):
            load_dotenv(mcp_env)
        
        self.is_sqlite = False
        
        if connection_string:
            self.connection_string = connection_string
        elif os.getenv("DATABASE_URL"):
            self.connection_string = os.getenv("DATABASE_URL")
        else:
            self.host = host or os.getenv("POSTGRES_HOST", "localhost")
            self.port = port or int(os.getenv("POSTGRES_PORT", "5432"))
            self.user = user or os.getenv("POSTGRES_USER", "postgres")
            self.password = password or os.getenv("POSTGRES_PASSWORD", "")
            self.database = database or os.getenv("POSTGRES_DATABASE", "ifrs16_licenses")
            
            self.connection_string = (
                f"postgresql://{self.user}:{self.password}@"
                f"{self.host}:{self.port}/{self.database}"
            )
        
        # Verificar se é SQLite (suporta formatos sqlalchemy e puros)
        clean_conn = self.connection_string.lower()
        if "sqlite" in clean_conn:
            self.is_sqlite = True
            # Extrair o caminho do arquivo
            if "///" in self.connection_string:
                self.sqlite_path = self.connection_string.split("///")[-1]
            else:
                self.sqlite_path = self.connection_string.split("sqlite:")[-1].lstrip("/")
            
            if not os.path.isabs(self.sqlite_path):
                # Tentar localizar o arquivo em pastas comuns
                possible_paths = [
                    os.path.join(os.getcwd(), self.sqlite_path),
                    os.path.join(os.getcwd(), "backend", self.sqlite_path),
                    os.path.join(os.path.dirname(__file__), "..", "backend", self.sqlite_path)
                ]
                for p in possible_paths:
                    if os.path.exists(p):
                        self.sqlite_path = os.path.abspath(p)
                        break
        
        self._pool = None
        self._engine = None
        self._sqlite_conn = None

    async def _get_conn(self):
        """Retorna conexão ativa (PostgreSQL ou SQLite)"""
        if self.is_sqlite:
            if self._sqlite_conn is None:
                import aiosqlite
                self._sqlite_conn = await aiosqlite.connect(self.sqlite_path)
                self._sqlite_conn.row_factory = aiosqlite.Row
            return self._sqlite_conn
        else:
            pool = await self._get_pool()
            return await pool.acquire()

    async def _release_conn(self, conn):
        """Libera conexão"""
        if self.is_sqlite:
            # SQLite mantém a conexão aberta no _sqlite_conn
            pass
        else:
            pool = await self._get_pool()
            await pool.release(conn)

    async def _get_pool(self):
        """Retorna pool de conexões asyncpg"""
        if not ASYNCPG_AVAILABLE:
            raise ImportError("asyncpg não está instalado")
        
        if self._pool is None:
            # Extrair parâmetros da connection string
            import urllib.parse
            parsed = urllib.parse.urlparse(self.connection_string)
            
            self._pool = await asyncpg.create_pool(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip('/'),
                min_size=1,
                max_size=10,
                ssl='require' if 'sslmode=require' in self.connection_string else None
            )
        
        return self._pool
    
    async def close(self):
        """Fecha conexões"""
        if self._pool:
            await self._pool.close()
            self._pool = None
    
    # =========================================================================
    # QUERIES
    # =========================================================================
    
    async def execute_query(
        self,
        query: str,
        params: List = None,
        fetch: bool = True
    ) -> Dict:
        """
        Executa uma query SQL.
        """
        conn = await self._get_conn()
        
        try:
            if self.is_sqlite:
                # Converter placeholders $1 para ? do SQLite
                import re
                sqlite_query = re.sub(r'\$(\d+)', r'?', query)
                
                if fetch:
                    async with conn.execute(sqlite_query, params or []) as cursor:
                        rows = await cursor.fetchall()
                        results = [dict(row) for row in rows]
                        return {
                            "success": True,
                            "rows": results,
                            "row_count": len(results)
                        }
                else:
                    await conn.execute(sqlite_query, params or [])
                    await conn.commit()
                    return {
                        "success": True,
                        "status": "Success",
                        "message": "Query executada com sucesso"
                    }
            else:
                # PostgreSQL (asyncpg)
                if fetch:
                    if params:
                        rows = await conn.fetch(query, *params)
                    else:
                        rows = await conn.fetch(query)
                    
                    results = [dict(row) for row in rows]
                    return {
                        "success": True,
                        "rows": results,
                        "row_count": len(results)
                    }
                else:
                    if params:
                        result = await conn.execute(query, *params)
                    else:
                        result = await conn.execute(query)
                    
                    return {
                        "success": True,
                        "status": result,
                        "message": "Query executada com sucesso"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
        finally:
            await self._release_conn(conn)
    
    async def execute_many(
        self,
        query: str,
        params_list: List[List]
    ) -> Dict:
        """Executa uma query múltiplas vezes com diferentes parâmetros"""
        pool = await self._get_pool()
        
        async with pool.acquire() as conn:
            try:
                await conn.executemany(query, params_list)
                return {
                    "success": True,
                    "executed_count": len(params_list)
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
    
    # =========================================================================
    # SCHEMA / TABELAS
    # =========================================================================
    
    async def list_tables(self, schema: str = "public") -> List[Dict]:
        """Lista todas as tabelas do banco"""
        query = """
            SELECT 
                table_name,
                table_type,
                (SELECT COUNT(*) FROM information_schema.columns 
                 WHERE table_name = t.table_name AND table_schema = t.table_schema) as column_count
            FROM information_schema.tables t
            WHERE table_schema = $1
            ORDER BY table_name
        """
        result = await self.execute_query(query, [schema])
        return result.get("rows", [])
    
    async def describe_table(self, table_name: str, schema: str = "public") -> Dict:
        """Retorna estrutura de uma tabela"""
        # Colunas
        columns_query = """
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default,
                ordinal_position
            FROM information_schema.columns
            WHERE table_name = $1 AND table_schema = $2
            ORDER BY ordinal_position
        """
        columns_result = await self.execute_query(columns_query, [table_name, schema])
        
        # Índices
        indexes_query = """
            SELECT
                indexname,
                indexdef
            FROM pg_indexes
            WHERE tablename = $1 AND schemaname = $2
        """
        indexes_result = await self.execute_query(indexes_query, [table_name, schema])
        
        # Constraints
        constraints_query = """
            SELECT
                constraint_name,
                constraint_type
            FROM information_schema.table_constraints
            WHERE table_name = $1 AND table_schema = $2
        """
        constraints_result = await self.execute_query(constraints_query, [table_name, schema])
        
        # Contagem de registros
        count_result = await self.execute_query(
            f'SELECT COUNT(*) as count FROM "{schema}"."{table_name}"'
        )
        
        return {
            "table_name": table_name,
            "schema": schema,
            "columns": columns_result.get("rows", []),
            "indexes": indexes_result.get("rows", []),
            "constraints": constraints_result.get("rows", []),
            "row_count": count_result.get("rows", [{}])[0].get("count", 0)
        }
    
    async def get_table_stats(self, table_name: str, schema: str = "public") -> Dict:
        """Retorna estatísticas de uma tabela"""
        query = """
            SELECT
                relname as table_name,
                n_live_tup as live_rows,
                n_dead_tup as dead_rows,
                last_vacuum,
                last_autovacuum,
                last_analyze,
                last_autoanalyze
            FROM pg_stat_user_tables
            WHERE relname = $1 AND schemaname = $2
        """
        result = await self.execute_query(query, [table_name, schema])
        
        if result.get("rows"):
            row = result["rows"][0]
            # Converter datetimes para string
            for key in ["last_vacuum", "last_autovacuum", "last_analyze", "last_autoanalyze"]:
                if row.get(key):
                    row[key] = row[key].isoformat()
            return row
        
        return {}
    
    # =========================================================================
    # CRUD GENÉRICO
    # =========================================================================
    
    async def select(
        self,
        table: str,
        columns: List[str] = None,
        where: Dict = None,
        order_by: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        SELECT genérico em uma tabela.
        
        Args:
            table: Nome da tabela
            columns: Lista de colunas (None = todas)
            where: Dict de condições {coluna: valor}
            order_by: Coluna para ordenação
            limit: Limite de registros
            offset: Offset para paginação
        """
        cols = ", ".join(columns) if columns else "*"
        query = f'SELECT {cols} FROM "{table}"'
        params = []
        
        if where:
            conditions = []
            for i, (key, value) in enumerate(where.items(), 1):
                conditions.append(f'"{key}" = ${i}')
                params.append(value)
            query += " WHERE " + " AND ".join(conditions)
        
        if order_by:
            query += f' ORDER BY "{order_by}"'
        
        query += f" LIMIT {limit} OFFSET {offset}"
        
        result = await self.execute_query(query, params if params else None)
        return result.get("rows", [])
    
    async def insert(
        self,
        table: str,
        data: Dict,
        returning: List[str] = None
    ) -> Dict:
        """
        INSERT em uma tabela.
        
        Args:
            table: Nome da tabela
            data: Dict com dados {coluna: valor}
            returning: Colunas para retornar após insert
        """
        columns = list(data.keys())
        values = list(data.values())
        
        cols_str = ", ".join(f'"{c}"' for c in columns)
        vals_str = ", ".join(f"${i}" for i in range(1, len(values) + 1))
        
        query = f'INSERT INTO "{table}" ({cols_str}) VALUES ({vals_str})'
        
        if returning:
            query += " RETURNING " + ", ".join(f'"{c}"' for c in returning)
            result = await self.execute_query(query, values)
            return {
                "success": True,
                "inserted": result.get("rows", [{}])[0] if result.get("rows") else {}
            }
        else:
            result = await self.execute_query(query, values, fetch=False)
            return result
    
    async def update(
        self,
        table: str,
        data: Dict,
        where: Dict
    ) -> Dict:
        """
        UPDATE em uma tabela.
        
        Args:
            table: Nome da tabela
            data: Dict com dados para atualizar
            where: Dict de condições
        """
        set_parts = []
        params = []
        param_idx = 1
        
        for key, value in data.items():
            set_parts.append(f'"{key}" = ${param_idx}')
            params.append(value)
            param_idx += 1
        
        where_parts = []
        for key, value in where.items():
            where_parts.append(f'"{key}" = ${param_idx}')
            params.append(value)
            param_idx += 1
        
        query = f'UPDATE "{table}" SET {", ".join(set_parts)} WHERE {" AND ".join(where_parts)}'
        
        result = await self.execute_query(query, params, fetch=False)
        return result
    
    async def delete(
        self,
        table: str,
        where: Dict
    ) -> Dict:
        """
        DELETE em uma tabela.
        
        Args:
            table: Nome da tabela
            where: Dict de condições
        """
        where_parts = []
        params = []
        
        for i, (key, value) in enumerate(where.items(), 1):
            where_parts.append(f'"{key}" = ${i}')
            params.append(value)
        
        query = f'DELETE FROM "{table}" WHERE {" AND ".join(where_parts)}'
        
        result = await self.execute_query(query, params, fetch=False)
        return result
    
    # =========================================================================
    # ESPECÍFICO IFRS 16
    # =========================================================================
    
    async def get_licenses(
        self,
        status: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """Lista licenças do sistema IFRS 16"""
        where = {"status": status} if status else None
        return await self.select("licenses", where=where, limit=limit, order_by="created_at")
    
    async def get_license_by_key(self, key: str) -> Optional[Dict]:
        """Busca licença por chave"""
        results = await self.select("licenses", where={"key": key}, limit=1)
        return results[0] if results else None
    
    async def get_users(self, limit: int = 100) -> List[Dict]:
        """Lista usuários do sistema"""
        return await self.select("users", limit=limit, order_by="created_at")
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Busca usuário por email"""
        results = await self.select("users", where={"email": email}, limit=1)
        return results[0] if results else None
    
    async def get_subscriptions(
        self,
        user_id: str = None,
        status: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """Lista assinaturas"""
        where = {}
        if user_id:
            where["user_id"] = user_id
        if status:
            where["status"] = status
        
        return await self.select(
            "subscriptions",
            where=where if where else None,
            limit=limit,
            order_by="created_at"
        )
    
    async def get_admin_users(self) -> List[Dict]:
        """Lista administradores"""
        return await self.select("admin_users", order_by="created_at")
    
    async def get_validation_logs(
        self,
        license_key: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """Lista logs de validação"""
        where = {"license_key": license_key} if license_key else None
        return await self.select(
            "validation_logs",
            where=where,
            limit=limit,
            order_by="timestamp"
        )
    
    # =========================================================================
    # MONITORAMENTO
    # =========================================================================
    
    async def get_database_size(self) -> Dict:
        """Retorna tamanho do banco de dados"""
        query = """
            SELECT 
                pg_database.datname as database,
                pg_size_pretty(pg_database_size(pg_database.datname)) as size,
                pg_database_size(pg_database.datname) as size_bytes
            FROM pg_database
            WHERE datname = current_database()
        """
        result = await self.execute_query(query)
        return result.get("rows", [{}])[0]
    
    async def get_active_connections(self) -> List[Dict]:
        """Lista conexões ativas"""
        query = """
            SELECT 
                pid,
                usename as username,
                application_name,
                client_addr,
                state,
                query_start,
                state_change
            FROM pg_stat_activity
            WHERE datname = current_database()
            AND pid != pg_backend_pid()
        """
        result = await self.execute_query(query)
        rows = result.get("rows", [])
        
        # Converter datetimes
        for row in rows:
            for key in ["query_start", "state_change"]:
                if row.get(key):
                    row[key] = row[key].isoformat()
        
        return rows
    
    async def get_slow_queries(self, min_duration_ms: int = 1000) -> List[Dict]:
        """Lista queries lentas (requer pg_stat_statements)"""
        query = """
            SELECT 
                query,
                calls,
                total_exec_time as total_time_ms,
                mean_exec_time as avg_time_ms,
                rows
            FROM pg_stat_statements
            WHERE mean_exec_time > $1
            ORDER BY mean_exec_time DESC
            LIMIT 20
        """
        try:
            result = await self.execute_query(query, [min_duration_ms])
            return result.get("rows", [])
        except:
            return []  # pg_stat_statements pode não estar habilitado
    
    async def health_check(self) -> Dict:
        """Verifica saúde da conexão"""
        try:
            result = await self.execute_query("SELECT 1 as ok, NOW() as timestamp")
            if result.get("success"):
                return {
                    "status": "healthy",
                    "timestamp": result["rows"][0]["timestamp"].isoformat(),
                    "connection": "ok"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection": "failed"
            }


# =========================================================================
# MCP TOOLS DEFINITION
# =========================================================================

MCP_TOOLS = {
    "cloudsql_execute_query": {
        "description": "Executa uma query SQL no Cloud SQL",
        "parameters": {
            "query": {"type": "string", "required": True},
            "params": {"type": "array", "optional": True},
            "fetch": {"type": "boolean", "default": True},
        }
    },
    "cloudsql_list_tables": {
        "description": "Lista todas as tabelas do banco",
        "parameters": {
            "schema": {"type": "string", "default": "public"},
        }
    },
    "cloudsql_describe_table": {
        "description": "Retorna estrutura de uma tabela",
        "parameters": {
            "table_name": {"type": "string", "required": True},
        }
    },
    "cloudsql_select": {
        "description": "SELECT genérico em uma tabela",
        "parameters": {
            "table": {"type": "string", "required": True},
            "columns": {"type": "array", "optional": True},
            "where": {"type": "object", "optional": True},
            "limit": {"type": "integer", "default": 100},
        }
    },
    "cloudsql_insert": {
        "description": "INSERT em uma tabela",
        "parameters": {
            "table": {"type": "string", "required": True},
            "data": {"type": "object", "required": True},
        }
    },
    "cloudsql_update": {
        "description": "UPDATE em uma tabela",
        "parameters": {
            "table": {"type": "string", "required": True},
            "data": {"type": "object", "required": True},
            "where": {"type": "object", "required": True},
        }
    },
    "cloudsql_delete": {
        "description": "DELETE em uma tabela",
        "parameters": {
            "table": {"type": "string", "required": True},
            "where": {"type": "object", "required": True},
        }
    },
    # IFRS 16 específico
    "cloudsql_get_licenses": {
        "description": "Lista licenças do sistema IFRS 16",
        "parameters": {
            "status": {"type": "string", "optional": True},
            "limit": {"type": "integer", "default": 100},
        }
    },
    "cloudsql_get_users": {
        "description": "Lista usuários do sistema",
        "parameters": {
            "limit": {"type": "integer", "default": 100},
        }
    },
    "cloudsql_get_subscriptions": {
        "description": "Lista assinaturas",
        "parameters": {
            "user_id": {"type": "string", "optional": True},
            "status": {"type": "string", "optional": True},
        }
    },
    # Monitoramento
    "cloudsql_health_check": {
        "description": "Verifica saúde da conexão com o banco",
        "parameters": {}
    },
    "cloudsql_get_database_size": {
        "description": "Retorna tamanho do banco de dados",
        "parameters": {}
    },
    "cloudsql_get_active_connections": {
        "description": "Lista conexões ativas no banco",
        "parameters": {}
    },
}


if __name__ == "__main__":
    # Teste básico
    import asyncio
    
    async def test():
        # Usar variáveis de ambiente ou connection string
        server = CloudSQLMCPServer()
        
        # Health check
        health = await server.health_check()
        print("Health:", json.dumps(health, indent=2, default=str))
        
        # Listar tabelas
        tables = await server.list_tables()
        print("Tabelas:", json.dumps(tables, indent=2, default=str))
        
        # Fechar conexão
        await server.close()
    
    asyncio.run(test())
