"""
Cloud Run Job: Sincronização de Índices Econômicos do BCB

Este script é executado mensalmente via Cloud Scheduler para
atualizar os índices econômicos (SELIC, IGPM, IPCA, CDI, INPC, TR).

Configuração:
- Cloud Scheduler: dia 5 de cada mês às 08:00 (horário de Brasília)
- Isso garante que os índices do mês anterior já foram publicados pelo BCB
"""

import os
import sys
import httpx
from datetime import datetime

# Configurações
API_URL = os.getenv("API_URL", "https://ifrs16-backend-1051753255664.us-central1.run.app")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

# Quantos meses buscar (últimos 3 para garantir atualizações retroativas)
LAST_N_MONTHS = 3


def sync_indexes():
    """Sincroniza todos os índices econômicos do BCB."""
    print(f"[{datetime.now().isoformat()}] Iniciando sincronização de índices econômicos...")
    print(f"[INFO] API URL: {API_URL}")

    if not ADMIN_TOKEN:
        print("[ERROR] ADMIN_TOKEN não configurado!")
        sys.exit(1)

    url = f"{API_URL}/api/economic-indexes/sync-all?last_n={LAST_N_MONTHS}"
    headers = {
        "X-Admin-Token": ADMIN_TOKEN,
        "Content-Type": "application/json",
        "Content-Length": "0"
    }

    try:
        print(f"[INFO] Chamando {url}...")

        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, headers=headers)

        print(f"[INFO] Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] {data.get('message', 'OK')}")
            print(f"[RESULTS] {data.get('results', {})}")

            if data.get("errors"):
                print(f"[WARN] Erros em alguns índices: {data['errors']}")
                # Não falha o job por erros parciais

            return True
        else:
            print(f"[ERROR] Falha na sincronização: {response.text}")
            sys.exit(1)

    except httpx.TimeoutException:
        print("[ERROR] Timeout ao chamar API")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Erro inesperado: {e}")
        sys.exit(1)


def main():
    """Ponto de entrada do job."""
    print("=" * 60)
    print("IFRS 16 - Sincronização de Índices Econômicos BCB")
    print("=" * 60)

    sync_indexes()

    print("=" * 60)
    print(f"[{datetime.now().isoformat()}] Job concluído com sucesso!")
    print("=" * 60)


if __name__ == "__main__":
    main()
