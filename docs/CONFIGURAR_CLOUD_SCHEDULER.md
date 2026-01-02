# 📅 Configuração do Cloud Scheduler

Este documento explica como configurar os Cloud Schedulers para executar tarefas automáticas do sistema IFRS 16.

---

## 🎯 O que são os Cloud Schedulers?

Os Cloud Schedulers são tarefas agendadas que executam automaticamente endpoints da API em horários específicos:

1. **Remensuração Automática** - Dia 5 de cada mês às 08:00
2. **Contratos Vencendo** - Diariamente às 09:00
3. **Limpeza de Notificações** - Domingo às 03:00

---

## ✅ Pré-requisitos

1. **Google Cloud SDK (`gcloud`) instalado**
   - Download: https://cloud.google.com/sdk/docs/install
   - Ou use o Cloud Shell no console do GCP (já tem `gcloud` instalado)

2. **Autenticação no GCP**
   ```bash
   gcloud auth login
   gcloud config set project ifrs16-app
   ```

3. **Variáveis de ambiente**
   - `INTERNAL_JOB_TOKEN` ou `ADMIN_TOKEN` (token de segurança para os endpoints)

---

## 🚀 Método 1: Script Automático (Recomendado)

### No Cloud Shell ou ambiente com `gcloud`:

```bash
cd backend

# Verificar status atual
python scripts/verify_cloud_scheduler.py

# Configurar todos os schedulers faltantes
python scripts/verify_cloud_scheduler.py --configure
```

---

## 🛠️ Método 2: Configuração Manual via gcloud CLI

### 1. Remensuração Automática (Mensal)

```bash
gcloud scheduler jobs create http remeasurement-scheduler \
  --project=ifrs16-app \
  --location=us-central1 \
  --schedule="0 8 5 * *" \
  --time-zone="America/Sao_Paulo" \
  --uri="https://ifrs16-backend-1051753255664.us-central1.run.app/api/internal/jobs/remeasurement" \
  --http-method=POST \
  --headers="X-Internal-Token=SEU_TOKEN_AQUI,Content-Type=application/json" \
  --description="Remensuração Automática Mensal - Executa no dia 5 de cada mês às 08:00"
```

**Substitua `SEU_TOKEN_AQUI` pelo valor de `ADMIN_TOKEN` ou `INTERNAL_JOB_TOKEN`**

---

### 2. Verificação de Contratos Vencendo (Diário)

```bash
gcloud scheduler jobs create http check-expiring-contracts-scheduler \
  --project=ifrs16-app \
  --location=us-central1 \
  --schedule="0 9 * * *" \
  --time-zone="America/Sao_Paulo" \
  --uri="https://ifrs16-backend-1051753255664.us-central1.run.app/api/internal/jobs/check-expiring-contracts" \
  --http-method=POST \
  --headers="X-Internal-Token=SEU_TOKEN_AQUI,Content-Type=application/json" \
  --description="Verificação Diária de Contratos Vencendo - Executa diariamente às 09:00"
```

---

### 3. Limpeza de Notificações (Semanal)

```bash
gcloud scheduler jobs create http cleanup-notifications-scheduler \
  --project=ifrs16-app \
  --location=us-central1 \
  --schedule="0 3 * * 0" \
  --time-zone="America/Sao_Paulo" \
  --uri="https://ifrs16-backend-1051753255664.us-central1.run.app/api/internal/jobs/cleanup-notifications" \
  --http-method=POST \
  --headers="X-Internal-Token=SEU_TOKEN_AQUI,Content-Type=application/json" \
  --description="Limpeza Semanal de Notificações Antigas - Executa domingo às 03:00"
```

---

## 🔍 Verificar Schedulers Configurados

### Listar todos os schedulers:

```bash
gcloud scheduler jobs list \
  --project=ifrs16-app \
  --location=us-central1
```

### Ver detalhes de um scheduler específico:

```bash
gcloud scheduler jobs describe remeasurement-scheduler \
  --project=ifrs16-app \
  --location=us-central1
```

---

## 🧪 Testar Schedulers Manualmente

### Executar um scheduler imediatamente:

```bash
# Remensuração
gcloud scheduler jobs run remeasurement-scheduler \
  --project=ifrs16-app \
  --location=us-central1

# Contratos vencendo
gcloud scheduler jobs run check-expiring-contracts-scheduler \
  --project=ifrs16-app \
  --location=us-central1

# Limpeza
gcloud scheduler jobs run cleanup-notifications-scheduler \
  --project=ifrs16-app \
  --location=us-central1
```

