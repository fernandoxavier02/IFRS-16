"""
Serviço de gestão de documentos (upload/download) com Firebase Storage.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, BinaryIO
from pathlib import Path

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..models import Document, Contract

# Tentar importar Firebase Admin SDK
try:
    import firebase_admin
    from firebase_admin import credentials, storage
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("[WARN] firebase-admin não instalado. Upload de documentos desabilitado.")


settings = get_settings()


class DocumentServiceError(Exception):
    """Exceção base para erros do serviço de documentos"""
    pass


class FileTooLargeError(DocumentServiceError):
    """Arquivo excede o tamanho máximo permitido"""
    pass


class InvalidMimeTypeError(DocumentServiceError):
    """Tipo de arquivo não permitido"""
    pass


class DocumentNotFoundError(DocumentServiceError):
    """Documento não encontrado"""
    pass


class StorageNotConfiguredError(DocumentServiceError):
    """Firebase Storage não está configurado"""
    pass


class DocumentService:
    """
    Serviço para upload, download e gestão de documentos.
    Usa Firebase Storage para armazenamento e PostgreSQL para metadados.
    """

    def __init__(self):
        self._bucket = None
        self._initialized = False

    def _ensure_initialized(self):
        """Inicializa conexão com Firebase Storage se necessário"""
        if self._initialized:
            return

        if not FIREBASE_AVAILABLE:
            raise StorageNotConfiguredError(
                "firebase-admin não está instalado. Execute: pip install firebase-admin"
            )

        try:
            # Verificar se já foi inicializado
            try:
                firebase_admin.get_app()
            except ValueError:
                # Não inicializado, inicializar agora
                cred_path = settings.FIREBASE_CREDENTIALS_PATH
                if cred_path and Path(cred_path).exists():
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred, {
                        'storageBucket': settings.FIREBASE_STORAGE_BUCKET
                    })
                else:
                    # Usar credenciais padrão (Application Default Credentials)
                    # Funciona automaticamente no Cloud Run
                    firebase_admin.initialize_app(options={
                        'storageBucket': settings.FIREBASE_STORAGE_BUCKET
                    })

            self._bucket = storage.bucket()
            self._initialized = True
            print(f"[OK] Firebase Storage inicializado: {settings.FIREBASE_STORAGE_BUCKET}")

        except Exception as e:
            raise StorageNotConfiguredError(f"Erro ao inicializar Firebase Storage: {e}")

    def _validate_file(self, filename: str, file_size: int, mime_type: str):
        """Valida arquivo antes do upload"""
        # Validar tamanho
        max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # Converter MB para bytes
        if file_size > max_size:
            raise FileTooLargeError(
                f"Arquivo muito grande ({file_size / 1024 / 1024:.2f}MB). "
                f"Máximo permitido: {settings.MAX_FILE_SIZE_MB}MB"
            )

        # Validar tipo MIME
        allowed_types = settings.allowed_mime_types_list
        if mime_type not in allowed_types:
            raise InvalidMimeTypeError(
                f"Tipo de arquivo não permitido: {mime_type}. "
                f"Tipos permitidos: {', '.join(allowed_types)}"
            )

    def _generate_storage_path(self, user_id: str, contract_id: str, filename: str) -> str:
        """Gera caminho único no storage"""
        # Formato: documents/{user_id}/{contract_id}/{uuid}_{filename}
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        return f"documents/{user_id}/{contract_id}/{unique_id}_{safe_filename}"

    async def upload_document(
        self,
        db: AsyncSession,
        user_id: str,
        contract_id: str,
        filename: str,
        file_content: bytes,
        mime_type: str,
        description: Optional[str] = None
    ) -> Document:
        """
        Faz upload de um documento para o Firebase Storage.

        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            contract_id: ID do contrato
            filename: Nome original do arquivo
            file_content: Conteúdo do arquivo em bytes
            mime_type: Tipo MIME do arquivo
            description: Descrição opcional

        Returns:
            Document: Documento criado

        Raises:
            FileTooLargeError: Se arquivo excede tamanho máximo
            InvalidMimeTypeError: Se tipo de arquivo não é permitido
            StorageNotConfiguredError: Se Firebase não está configurado
        """
        self._ensure_initialized()

        file_size = len(file_content)
        self._validate_file(filename, file_size, mime_type)

        # Gerar caminho no storage
        storage_path = self._generate_storage_path(user_id, contract_id, filename)

        # Upload para Firebase Storage
        blob = self._bucket.blob(storage_path)
        blob.upload_from_string(file_content, content_type=mime_type)

        # Criar registro no banco (usar datetime sem timezone para PostgreSQL)
        document = Document(
            id=uuid.uuid4(),
            contract_id=uuid.UUID(contract_id),
            user_id=uuid.UUID(user_id),
            filename=filename,
            storage_path=storage_path,
            file_size=file_size,
            mime_type=mime_type,
            description=description,
            version=1,
            created_at=datetime.utcnow()
        )

        db.add(document)
        await db.commit()
        await db.refresh(document)

        print(f"[OK] Documento uploaded: {filename} ({file_size} bytes)")
        return document

    async def get_document(self, db: AsyncSession, document_id: str) -> Optional[Document]:
        """Busca documento por ID"""
        result = await db.execute(
            select(Document).where(
                and_(
                    Document.id == uuid.UUID(document_id),
                    Document.is_deleted == False
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_documents_by_contract(
        self,
        db: AsyncSession,
        contract_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Document], int]:
        """
        Lista documentos de um contrato.

        Returns:
            Tupla (lista de documentos, total)
        """
        # Contar total
        count_query = select(Document).where(
            and_(
                Document.contract_id == uuid.UUID(contract_id),
                Document.is_deleted == False
            )
        )
        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        # Buscar com paginação
        query = (
            select(Document)
            .where(
                and_(
                    Document.contract_id == uuid.UUID(contract_id),
                    Document.is_deleted == False
                )
            )
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(query)
        documents = result.scalars().all()

        return list(documents), total

    async def get_documents_by_user(
        self,
        db: AsyncSession,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Document], int]:
        """Lista todos os documentos de um usuário"""
        # Contar total
        count_query = select(Document).where(
            and_(
                Document.user_id == uuid.UUID(user_id),
                Document.is_deleted == False
            )
        )
        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        # Buscar com paginação
        query = (
            select(Document)
            .where(
                and_(
                    Document.user_id == uuid.UUID(user_id),
                    Document.is_deleted == False
                )
            )
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(query)
        documents = result.scalars().all()

        return list(documents), total

    def get_download_url(self, storage_path: str, expires_in_seconds: int = 3600) -> str:
        """
        Gera URL assinada para download do arquivo.

        Args:
            storage_path: Caminho do arquivo no storage
            expires_in_seconds: Tempo de expiração da URL (padrão 1 hora)

        Returns:
            URL assinada para download
        """
        self._ensure_initialized()

        blob = self._bucket.blob(storage_path)
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(seconds=expires_in_seconds),
            method="GET"
        )
        return url

    async def delete_document(
        self,
        db: AsyncSession,
        document_id: str,
        user_id: str,
        hard_delete: bool = False
    ) -> bool:
        """
        Deleta um documento.

        Args:
            db: Sessão do banco de dados
            document_id: ID do documento
            user_id: ID do usuário (para verificar permissão)
            hard_delete: Se True, remove permanentemente. Se False, soft delete.

        Returns:
            True se deletado com sucesso

        Raises:
            DocumentNotFoundError: Se documento não existe ou não pertence ao usuário
        """
        self._ensure_initialized()

        # Buscar documento
        result = await db.execute(
            select(Document).where(
                and_(
                    Document.id == uuid.UUID(document_id),
                    Document.user_id == uuid.UUID(user_id),
                    Document.is_deleted == False
                )
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentNotFoundError(f"Documento não encontrado: {document_id}")

        if hard_delete:
            # Deletar do storage
            try:
                blob = self._bucket.blob(document.storage_path)
                blob.delete()
            except Exception as e:
                print(f"[WARN] Erro ao deletar do storage: {e}")

            # Deletar do banco
            await db.delete(document)
        else:
            # Soft delete
            document.mark_deleted()

        await db.commit()
        print(f"[OK] Documento deletado: {document.filename}")
        return True

    async def update_document(
        self,
        db: AsyncSession,
        document_id: str,
        user_id: str,
        description: Optional[str] = None
    ) -> Document:
        """
        Atualiza metadados de um documento.

        Args:
            db: Sessão do banco de dados
            document_id: ID do documento
            user_id: ID do usuário
            description: Nova descrição

        Returns:
            Documento atualizado
        """
        result = await db.execute(
            select(Document).where(
                and_(
                    Document.id == uuid.UUID(document_id),
                    Document.user_id == uuid.UUID(user_id),
                    Document.is_deleted == False
                )
            )
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentNotFoundError(f"Documento não encontrado: {document_id}")

        if description is not None:
            document.description = description

        document.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(document)

        return document


# Instância global do serviço
document_service = DocumentService()
