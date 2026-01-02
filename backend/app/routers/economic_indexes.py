"""
Endpoints para índices econômicos (BCB)
SELIC, IGPM, IPCA, CDI, INPC, TR
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas import (
    EconomicIndexResponse,
    EconomicIndexListResponse,
    EconomicIndexLatestResponse,
    EconomicIndexSyncResponse,
    EconomicIndexTypeEnum,
)
from ..services.bcb_service import BCBService
from ..auth import get_current_admin, get_current_user

router = APIRouter(
    prefix="/api/economic-indexes",
    tags=["Economic Indexes"]
)


@router.get(
    "",
    response_model=EconomicIndexListResponse,
    summary="Listar índices econômicos",
    description="Lista índices econômicos armazenados no banco de dados"
)
async def list_indexes(
    index_type: Optional[str] = Query(
        None,
        description="Filtrar por tipo (selic, igpm, ipca, cdi, inpc, tr)"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista índices econômicos do banco de dados.

    Endpoint público para consulta.

    - **index_type**: Filtrar por tipo de índice
    - **limit**: Máximo de registros
    - **offset**: Offset para paginação
    """
    # Validar index_type se fornecido
    if index_type:
        try:
            EconomicIndexTypeEnum(index_type.lower())
        except ValueError:
            valid_types = [e.value for e in EconomicIndexTypeEnum]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de índice inválido. Use: {', '.join(valid_types)}"
            )

    indexes, total = await BCBService.get_index_history(
        db=db,
        index_type=index_type,
        limit=limit,
        offset=offset
    )

    return EconomicIndexListResponse(
        indexes=[EconomicIndexResponse.model_validate(idx) for idx in indexes],
        total=total
    )


@router.get(
    "/types",
    summary="Listar tipos de índices suportados",
    description="Retorna lista de tipos de índices econômicos suportados"
)
async def list_index_types():
    """
    Retorna os tipos de índices econômicos suportados.

    Endpoint público.
    """
    return {
        "types": BCBService.get_supported_indexes(),
        "available": list(EconomicIndexTypeEnum)
    }


@router.get(
    "/{index_type}/latest",
    response_model=EconomicIndexLatestResponse,
    summary="Último valor de um índice",
    description="Retorna o valor mais recente de um índice econômico"
)
async def get_latest_index(
    index_type: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Retorna o valor mais recente de um índice econômico.

    Endpoint público.

    - **index_type**: Tipo do índice (selic, igpm, ipca, cdi, inpc, tr)
    """
    # Validar tipo
    try:
        EconomicIndexTypeEnum(index_type.lower())
    except ValueError:
        valid_types = [e.value for e in EconomicIndexTypeEnum]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de índice inválido. Use: {', '.join(valid_types)}"
        )

    latest = await BCBService.get_latest_value(db, index_type)

    if not latest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nenhum valor encontrado para índice '{index_type}'. Execute sync primeiro."
        )

    return EconomicIndexLatestResponse(
        index_type=latest.index_type,
        reference_date=latest.reference_date,
        value=latest.value,
        source=latest.source
    )


@router.post(
    "/sync/{index_type}",
    response_model=EconomicIndexSyncResponse,
    summary="Sincronizar índice do BCB",
    description="Busca dados do Banco Central e salva no banco de dados (admin only)"
)
async def sync_index(
    index_type: str,
    last_n: int = Query(12, ge=1, le=120, description="Últimos N registros"),
    admin_data: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Sincroniza um índice econômico do Banco Central.

    Requer: Token JWT de administrador

    - **index_type**: Tipo do índice (selic, igpm, ipca, cdi, inpc, tr)
    - **last_n**: Quantidade de registros mais recentes a buscar
    """
    # Validar tipo
    try:
        EconomicIndexTypeEnum(index_type.lower())
    except ValueError:
        valid_types = [e.value for e in EconomicIndexTypeEnum]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de índice inválido. Use: {', '.join(valid_types)}"
        )

    try:
        synced_count = await BCBService.sync_index_to_db(
            db=db,
            index_type=index_type,
            last_n=last_n
        )

        return EconomicIndexSyncResponse(
            success=True,
            message=f"Sincronização concluída com sucesso",
            synced_count=synced_count,
            index_type=index_type.lower()
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao sincronizar: {str(e)}"
        )


@router.post(
    "/sync-all",
    summary="Sincronizar todos os índices",
    description="Sincroniza todos os índices econômicos do BCB (admin only)"
)
async def sync_all_indexes(
    last_n: int = Query(12, ge=1, le=120, description="Últimos N registros por índice"),
    admin_data: dict = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Sincroniza todos os índices econômicos do Banco Central.

    Requer: Token JWT de administrador

    - **last_n**: Quantidade de registros mais recentes por índice
    """
    try:
        results = await BCBService.sync_all_indexes(db=db, last_n=last_n)

        total_synced = sum(v for v in results.values() if v > 0)
        errors = [k for k, v in results.items() if v < 0]

        return {
            "success": len(errors) == 0,
            "message": f"Sincronização concluída. Total: {total_synced} registros.",
            "results": results,
            "errors": errors if errors else None
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao sincronizar: {str(e)}"
        )
