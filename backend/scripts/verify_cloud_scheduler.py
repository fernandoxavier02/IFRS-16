#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar e configurar Cloud Scheduler para jobs do IFRS 16

Uso:
    python scripts/verify_cloud_scheduler.py [--configure]
"""

import os
import sys
import subprocess
import json
from typing import Dict, List, Optional

# Configurar encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configurações
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "ifrs16-app")
REGION = os.getenv("GCP_REGION", "us-central1")
API_URL = os.getenv("API_URL", "https://ifrs16-backend-1051753255664.us-central1.run.app")
INTERNAL_TOKEN = os.getenv("INTERNAL_JOB_TOKEN", os.getenv("ADMIN_TOKEN", ""))


def run_command(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Executa comando shell e retorna resultado"""
    print(f"🔧 Executando: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao executar comando: {e}")
        if e.stdout:
            print(f"   stdout: {e.stdout}")
        if e.stderr:
            print(f"   stderr: {e.stderr}")
        raise


def list_schedulers() -> List[Dict]:
    """Lista todos os schedulers configurados"""
    print("\n📋 Listando Cloud Schedulers...")
    
    cmd = [
        "gcloud", "scheduler", "jobs", "list",
        "--project", PROJECT_ID,
        "--location", REGION,
        "--format", "json"
    ]
    
    try:
        result = run_command(cmd, check=False)
        if result.returncode == 0 and result.stdout.strip():
            schedulers = json.loads(result.stdout)
            return schedulers
        else:
            print("   ⚠️  Nenhum scheduler encontrado ou erro ao listar")
            return []
    except Exception as e:
        print(f"   ❌ Erro ao listar schedulers: {e}")
        return []


def check_scheduler(name: str) -> Optional[Dict]:
    """Verifica se um scheduler específico existe"""
    schedulers = list_schedulers()
    for scheduler in schedulers:
        if scheduler.get("name", "").endswith(f"/{name}"):
            return scheduler
    return None


def describe_scheduler(name: str) -> Optional[Dict]:
    """Obtém detalhes de um scheduler"""
    print(f"\n🔍 Descrevendo scheduler: {name}")
    
    cmd = [
        "gcloud", "scheduler", "jobs", "describe", name,
        "--project", PROJECT_ID,
        "--location", REGION,
        "--format", "json"
    ]
    
    try:
        result = run_command(cmd, check=False)
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        else:
            print(f"   ⚠️  Scheduler '{name}' não encontrado")
            return None
    except Exception as e:
        print(f"   ❌ Erro ao descrever scheduler: {e}")
        return None


def create_remeasurement_scheduler() -> bool:
    """Cria scheduler para remensuração"""
    print("\n🔧 Criando scheduler de remensuração...")
    
    if not INTERNAL_TOKEN:
        print("   ❌ INTERNAL_JOB_TOKEN ou ADMIN_TOKEN não configurado")
        return False
    
    scheduler_name = "remeasurement-scheduler"
    
    # Verificar se já existe
    existing = check_scheduler(scheduler_name)
    if existing:
        print(f"   ⚠️  Scheduler '{scheduler_name}' já existe")
        return True
    
    cmd = [
        "gcloud", "scheduler", "jobs", "create", "http", scheduler_name,
        "--project", PROJECT_ID,
        "--location", REGION,
        "--schedule", "0 8 5 * *",  # Dia 5 de cada mês às 08:00
        "--time-zone", "America/Sao_Paulo",
        "--uri", f"{API_URL}/api/internal/jobs/remeasurement",
        "--http-method", "POST",
        "--headers", f"X-Internal-Token={INTERNAL_TOKEN},Content-Type=application/json"
    ]
    
    try:
        run_command(cmd)
        print(f"   ✅ Scheduler '{scheduler_name}' criado com sucesso")
        return True
    except Exception as e:
        print(f"   ❌ Erro ao criar scheduler: {e}")
        return False


def create_expiring_contracts_scheduler() -> bool:
    """Cria scheduler para verificar contratos vencendo"""
    print("\n🔧 Criando scheduler de contratos vencendo...")
    
    if not INTERNAL_TOKEN:
        print("   ❌ INTERNAL_JOB_TOKEN ou ADMIN_TOKEN não configurado")
        return False
    
    scheduler_name = "check-expiring-contracts-scheduler"
    
    # Verificar se já existe
    existing = check_scheduler(scheduler_name)
    if existing:
        print(f"   ⚠️  Scheduler '{scheduler_name}' já existe")
        return True
    
    cmd = [
        "gcloud", "scheduler", "jobs", "create", "http", scheduler_name,
        "--project", PROJECT_ID,
        "--location", REGION,
        "--schedule", "0 9 * * *",  # Diariamente às 09:00
        "--time-zone", "America/Sao_Paulo",
        "--uri", f"{API_URL}/api/internal/jobs/check-expiring-contracts",
        "--http-method", "POST",
        "--headers", f"X-Internal-Token={INTERNAL_TOKEN},Content-Type=application/json"
    ]
    
    try:
        run_command(cmd)
        print(f"   ✅ Scheduler '{scheduler_name}' criado com sucesso")
        return True
    except Exception as e:
        print(f"   ❌ Erro ao criar scheduler: {e}")
        return False


