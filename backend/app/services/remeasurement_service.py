"""
Serviço de Remensuração Automática de Contratos IFRS 16
Detecta mudanças em índices econômicos e cria novas versões de contratos automaticamente
"""

import json
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Contract, User, EconomicIndex, NotificationType
from .notification_service import NotificationService

logger = logging.getLogger(__name__)


class RemeasurementService:
    """Serviço para remensuração automática de contratos"""

    # Mapeamento de tipos de reajuste para tipos de índice
    REAJUSTE_TO_INDEX = {
        'igpm': 'igpm',
        'ipca': 'ipca',
        'selic': 'selic',
        'cdi': 'cdi',
        'inpc': 'inpc',
        'tr': 'tr'
    }

    @staticmethod
    async def get_contracts_for_remeasurement(db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Busca todos os contratos que usam índices econômicos para reajuste.

        Returns:
            Lista de contratos com suas versões mais recentes
        """
        # Buscar contratos ativos que usam índices econômicos
        query = text("""
            SELECT
                c.id as contract_id,
                c.name as contract_name,
                c.user_id,
                c.categoria,
                c.numero_sequencial,
                cv.id as version_id,
                cv.version_number,
                cv.data_inicio,
                cv.prazo_meses,
                cv.carencia_meses,
                cv.parcela_inicial,
                cv.taxa_desconto_anual,
                cv.reajuste_tipo,
                cv.reajuste_periodicidade,
                cv.reajuste_valor,
                cv.mes_reajuste,
                cv.resultados_json,
                cv.total_vp,
                cv.total_nominal,
                cv.avp,
                cv.notas,
                cv.created_at as version_created_at
            FROM contracts c
            JOIN contract_versions cv ON c.id = cv.contract_id
            WHERE c.is_deleted = FALSE
            AND cv.reajuste_tipo IN ('igpm', 'ipca', 'selic', 'cdi', 'inpc', 'tr')
            AND cv.version_number = (
                SELECT MAX(cv2.version_number)
                FROM contract_versions cv2
                WHERE cv2.contract_id = c.id
            )
            ORDER BY c.user_id, c.id
        """)

        result = await db.execute(query)
        rows = result.fetchall()

        contracts = []
        for row in rows:
            contracts.append({
                'contract_id': str(row[0]),
                'contract_name': row[1],
                'user_id': str(row[2]),
                'categoria': row[3],
                'numero_sequencial': row[4],
                'version_id': str(row[5]),
                'version_number': row[6],
                'data_inicio': row[7],
                'prazo_meses': row[8],
                'carencia_meses': row[9],
                'parcela_inicial': float(row[10]) if row[10] else 0,
                'taxa_desconto_anual': float(row[11]) if row[11] else 0,
                'reajuste_tipo': row[12],
                'reajuste_periodicidade': row[13] or 'anual',
                'reajuste_valor': float(row[14]) if row[14] else None,
                'mes_reajuste': row[15],
                'resultados_json': row[16],
                'total_vp': float(row[17]) if row[17] else 0,
                'total_nominal': float(row[18]) if row[18] else 0,
                'avp': float(row[19]) if row[19] else 0,
                'notas': row[20],
                'version_created_at': row[21]
            })

        return contracts

    @staticmethod
    async def get_latest_index(
        db: AsyncSession,
        index_type: str,
        reference_date: Optional[date] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Busca o índice econômico mais recente de um tipo.

        Args:
            db: Sessão do banco
            index_type: Tipo do índice (igpm, ipca, etc.)
            reference_date: Data de referência opcional

        Returns:
            Dicionário com dados do índice ou None
        """
        query = select(EconomicIndex).where(
            EconomicIndex.index_type == index_type.lower()
        )

        if reference_date:
            query = query.where(EconomicIndex.reference_date <= reference_date)

        query = query.order_by(EconomicIndex.reference_date.desc()).limit(1)

        result = await db.execute(query)
        index = result.scalar_one_or_none()

        if index:
            return {
                'id': str(index.id),
                'index_type': index.index_type,
                'reference_date': index.reference_date,
                'value': index.value,
                'source': index.source
            }

        return None

    @staticmethod
    async def get_accumulated_annual_index(
        db: AsyncSession,
        index_type: str,
        reference_date: Optional[date] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Calcula o índice acumulado dos últimos 12 meses.

        A taxa acumulada é calculada como:
        ((1 + taxa_mes1/100) * (1 + taxa_mes2/100) * ... * (1 + taxa_mes12/100) - 1) * 100

        Args:
            db: Sessão do banco
            index_type: Tipo do índice (igpm, ipca, etc.)
            reference_date: Data de referência opcional

        Returns:
            Dicionário com taxa acumulada ou None
        """
        from datetime import timedelta
        from dateutil.relativedelta import relativedelta

        # Data de referência (usa hoje se não especificada)
        ref_date = reference_date or date.today()

        # Buscar últimos 12 meses de índices
        start_date = ref_date - relativedelta(months=12)

        query = select(EconomicIndex).where(
            EconomicIndex.index_type == index_type.lower(),
            EconomicIndex.reference_date > start_date,
            EconomicIndex.reference_date <= ref_date
        ).order_by(EconomicIndex.reference_date.asc())

        result = await db.execute(query)
        indexes = result.scalars().all()

        if not indexes:
            return None

        # Calcular taxa acumulada
        accumulated = 1.0
        for idx in indexes:
            try:
                monthly_rate = float(idx.value) / 100  # Converter de % para decimal
                accumulated *= (1 + monthly_rate)
            except (ValueError, TypeError):
                continue

        # Converter de volta para percentual
        accumulated_pct = (accumulated - 1) * 100

        # Usar a data do último índice como referência
        last_index = indexes[-1]

        return {
            'id': str(last_index.id),
            'index_type': index_type,
            'reference_date': last_index.reference_date,
            'value': str(round(accumulated_pct, 4)),
            'monthly_value': last_index.value,  # Taxa mensal para referência
            'source': last_index.source,
            'months_used': len(indexes),
            'is_accumulated': True
        }

    @staticmethod
    async def get_index_for_remeasurement(
        db: AsyncSession,
        index_type: str,
        periodicidade: str,
        reference_date: Optional[date] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtém o índice correto para remensuração baseado na periodicidade.

        - periodicidade='mensal': Retorna a taxa do último mês
        - periodicidade='anual': Retorna a taxa acumulada dos últimos 12 meses

        Args:
            db: Sessão do banco
            index_type: Tipo do índice
            periodicidade: 'mensal' ou 'anual'
            reference_date: Data de referência opcional

        Returns:
            Dicionário com dados do índice apropriado
        """
        if periodicidade == 'mensal':
            return await RemeasurementService.get_latest_index(db, index_type, reference_date)
        else:
            # Default é anual (taxa acumulada 12 meses)
            return await RemeasurementService.get_accumulated_annual_index(db, index_type, reference_date)

    @staticmethod
    async def check_if_needs_remeasurement(
        db: AsyncSession,
        contract: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Verifica se um contrato precisa de remensuração.

        Critérios:
        1. O mês atual é o mês de reajuste do contrato (para reajuste anual)
           OU qualquer mês (para reajuste mensal)
        2. Existe um índice econômico mais recente do que a última versão
        3. O índice mudou significativamente

        Returns:
            Dicionário com dados da remensuração necessária ou None
        """
        index_type = contract['reajuste_tipo']
        periodicidade = contract.get('reajuste_periodicidade', 'anual')
        mes_reajuste = contract['mes_reajuste'] or 1
        version_created_at = contract['version_created_at']

        # Para reajuste anual: verificar se é o mês de reajuste
        # Para reajuste mensal: sempre verificar
        current_month = datetime.utcnow().month
        if periodicidade == 'anual' and current_month != mes_reajuste:
            return None

        # Buscar índice correto baseado na periodicidade
        # - Mensal: taxa do último mês
        # - Anual: taxa acumulada dos últimos 12 meses
        latest_index = await RemeasurementService.get_index_for_remeasurement(
            db, index_type, periodicidade
        )

        if not latest_index:
            logger.warning(
                f"Índice {index_type} ({periodicidade}) não encontrado "
                f"para contrato {contract['contract_id']}"
            )
            return None

        # Verificar se o índice é mais recente que a última versão
        index_date = latest_index['reference_date']
        if isinstance(version_created_at, datetime):
            version_date = version_created_at
        else:
            version_date = datetime.combine(version_created_at, datetime.min.time())

        # Para reajuste mensal, verificar se já remensurou este mês
        if periodicidade == 'mensal':
            # Se a versão foi criada no mesmo mês do índice, não remensura novamente
            if (version_date.year == index_date.year and
                version_date.month == index_date.month):
                return None
        else:
            # Para anual, verificar se índice é mais recente
            if index_date <= version_date:
                return None

        # Calcular variação
        current_index_value = float(latest_index['value'])
        previous_value = contract['reajuste_valor'] or 0

        if previous_value == 0:
            variation_pct = current_index_value
        else:
            variation_pct = ((current_index_value - previous_value) / abs(previous_value)) * 100

        # Se a variação for significativa (> 0.01%), precisa remensura
        if abs(variation_pct) < 0.01:
            return None

        return {
            'contract': contract,
            'latest_index': latest_index,
            'previous_value': previous_value,
            'new_value': current_index_value,
            'variation_pct': variation_pct,
            'periodicidade': periodicidade
        }

    @staticmethod
    async def calculate_new_values(
        contract: Dict[str, Any],
        new_index_value: float
    ) -> Dict[str, Any]:
        """
        Calcula os novos valores do contrato após remensuração.

        Aplica o novo índice às parcelas e recalcula VP, AVP, etc.
        """
        # Obter dados da versão atual
        parcela_inicial = contract['parcela_inicial']
        prazo_meses = contract['prazo_meses']
        carencia_meses = contract['carencia_meses']
        taxa_anual = contract['taxa_desconto_anual']
        resultados_atuais = contract['resultados_json'] or {}

        # Taxa mensal
        taxa_mensal = (1 + taxa_anual / 100) ** (1/12) - 1

        # Calcular nova parcela com reajuste
        previous_value = contract['reajuste_valor'] or 0
        if previous_value > 0:
            fator_reajuste = new_index_value / previous_value
        else:
            fator_reajuste = 1 + (new_index_value / 100)

        nova_parcela = parcela_inicial * fator_reajuste

        # Recalcular fluxo de caixa
        parcelas = []
        for mes in range(1, prazo_meses + 1):
            if mes <= carencia_meses:
                # Durante carência: apenas juros
                parcelas.append({
                    'mes': mes,
                    'parcela': 0,
                    'tipo': 'carencia'
                })
            else:
                parcelas.append({
                    'mes': mes,
                    'parcela': nova_parcela,
                    'tipo': 'normal'
                })

        # Calcular VP
        total_vp = 0
        for i, p in enumerate(parcelas):
            if p['parcela'] > 0:
                # VP = Parcela / (1 + taxa)^n
                vp_parcela = p['parcela'] / ((1 + taxa_mensal) ** (i + 1))
                total_vp += vp_parcela

        # Calcular total nominal
        total_nominal = sum(p['parcela'] for p in parcelas)

        # AVP = Total Nominal - Total VP
        avp = total_nominal - total_vp

        return {
            'nova_parcela': nova_parcela,
            'total_vp': round(total_vp, 2),
            'total_nominal': round(total_nominal, 2),
            'avp': round(avp, 2),
            'fator_reajuste': fator_reajuste,
            'parcelas': parcelas
        }

    @staticmethod
    async def create_remeasured_version(
        db: AsyncSession,
        contract: Dict[str, Any],
        new_values: Dict[str, Any],
        new_index_value: float,
        index_type: str,
        periodicidade: str = 'anual'
    ) -> Dict[str, Any]:
        """
        Cria uma nova versão do contrato com os valores remensurados.

        Args:
            db: Sessão do banco
            contract: Dados do contrato
            new_values: Novos valores calculados
            new_index_value: Valor do índice utilizado
            index_type: Tipo do índice
            periodicidade: 'mensal' ou 'anual'

        Returns:
            Dados da nova versão criada
        """
        # Próximo número de versão
        new_version_number = contract['version_number'] + 1

        # Gerar version_id
        categoria = contract['categoria'] or 'OT'
        numero_seq = contract['numero_sequencial'] or 1
        version_id = f"ID{categoria}{new_version_number}-{numero_seq:04d}"

        # Nota explicando a remensuração
        periodicidade_label = "mensal" if periodicidade == "mensal" else "anual (acumulado 12m)"
        nota = (
            f"Remensuração automática - Índice {index_type.upper()} ({periodicidade_label}) "
            f"atualizado para {new_index_value:.4f}%"
        )
        if contract['notas']:
            nota = f"{contract['notas']}\n\n{nota}"

        # Resultados JSON com informações da remensuração
        resultados_json = {
            'parcelas': new_values['parcelas'],
            'remeasurement_info': {
                'type': 'automatic',
                'index_type': index_type,
                'periodicidade': periodicidade,
                'previous_value': contract['reajuste_valor'],
                'new_value': new_index_value,
                'adjustment_factor': new_values['fator_reajuste'],
                'date': datetime.utcnow().isoformat()
            }
        }

        # Inserir nova versão
        insert_query = text("""
            INSERT INTO contract_versions (
                contract_id, version_number, version_id, data_inicio, prazo_meses, carencia_meses,
                parcela_inicial, taxa_desconto_anual, reajuste_tipo, reajuste_periodicidade,
                reajuste_valor, mes_reajuste, resultados_json, total_vp, total_nominal, avp, notas
            )
            VALUES (
                :contract_id, :version_number, :version_id, :data_inicio, :prazo_meses, :carencia_meses,
                :parcela_inicial, :taxa_desconto_anual, :reajuste_tipo, :reajuste_periodicidade,
                :reajuste_valor, :mes_reajuste, :resultados_json, :total_vp, :total_nominal, :avp, :notas
            )
            RETURNING id, version_number, version_id, created_at
        """)

        result = await db.execute(
            insert_query,
            {
                'contract_id': contract['contract_id'],
                'version_number': new_version_number,
                'version_id': version_id,
                'data_inicio': contract['data_inicio'],
                'prazo_meses': contract['prazo_meses'],
                'carencia_meses': contract['carencia_meses'],
                'parcela_inicial': new_values['nova_parcela'],
                'taxa_desconto_anual': contract['taxa_desconto_anual'],
                'reajuste_tipo': index_type,
                'reajuste_periodicidade': periodicidade,
                'reajuste_valor': new_index_value,
                'mes_reajuste': contract['mes_reajuste'],
                'resultados_json': json.dumps(resultados_json),
                'total_vp': new_values['total_vp'],
                'total_nominal': new_values['total_nominal'],
                'avp': new_values['avp'],
                'notas': nota
            }
        )

        row = result.fetchone()
        await db.commit()

        return {
            'id': str(row[0]),
            'version_number': row[1],
            'version_id': row[2],
            'created_at': row[3]
        }

    @staticmethod
    async def run_remeasurement_job(db: AsyncSession) -> Dict[str, Any]:
        """
        Executa o job de remensuração automática para todos os contratos elegíveis.

        Este método é chamado pelo Cloud Run Job agendado mensalmente.

        Returns:
            Relatório com resultados da remensuração
        """
        logger.info("Iniciando job de remensuração automática")

        results = {
            'started_at': datetime.utcnow().isoformat(),
            'contracts_analyzed': 0,
            'contracts_remeasured': 0,
            'contracts_skipped': 0,
            'errors': [],
            'remeasurements': []
        }

        try:
            # Buscar contratos elegíveis
            contracts = await RemeasurementService.get_contracts_for_remeasurement(db)
            results['contracts_analyzed'] = len(contracts)

            logger.info(f"Encontrados {len(contracts)} contratos para análise")

            for contract in contracts:
                try:
                    # Verificar se precisa remensurar
                    remeasurement_data = await RemeasurementService.check_if_needs_remeasurement(
                        db, contract
                    )

                    if not remeasurement_data:
                        results['contracts_skipped'] += 1
                        continue

                    # Calcular novos valores
                    new_values = await RemeasurementService.calculate_new_values(
                        contract,
                        remeasurement_data['new_value']
                    )

                    # Obter periodicidade do contrato
                    periodicidade = remeasurement_data.get('periodicidade', 'anual')

                    # Criar nova versão
                    new_version = await RemeasurementService.create_remeasured_version(
                        db,
                        contract,
                        new_values,
                        remeasurement_data['new_value'],
                        contract['reajuste_tipo'],
                        periodicidade
                    )

                    # Criar notificação para o usuário
                    await NotificationService.notify_remeasurement_done(
                        db=db,
                        user_id=UUID(contract['user_id']),
                        contract_id=UUID(contract['contract_id']),
                        contract_name=contract['contract_name'],
                        version_number=new_version['version_number'],
                        index_type=contract['reajuste_tipo'],
                        old_value=remeasurement_data['previous_value'],
                        new_value=remeasurement_data['new_value']
                    )

                    results['contracts_remeasured'] += 1
                    results['remeasurements'].append({
                        'contract_id': contract['contract_id'],
                        'contract_name': contract['contract_name'],
                        'user_id': contract['user_id'],
                        'new_version_number': new_version['version_number'],
                        'index_type': contract['reajuste_tipo'],
                        'periodicidade': periodicidade,
                        'old_value': remeasurement_data['previous_value'],
                        'new_value': remeasurement_data['new_value'],
                        'variation_pct': remeasurement_data['variation_pct']
                    })

                    logger.info(
                        f"Contrato {contract['contract_id']} remensurado: "
                        f"versão {new_version['version_number']} criada"
                    )

                except Exception as e:
                    error_msg = f"Erro ao processar contrato {contract['contract_id']}: {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)

        except Exception as e:
            error_msg = f"Erro geral no job de remensuração: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)

        results['finished_at'] = datetime.utcnow().isoformat()

        logger.info(
            f"Job finalizado: {results['contracts_remeasured']} remensurados, "
            f"{results['contracts_skipped']} ignorados, "
            f"{len(results['errors'])} erros"
        )

        return results
