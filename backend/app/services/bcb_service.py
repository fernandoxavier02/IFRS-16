"""
Serviço de integração com API do Banco Central do Brasil
Busca índices econômicos: SELIC, IGPM, IPCA, CDI, INPC, TR
"""

import httpx
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from ..models import EconomicIndex

# Códigos das séries MENSAIS do BCB
# Referência: https://www3.bcb.gov.br/sgspub/localizarseries/localizarSeries.do
# IMPORTANTE: Usando séries mensais para evitar problemas com limites de datas
BCB_SERIES_CODES = {
    "selic": 4189,   # Taxa SELIC acumulada no mês (% a.m.) - série mensal
    "igpm": 189,     # IGP-M - Índice Geral de Preços do Mercado (% a.m.)
    "ipca": 433,     # IPCA - Índice Nacional de Preços ao Consumidor Amplo (% a.m.)
    "cdi": 4391,     # CDI acumulado no mês (% a.m.) - série mensal
    "inpc": 188,     # INPC - Índice Nacional de Preços ao Consumidor (% a.m.)
    "tr": 226        # TR - Taxa Referencial (% a.m.)
}

# Descrições dos índices
BCB_INDEX_DESCRIPTIONS = {
    "selic": "Taxa SELIC - Meta COPOM",
    "igpm": "IGP-M - Índice Geral de Preços do Mercado",
    "ipca": "IPCA - Índice de Preços ao Consumidor Amplo",
    "cdi": "CDI - Certificado de Depósito Interbancário",
    "inpc": "INPC - Índice Nacional de Preços ao Consumidor",
    "tr": "TR - Taxa Referencial"
}


