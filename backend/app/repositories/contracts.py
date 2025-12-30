"""
Repository para operações de banco de dados de contratos
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..models import Contract, User


class ContractRepository:
    """Repository para operações CRUD de contratos"""
    
    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        contract_id: UUID,
        user_id: UUID
    ) -> Optional[Contract]:
        """Obtém um contrato por ID"""
        result = await db.execute(
            select(Contract).where(
                Contract.id == contract_id,
                Contract.user_id == user_id,
                Contract.is_deleted == False
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all_by_user(
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Contract]:
        """Obtém todos os contratos de um usuário"""
        result = await db.execute(
            select(Contract).where(
                Contract.user_id == user_id,
                Contract.is_deleted == False
            ).offset(skip).limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def count_by_user(
        db: AsyncSession,
        user_id: UUID
    ) -> int:
        """Conta contratos de um usuário"""
        result = await db.scalar(
            select(func.count()).select_from(Contract).where(
                Contract.user_id == user_id,
                Contract.is_deleted == False
            )
        )
        return result or 0
    
    @staticmethod
    async def create(
        db: AsyncSession,
        contract: Contract
    ) -> Contract:
        """Cria um novo contrato"""
        db.add(contract)
        await db.commit()
        await db.refresh(contract)
        return contract
    
    @staticmethod
    async def update(
        db: AsyncSession,
        contract: Contract
    ) -> Contract:
        """Atualiza um contrato"""
        await db.commit()
        await db.refresh(contract)
        return contract
    
    @staticmethod
    async def delete(
        db: AsyncSession,
        contract: Contract
    ) -> None:
        """Soft delete de um contrato"""
        contract.is_deleted = True
        await db.commit()
