"""
Endpoints para gerenciamento de contratos IFRS 16
Persistência em banco de dados Cloud SQL
Versões são imutáveis - apenas delete permitido
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime, date
import json

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from pydantic import BaseModel

from ..database import get_db
from ..auth import get_current_user
from ..models import User, License, LicenseStatus


router = APIRouter(prefix="/api/contracts", tags=["Contratos"])


# =============================================================================
# SCHEMAS
# =============================================================================

class ContractBase(BaseModel):
    name: str
    description: Optional[str] = None
    contract_code: Optional[str] = None
    status: str = "draft"


class ContractCreate(ContractBase):
    pass


class ContractUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    contract_code: Optional[str] = None
    status: Optional[str] = None


class ContractResponse(ContractBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContractVersionCreate(BaseModel):
    data_inicio: str
    prazo_meses: int
    carencia_meses: int = 0
    parcela_inicial: float
    taxa_desconto_anual: float
    reajuste_tipo: str = "manual"
    reajuste_valor: Optional[float] = None
    mes_reajuste: int = 1
    resultados_json: dict
    total_vp: float
    total_nominal: float
    avp: float
    notas: Optional[str] = None


class ContractVersionResponse(BaseModel):
    id: str
    contract_id: str
    version_number: int
    data_inicio: str
    prazo_meses: int
    total_vp: float
    notas: Optional[str] = None
    archived_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# HELPERS
# =============================================================================

async def get_active_license(db: AsyncSession, user: User) -> Optional[License]:
    """Obtém a licença ativa do usuário"""
    result = await db.execute(
        select(License).where(
            License.user_id == user.id,
            License.status == LicenseStatus.ACTIVE,
            License.revoked == False
        ).order_by(License.created_at.desc())
    )
    user_license = result.scalar_one_or_none()
    
    if not user_license:
        return None
    
    if user_license.expires_at and datetime.utcnow() > user_license.expires_at:
        return None
    
    return user_license


# =============================================================================
# ENDPOINTS - CONTRATOS
# =============================================================================

@router.get(
    "",
    summary="Listar Contratos",
    description="Lista todos os contratos do usuário"
)
async def list_contracts(
    search_name: Optional[str] = Query(None, description="Filtrar por nome"),
    search_code: Optional[str] = Query(None, description="Filtrar por código"),
    start_date: Optional[str] = Query(None, description="Data início"),
    end_date: Optional[str] = Query(None, description="Data fim"),
    user_data: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lista contratos do usuário autenticado"""
    user = user_data["user"]
    
    # Verificar licença ativa
    user_license = await get_active_license(db, user)
    if not user_license:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você precisa de uma licença ativa para gerenciar contratos"
        )
    
    # Query base
    query = """
        SELECT id, user_id, name, description, contract_code, status, 
               created_at, updated_at
        FROM contracts 
        WHERE user_id = :user_id AND is_deleted = FALSE
    """
    params = {"user_id": str(user.id)}
    
    # Aplicar filtros
    if search_name:
        query += " AND LOWER(name) LIKE :search_name"
        params["search_name"] = f"%{search_name.lower()}%"
    
    if search_code:
        query += " AND LOWER(contract_code) LIKE :search_code"
        params["search_code"] = f"%{search_code.lower()}%"
    
    query += " ORDER BY created_at DESC"
    
    result = await db.execute(text(query), params)
    rows = result.fetchall()
    
    contracts = []
    for row in rows:
        contracts.append({
            "id": str(row[0]),
            "user_id": str(row[1]),
            "name": row[2],
            "description": row[3],
            "contract_code": row[4],
            "status": row[5],
            "created_at": row[6].isoformat() if row[6] else None,
            "updated_at": row[7].isoformat() if row[7] else None
        })
    
    return {"contracts": contracts}


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Criar Contrato",
    description="Cria um novo contrato"
)
async def create_contract(
    data: ContractCreate,
    user_data: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cria um novo contrato para o usuário"""
    user = user_data["user"]
    
    # Verificar licença ativa
    user_license = await get_active_license(db, user)
    if not user_license:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você precisa de uma licença ativa para criar contratos"
        )
    
    # Verificar limite de contratos
    features = user_license.features
    max_contracts = features.get("max_contracts", 0)
    
    if max_contracts != -1:
        # Contar contratos ativos
        count_result = await db.execute(
            text("SELECT COUNT(*) FROM contracts WHERE user_id = :user_id AND is_deleted = FALSE"),
            {"user_id": str(user.id)}
        )
        current_count = count_result.scalar()
        
        if current_count >= max_contracts:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Limite de contratos excedido. Seu plano permite até {max_contracts} contratos."
            )
    
    # Inserir contrato no banco
    insert_query = """
        INSERT INTO contracts (user_id, name, description, contract_code, status)
        VALUES (:user_id, :name, :description, :contract_code, :status)
        RETURNING id, user_id, name, description, contract_code, status, created_at, updated_at
    """
    
    result = await db.execute(
        text(insert_query),
        {
            "user_id": str(user.id),
            "name": data.name,
            "description": data.description,
            "contract_code": data.contract_code,
            "status": data.status
        }
    )
    row = result.fetchone()
    await db.commit()
    
    return {
        "id": str(row[0]),
        "user_id": str(row[1]),
        "name": row[2],
        "description": row[3],
        "contract_code": row[4],
        "status": row[5],
        "created_at": row[6].isoformat() if row[6] else None,
        "updated_at": row[7].isoformat() if row[7] else None
    }


@router.get(
    "/{contract_id}",
    summary="Obter Contrato",
    description="Obtém detalhes de um contrato específico"
)
async def get_contract(
    contract_id: str,
    user_data: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtém um contrato específico"""
    user = user_data["user"]
    
    result = await db.execute(
        text("""
            SELECT id, user_id, name, description, contract_code, status, created_at, updated_at
            FROM contracts 
            WHERE id = :contract_id AND user_id = :user_id AND is_deleted = FALSE
        """),
        {"contract_id": contract_id, "user_id": str(user.id)}
    )
    row = result.fetchone()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrato não encontrado"
        )
    
    return {
        "id": str(row[0]),
        "user_id": str(row[1]),
        "name": row[2],
        "description": row[3],
        "contract_code": row[4],
        "status": row[5],
        "created_at": row[6].isoformat() if row[6] else None,
        "updated_at": row[7].isoformat() if row[7] else None
    }


