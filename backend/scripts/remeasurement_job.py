#!/usr/bin/env python3
"""
Script para execução do Job de Remensuração Automática
Chamado pelo Cloud Run Jobs mensalmente

Uso:
    python remeasurement_job.py

Configuração:
    - API_URL: URL da API (ex: https://ifrs16-backend-xxx.run.app)
    - INTERNAL_JOB_TOKEN: Token de autenticação para jobs internos
"""

import os
import sys
import requests
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_remeasurement():
    """Executa o job de remensuração via API"""

    api_url = os.getenv('API_URL', 'https://ifrs16-backend-1051753255664.us-central1.run.app')
    job_token = os.getenv('INTERNAL_JOB_TOKEN')

    if not job_token:
        logger.error("INTERNAL_JOB_TOKEN não configurado")
        sys.exit(1)

    endpoint = f"{api_url}/api/internal/jobs/remeasurement"

    logger.info(f"Iniciando job de remensuração")
    logger.info(f"API URL: {api_url}")

    try:
        response = requests.post(
            endpoint,
            headers={
                'X-Internal-Token': job_token,
                'Content-Type': 'application/json'
            },
            timeout=300  # 5 minutos de timeout
        )

        if response.status_code == 200:
            result = response.json()
            logger.info(f"Job executado com sucesso!")
            logger.info(f"Contratos analisados: {result.get('result', {}).get('contracts_analyzed', 0)}")
            logger.info(f"Contratos remensurados: {result.get('result', {}).get('contracts_remeasured', 0)}")
            logger.info(f"Contratos ignorados: {result.get('result', {}).get('contracts_skipped', 0)}")

            errors = result.get('result', {}).get('errors', [])
            if errors:
                logger.warning(f"Erros encontrados: {len(errors)}")
                for error in errors:
                    logger.warning(f"  - {error}")

            return 0

        else:
            logger.error(f"Erro na API: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return 1

    except requests.exceptions.Timeout:
        logger.error("Timeout ao chamar a API")
        return 1

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro de conexão: {str(e)}")
        return 1

    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        return 1


if __name__ == '__main__':
    logger.info(f"=== Job de Remensuração IFRS 16 ===")
    logger.info(f"Iniciado em: {datetime.utcnow().isoformat()}")

    exit_code = run_remeasurement()

    logger.info(f"Finalizado em: {datetime.utcnow().isoformat()}")
    sys.exit(exit_code)