### Ou testar diretamente via HTTP:

```bash
# Remensuração
curl -X POST \
  "https://ifrs16-backend-1051753255664.us-central1.run.app/api/internal/jobs/remeasurement" \
  -H "X-Internal-Token: SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json"

# Contratos vencendo
curl -X POST \
  "https://ifrs16-backend-1051753255664.us-central1.run.app/api/internal/jobs/check-expiring-contracts" \
  -H "X-Internal-Token: SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json"

# Limpeza
curl -X POST \
  "https://ifrs16-backend-1051753255664.us-central1.run.app/api/internal/jobs/cleanup-notifications?days=90" \
  -H "X-Internal-Token: SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json"
```

---

## 📊 Verificar Logs de Execução

### Ver histórico de execuções:

```bash
# Listar execuções do scheduler
gcloud scheduler jobs list-executions remeasurement-scheduler \
  --project=ifrs16-app \
  --location=us-central1

# Ver logs de uma execução específica
gcloud logging read "resource.type=cloud_scheduler_job AND resource.labels.job_id=remeasurement-scheduler" \
  --project=ifrs16-app \
  --limit=10 \
  --format=json
```

---

## ⚙️ Atualizar um Scheduler Existente

### Atualizar schedule:

```bash
gcloud scheduler jobs update http remeasurement-scheduler \
  --project=ifrs16-app \
  --location=us-central1 \
  --schedule="0 9 5 * *"  # Novo horário: 09:00 em vez de 08:00
```

### Atualizar token:

```bash
gcloud scheduler jobs update http remeasurement-scheduler \
  --project=ifrs16-app \
  --location=us-central1 \
  --update-headers="X-Internal-Token=NOVO_TOKEN_AQUI"
```

---

## 🗑️ Deletar um Scheduler

```bash
gcloud scheduler jobs delete remeasurement-scheduler \
  --project=ifrs16-app \
  --location=us-central1
```

---

## 📝 Formato de Schedule (Cron)

O formato usado é: `minuto hora dia mês dia-da-semana`

- `0 8 5 * *` = Dia 5 de cada mês às 08:00
- `0 9 * * *` = Diariamente às 09:00
- `0 3 * * 0` = Domingo às 03:00

**Fuso horário:** `America/Sao_Paulo` (UTC-3)

---

## 🔒 Segurança

- Os endpoints são protegidos por `X-Internal-Token`
- O token deve ser o mesmo configurado em `ADMIN_TOKEN` ou `INTERNAL_JOB_TOKEN`
- **Nunca exponha o token publicamente**
- Use variáveis de ambiente ou Google Secret Manager para armazenar o token

---

## ✅ Checklist de Configuração

- [ ] `gcloud` CLI instalado e autenticado
- [ ] Projeto GCP configurado (`ifrs16-app`)
- [ ] Token de segurança obtido (`ADMIN_TOKEN` ou `INTERNAL_JOB_TOKEN`)
- [ ] Scheduler de remensuração criado
- [ ] Scheduler de contratos vencendo criado
- [ ] Scheduler de limpeza criado
- [ ] Testes manuais executados com sucesso
- [ ] Logs verificados após primeira execução automática

---

## 🆘 Troubleshooting

### Erro: "Permission denied"
- Verifique se você tem permissões de `Cloud Scheduler Admin` no projeto
- Execute: `gcloud projects add-iam-policy-binding ifrs16-app --member=user:SEU_EMAIL --role=roles/cloudscheduler.admin`

### Erro: "Job not found"
- Verifique se o scheduler foi criado na região correta (`us-central1`)
- Liste todos os schedulers: `gcloud scheduler jobs list --location=us-central1`

### Erro: "401 Unauthorized" ao executar
- Verifique se o token no header está correto
- Confirme que o `ADMIN_TOKEN` no backend está configurado

### Scheduler não executa automaticamente
- Verifique o schedule (formato cron)
- Verifique o timezone (`America/Sao_Paulo`)
- Veja os logs: `gcloud logging read "resource.type=cloud_scheduler_job" --limit=50`

---

## 📚 Referências

- [Documentação do Cloud Scheduler](https://cloud.google.com/scheduler/docs)
- [Formato Cron](https://cloud.google.com/scheduler/docs/configuring/cron-job-schedules)
- [Script de Verificação](../backend/scripts/verify_cloud_scheduler.py)

---

**Última Atualização:** 2026-01-02