class BCBService:
    """Serviço para buscar índices econômicos do Banco Central do Brasil"""

    BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
    TIMEOUT = 30.0  # segundos

    @classmethod
    def get_supported_indexes(cls) -> Dict[str, str]:
        """Retorna dict com índices suportados e suas descrições"""
        return BCB_INDEX_DESCRIPTIONS.copy()

    @classmethod
    def get_bcb_code(cls, index_type: str) -> Optional[int]:
        """Retorna o código BCB para um tipo de índice"""
        return BCB_SERIES_CODES.get(index_type.lower())

    @classmethod
    async def fetch_from_bcb(
        cls,
        index_type: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        last_n: Optional[int] = None
    ) -> List[Dict]:
        """
        Busca dados de índice econômico da API do BCB.

        Args:
            index_type: Tipo do índice (selic, igpm, ipca, cdi, inpc, tr)
            start_date: Data inicial no formato DD/MM/YYYY
            end_date: Data final no formato DD/MM/YYYY
            last_n: Retorna apenas os últimos N registros

        Returns:
            Lista de dicts com {data: "DD/MM/YYYY", valor: "10.50"}

        Raises:
            ValueError: Se index_type não for suportado
            httpx.HTTPError: Se houver erro na requisição
        """
        codigo = cls.get_bcb_code(index_type)
        if codigo is None:
            raise ValueError(
                f"Índice '{index_type}' não suportado. "
                f"Use: {', '.join(BCB_SERIES_CODES.keys())}"
            )

        url = cls.BASE_URL.format(codigo=codigo)
        params = {"formato": "json"}

        if start_date:
            params["dataInicial"] = start_date
        if end_date:
            params["dataFinal"] = end_date
        if last_n:
            params["ultimos"] = last_n

        async with httpx.AsyncClient(timeout=cls.TIMEOUT) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    @classmethod
    def parse_bcb_date(cls, date_str: str) -> datetime:
        """Converte data do formato BCB (DD/MM/YYYY) para datetime"""
        return datetime.strptime(date_str, "%d/%m/%Y")

    @classmethod
    async def sync_index_to_db(
        cls,
        db: AsyncSession,
        index_type: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        last_n: Optional[int] = 12  # Default: últimos 12 meses
    ) -> int:
        """
        Busca índices do BCB e salva no banco de dados.
        Usa upsert para evitar duplicatas.

        Args:
            db: Sessão do banco de dados
            index_type: Tipo do índice
            start_date: Data inicial (DD/MM/YYYY)
            end_date: Data final (DD/MM/YYYY)
            last_n: Número de registros mais recentes

        Returns:
            Número de registros sincronizados
        """
        # Buscar dados do BCB
        data = await cls.fetch_from_bcb(
            index_type=index_type,
            start_date=start_date,
            end_date=end_date,
            last_n=last_n
        )

        if not data:
            return 0

        index_type_lower = index_type.lower()
        synced_count = 0

        for item in data:
            try:
                reference_date = cls.parse_bcb_date(item["data"])
                value = item["valor"]

                # Verificar se já existe
                existing = await db.execute(
                    select(EconomicIndex).where(
                        and_(
                            EconomicIndex.index_type == index_type_lower,
                            EconomicIndex.reference_date == reference_date
                        )
                    )
                )
                existing_record = existing.scalar_one_or_none()

                if existing_record:
                    # Atualizar valor se diferente
                    if existing_record.value != value:
                        existing_record.value = value
                        synced_count += 1
                else:
                    # Criar novo registro
                    new_index = EconomicIndex(
                        index_type=index_type_lower,
                        reference_date=reference_date,
                        value=value,
                        source="BCB"
                    )
                    db.add(new_index)
                    synced_count += 1

            except (KeyError, ValueError) as e:
                print(f"[BCB] Erro ao processar item {item}: {e}")
                continue

        await db.commit()
        return synced_count

    @classmethod
    async def sync_all_indexes(
        cls,
        db: AsyncSession,
        last_n: int = 12
    ) -> Dict[str, int]:
        """
        Sincroniza todos os índices suportados.

        Args:
            db: Sessão do banco de dados
            last_n: Número de registros mais recentes por índice

        Returns:
            Dict com contagem de registros sincronizados por índice
        """
        results = {}
        for index_type in BCB_SERIES_CODES.keys():
            try:
                count = await cls.sync_index_to_db(db, index_type, last_n=last_n)
                results[index_type] = count
                print(f"[BCB] {index_type.upper()}: {count} registros sincronizados")
            except Exception as e:
                print(f"[BCB] Erro ao sincronizar {index_type}: {e}")
                results[index_type] = -1  # Indica erro

        return results

    @classmethod
    async def get_latest_value(
        cls,
        db: AsyncSession,
        index_type: str,
        max_age_days: Optional[int] = None
    ) -> Optional[EconomicIndex]:
        """
        Retorna o valor mais recente de um índice do banco de dados.
        
        Se max_age_days for fornecido, verifica se o índice é recente o suficiente.
        Se o índice for antigo (> max_age_days), retorna None para forçar refresh.

        Args:
            db: Sessão do banco de dados
            index_type: Tipo do índice
            max_age_days: Idade máxima em dias (opcional, para cache agressivo)

        Returns:
            EconomicIndex mais recente ou None
        """
        from datetime import datetime, timedelta
        
        result = await db.execute(
            select(EconomicIndex)
            .where(EconomicIndex.index_type == index_type.lower())
            .order_by(EconomicIndex.reference_date.desc())
            .limit(1)
        )
        index = result.scalar_one_or_none()
        
        # Cache agressivo: se max_age_days fornecido e índice é antigo, retornar None
        if index and max_age_days:
            age = (datetime.utcnow() - index.reference_date).days
            if age > max_age_days:
                return None
        
        return index

    @classmethod
    async def get_index_history(
        cls,
        db: AsyncSession,
        index_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[EconomicIndex], int]:
        """
        Retorna histórico de índices do banco de dados.

        Args:
            db: Sessão do banco de dados
            index_type: Filtrar por tipo (opcional)
            limit: Limite de registros
            offset: Offset para paginação

        Returns:
            Tupla com (lista de índices, total de registros)
        """
        query = select(EconomicIndex)

        if index_type:
            query = query.where(EconomicIndex.index_type == index_type.lower())

        # Contar total
        from sqlalchemy import func
        count_query = select(func.count()).select_from(EconomicIndex)
        if index_type:
            count_query = count_query.where(EconomicIndex.index_type == index_type.lower())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Buscar registros com paginação
        query = query.order_by(
            EconomicIndex.index_type,
            EconomicIndex.reference_date.desc()
        ).offset(offset).limit(limit)

        result = await db.execute(query)
        indexes = result.scalars().all()

        return list(indexes), total
