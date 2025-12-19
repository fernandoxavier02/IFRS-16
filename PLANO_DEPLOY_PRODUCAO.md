# 🚀 PLANO DE DEPLOY EM PRODUÇÃO - EXECUÇÃO COMPLETA

**Data:** 19/12/2025 17:15 BRT  
**Objetivo:** Deploy completo usando Cloud SQL, Cloud Run e Firebase

---

## 📊 INFRAESTRUTURA EXISTENTE

### Cloud SQL
- **Instância:** `ifrs16-app:us-central1:ifrs16-database`
- **Banco:** `ifrs16_licenses`
- **Usuário:** `ifrs16_user`
- **Senha:** `bBMOLk2HURjQAvDiPNYE`
- **Connection String:** `/cloudsql/ifrs16-app:us-central1:ifrs16-database`

### Cloud Run
- **Serviço:** `ifrs16-backend`
- **Região:** `us-central1`
- **URL:** `https://ifrs16-backend-1051753255664.us-central1.run.app`

### Firebase
- **Projeto:** `ifrs16-app`
- **Domínio:** `https://fxstudioai.com`
- **Hosting:** `https://ifrs16-app.web.app`

### Stripe
- **Price IDs já configurados:**
  - Basic Monthly: `price_1Sbs0oGEyVmwHCe6P9IylBWe`
  - Basic Yearly: `price_1SbrmCGEyVmwHCe6wlkuX7Z9`
  - Pro Monthly: `price_1Sbs0pGEyVmwHCe6pRDe6BfP`
  - Pro Yearly: `price_1Sbs0qGEyVmwHCe6NbW9697S`
  - Enterprise Monthly: `price_1Sbs0sGEyVmwHCe6gRVChJI6`
  - Enterprise Yearly: `price_1Sbs0uGEyVmwHCe6MHEVICw5`

---

## 🎯 PLANO DE EXECUÇÃO (8 ETAPAS)

### ETAPA 1: Preparar Variáveis de Ambiente
**Status:** Pronto para executar  
**Ação:** Criar arquivo `cloud_run_env.local.yaml` com valores reais

### ETAPA 2: Conectar ao Cloud SQL
**Status:** Aguardando execução  
**Ação:** Usar Cloud SQL Proxy para aplicar migração

### ETAPA 3: Aplicar Migração no Banco
**Status:** Aguardando execução  
**Ação:** `alembic upgrade head` no Cloud SQL

### ETAPA 4: Atualizar Variáveis no Cloud Run
**Status:** Aguardando execução  
**Ação:** Aplicar variáveis de ambiente no serviço

### ETAPA 5: Deploy Backend
**Status:** Aguardando execução  
**Ação:** Deploy do código no Cloud Run

### ETAPA 6: Testar Backend em Produção
**Status:** Aguardando execução  
**Ação:** Validar endpoints críticos

### ETAPA 7: Deploy Frontend
**Status:** Aguardando execução  
**Ação:** `firebase deploy --only hosting`

### ETAPA 8: Teste End-to-End
**Status:** Aguardando execução  
**Ação:** Testar fluxo completo em produção

---

## 📝 COMANDOS PREPARADOS

### 1. Criar Variáveis de Ambiente
```yaml
# cloud_run_env.local.yaml
DATABASE_URL: "postgresql+asyncpg://ifrs16_user:bBMOLk2HURjQAvDiPNYE@/ifrs16_licenses?host=/cloudsql/ifrs16-app:us-central1:ifrs16-database"
JWT_SECRET_KEY: "ifrs16-jwt-secret-key-production-2025"
JWT_ALGORITHM: "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: "1440"
ENVIRONMENT: "production"
DEBUG: "false"
FRONTEND_URL: "https://fxstudioai.com"
API_URL: "https://ifrs16-backend-1051753255664.us-central1.run.app"
CORS_ORIGINS: "https://ifrs16-app.web.app,https://ifrs16-app.firebaseapp.com,https://fxstudioai.com,https://www.fxstudioai.com"
STRIPE_SECRET_KEY: "sk_test_51SbqyqGEyVmwHCe6..."
STRIPE_PUBLISHABLE_KEY: "pk_test_51SbqyqGEyVmwHCe6..."
STRIPE_WEBHOOK_SECRET: "whsec_..."
STRIPE_PRICE_BASIC_MONTHLY: "price_1Sbs0oGEyVmwHCe6P9IylBWe"
STRIPE_PRICE_BASIC_YEARLY: "price_1SbrmCGEyVmwHCe6wlkuX7Z9"
STRIPE_PRICE_PRO_MONTHLY: "price_1Sbs0pGEyVmwHCe6pRDe6BfP"
STRIPE_PRICE_PRO_YEARLY: "price_1Sbs0qGEyVmwHCe6NbW9697S"
STRIPE_PRICE_ENTERPRISE_MONTHLY: "price_1Sbs0sGEyVmwHCe6gRVChJI6"
STRIPE_PRICE_ENTERPRISE_YEARLY: "price_1Sbs0uGEyVmwHCe6MHEVICw5"
CLOUD_SQL_USER: "ifrs16_user"
CLOUD_SQL_PASSWORD: "bBMOLk2HURjQAvDiPNYE"
DATABASE_URL_PROD: "postgresql+asyncpg://ifrs16_user:bBMOLk2HURjQAvDiPNYE@/ifrs16_licenses?host=/cloudsql/ifrs16-app:us-central1:ifrs16-database"
```

