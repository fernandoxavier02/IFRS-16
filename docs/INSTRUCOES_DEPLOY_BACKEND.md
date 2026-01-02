# 🚀 INSTRUÇÕES DE DEPLOY DO BACKEND - CLOUD RUN

> **Última atualização:** 2026-01-02  
> **Região:** `southamerica-east1`  
> **Projeto:** `ifrs16-app`

---

## ⚠️ REGRAS IMPORTANTES

1. **SEMPRE use Kaniko** para builds (mais rápido com cache)
2. **NUNCA use** `gcloud builds submit .` diretamente
3. **SEMPRE use** `--config=cloudbuild.yaml` para aproveitar cache
4. **Região correta:** `southamerica-east1` (não `us-central1`)

---

## 📋 PROCESSO COMPLETO DE DEPLOY

### Passo 1: Build com Kaniko

```bash
cd "IFRS 16-20251217T150830Z-1-001/IFRS 16/backend"
gcloud builds submit --config=cloudbuild.yaml
```

**O que faz:**
- Usa Kaniko para build otimizado
- Aproveita cache de layers Docker
- Build mais rápido que método tradicional
- Gera imagem: `gcr.io/ifrs16-app/ifrs16-backend:latest`

---

### Passo 2: Deploy no Cloud Run

```bash
gcloud run deploy ifrs16-backend \
  --image gcr.io/ifrs16-app/ifrs16-backend:latest \
  --region southamerica-east1 \
  --project ifrs16-app
```

**O que faz:**
- Faz deploy da imagem buildada
- Atualiza o serviço Cloud Run
- Mantém configurações existentes
- Cria nova revisão automaticamente

---

### Passo 3: Atualizar Variáveis de Ambiente (se necessário)

**⚠️ Apenas se der erro de variáveis de ambiente:**

```bash
gcloud run services update ifrs16-backend \
  --region southamerica-east1 \
  --project ifrs16-app \
  --env-vars-file=cloud_run_env_deploy.yaml
```

**Quando usar:**
- Primeira vez fazendo deploy
- Adicionando novas variáveis de ambiente
- Atualizando valores de variáveis existentes
- Corrigindo erros de configuração

---

## 🔍 VERIFICAÇÃO PÓS-DEPLOY

### Verificar Status do Serviço

```bash
gcloud run services describe ifrs16-backend \
  --region southamerica-east1 \
  --project ifrs16-app
```

### Ver Logs

```bash
gcloud run services logs read ifrs16-backend \
  --region southamerica-east1 \
  --project ifrs16-app \
  --limit 50
```

### Testar Endpoint

```bash
curl https://ifrs16-backend-1051753255664.southamerica-east1.run.app/api/health
```

---

## 📝 ARQUIVOS NECESSÁRIOS

### `backend/cloudbuild.yaml`
- Configuração do Cloud Build
- Usa Kaniko para builds otimizados
- Define steps de build e push

### `backend/Dockerfile`
- Imagem Docker do backend
- Base: `python:3.11-slim`
- Instala dependências e copia código

### `backend/cloud_run_env_deploy.yaml` (NÃO COMMITADO)
- Variáveis de ambiente do Cloud Run
- **⚠️ Contém secrets - NÃO commitar no Git**
- Usado apenas para atualizar env vars

---

## 🚫 O QUE NÃO FAZER

❌ **NÃO use:**
```bash
gcloud builds submit .
```

✅ **USE:**
```bash
gcloud builds submit --config=cloudbuild.yaml
```

**Motivo:** O método direto não usa cache do Kaniko e é muito mais lento.

---

## 🔄 FLUXO COMPLETO (Copy-Paste)

```bash
# 1. Ir para diretório do backend
cd "IFRS 16-20251217T150830Z-1-001/IFRS 16/backend"

# 2. Build com Kaniko
gcloud builds submit --config=cloudbuild.yaml

# 3. Deploy no Cloud Run
gcloud run deploy ifrs16-backend \
  --image gcr.io/ifrs16-app/ifrs16-backend:latest \
  --region southamerica-east1 \
  --project ifrs16-app

# 4. (Opcional) Atualizar env vars se necessário
gcloud run services update ifrs16-backend \
  --region southamerica-east1 \
  --project ifrs16-app \
  --env-vars-file=cloud_run_env_deploy.yaml
```

---

## 📊 INFORMAÇÕES DO SERVIÇO

- **Nome:** `ifrs16-backend`
- **Região:** `southamerica-east1`
- **Projeto:** `ifrs16-app`
- **URL:** `https://ifrs16-backend-1051753255664.southamerica-east1.run.app`
- **Imagem:** `gcr.io/ifrs16-app/ifrs16-backend:latest`

---

**Última atualização:** 2026-01-02  
**Status:** ✅ Instruções validadas e funcionando