def create_cleanup_notifications_scheduler() -> bool:
    """Cria scheduler para limpeza de notificações"""
    print("\n🔧 Criando scheduler de limpeza de notificações...")
    
    if not INTERNAL_TOKEN:
        print("   ❌ INTERNAL_JOB_TOKEN ou ADMIN_TOKEN não configurado")
        return False
    
    scheduler_name = "cleanup-notifications-scheduler"
    
    # Verificar se já existe
    existing = check_scheduler(scheduler_name)
    if existing:
        print(f"   ⚠️  Scheduler '{scheduler_name}' já existe")
        return True
    
    cmd = [
        "gcloud", "scheduler", "jobs", "create", "http", scheduler_name,
        "--project", PROJECT_ID,
        "--location", REGION,
        "--schedule", "0 3 * * 0",  # Domingo às 03:00
        "--time-zone", "America/Sao_Paulo",
        "--uri", f"{API_URL}/api/internal/jobs/cleanup-notifications?days=90",
        "--http-method", "POST",
        "--headers", f"X-Internal-Token={INTERNAL_TOKEN},Content-Type=application/json"
    ]
    
    try:
        run_command(cmd)
        print(f"   ✅ Scheduler '{scheduler_name}' criado com sucesso")
        return True
    except Exception as e:
        print(f"   ❌ Erro ao criar scheduler: {e}")
        return False


def main():
    """Função principal"""
    import argparse
    
    global PROJECT_ID, REGION
    
    parser = argparse.ArgumentParser(description="Verificar e configurar Cloud Scheduler")
    parser.add_argument(
        "--configure",
        action="store_true",
        help="Criar schedulers se não existirem"
    )
    parser.add_argument(
        "--project",
        default=PROJECT_ID,
        help=f"GCP Project ID (default: {PROJECT_ID})"
    )
    parser.add_argument(
        "--region",
        default=REGION,
        help=f"GCP Region (default: {REGION})"
    )
    
    args = parser.parse_args()
    
    PROJECT_ID = args.project
    REGION = args.region
    
    print("=" * 70)
    print("🔍 VERIFICAÇÃO DE CLOUD SCHEDULER - IFRS 16")
    print("=" * 70)
    print(f"\n📌 Configurações:")
    print(f"   Project ID: {PROJECT_ID}")
    print(f"   Region: {REGION}")
    print(f"   API URL: {API_URL}")
    print(f"   Token configurado: {'✅' if INTERNAL_TOKEN else '❌'}")
    
    # Listar schedulers existentes
    schedulers = list_schedulers()
    
    # Verificar schedulers esperados
    expected_schedulers = {
        "remeasurement-scheduler": {
            "name": "Remensuração Automática",
            "schedule": "Dia 5 de cada mês às 08:00",
            "endpoint": "/api/internal/jobs/remeasurement"
        },
        "check-expiring-contracts-scheduler": {
            "name": "Contratos Vencendo",
            "schedule": "Diariamente às 09:00",
            "endpoint": "/api/internal/jobs/check-expiring-contracts"
        },
        "cleanup-notifications-scheduler": {
            "name": "Limpeza de Notificações",
            "schedule": "Domingo às 03:00",
            "endpoint": "/api/internal/jobs/cleanup-notifications"
        }
    }
    
    print("\n" + "=" * 70)
    print("📊 STATUS DOS SCHEDULERS")
    print("=" * 70)
    
    all_ok = True
    for scheduler_name, info in expected_schedulers.items():
        scheduler = check_scheduler(scheduler_name)
        if scheduler:
            print(f"\n✅ {info['name']} ({scheduler_name})")
            print(f"   Status: {scheduler.get('state', 'UNKNOWN')}")
            print(f"   Schedule: {info['schedule']}")
            print(f"   Endpoint: {info['endpoint']}")
        else:
            print(f"\n❌ {info['name']} ({scheduler_name}) - NÃO CONFIGURADO")
            print(f"   Schedule esperado: {info['schedule']}")
            print(f"   Endpoint: {info['endpoint']}")
            all_ok = False
    
    if not all_ok and args.configure:
        print("\n" + "=" * 70)
        print("🔧 CONFIGURANDO SCHEDULERS FALTANTES")
        print("=" * 70)
        
        if not check_scheduler("remeasurement-scheduler"):
            create_remeasurement_scheduler()
        
        if not check_scheduler("check-expiring-contracts-scheduler"):
            create_expiring_contracts_scheduler()
        
        if not check_scheduler("cleanup-notifications-scheduler"):
            create_cleanup_notifications_scheduler()
        
        print("\n✅ Configuração concluída!")
    elif not all_ok:
        print("\n💡 Dica: Execute com --configure para criar os schedulers faltantes")
    
    print("\n" + "=" * 70)
    print("✅ Verificação concluída!")
    print("=" * 70)


if __name__ == "__main__":
    main()
