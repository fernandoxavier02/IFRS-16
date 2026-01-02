"""
Service para agregar métricas do dashboard analítico
"""

from datetime import date, timedelta
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


class DashboardService:
    """Service para calcular métricas agregadas do dashboard"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_metrics(self, user_id: str) -> Dict:
        """
        Retorna métricas gerais agregadas dos contratos do usuário.
        
        Returns:
            Dict com:
            - total_contracts: int
            - total_passivos: float
            - total_ativos: float
            - total_despesas_mensais: float
        """
        # Buscar última versão de cada contrato ativo do usuário
        query = text("""
            SELECT 
                COUNT(DISTINCT c.id) as total_contracts,
                COALESCE(SUM(cv.total_vp), 0) as total_passivos,
                COALESCE(SUM(cv.total_vp), 0) as total_ativos,
                COALESCE(SUM(
                    CASE 
                        WHEN cv.resultados_json->'contabilizacao' IS NOT NULL 
                        THEN (
                            SELECT SUM((item->>'despTotal')::numeric)
                            FROM jsonb_array_elements(cv.resultados_json->'contabilizacao') item
                            WHERE (item->>'mes')::int = 1
                        )
                        ELSE 0
                    END
                ), 0) as total_despesas_mensais
            FROM contracts c
            LEFT JOIN LATERAL (
                SELECT cv.*
                FROM contract_versions cv
                WHERE cv.contract_id = c.id
                ORDER BY cv.version_number DESC
                LIMIT 1
            ) cv ON true
            WHERE c.user_id = CAST(:user_id AS uuid)
                AND c.is_deleted = false
                AND c.status = 'active'
        """)
        
        print(f"[DashboardService] Buscando métricas para user_id: {user_id}")
        result = await self.db.execute(query, {"user_id": user_id})
        row = result.fetchone()
        
        metrics = {
            "total_contracts": int(row[0]) if row[0] else 0,
            "total_passivos": float(row[1]) if row[1] else 0.0,
            "total_ativos": float(row[2]) if row[2] else 0.0,
            "total_despesas_mensais": float(row[3]) if row[3] else 0.0
        }
        print(f"[DashboardService] Métricas retornadas: {metrics}")
        return metrics

    async def get_evolution(self, user_id: str, months: int = 12) -> List[Dict]:
        """
        Retorna evolução do passivo ao longo do tempo.
        
        Args:
            user_id: ID do usuário
            months: Número de meses para retornar (padrão: 12)
            
        Returns:
            Lista de dicts com {month: str, passivo: float}
        """
        # Calcular data inicial (months meses atrás)
        end_date = date.today()
        start_date = end_date - timedelta(days=months * 30)
        
        # Buscar evolução mensal do passivo
        # Versão simplificada: soma o passivo atual de todos os contratos ativos
        # Para cada mês, retorna a soma do passivo das últimas versões
        query = text("""
            WITH months AS (
                SELECT generate_series(
                    DATE_TRUNC('month', CAST(:start_date AS date)),
                    DATE_TRUNC('month', CAST(:end_date AS date)),
                    '1 month'::interval
                )::date as month
            )
            SELECT 
                TO_CHAR(m.month, 'YYYY-MM') as month,
                COALESCE(SUM(cv.total_vp), 0) as passivo
            FROM months m
            CROSS JOIN contracts c
            LEFT JOIN LATERAL (
                SELECT cv.*
                FROM contract_versions cv
                WHERE cv.contract_id = c.id
                    AND DATE_TRUNC('month', cv.archived_at::date) <= m.month
                ORDER BY cv.version_number DESC
                LIMIT 1
            ) cv ON true
            WHERE c.user_id = CAST(:user_id AS uuid)
                AND c.is_deleted = false
                AND c.status = 'active'
            GROUP BY m.month
            ORDER BY m.month
        """)
        
        result = await self.db.execute(query, {
            "user_id": user_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        })
        
        rows = result.fetchall()
        return [
            {"month": row[0], "passivo": float(row[1]) if row[1] else 0.0}
            for row in rows
        ]

    async def get_distribution(self, user_id: str) -> List[Dict]:
        """
        Retorna distribuição de contratos por categoria.
        
        Returns:
            Lista de dicts com {category: str, count: int, value: float}
        """
        query = text("""
            SELECT 
                c.categoria,
                COUNT(DISTINCT c.id) as count,
                COALESCE(SUM(cv.total_vp), 0) as value
            FROM contracts c
            LEFT JOIN LATERAL (
                SELECT cv.*
                FROM contract_versions cv
                WHERE cv.contract_id = c.id
                ORDER BY cv.version_number DESC
                LIMIT 1
            ) cv ON true
            WHERE c.user_id = CAST(:user_id AS uuid)
                AND c.is_deleted = false
                AND c.status = 'active'
            GROUP BY c.categoria
            ORDER BY value DESC
        """)
        
        result = await self.db.execute(query, {"user_id": user_id})
        rows = result.fetchall()
        
        return [
            {
                "category": row[0] or "Sem categoria",
                "count": int(row[1]) if row[1] else 0,
                "value": float(row[2]) if row[2] else 0.0
            }
            for row in rows
        ]

    async def get_monthly_expenses(self, user_id: str) -> List[Dict]:
        """
        Retorna despesas mensais por contrato.
        
        Returns:
            Lista de dicts com {contract_name: str, despesa_mensal: float}
        """
        query = text("""
            SELECT 
                c.name as contract_name,
                COALESCE((
                    SELECT SUM((item->>'despTotal')::numeric)
                    FROM jsonb_array_elements(cv.resultados_json->'contabilizacao') item
                    WHERE (item->>'mes')::int = 1
                ), 0) as despesa_mensal
            FROM contracts c
            LEFT JOIN LATERAL (
                SELECT cv.*
                FROM contract_versions cv
                WHERE cv.contract_id = c.id
                ORDER BY cv.version_number DESC
                LIMIT 1
            ) cv ON true
            WHERE c.user_id = CAST(:user_id AS uuid)
                AND c.is_deleted = false
                AND c.status = 'active'
            ORDER BY despesa_mensal DESC
            LIMIT 20
        """)
        
        result = await self.db.execute(query, {"user_id": user_id})
        rows = result.fetchall()
        
        return [
            {
                "contract_name": row[0] or "Sem nome",
                "despesa_mensal": float(row[1]) if row[1] else 0.0
            }
            for row in rows
        ]

    async def get_upcoming_expirations(self, user_id: str, days: int = 90) -> List[Dict]:
        """
        Retorna contratos próximos do vencimento.
        
        Args:
            user_id: ID do usuário
            days: Número de dias para buscar (padrão: 90)
            
        Returns:
            Lista de dicts com informações de vencimento
        """
        query = text("""
            SELECT 
                c.id::text as contract_id,
                c.name as contract_name,
                (cv.data_inicio + (cv.prazo_meses || ' months')::interval)::date as expiration_date,
                (cv.data_inicio + (cv.prazo_meses || ' months')::interval)::date - CURRENT_DATE as days_until_expiration
            FROM contracts c
            LEFT JOIN LATERAL (
                SELECT cv.*
                FROM contract_versions cv
                WHERE cv.contract_id = c.id
                ORDER BY cv.version_number DESC
                LIMIT 1
            ) cv ON true
            WHERE c.user_id = CAST(:user_id AS uuid)
                AND c.is_deleted = false
                AND c.status = 'active'
                AND cv.id IS NOT NULL
                AND (cv.data_inicio + (cv.prazo_meses || ' months')::interval)::date BETWEEN CURRENT_DATE AND (CURRENT_DATE + CAST(:days AS interval))
            ORDER BY expiration_date ASC
        """)
        
        result = await self.db.execute(query, {
            "user_id": user_id,
            "days": f"{days} days"
        })
        rows = result.fetchall()
        
        expirations = []
        for row in rows:
            days_until = int(row[3]) if row[3] else 0
            status = "critical" if days_until <= 30 else ("warning" if days_until <= 60 else "normal")
            
            expirations.append({
                "contract_id": row[0],
                "contract_name": row[1] or "Sem nome",
                "expiration_date": row[2].isoformat() if row[2] else None,
                "days_until_expiration": days_until,
                "status": status
            })
        
        return expirations
