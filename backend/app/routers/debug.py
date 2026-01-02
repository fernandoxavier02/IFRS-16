"""
Router de debug para investigar problemas de dados
REMOVER EM PRODUÇÃO!
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from ..database import get_db
from ..auth import get_current_user
from ..schemas import UserResponse

router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.get("/contracts")
async def debug_contracts(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint de debug para ver todos os contratos do usuário.
    REMOVER EM PRODUÇÃO!
    """
    
    # Query 1: Contratos do usuário
    query1 = text("""
        SELECT 
            c.id::text,
            c.user_id::text,
            c.name,
            c.status,
            c.is_deleted,
            c.categoria,
            c.created_at
        FROM contracts c
        WHERE c.user_id = CAST(:user_id AS uuid)
        ORDER BY c.created_at DESC
    """)
    
    result1 = await db.execute(query1, {"user_id": current_user.id})
    contracts = result1.fetchall()
    
    # Query 2: Contratos com versões
    query2 = text("""
        SELECT 
            c.id::text as contract_id,
            c.name,
            c.status,
            c.is_deleted,
            cv.id::text as version_id,
            cv.version_number,
            cv.total_vp,
            cv.data_inicio,
            cv.prazo_meses
        FROM contracts c
        LEFT JOIN LATERAL (
            SELECT cv.*
            FROM contract_versions cv
            WHERE cv.contract_id = c.id
            ORDER BY cv.version_number DESC
            LIMIT 1
        ) cv ON true
        WHERE c.user_id = CAST(:user_id AS uuid)
        ORDER BY c.created_at DESC
    """)
    
    result2 = await db.execute(query2, {"user_id": current_user.id})
    contracts_with_versions = result2.fetchall()
    
    # Query 3: Contar por status
    query3 = text("""
        SELECT 
            status,
            is_deleted,
            COUNT(*) as total
        FROM contracts
        WHERE user_id = CAST(:user_id AS uuid)
        GROUP BY status, is_deleted
    """)
    
    result3 = await db.execute(query3, {"user_id": current_user.id})
    counts = result3.fetchall()
    
    # Query 4: Testar a query do dashboard
    query4 = text("""
        SELECT 
            COUNT(DISTINCT c.id) as total_contracts,
            COALESCE(SUM(cv.total_vp), 0) as total_passivos
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
    
    result4 = await db.execute(query4, {"user_id": current_user.id})
    dashboard_test = result4.fetchone()
    
    return {
        "user_id": current_user.id,
        "user_email": current_user.email,
        "total_contracts": len(contracts),
        "contracts": [
            {
                "id": row[0],
                "user_id": row[1],
                "name": row[2],
                "status": row[3],
                "is_deleted": row[4],
                "categoria": row[5],
                "created_at": row[6].isoformat() if row[6] else None
            }
            for row in contracts
        ],
        "contracts_with_versions": [
            {
                "contract_id": row[0],
                "name": row[1],
                "status": row[2],
                "is_deleted": row[3],
                "version_id": row[4],
                "version_number": row[5],
                "total_vp": float(row[6]) if row[6] else None,
                "data_inicio": row[7].isoformat() if row[7] else None,
                "prazo_meses": row[8]
            }
            for row in contracts_with_versions
        ],
        "counts_by_status": [
            {
                "status": row[0],
                "is_deleted": row[1],
                "total": row[2]
            }
            for row in counts
        ],
        "dashboard_query_test": {
            "total_contracts": int(dashboard_test[0]) if dashboard_test[0] else 0,
            "total_passivos": float(dashboard_test[1]) if dashboard_test[1] else 0.0
        }
    }
