# Configuração dos Cloud Run Jobs

Este documento descreve como configurar os jobs agendados para o sistema IFRS 16.

## Jobs Disponíveis

### 1. Job de Remensuração Automática

Executa mensalmente no dia 5 às 08:00 para:
- Verificar contratos que usam índices econômicos (IGPM, IPCA, SELIC, etc.)
- Detectar variações nos índices
- Criar novas versões automaticamente quando necessário
- Notificar usuários sobre remensurações realizadas

### 2. Job de Sincronização de Índices Econômicos

Já configurado (ver `PLANO_IMPLEMENTACAO_MELHORIAS.md`):
- Executa no dia 5 de cada mês às 08:00
- Sincroniza índices do BCB

### 3. Job de Limpeza de Notificações

Remove notificações lidas antigas (>90 dias) para manter o banco limpo.

## Comandos de Configuração

### Pré-requisitos

```bash
# Definir variáveis
export PROJECT_ID=ifrs16-app
export REGION=us-central1
export API_URL=https://ifrs16-backend-1051753255664.us-central1.run.app
export INTERNAL_JOB_TOKEN=<seu-token-aqui>  # Use o ADMIN_TOKEN
```

### Criar Job de Remensuração

```bash
# Criar o Cloud Run Job
gcloud run jobs create remeasurement-job \
  --project=$PROJECT_ID \
  --region=$REGION \
  --image=gcr.io/$PROJECT_ID/ifrs16-backend:latest \
  --command=python \
  --args="scripts/remeasurement_job.py" \
  --set-env-vars="API_URL=$API_URL,INTERNAL_JOB_TOKEN=$INTERNAL_JOB_TOKEN" \
  --max-retries=3 \
  --task-timeout=10m \
  --service-account=ifrs16-backend@$PROJECT_ID.iam.gserviceaccount.com
```

### Agendar Execução Mensal

```bash
# Criar scheduler para dia 5 de cada mês às 08:00 (horário de Brasília)
gcloud scheduler jobs create http remeasurement-scheduler \
  --project=$PROJECT_ID \
  --location=$REGION \
  --schedule="0 8 5 * *" \
  --time-zone="America/Sao_Paulo" \
  --uri="https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/remeasurement-job:run" \
  --http-method=POST \
  --oauth-service-account-email=ifrs16-backend@$PROJECT_ID.iam.gserviceaccount.com
```

### Alternativa: Usar HTTP Trigger Direto

Se preferir usar o endpoint HTTP diretamente:

```bash
# Criar scheduler chamando endpoint da API
gcloud scheduler jobs create http remeasurement-http-trigger \
  --project=$PROJECT_ID \
  --location=$REGION \
  --schedule="0 8 5 * *" \
  --time-zone="America/Sao_Paulo" \
  --uri="$API_URL/api/internal/jobs/remeasurement" \
  --http-method=POST \
  --headers="X-Internal-Token=$INTERNAL_JOB_TOKEN,Content-Type=application/json"
```

### Criar Job de Limpeza de Notificações

```bash
# Scheduler para limpeza semanal (domingo às 03:00)
gcloud scheduler jobs create http cleanup-notifications-scheduler \
  --project=$PROJECT_ID \
  --location=$REGION \
  --schedule="0 3 * * 0" \
  --time-zone="America/Sao_Paulo" \
  --uri="$API_URL/api/internal/jobs/cleanup-notifications" \
  --http-method=POST \
  --headers="X-Internal-Token=$INTERNAL_JOB_TOKEN,Content-Type=application/json"
```

## Testes

### Testar Endpoint Manualmente

```bash
# Testar remensuração
curl -X POST "$API_URL/api/internal/jobs/remeasurement" \
  -H "X-Internal-Token: $INTERNAL_JOB_TOKEN" \
  -H "Content-Type: application/json"

# Testar limpeza
curl -X POST "$API_URL/api/internal/jobs/cleanup-notifications?days=90" \
  -H "X-Internal-Token: $INTERNAL_JOB_TOKEN" \
  -H "Content-Type: application/json"
```

### Executar Job Manualmente

```bash
# Executar job de remensuração
gcloud run jobs execute remeasurement-job \
  --project=$PROJECT_ID \
  --region=$REGION

# Ver logs
gcloud run jobs executions list --job=remeasurement-job \
  --project=$PROJECT_ID \
  --region=$REGION
```

## Monitoramento

### Ver Logs

```bash
# Logs do job
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=remeasurement-job" \
  --project=$PROJECT_ID \
  --limit=50

# Logs da API (endpoint de jobs)
gcloud logging read "resource.type=cloud_run_revision AND textPayload:remeasurement" \
  --project=$PROJECT_ID \
  --limit=50
```

### Alertas

Configurar alertas no Cloud Monitoring para:
- Falhas no job (error rate > 0)
- Timeout no job
- Erros no endpoint de remensuração

## Segurança

1. **Token Interno**: O `INTERNAL_JOB_TOKEN` deve ser uma string aleatória segura
2. **Service Account**: Jobs devem usar service account com permissões mínimas
3. **Não expor endpoint**: O endpoint `/api/internal/jobs/*` não deve ser acessível publicamente sem token

## Fluxo de Remensuração

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUXO MENSAL                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Dia 5 - 08:00                                             │
│        │                                                    │
│        ▼                                                    │
│   Cloud Scheduler                                           │
│        │                                                    │
│        ▼                                                    │
│   POST /api/internal/jobs/remeasurement                     │
│        │                                                    │
│        ▼                                                    │
│   RemeasurementService.run_remeasurement_job()              │
│        │                                                    │
│        ├─► Buscar contratos com reajuste por índice         │
│        │                                                    │
│        ├─► Para cada contrato:                              │
│        │   ├─► Verificar se é mês de reajuste               │
│        │   ├─► Buscar índice mais recente                   │
│        │   ├─► Calcular variação                            │
│        │   ├─► Se variou > 0.01%:                           │
│        │   │   ├─► Recalcular valores                       │
│        │   │   ├─► Criar nova versão                        │
│        │   │   └─► Notificar usuário                        │
│        │   └─► Se não variou: ignorar                       │
│        │                                                    │
│        └─► Retornar relatório                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Troubleshooting

### Job não executa
1. Verificar se o scheduler está ativo
2. Verificar permissões da service account
3. Ver logs do scheduler

### Remensuração não detecta contratos
1. Verificar se existem contratos com `reajuste_tipo` em (igpm, ipca, selic, etc.)
2. Verificar se é o mês de reajuste configurado no contrato
3. Verificar se existem índices econômicos na tabela `economic_indexes`

### Notificações não aparecem
1. Verificar se a tabela `notifications` existe
2. Ver logs de erro no job
3. Testar endpoint de notificações manualmente