@router.put(
    "/{contract_id}",
    summary="Atualizar Contrato",
    description="Atualiza um contrato existente"
)
async def update_contract(
    contract_id: str,
    data: ContractUpdate,
    user_data: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Atualiza um contrato"""
    user = user_data["user"]
    
    # Verificar se contrato existe
    check_result = await db.execute(
        text("SELECT id FROM contracts WHERE id = :contract_id AND user_id = :user_id AND is_deleted = FALSE"),
        {"contract_id": contract_id, "user_id": str(user.id)}
    )
    if not check_result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrato não encontrado"
        )
    
    # Construir query de update dinamicamente
    updates = []
    params = {"contract_id": contract_id, "user_id": str(user.id)}
    
    if data.name is not None:
        updates.append("name = :name")
        params["name"] = data.name
    if data.description is not None:
        updates.append("description = :description")
        params["description"] = data.description
    if data.contract_code is not None:
        updates.append("contract_code = :contract_code")
        params["contract_code"] = data.contract_code
    if data.status is not None:
        updates.append("status = :status")
        params["status"] = data.status
    
    updates.append("updated_at = NOW()")
    
    update_query = f"""
        UPDATE contracts 
        SET {', '.join(updates)}
        WHERE id = :contract_id AND user_id = :user_id
        RETURNING id, user_id, name, description, contract_code, status, created_at, updated_at
    """
    
    result = await db.execute(text(update_query), params)
    row = result.fetchone()
    await db.commit()
    
    return {
        "id": str(row[0]),
        "user_id": str(row[1]),
        "name": row[2],
        "description": row[3],
        "contract_code": row[4],
        "status": row[5],
        "created_at": row[6].isoformat() if row[6] else None,
        "updated_at": row[7].isoformat() if row[7] else None
    }


@router.delete(
    "/{contract_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir Contrato",
    description="Exclui um contrato (soft delete)"
)
async def delete_contract(
    contract_id: str,
    user_data: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Exclui um contrato (soft delete)"""
    user = user_data["user"]
    
    result = await db.execute(
        text("""
            UPDATE contracts 
            SET is_deleted = TRUE, deleted_at = NOW()
            WHERE id = :contract_id AND user_id = :user_id AND is_deleted = FALSE
            RETURNING id
        """),
        {"contract_id": contract_id, "user_id": str(user.id)}
    )
    
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrato não encontrado"
        )
    
    await db.commit()
    return None


# =============================================================================
# VERSÕES DE CONTRATOS (IMUTÁVEIS - APENAS DELETE PERMITIDO)
# =============================================================================

