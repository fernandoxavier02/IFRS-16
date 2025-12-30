"""
Service para regras de negócio de contratos
"""

from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models import User, License, LicenseStatus, Contract
from ..repositories.contracts import ContractRepository


class ContractService:
    """Service para operações de contratos com validação de regras de negócio"""
    
    @staticmethod
    async def _get_active_license(
        db: AsyncSession,
        user: User
    ) -> Optional[License]:
        """
        Obtém a licença ativa do usuário.
        
        Args:
            db: Sessão do banco de dados
            user: Usuário
            
        Returns:
            Licença ativa se encontrada, None caso contrário
        """
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
        
        # Verificar se expirou
        if user_license.expires_at and datetime.utcnow() > user_license.expires_at:
            return None
        
        return user_license
    
    @staticmethod
    async def create_contract(
        db: AsyncSession,
        user: User,
        data: Any
    ) -> Contract:
        """
        Cria um novo contrato para o usuário, validando limite da licença.
        
        Args:
            db: Sessão do banco de dados
            user: Usuário autenticado
            data: Dados do contrato
            
        Returns:
            Contrato criado
            
        Raises:
            HTTPException: Se o limite de contratos for excedido ou não houver licença ativa
        """
        # Obter licença ativa
        user_license = await ContractService._get_active_license(db, user)
        
        if not user_license:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário não possui licença ativa. É necessário uma licença válida para criar contratos."
            )
        
        # Obter limite de contratos da licença
        features = user_license.features
        max_contracts = features.get("max_contracts", 0)
        
        # Se ilimitado (-1), não precisa validar
        if max_contracts != -1:
            # Contar contratos ativos do usuário
            current_count = await ContractRepository.count_active_contracts(db, user.id)
            
            if current_count >= max_contracts:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Limite de contratos excedido. Seu plano permite até {max_contracts} contratos. Você já possui {current_count} contrato(s)."
                )
        
        # Criar contrato via repository
        return await ContractRepository.create_contract(db, user.id, data)
    
    @staticmethod
    async def list_contracts(
        db: AsyncSession,
        user: User,
        include_deleted: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[Contract]:
        """
        Lista contratos do usuário.
        
        Args:
            db: Sessão do banco de dados
            user: Usuário autenticado
            include_deleted: Se True, inclui contratos deletados
            skip: Número de registros a pular
            limit: Limite de registros a retornar
            
        Returns:
            Lista de contratos do usuário
        """
        return await ContractRepository.list_contracts(
            db, user.id, include_deleted=include_deleted, skip=skip, limit=limit
        )
    
    @staticmethod
    async def get_contract(
        db: AsyncSession,
        user: User,
        contract_id: UUID
    ) -> Contract:
        """
        Obtém um contrato específico do usuário.
        
        Args:
            db: Sessão do banco de dados
            user: Usuário autenticado
            contract_id: ID do contrato
            
        Returns:
            Contrato encontrado
            
        Raises:
            HTTPException: Se o contrato não for encontrado ou não pertencer ao usuário
        """
        contract = await ContractRepository.get_contract_by_id(db, user.id, contract_id)
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contrato não encontrado ou você não tem permissão para acessá-lo."
            )
        
        return contract
    
    @staticmethod
    async def update_contract(
        db: AsyncSession,
        user: User,
        contract_id: UUID,
        data: Any
    ) -> Contract:
        """
        Atualiza um contrato do usuário.
        
        Args:
            db: Sessão do banco de dados
            user: Usuário autenticado
            contract_id: ID do contrato
            data: Dados a atualizar
            
        Returns:
            Contrato atualizado
            
        Raises:
            HTTPException: Se o contrato não for encontrado ou não pertencer ao usuário
        """
        contract = await ContractRepository.update_contract(db, user.id, contract_id, data)
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contrato não encontrado ou você não tem permissão para atualizá-lo."
            )
        
        return contract
    
    @staticmethod
    async def delete_contract(
        db: AsyncSession,
        user: User,
        contract_id: UUID
    ) -> bool:
        """
        Realiza soft delete de um contrato do usuário.
        
        Args:
            db: Sessão do banco de dados
            user: Usuário autenticado
            contract_id: ID do contrato
            
        Returns:
            True se deletado com sucesso
            
        Raises:
            HTTPException: Se o contrato não for encontrado ou não pertencer ao usuário
        """
        success = await ContractRepository.soft_delete_contract(db, user.id, contract_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contrato não encontrado ou você não tem permissão para deletá-lo."
            )
        
        return True
