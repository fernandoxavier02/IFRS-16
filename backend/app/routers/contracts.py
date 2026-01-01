"""
Endpoints para gerenciamento de contratos IFRS 16
Persistência em banco de dados Cloud SQL
Versões são imutáveis - apenas delete permitido
"""

from typing import Optional, List
from uuid import UUID, uuid4
from datetime import datetime, date
import json

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from pydantic import BaseModel

from ..database import get_db
from ..auth import get_current_user, get_current_user_with_session
from ..models import User, License, LicenseStatus, Contract, ContractStatus


router = APIRouter(prefix="/api/contracts", tags=["Contratos"])


# =============================================================================
# SCHEMAS
# =============================================================================

class ContractBase(BaseModel):
    name: str
    description: Optional[str] = None
    contract_code: Optional[str] = None
    categoria: str = "OT"  # IM, VE, EQ, PC, OT
    status: str = "draft"


class ContractCreate(ContractBase):
    pass


class ContractUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    contract_code: Optional[str] = None
    categoria: Optional[str] = None
    status: Optional[str] = None


# Categorias válidas
CATEGORIAS_VALIDAS = {
    "IM": "Imóvel",
    "VE": "Veículo", 
    "EQ": "Equipamento",
    "PC": "Computadores e Periféricos",
    "OT": "Outros"
}

# Status válidos
STATUS_VALIDOS = {"draft", "active", "completed", "cancelled"}


def validate_status(status_value: str) -> str:
    """Valida e normaliza o status do contrato"""
    if not status_value:
        return "draft"
    normalized = status_value.lower().strip()
    if normalized not in STATUS_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Status inválido: '{status_value}'. Valores permitidos: {', '.join(sorted(STATUS_VALIDOS))}"
        )
    return normalized


def validate_categoria(categoria_value: str) -> str:
    """Valida e normaliza a categoria do contrato"""
    if not categoria_value:
        return "OT"
    normalized = categoria_value.upper().strip()
    if normalized not in CATEGORIAS_VALIDAS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Categoria inválida: '{categoria_value}'. Valores permitidos: {', '.join(sorted(CATEGORIAS_VALIDAS.keys()))}"
        )
    return normalized


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


def serialize_contract(contract: Contract) -> dict:
    """Converte contrato ORM em dict serializável"""
    return {
        "id": str(contract.id),
        "user_id": str(contract.user_id),
        "name": contract.name,
        "description": contract.description,
        "contract_code": contract.contract_code,
        "status": contract.status.value if isinstance(contract.status, ContractStatus) else contract.status,
        "created_at": contract.created_at.isoformat() if contract.created_at else None,
        "updated_at": contract.updated_at.isoformat() if contract.updated_at else None,
    }


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
    include_deleted: bool = Query(False, description="Incluir contratos deletados"),
    user_data: dict = Depends(get_current_user_with_session),
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

    query = select(Contract).where(Contract.user_id == user.id)

    if not include_deleted:
        query = query.where(Contract.deleted_at.is_(None), Contract.is_deleted == False)  # noqa: E712

    if search_name:
        # Escapar caracteres especiais do LIKE para prevenir bypass de filtros
        search_escaped = search_name.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        query = query.where(func.lower(Contract.name).like(f"%{search_escaped.lower()}%", escape='\\'))
    if search_code:
        # Escapar caracteres especiais do LIKE para prevenir bypass de filtros
        search_escaped = search_code.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        query = query.where(func.lower(Contract.contract_code).like(f"%{search_escaped.lower()}%", escape='\\'))

    query = query.order_by(Contract.created_at.desc())

    result = await db.execute(query)
    contracts = result.scalars().all()

    return {
        "total": len(contracts),
        "contracts": [serialize_contract(c) for c in contracts]
    }


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Criar Contrato",
    description="Cria um novo contrato"
)
async def create_contract(
    data: ContractCreate,
    user_data: dict = Depends(get_current_user_with_session),
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
        current_count = await db.scalar(
            select(func.count()).select_from(Contract).where(
                Contract.user_id == user.id,
                Contract.deleted_at.is_(None),
                Contract.is_deleted == False  # noqa: E712
            )
        )
        if current_count and current_count >= max_contracts:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Limite de contratos excedido. Seu plano permite até {max_contracts} contratos."
            )
    
    contract = Contract(
        id=uuid4(),
        user_id=user.id,
        name=data.name,
        description=data.description,
        contract_code=data.contract_code,
        status=ContractStatus(validate_status(data.status)),
        categoria=validate_categoria(data.categoria),
        numero_sequencial=None
    )

    # Atribuir número sequencial simples (contagem + 1) apenas para rastreamento local
    existing_count = await db.scalar(
        select(func.count()).select_from(Contract).where(Contract.user_id == user.id)
    )
    contract.numero_sequencial = (existing_count or 0) + 1

    db.add(contract)
    await db.commit()
    await db.refresh(contract)
    
    return serialize_contract(contract)


