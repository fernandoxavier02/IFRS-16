"""
Router para upload e gestão de documentos.
Permite anexar PDFs e outros arquivos aos contratos IFRS 16.
"""

from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..auth import get_current_user
from ..models import User, Contract
from ..schemas import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentListResponse,
    DocumentDownloadResponse,
    DocumentUpdateRequest,
    DocumentDeleteResponse,
)
from ..services.document_service import (
    document_service,
    DocumentServiceError,
    FileTooLargeError,
    InvalidMimeTypeError,
    DocumentNotFoundError,
    StorageNotConfiguredError,
)

router = APIRouter(prefix="/api/documents", tags=["Documents"])


async def verify_contract_ownership(
    db: AsyncSession,
    contract_id: str,
    user_id: str
) -> Contract:
    """Verifica se o contrato existe e pertence ao usuário"""
    result = await db.execute(
        select(Contract).where(
            Contract.id == UUID(contract_id),
            Contract.user_id == UUID(user_id),
            Contract.is_deleted == False
        )
    )
    contract = result.scalar_one_or_none()

    if not contract:
        raise HTTPException(
            status_code=404,
            detail="Contrato não encontrado ou não pertence ao usuário"
        )

    return contract


@router.post(
    "/contracts/{contract_id}/upload",
    response_model=DocumentUploadResponse,
    summary="Upload de documento",
    description="Faz upload de um documento (PDF, imagem) para um contrato"
)
async def upload_document(
    contract_id: str,
    file: UploadFile = File(..., description="Arquivo para upload (PDF, JPG, PNG)"),
    description: Optional[str] = Form(None, description="Descrição opcional do documento"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Faz upload de um documento para um contrato.

    - **file**: Arquivo (PDF, JPG, PNG, GIF). Máximo 10MB.
    - **description**: Descrição opcional do documento.

    Retorna os metadados do documento criado.
    """
    # Verificar se contrato existe e pertence ao usuário
    user_id = current_user["id"]
    await verify_contract_ownership(db, contract_id, user_id)

    try:
        # Ler conteúdo do arquivo
        file_content = await file.read()
        mime_type = file.content_type or "application/octet-stream"

        # Fazer upload
        document = await document_service.upload_document(
            db=db,
            user_id=user_id,
            contract_id=contract_id,
            filename=file.filename or "documento",
            file_content=file_content,
            mime_type=mime_type,
            description=description
        )

        # Gerar URL de download
        download_url = document_service.get_download_url(document.storage_path)

        return DocumentUploadResponse(
            id=document.id,
            contract_id=document.contract_id,
            filename=document.filename,
            file_size=document.file_size,
            mime_type=document.mime_type,
            description=document.description,
            version=document.version,
            created_at=document.created_at,
            download_url=download_url
        )

    except FileTooLargeError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except InvalidMimeTypeError as e:
        raise HTTPException(status_code=415, detail=str(e))
    except StorageNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        print(f"[ERROR] Erro no upload: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao fazer upload: {str(e)}")


@router.get(
    "/contracts/{contract_id}",
    response_model=DocumentListResponse,
    summary="Listar documentos do contrato",
    description="Lista todos os documentos anexados a um contrato"
)
async def list_contract_documents(
    contract_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Lista documentos de um contrato específico.

    - **contract_id**: ID do contrato
    - **limit**: Máximo de documentos por página
    - **offset**: Offset para paginação
    """
    # Verificar se contrato pertence ao usuário
    user_id = current_user["id"]
    await verify_contract_ownership(db, contract_id, user_id)

    try:
        documents, total = await document_service.get_documents_by_contract(
            db=db,
            contract_id=contract_id,
            limit=limit,
            offset=offset
        )

        return DocumentListResponse(
            documents=[DocumentResponse.model_validate(doc) for doc in documents],
            total=total
        )

    except Exception as e:
        print(f"[ERROR] Erro ao listar documentos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar documentos: {str(e)}")


@router.get(
    "/my-documents",
    response_model=DocumentListResponse,
    summary="Listar meus documentos",
    description="Lista todos os documentos do usuário logado"
)
async def list_my_documents(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Lista todos os documentos do usuário logado.
    """
    user_id = current_user["id"]
    try:
        documents, total = await document_service.get_documents_by_user(
            db=db,
            user_id=user_id,
            limit=limit,
            offset=offset
        )

        return DocumentListResponse(
            documents=[DocumentResponse.model_validate(doc) for doc in documents],
            total=total
        )

    except Exception as e:
        print(f"[ERROR] Erro ao listar documentos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar documentos: {str(e)}")


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Obter documento",
    description="Obtém metadados de um documento específico"
)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Obtém metadados de um documento específico.
    """
    user_id = current_user["id"]
    try:
        document = await document_service.get_document(db, document_id)

        if not document:
            raise HTTPException(status_code=404, detail="Documento não encontrado")

        # Verificar se pertence ao usuário
        if str(document.user_id) != user_id:
            raise HTTPException(status_code=403, detail="Acesso negado")

        return DocumentResponse.model_validate(document)

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Erro ao obter documento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter documento: {str(e)}")


@router.get(
    "/{document_id}/download",
    response_model=DocumentDownloadResponse,
    summary="Obter URL de download",
    description="Gera uma URL temporária para download do documento"
)
async def get_download_url(
    document_id: str,
    expires_in: int = Query(3600, ge=60, le=86400, description="Tempo de expiração em segundos (1min - 24h)"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Gera uma URL assinada temporária para download do documento.

    - **expires_in**: Tempo de expiração da URL em segundos (padrão 1 hora, máx 24 horas)
    """
    user_id = current_user["id"]
    try:
        document = await document_service.get_document(db, document_id)

        if not document:
            raise HTTPException(status_code=404, detail="Documento não encontrado")

        # Verificar se pertence ao usuário
        if str(document.user_id) != user_id:
            raise HTTPException(status_code=403, detail="Acesso negado")

        # Gerar URL assinada
        download_url = document_service.get_download_url(
            document.storage_path,
            expires_in_seconds=expires_in
        )

        return DocumentDownloadResponse(
            id=document.id,
            filename=document.filename,
            download_url=download_url,
            expires_in=expires_in
        )

    except StorageNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Erro ao gerar URL de download: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar URL: {str(e)}")


@router.patch(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Atualizar documento",
    description="Atualiza metadados de um documento (descrição)"
)
async def update_document(
    document_id: str,
    update_data: DocumentUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Atualiza metadados de um documento.

    - **description**: Nova descrição do documento
    """
    user_id = current_user["id"]
    try:
        document = await document_service.update_document(
            db=db,
            document_id=document_id,
            user_id=user_id,
            description=update_data.description
        )

        return DocumentResponse.model_validate(document)

    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    except Exception as e:
        print(f"[ERROR] Erro ao atualizar documento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar: {str(e)}")


@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="Deletar documento",
    description="Remove um documento (soft delete por padrão)"
)
async def delete_document(
    document_id: str,
    hard_delete: bool = Query(False, description="Se True, remove permanentemente"),
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Deleta um documento.

    - **hard_delete**: Se True, remove permanentemente do storage e banco.
                       Se False (padrão), apenas marca como deletado.
    """
    user_id = current_user["id"]
    try:
        await document_service.delete_document(
            db=db,
            document_id=document_id,
            user_id=user_id,
            hard_delete=hard_delete
        )

        return DocumentDeleteResponse(
            success=True,
            message="Documento deletado com sucesso",
            id=UUID(document_id)
        )

    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    except StorageNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        print(f"[ERROR] Erro ao deletar documento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao deletar: {str(e)}")
