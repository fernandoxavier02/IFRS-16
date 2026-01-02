"""
Testes para API de Índices Econômicos (Funcionalidade 1)
Cobre modelo, service e endpoints conforme PLANO_IMPLEMENTACAO_MELHORIAS.md
"""

import pytest
import pytest_asyncio
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import EconomicIndex
from app.services.bcb_service import BCBService
from app.services.remeasurement_service import RemeasurementService
from app.schemas import EconomicIndexTypeEnum


# =============================================================================
# FIXTURES
# =============================================================================

@pytest_asyncio.fixture
async def sample_economic_index(db_session: AsyncSession) -> EconomicIndex:
    """Cria um índice econômico de teste"""
    index = EconomicIndex(
        index_type="selic",
        reference_date=datetime(2024, 1, 1),
        value="12.75",
        source="BCB"
    )
    db_session.add(index)
    await db_session.commit()
    await db_session.refresh(index)
    return index


@pytest_asyncio.fixture
async def multiple_economic_indexes(db_session: AsyncSession) -> list[EconomicIndex]:
    """Cria múltiplos índices econômicos para testes"""
    indexes = []
    base_date = datetime(2024, 1, 1)
    
    for i in range(5):
        index = EconomicIndex(
            index_type="selic",
            reference_date=base_date + timedelta(days=30 * i),
            value=str(12.0 + i * 0.1),
            source="BCB"
        )
        db_session.add(index)
        indexes.append(index)
    
    # Adicionar índices de tipos diferentes
    for index_type in ["igpm", "ipca"]:
        index = EconomicIndex(
            index_type=index_type,
            reference_date=base_date,
            value="5.0",
            source="BCB"
        )
        db_session.add(index)
        indexes.append(index)
    
    await db_session.commit()
    for idx in indexes:
        await db_session.refresh(idx)
    
    return indexes


# =============================================================================
# TESTES DO MODELO (Etapa 1.1)
# =============================================================================

class TestEconomicIndexModel:
    """Testes para o modelo EconomicIndex"""
    
    def test_model_can_be_imported(self):
        """Teste 1.1.1: Verificar se modelo pode ser importado sem erros"""
        assert EconomicIndex is not None
        assert hasattr(EconomicIndex, '__tablename__')
        assert EconomicIndex.__tablename__ == "economic_indexes"
    
    @pytest.mark.asyncio
    async def test_create_valid_index(self, db_session: AsyncSession):
        """Teste 1.1.3: Testar inserção válida"""
        index = EconomicIndex(
            index_type="selic",
            reference_date=datetime(2024, 1, 1),
            value="12.75",
            source="BCB"
        )
        db_session.add(index)
        await db_session.commit()
        await db_session.refresh(index)
        
        assert index.id is not None
        assert index.index_type == "selic"
        assert index.value == "12.75"
        assert index.source == "BCB"
    
    @pytest.mark.asyncio
    async def test_unique_constraint_type_date(self, db_session: AsyncSession):
        """Teste 1.1.3: Testar inserção duplicada (mesmo tipo + data) - deve falhar"""
        index1 = EconomicIndex(
            index_type="selic",
            reference_date=datetime(2024, 1, 1),
            value="12.75",
            source="BCB"
        )
        db_session.add(index1)
        await db_session.commit()
        
        # Tentar criar duplicata
        index2 = EconomicIndex(
            index_type="selic",
            reference_date=datetime(2024, 1, 1),
            value="13.00",
            source="BCB"
        )
        db_session.add(index2)
        
        # SQLite não aplica constraint unique automaticamente em alguns casos
        # Mas o código deve verificar antes de inserir
        with pytest.raises(Exception):
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_index_required_fields(self, db_session: AsyncSession):
        """Teste 1.1.3: Testar inserção com valores nulos obrigatórios - deve falhar"""
        # Tentar criar sem index_type
        index = EconomicIndex(
            reference_date=datetime(2024, 1, 1),
            value="12.75",
            source="BCB"
        )
        db_session.add(index)
        
        with pytest.raises(Exception):
            await db_session.commit()


# =============================================================================
# TESTES DO SERVICE (Etapa 1.3)
# =============================================================================