### 2. Conectar ao Cloud SQL (via Proxy)
```bash
# Baixar Cloud SQL Proxy (se necessário)
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.windows.amd64.exe

# Iniciar proxy
./cloud-sql-proxy ifrs16-app:us-central1:ifrs16-database
```

### 3. Aplicar Migração
```bash
# Com proxy rodando, aplicar migração
cd backend
$env:DATABASE_URL="postgresql+asyncpg://ifrs16_user:bBMOLk2HURjQAvDiPNYE@localhost:5432/ifrs16_licenses"
alembic upgrade head
```

### 4. Atualizar Variáveis Cloud Run
```bash
gcloud run services update ifrs16-backend \
  --env-vars-file=cloud_run_env.local.yaml \
  --region=us-central1 \
  --project=ifrs16-app
```

### 5. Deploy Backend
```bash
cd backend
gcloud run deploy ifrs16-backend \
  --source . \
  --region us-central1 \
  --project ifrs16-app \
  --allow-unauthenticated \
  --add-cloudsql-instances ifrs16-app:us-central1:ifrs16-database
```

### 6. Testar Backend
```bash
# Health check
curl https://ifrs16-backend-1051753255664.us-central1.run.app/health

# Listar preços Stripe
curl https://ifrs16-backend-1051753255664.us-central1.run.app/api/stripe/prices
```

### 7. Deploy Frontend
```bash
firebase deploy --only hosting --project ifrs16-app
```

### 8. Teste End-to-End
```
1. Acessar https://fxstudioai.com
2. Clicar em "Minha Conta"
3. Criar nova conta
4. Fazer login
5. Verificar dashboard
6. Testar botão Stripe
```

---

## ⚠️ PONTOS DE ATENÇÃO

### Segurança
- ✅ JWT_SECRET_KEY deve ser forte em produção
- ✅ Stripe keys devem ser modo teste primeiro
- ✅ Não commitar cloud_run_env.local.yaml

### Cloud SQL
- ✅ Proxy necessário para migração local
- ✅ Connection string usa Unix socket
- ✅ Cloud Run precisa do flag --add-cloudsql-instances

### Stripe
- ⚠️ Usar sk_test primeiro para validar
- ⚠️ Trocar para sk_live após testes
- ⚠️ Configurar webhook para produção

---

## 🔄 ORDEM DE EXECUÇÃO

```
1. Criar cloud_run_env.local.yaml
   ↓
2. Iniciar Cloud SQL Proxy
   ↓
3. Aplicar migração (alembic upgrade head)
   ↓
4. Atualizar variáveis Cloud Run
   ↓
5. Deploy backend (gcloud run deploy)
   ↓
6. Testar backend (curl health + prices)
   ↓
7. Deploy frontend (firebase deploy)
   ↓
8. Teste completo (registro → login → dashboard)
```

---

## ✅ CHECKLIST DE VALIDAÇÃO

### Pré-Deploy
- [ ] Cloud SQL acessível
- [ ] Credenciais corretas
- [ ] Migração testada localmente
- [ ] Variáveis de ambiente preparadas

### Deploy Backend
- [ ] Build bem-sucedido
- [ ] Serviço rodando
- [ ] Health check OK
- [ ] Endpoints respondendo
- [ ] Cloud SQL conectado

### Deploy Frontend
- [ ] Build bem-sucedido
- [ ] Arquivos deployados
- [ ] DNS resolvendo
- [ ] Assets carregando

### Testes
- [ ] Registro funcionando
- [ ] Login funcionando
- [ ] Dashboard carregando
- [ ] Dados do usuário corretos
- [ ] Stripe prices listando
- [ ] Portal Stripe acessível

---

## 🚨 ROLLBACK (Se necessário)

### Backend
```bash
# Voltar para versão anterior
gcloud run services update-traffic ifrs16-backend \
  --to-revisions=PREVIOUS_REVISION=100 \
  --region=us-central1
```

### Frontend
```bash
# Ver versões
firebase hosting:channel:list

# Rollback
firebase hosting:rollback
```

### Banco
```bash
# Reverter migração
alembic downgrade -1
```

---

**Plano criado e pronto para execução!**
**Aguardando confirmação para iniciar deploy...**