@router.get(
    "/{contract_id}",
    summary="Obter Contrato",
    description="Obtém detalhes de um contrato específico"
)
async def get_contract(
    contract_id: str,
    user_data: dict = Depends(get_current_user_with_session),
    db: AsyncSession = Depends(get_db)
):
    """Obtém um contrato específico"""
    user = user_data["user"]

    try:
        contract_uuid = UUID(contract_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")
    
    result = await db.execute(
        select(Contract).where(
            Contract.id == contract_uuid,
            Contract.user_id == user.id,
            Contract.deleted_at.is_(None),
            Contract.is_deleted == False  # noqa: E712
        )
    )
    contract = result.scalar_one_or_none()
    
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrato não encontrado"
        )
    
    return serialize_contract(contract)


@router.put(
    "/{contract_id}",
    summary="Atualizar Contrato",
    description="Atualiza um contrato existente"
)
async def update_contract(
    contract_id: str,
    data: ContractUpdate,
    user_data: dict = Depends(get_current_user_with_session),
    db: AsyncSession = Depends(get_db)
):
    """Atualiza um contrato"""
    user = user_data["user"]

    try:
        contract_uuid = UUID(contract_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")
    
    result = await db.execute(
        select(Contract).where(
            Contract.id == contract_uuid,
            Contract.user_id == user.id,
            Contract.deleted_at.is_(None),
            Contract.is_deleted == False  # noqa: E712
        )
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrato não encontrado"
        )
    
    if data.name is not None:
        contract.name = data.name
    if data.description is not None:
        contract.description = data.description
    if data.contract_code is not None:
        contract.contract_code = data.contract_code
    if data.status is not None:
        contract.status = ContractStatus(validate_status(data.status))
    if data.categoria is not None:
        contract.categoria = validate_categoria(data.categoria)

    contract.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(contract)
    
    return serialize_contract(contract)


@router.delete(
    "/{contract_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir Contrato",
    description="Exclui um contrato (soft delete)"
)
async def delete_contract(
    contract_id: str,
    user_data: dict = Depends(get_current_user_with_session),
    db: AsyncSession = Depends(get_db)
):
    """Exclui um contrato (soft delete)"""
    user = user_data["user"]

    try:
        contract_uuid = UUID(contract_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contrato não encontrado")
    
    result = await db.execute(
        select(Contract).where(
            Contract.id == contract_uuid,
            Contract.user_id == user.id,
            Contract.deleted_at.is_(None),
            Contract.is_deleted == False  # noqa: E712
        )
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contrato não encontrado"
        )
    
    contract.mark_deleted()
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
    user_data: dict = Depends(get_current_user_with_session),
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
            SELECT id, contract_id, version_number, version_id, data_inicio, prazo_meses,
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
            "version_id": row[3],
            "data_inicio": str(row[4]) if row[4] else None,
            "prazo_meses": row[5],
            "carencia_meses": row[6],
            "parcela_inicial": float(row[7]) if row[7] else 0,
            "taxa_desconto_anual": float(row[8]) if row[8] else 0,
            "reajuste_tipo": row[9],
            "reajuste_valor": float(row[10]) if row[10] else None,
            "mes_reajuste": row[11],
            "resultados_json": row[12],
            "total_vp": float(row[13]) if row[13] else 0,
            "total_nominal": float(row[14]) if row[14] else 0,
            "avp": float(row[15]) if row[15] else 0,
            "notas": row[16],
            "archived_at": row[17].isoformat() if row[17] else None,
            "created_at": row[18].isoformat() if row[18] else None
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
    user_data: dict = Depends(get_current_user_with_session),
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
    
    # Obter categoria e número sequencial do contrato para gerar version_id
    contract_info = await db.execute(
        text("SELECT categoria, numero_sequencial FROM contracts WHERE id = :contract_id"),
        {"contract_id": contract_id}
    )
    contract_row = contract_info.fetchone()
    categoria = contract_row[0] if contract_row and contract_row[0] else "OT"
    numero_seq = contract_row[1] if contract_row and contract_row[1] else 1
    
    # Gerar version_id no formato ID{CATEGORIA}{VERSAO}-{NUMERO_SEQUENCIAL:04d}
    # Exemplo: IDVE2-0001 = ID + VE (veículo) + 2 (versão 2) + - + 0001 (contrato 1)
    version_id = f"ID{categoria}{version_number}-{numero_seq:04d}"
    
    # Inserir versão imutável
    insert_query = """
        INSERT INTO contract_versions (
            contract_id, version_number, version_id, data_inicio, prazo_meses, carencia_meses,
            parcela_inicial, taxa_desconto_anual, reajuste_tipo, reajuste_valor,
            mes_reajuste, resultados_json, total_vp, total_nominal, avp, notas
        )
        VALUES (
            :contract_id, :version_number, :version_id, :data_inicio, :prazo_meses, :carencia_meses,
            :parcela_inicial, :taxa_desconto_anual, :reajuste_tipo, :reajuste_valor,
            :mes_reajuste, :resultados_json, :total_vp, :total_nominal, :avp, :notas
        )
        RETURNING id, contract_id, version_number, version_id, data_inicio, prazo_meses,
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
            "version_id": version_id,
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
        "version_id": row[3],
        "data_inicio": str(row[4]) if row[4] else None,
        "prazo_meses": row[5],
        "total_vp": float(row[6]) if row[6] else 0,
        "notas": row[7],
        "archived_at": row[8].isoformat() if row[8] else None,
        "created_at": row[9].isoformat() if row[9] else None
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
    user_data: dict = Depends(get_current_user_with_session),
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
