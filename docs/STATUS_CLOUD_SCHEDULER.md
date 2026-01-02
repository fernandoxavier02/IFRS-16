# ✅ Status dos Cloud Schedulers

**Data de Configuração:** 2026-01-02  
**Status:** ✅ **TODOS CONFIGURADOS E ATIVOS**

---

## 📅 Schedulers Configurados

### 1. ✅ Remensuração Automática
- **Nome:** `remeasurement-scheduler`
- **Schedule:** Dia 5 de cada mês às 08:00 (horário de Brasília)
- **Cron:** `0 8 5 * *`
- **Endpoint:** `/api/internal/jobs/remeasurement`
- **Estado:** `ENABLED`
- **Descrição:** Remensuração Automática Mensal - Executa no dia 5 de cada mês às 08:00

### 2. ✅ Verificação de Contratos Vencendo
- **Nome:** `check-expiring-contracts-scheduler`
- **Schedule:** Diariamente às 09:00 (horário de Brasília)
- **Cron:** `0 9 * * *`
- **Endpoint:** `/api/internal/jobs/check-expiring-contracts`
- **Estado:** `ENABLED`
- **Descrição:** Verificação Diária de Contratos Vencendo - Executa diariamente às 09:00

### 3. ✅ Limpeza de Notificações
- **Nome:** `cleanup-notifications-scheduler`
- **Schedule:** Domingo às 03:00 (horário de Brasília)
- **Cron:** `0 3 * * 0`
- **Endpoint:** `/api/internal/jobs/cleanup-notifications`
- **Estado:** `ENABLED`
- **Descrição:** Limpeza Semanal de Notificações Antigas - Executa domingo às 03:00

### 4. ✅ Sincronização de Índices Econômicos (já existia)
- **Nome:** `sync-economic-indexes-monthly`
- **Schedule:** Dia 5 de cada mês às 08:00 (horário de Brasília)
- **Cron:** `0 8 5 * *`
- **Estado:** `ENABLED`
- **Descrição:** Sincroniza índices econômicos BCB no dia 5 de cada mês às 08:00

---

## ⚙️ Configurações

- **Projeto GCP:** `ifrs16-app`
- **Região:** `us-central1`
- **API URL:** `https://ifrs16-backend-1051753255664.us-central1.run.app`
- **Token:** Configurado via `X-Internal-Token` header
- **Timeout:** 600 segundos (10 minutos)
- **Retry:** Configurado automaticamente pelo GCP

---

## ✅ Token Configurado

Os schedulers foram atualizados com o token de produção:
- **Token:** `bzFh8l2ZpOeKakS9JBUGQrQiTyKcCAbVvn0x0vH9mxqcvie19fygJR4ISrQBtH7M`
- **Data de atualização:** 2026-01-02
- **Status:** ✅ Todos os 3 schedulers atualizados

**Se precisar atualizar novamente:**

```bash
# Atualizar token do scheduler de remensuração
gcloud scheduler jobs update http remeasurement-scheduler \
  --location=us-central1 \
  --update-headers="X-Internal-Token=SEU_TOKEN_REAL_AQUI"

# Atualizar token do scheduler de contratos vencendo
gcloud scheduler jobs update http check-expiring-contracts-scheduler \
  --location=us-central1 \
  --update-headers="X-Internal-Token=SEU_TOKEN_REAL_AQUI"

# Atualizar token do scheduler de limpeza
gcloud scheduler jobs update http cleanup-notifications-scheduler \
  --location=us-central1 \
  --update-headers="X-Internal-Token=SEU_TOKEN_REAL_AQUI"
```

---

## 🧪 Testar Schedulers Manualmente

### Executar Remensuração
```bash
gcloud scheduler jobs run remeasurement-scheduler \
  --project=ifrs16-app \
  --location=us-central1
```

### Executar Verificação de Contratos
```bash
gcloud scheduler jobs run check-expiring-contracts-scheduler \
  --project=ifrs16-app \
  --location=us-central1
```

### Executar Limpeza
```bash
gcloud scheduler jobs run cleanup-notifications-scheduler \
  --project=ifrs16-app \
  --location=us-central1
```

---

## 📊 Verificar Status

### Listar todos os schedulers
```bash
gcloud scheduler jobs list \
  --project=ifrs16-app \
  --location=us-central1
```

### Ver detalhes de um scheduler
```bash
gcloud scheduler jobs describe remeasurement-scheduler \
  --project=ifrs16-app \
  --location=us-central1
```

### Ver histórico de execuções
```bash
gcloud scheduler jobs list-executions remeasurement-scheduler \
  --project=ifrs16-app \
  --location=us-central1
```

### Ver logs
```bash
gcloud logging read "resource.type=cloud_scheduler_job AND resource.labels.job_id=remeasurement-scheduler" \
  --project=ifrs16-app \
  --limit=10 \
  --format=json
```

---

## ✅ Checklist de Validação

- [x] Scheduler de remensuração criado
- [x] Scheduler de contratos vencendo criado
- [x] Scheduler de limpeza criado
- [x] Todos os schedulers estão ENABLED
- [x] Token atualizado com valor real de produção ✅
- [ ] Teste manual executado com sucesso
- [ ] Logs verificados após primeira execução automática

---

## 📝 Próximas Execuções Agendadas

- **Remensuração:** 2026-01-05 às 08:00 (Brasília)
- **Contratos Vencendo:** 2026-01-02 às 09:00 (Brasília) - Próxima execução diária
- **Limpeza:** 2026-01-04 às 03:00 (Brasília) - Próximo domingo
- **Sincronização de Índices:** 2026-01-05 às 08:00 (Brasília)

---

**Última Atualização:** 2026-01-02