@router.get(
    "/{contract_id}/versions",
    summary="Listar Versões",
    description="Lista todas as versões de um contrato"
)
async def list_versions(
    contract_id: str,
    user_data: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lista versões de um contrato"""
    user = user_data["user"]
    
    # Verificar se contrato pertence ao usuário
    check_result = await db.execute(
        text("SELECT id FROM contracts WHERE id = :contract_id AND user_id = :user_id AND is_deleted = FALSE"),
        {"contract_id": contract_id, "user_id": str(user.id)}
    )
    if not check_result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrato não encontrado"
        )
    
    # Buscar versões
    result = await db.execute(
        text("""
            SELECT id, contract_id, version_number, data_inicio, prazo_meses,
                   carencia_meses, parcela_inicial, taxa_desconto_anual,
                   reajuste_tipo, reajuste_valor, mes_reajuste,
                   resultados_json, total_vp, total_nominal, avp,
                   notas, archived_at, created_at
            FROM contract_versions
            WHERE contract_id = :contract_id
            ORDER BY version_number DESC
        """),
        {"contract_id": contract_id}
    )
    rows = result.fetchall()
    
    versions = []
    for row in rows:
        versions.append({
            "id": str(row[0]),
            "contract_id": str(row[1]),
            "version_number": row[2],
            "data_inicio": str(row[3]) if row[3] else None,
            "prazo_meses": row[4],
            "carencia_meses": row[5],
            "parcela_inicial": float(row[6]) if row[6] else 0,
            "taxa_desconto_anual": float(row[7]) if row[7] else 0,
            "reajuste_tipo": row[8],
            "reajuste_valor": float(row[9]) if row[9] else None,
            "mes_reajuste": row[10],
            "resultados_json": row[11],
            "total_vp": float(row[12]) if row[12] else 0,
            "total_nominal": float(row[13]) if row[13] else 0,
            "avp": float(row[14]) if row[14] else 0,
            "notas": row[15],
            "archived_at": row[16].isoformat() if row[16] else None,
            "created_at": row[17].isoformat() if row[17] else None
        })
    
    return {"versions": versions}


@router.post(
    "/{contract_id}/versions",
    status_code=status.HTTP_201_CREATED,
    summary="Criar Versão",
    description="Cria uma nova versão imutável do contrato"
)
async def create_version(
    contract_id: str,
    data: ContractVersionCreate,
    user_data: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cria uma nova versão imutável do contrato"""
    user = user_data["user"]
    
    # Verificar se contrato pertence ao usuário
    check_result = await db.execute(
        text("SELECT id FROM contracts WHERE id = :contract_id AND user_id = :user_id AND is_deleted = FALSE"),
        {"contract_id": contract_id, "user_id": str(user.id)}
    )
    if not check_result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrato não encontrado"
        )
    
    # Obter próximo número de versão
    version_result = await db.execute(
        text("SELECT COALESCE(MAX(version_number), 0) + 1 FROM contract_versions WHERE contract_id = :contract_id"),
        {"contract_id": contract_id}
    )
    version_number = version_result.scalar()
    
    # Inserir versão imutável
    insert_query = """
        INSERT INTO contract_versions (
            contract_id, version_number, data_inicio, prazo_meses, carencia_meses,
            parcela_inicial, taxa_desconto_anual, reajuste_tipo, reajuste_valor,
            mes_reajuste, resultados_json, total_vp, total_nominal, avp, notas
        )
        VALUES (
            :contract_id, :version_number, :data_inicio, :prazo_meses, :carencia_meses,
            :parcela_inicial, :taxa_desconto_anual, :reajuste_tipo, :reajuste_valor,
            :mes_reajuste, :resultados_json, :total_vp, :total_nominal, :avp, :notas
        )
        RETURNING id, contract_id, version_number, data_inicio, prazo_meses,
                  total_vp, notas, archived_at, created_at
    """
    
    # Converter data_inicio de string para date
    data_inicio_date = None
    if data.data_inicio:
        try:
            data_inicio_date = datetime.strptime(data.data_inicio, "%Y-%m-%d").date()
        except ValueError:
            # Tentar outros formatos
            try:
                data_inicio_date = datetime.strptime(data.data_inicio, "%d/%m/%Y").date()
            except ValueError:
                data_inicio_date = None
    
    result = await db.execute(
        text(insert_query),
        {
            "contract_id": contract_id,
            "version_number": version_number,
            "data_inicio": data_inicio_date,
            "prazo_meses": data.prazo_meses,
            "carencia_meses": data.carencia_meses,
            "parcela_inicial": data.parcela_inicial,
            "taxa_desconto_anual": data.taxa_desconto_anual,
            "reajuste_tipo": data.reajuste_tipo,
            "reajuste_valor": data.reajuste_valor,
            "mes_reajuste": data.mes_reajuste,
            "resultados_json": json.dumps(data.resultados_json),
            "total_vp": data.total_vp,
            "total_nominal": data.total_nominal,
            "avp": data.avp,
            "notas": data.notas
        }
    )
    row = result.fetchone()
    await db.commit()
    
    return {
        "id": str(row[0]),
        "contract_id": str(row[1]),
        "version_number": row[2],
        "data_inicio": str(row[3]) if row[3] else None,
        "prazo_meses": row[4],
        "total_vp": float(row[5]) if row[5] else 0,
        "notas": row[6],
        "archived_at": row[7].isoformat() if row[7] else None,
        "created_at": row[8].isoformat() if row[8] else None
    }


@router.delete(
    "/{contract_id}/versions/{version_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir Versão",
    description="Exclui uma versão do contrato (única operação permitida em versões)"
)
async def delete_version(
    contract_id: str,
    version_id: str,
    user_data: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Exclui uma versão do contrato"""
    user = user_data["user"]
    
    # Verificar se contrato pertence ao usuário
    check_result = await db.execute(
        text("SELECT id FROM contracts WHERE id = :contract_id AND user_id = :user_id AND is_deleted = FALSE"),
        {"contract_id": contract_id, "user_id": str(user.id)}
    )
    if not check_result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrato não encontrado"
        )
    
    # Deletar versão
    result = await db.execute(
        text("DELETE FROM contract_versions WHERE id = :version_id AND contract_id = :contract_id RETURNING id"),
        {"version_id": version_id, "contract_id": contract_id}
    )
    
    if not result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Versão não encontrada"
        )
    
    await db.commit()
    return None
