"""
Cloud Run Job: Verificação de Contratos Vencendo

Este script é executado diariamente via Cloud Scheduler para
verificar contratos próximos do vencimento e criar notificações.

Configuração:
- Cloud Scheduler: diariamente às 08:00 (horário de Brasília)
- Verifica contratos que vencem nos próximos 30 dias
"""

import os
import sys
import httpx
from datetime import datetime

# Configurações
API_URL = os.getenv("API_URL", "https://ifrs16-backend-1051753255664.us-central1.run.app")
INTERNAL_TOKEN = os.getenv("INTERNAL_JOB_TOKEN") or os.getenv("ADMIN_TOKEN")
DAYS_AHEAD = int(os.getenv("DAYS_AHEAD", "30"))


def check_expiring_contracts():
    """Verifica contratos vencendo e cria notificações."""
    print(f"[{datetime.now().isoformat()}] Iniciando verificação de contratos vencendo...")
    print(f"[INFO] API URL: {API_URL}")
    print(f"[INFO] Verificando próximos {DAYS_AHEAD} dias")

    if not INTERNAL_TOKEN:
        print("[ERROR] INTERNAL_JOB_TOKEN ou ADMIN_TOKEN não configurado!")
        sys.exit(1)

    url = f"{API_URL}/api/internal/jobs/check-expiring-contracts?days_ahead={DAYS_AHEAD}"
    headers = {
        "X-Internal-Token": INTERNAL_TOKEN,
        "Content-Type": "application/json"
    }

    try:
        print(f"[INFO] Chamando {url}...")

        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, headers=headers)

        print(f"[INFO] Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] {data.get('message', 'OK')}")
            
            result = data.get('result', {})
            print(f"[RESULTS] Contratos verificados: {result.get('contracts_checked', 0)}")
            print(f"[RESULTS] Notificações criadas: {result.get('notifications_created', 0)}")
            
            if result.get("errors"):
                print(f"[WARN] Erros: {result['errors']}")
                # Não falha o job por erros parciais

            return True
        else:
            print(f"[ERROR] Falha na verificação: {response.text}")
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
    print("IFRS 16 - Verificação de Contratos Vencendo")
    print("=" * 60)

    check_expiring_contracts()

    print("=" * 60)
    print(f"[{datetime.now().isoformat()}] Job concluído com sucesso!")
    print("=" * 60)


if __name__ == "__main__":
    main()