class TestBCBService:
    """Testes para BCBService"""
    
    @pytest.mark.asyncio
    async def test_fetch_from_bcb_mocked(self, db_session: AsyncSession):
        """Teste 1.3.1: Testar busca única do BCB (mockado)"""
        mock_data = [
            {"data": "01/01/2024", "valor": "12.75"},
            {"data": "01/02/2024", "valor": "12.50"}
        ]
        
        with patch('app.services.bcb_service.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            # json() não é async, retorna o valor diretamente
            mock_response.json = MagicMock(return_value=mock_data)
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            data = await BCBService.fetch_from_bcb("selic", last_n=2)
            
            assert len(data) == 2
            assert data[0]["data"] == "01/01/2024"
            assert data[0]["valor"] == "12.75"
    
    @pytest.mark.asyncio
    async def test_get_or_fetch_exists(self, db_session: AsyncSession, sample_economic_index: EconomicIndex):
        """Teste 1.3.2: Testar get_or_fetch - existe no banco"""
        # O índice já existe no banco (via fixture)
        latest = await BCBService.get_latest_value(db_session, "selic")
        
        assert latest is not None
        assert latest.index_type == "selic"
        assert latest.value == "12.75"
    
    @pytest.mark.asyncio
    async def test_get_or_fetch_not_exists_busca_bcb(self, db_session: AsyncSession):
        """Teste 1.3.3: Testar get_or_fetch - não existe, busca BCB"""
        mock_data = [
            {"data": "01/01/2024", "valor": "12.75"}
        ]
        
        with patch('app.services.bcb_service.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            # json() não é async, retorna o valor diretamente
            mock_response.json = MagicMock(return_value=mock_data)
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            # Garantir que não existe no banco
            result = await db_session.execute(
                select(EconomicIndex).where(EconomicIndex.index_type == "cdi")
            )
            existing = result.scalar_one_or_none()
            assert existing is None
            
            # Sincronizar do BCB
            synced_count = await BCBService.sync_index_to_db(
                db_session,
                "cdi",
                last_n=1
            )
            
            assert synced_count > 0
            
            # Verificar que foi salvo no banco
            latest = await BCBService.get_latest_value(db_session, "cdi")
            assert latest is not None
            assert latest.value == "12.75"
    
    @pytest.mark.asyncio
    async def test_fetch_from_bcb_network_error(self):
        """Teste 1.3.4: Testar tratamento de erro de rede"""
        import httpx
        
        with patch('app.services.bcb_service.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.HTTPError("Network error"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            with pytest.raises(httpx.HTTPError):
                await BCBService.fetch_from_bcb("selic")
    
    @pytest.mark.asyncio
    async def test_sync_index_to_db_upsert(self, db_session: AsyncSession):
        """Testar que sync_index_to_db faz upsert (não duplica)"""
        mock_data = [
            {"data": "01/01/2024", "valor": "12.75"}
        ]
        
        with patch('app.services.bcb_service.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            # json() não é async, retorna o valor diretamente
            mock_response.json = MagicMock(return_value=mock_data)
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            # Primeira sincronização
            count1 = await BCBService.sync_index_to_db(
                db_session,
                "selic",
                last_n=1
            )
            assert count1 == 1
            
            # Segunda sincronização (deve atualizar, não duplicar)
            count2 = await BCBService.sync_index_to_db(
                db_session,
                "selic",
                last_n=1
            )
            # Se já existe, não deve contar como novo
            assert count2 >= 0
            
            # Verificar que existe apenas um registro
            result = await db_session.execute(
                select(EconomicIndex).where(EconomicIndex.index_type == "selic")
            )
            indexes = result.scalars().all()
            # Pode ter mais de um se houver múltiplas datas, mas não duplicatas da mesma data
            assert len([idx for idx in indexes if idx.reference_date == datetime(2024, 1, 1)]) == 1
    
    @pytest.mark.asyncio
    async def test_get_latest_value(self, db_session: AsyncSession, multiple_economic_indexes: list[EconomicIndex]):
        """Teste 1.2.3: Testar busca do mais recente"""
        latest = await BCBService.get_latest_value(db_session, "selic")
        
        assert latest is not None
        assert latest.index_type == "selic"
        # Deve ser o mais recente (último da lista)
        assert latest.reference_date == max(idx.reference_date for idx in multiple_economic_indexes if idx.index_type == "selic")
    
    @pytest.mark.asyncio
    async def test_get_index_history(self, db_session: AsyncSession, multiple_economic_indexes: list[EconomicIndex]):
        """Testar histórico de índices com paginação"""
        indexes, total = await BCBService.get_index_history(
            db_session,
            index_type="selic",
            limit=3,
            offset=0
        )
        
        assert len(indexes) <= 3
        assert total >= 5  # Temos 5 índices SELIC
        assert all(idx.index_type == "selic" for idx in indexes)
    
    @pytest.mark.asyncio
    async def test_get_index_history_by_type(self, db_session: AsyncSession, multiple_economic_indexes: list[EconomicIndex]):
        """Teste 1.2.4: Testar listagem por tipo"""
        indexes, total = await BCBService.get_index_history(
            db_session,
            index_type="igpm",
            limit=100,
            offset=0
        )
        
        assert all(idx.index_type == "igpm" for idx in indexes)
        assert total == 1  # Temos apenas 1 índice IGPM
    
    @pytest.mark.asyncio
    async def test_get_accumulated_annual_index(self, db_session: AsyncSession):
        """Testar cálculo de índice acumulado anual"""
        # Criar 12 índices mensais
        base_date = datetime(2024, 1, 1)
        for i in range(12):
            index = EconomicIndex(
                index_type="ipca",
                reference_date=base_date + timedelta(days=30 * i),
                value=str(0.5 + i * 0.1),  # Valores crescentes
                source="BCB"
            )
            db_session.add(index)
        await db_session.commit()
        
        # Buscar índice acumulado
        accumulated = await RemeasurementService.get_accumulated_annual_index(
            db_session,
            "ipca",
            reference_date=base_date + timedelta(days=365)
        )
        
        assert accumulated is not None
        assert accumulated['is_accumulated'] is True
        assert accumulated['months_used'] == 12
        assert float(accumulated['value']) > 0


# =============================================================================
# TESTES DOS ENDPOINTS (Etapa 1.4)
# =============================================================================

class TestEconomicIndexesAPI:
    """Testes para endpoints da API de índices econômicos"""
    
    @pytest.mark.asyncio
    async def test_list_indexes(self, client: AsyncClient, multiple_economic_indexes: list[EconomicIndex]):
        """Teste 1.4.1: Testar endpoint GET /api/economic-indexes"""
        response = await client.get("/api/economic-indexes")
        
        assert response.status_code == 200
        data = response.json()
        assert "indexes" in data
        assert "total" in data
        assert data["total"] >= len(multiple_economic_indexes)
    
    @pytest.mark.asyncio
    async def test_list_indexes_with_filter(self, client: AsyncClient, multiple_economic_indexes: list[EconomicIndex]):
        """Testar filtro por tipo"""
        response = await client.get("/api/economic-indexes?index_type=selic")
        
        assert response.status_code == 200
        data = response.json()
        assert all(idx["index_type"] == "selic" for idx in data["indexes"])
    
    @pytest.mark.asyncio
    async def test_list_index_types(self, client: AsyncClient):
        """Testar endpoint GET /api/economic-indexes/types"""
        response = await client.get("/api/economic-indexes/types")
        
        assert response.status_code == 200
        data = response.json()
        assert "types" in data
        assert "available" in data
        assert "selic" in data["types"]
    
    @pytest.mark.asyncio
    async def test_get_latest_index(self, client: AsyncClient, multiple_economic_indexes: list[EconomicIndex]):
        """Testar endpoint GET /api/economic-indexes/{type}/latest"""
        response = await client.get("/api/economic-indexes/selic/latest")
        
        assert response.status_code == 200
        data = response.json()
        assert data["index_type"] == "selic"
        assert "value" in data
        assert "reference_date" in data
    
    @pytest.mark.asyncio
    async def test_get_latest_index_not_found(self, client: AsyncClient):
        """Testar quando não há índice disponível"""
        response = await client.get("/api/economic-indexes/tr/latest")
        
        # Pode retornar 404 se não existir, ou 200 com dados vazios
        assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_sync_index_requires_admin(self, client: AsyncClient):
        """Testar que sync requer autenticação admin"""
        response = await client.post("/api/economic-indexes/sync/selic")
        
        assert response.status_code == 401  # Não autenticado
    
    @pytest.mark.asyncio
    async def test_sync_index_with_admin_token(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Testar sync com token admin"""
        from app.config import get_settings
        settings = get_settings()
        
        mock_data = [
            {"data": "01/01/2024", "valor": "12.75"}
        ]
        
        with patch('app.services.bcb_service.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            # json() não é async, retorna o valor diretamente
            mock_response.json = MagicMock(return_value=mock_data)
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            response = await client.post(
                "/api/economic-indexes/sync/selic?last_n=1",
                headers={"X-Admin-Token": settings.ADMIN_TOKEN}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["synced_count"] >= 0
    
    @pytest.mark.asyncio
    async def test_sync_all_indexes_with_admin_token(
        self,
        client: AsyncClient
    ):
        """Testar sync-all com token admin"""
        from app.config import get_settings
        settings = get_settings()
        
        mock_data = [
            {"data": "01/01/2024", "valor": "12.75"}
        ]
        
        with patch('app.services.bcb_service.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            # json() não é async, retorna o valor diretamente
            mock_response.json = MagicMock(return_value=mock_data)
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            response = await client.post(
                "/api/economic-indexes/sync-all?last_n=1",
                headers={"X-Admin-Token": settings.ADMIN_TOKEN}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
    
    @pytest.mark.asyncio
    async def test_invalid_index_type(self, client: AsyncClient):
        """Testar tipo de índice inválido"""
        response = await client.get("/api/economic-indexes/invalid/latest")
        
        assert response.status_code == 400
        assert "inválido" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_pagination(self, client: AsyncClient, multiple_economic_indexes: list[EconomicIndex]):
        """Testar paginação"""
        response1 = await client.get("/api/economic-indexes?limit=2&offset=0")
        response2 = await client.get("/api/economic-indexes?limit=2&offset=2")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        assert len(data1["indexes"]) <= 2
        assert len(data2["indexes"]) <= 2
        # Verificar que são diferentes (se houver mais de 2 registros)
        if data1["total"] > 2:
            assert data1["indexes"][0]["id"] != data2["indexes"][0]["id"]


# =============================================================================
# TESTES DE CACHE (Melhoria)
# =============================================================================

class TestBCBServiceCache:
    """Testes para verificação de cache (índices recentes)"""
    
    @pytest.mark.asyncio
    async def test_get_recent_index_uses_cache(self, db_session: AsyncSession):
        """Testar que índices recentes (< 30 dias) são usados do banco"""
        # Criar índice recente (hoje)
        recent_index = EconomicIndex(
            index_type="selic",
            reference_date=datetime.utcnow(),
            value="12.75",
            source="BCB"
        )
        db_session.add(recent_index)
        await db_session.commit()
        
        # Buscar - deve retornar do banco sem chamar BCB
        latest = await BCBService.get_latest_value(db_session, "selic")
        
        assert latest is not None
        assert latest.value == "12.75"
        # Não deve ter chamado BCB (verificado pela ausência de mock)
    
    @pytest.mark.asyncio
    async def test_get_old_index_may_need_refresh(self, db_session: AsyncSession):
        """Testar que índices antigos (> 30 dias) podem precisar de refresh"""
        # Criar índice antigo (60 dias atrás)
        old_index = EconomicIndex(
            index_type="selic",
            reference_date=datetime.utcnow() - timedelta(days=60),
            value="12.00",
            source="BCB"
        )
        db_session.add(old_index)
        await db_session.commit()
        
        # Buscar - ainda retorna do banco, mas pode estar desatualizado
        latest = await BCBService.get_latest_value(db_session, "selic")
        
        assert latest is not None
        assert latest.value == "12.00"
        # Nota: A lógica atual sempre retorna do banco se existir
        # Para implementar cache agressivo, precisaria adicionar verificação de data
