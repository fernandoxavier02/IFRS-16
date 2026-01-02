#!/bin/bash
# Script para configurar Cloud Schedulers no GCP
# Execute este script no Cloud Shell ou em ambiente com gcloud CLI

set -e

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configurações
PROJECT_ID="${GCP_PROJECT_ID:-ifrs16-app}"
REGION="${GCP_REGION:-us-central1}"
API_URL="${API_URL:-https://ifrs16-backend-1051753255664.us-central1.run.app}"
INTERNAL_TOKEN="${INTERNAL_JOB_TOKEN:-${ADMIN_TOKEN}}"

if [ -z "$INTERNAL_TOKEN" ]; then
    echo -e "${RED}❌ Erro: INTERNAL_JOB_TOKEN ou ADMIN_TOKEN não configurado${NC}"
    echo "Configure uma das variáveis:"
    echo "  export INTERNAL_JOB_TOKEN=seu-token-aqui"
    echo "  ou"
    echo "  export ADMIN_TOKEN=seu-token-aqui"
    exit 1
fi

echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  📅 CONFIGURAÇÃO DE CLOUD SCHEDULERS - IFRS 16${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "📌 Configurações:"
echo "   Project ID: $PROJECT_ID"
echo "   Region: $REGION"
echo "   API URL: $API_URL"
echo "   Token: ${INTERNAL_TOKEN:0:10}... (oculto)"
echo ""

# Função para criar scheduler
create_scheduler() {
    local name=$1
    local description=$2
    local schedule=$3
    local endpoint=$4
    
    echo -e "${YELLOW}🔧 Criando scheduler: $name${NC}"
    
    gcloud scheduler jobs create http "$name" \
        --project="$PROJECT_ID" \
        --location="$REGION" \
        --schedule="$schedule" \
        --time-zone="America/Sao_Paulo" \
        --uri="${API_URL}${endpoint}" \
        --http-method=POST \
        --headers="X-Internal-Token=${INTERNAL_TOKEN},Content-Type=application/json" \
        --description="$description" \
        --attempt-deadline=600s \
        --max-retry-attempts=3 \
        --min-backoff-duration=10s \
        --max-backoff-duration=300s || {
            echo -e "${RED}❌ Erro ao criar $name${NC}"
            echo "   Verifique se já existe: gcloud scheduler jobs describe $name --location=$REGION"
            return 1
        }
    
    echo -e "${GREEN}✅ Scheduler '$name' criado com sucesso!${NC}"
    echo ""
}

# 1. Remensuração Automática
create_scheduler \
    "remeasurement-scheduler" \
    "Remensuração Automática Mensal - Executa no dia 5 de cada mês às 08:00" \
    "0 8 5 * *" \
    "/api/internal/jobs/remeasurement"

# 2. Contratos Vencendo
create_scheduler \
    "check-expiring-contracts-scheduler" \
    "Verificação Diária de Contratos Vencendo - Executa diariamente às 09:00" \
    "0 9 * * *" \
    "/api/internal/jobs/check-expiring-contracts"

# 3. Limpeza de Notificações
create_scheduler \
    "cleanup-notifications-scheduler" \
    "Limpeza Semanal de Notificações Antigas - Executa domingo às 03:00" \
    "0 3 * * 0" \
    "/api/internal/jobs/cleanup-notifications"

echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ CONFIGURAÇÃO CONCLUÍDA!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "📋 Verificar schedulers criados:"
echo "   gcloud scheduler jobs list --location=$REGION"
echo ""
echo "🧪 Testar manualmente:"
echo "   gcloud scheduler jobs run remeasurement-scheduler --location=$REGION"
echo ""
echo "📊 Ver logs:"
echo "   gcloud logging read \"resource.type=cloud_scheduler_job\" --limit=10"
echo ""
