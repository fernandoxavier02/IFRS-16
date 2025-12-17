# 🔥 Plano de Migração Completo para Firebase

**Objetivo:** Migrar tudo para Firebase (Hosting + Cloud Run + Cloud SQL)  
**Prazo:** 1-2 horas  
**Custo:** $10-30/mês (depende do uso)

---

## ✅ O QUE O FIREBASE OFERECE

- ✅ **Firebase Hosting** - Frontend estático (GRÁTIS até 10GB)
- ✅ **Cloud Run** - Backend Python/FastAPI (melhor que Functions para Python)
- ✅ **Cloud SQL** - PostgreSQL gerenciado
- ✅ **CDN Global** - Google Cloud CDN
- ✅ **HTTPS Automático** - SSL grátis
- ✅ **Deploy Automático** - Via GitHub Actions ou CLI
- ✅ **Sem Sleep** - Sempre ativo

---

## 📋 PRÉ-REQUISITOS

- [ ] Conta Google (Gmail)
- [ ] Projeto no GitHub
- [ ] Backup do banco de dados do Render

---

## 🚀 PASSO A PASSO COMPLETO

### 1️⃣ Criar Projeto Firebase (10 min)

1. Acesse: https://console.firebase.google.com
2. Clique em "Adicionar projeto"
3. **Nome do projeto:** `ifrs16-app` (ou outro nome)
4. **Google Analytics:** Opcional (pode desabilitar)
5. Clique em "Criar projeto"
6. Aguarde criação (1-2 minutos)

---

### 2️⃣ Instalar Firebase CLI (5 min)

```powershell
# Windows - via npm (se tiver Node.js)
npm install -g firebase-tools

# Ou via Chocolatey
choco install firebase-tools

# Verificar instalação
firebase --version
```

---

### 3️⃣ Login e Inicializar Firebase (5 min)

```bash
cd "c:\Projetos\IFRS 16"

# Login
firebase login

# Inicializar projeto
firebase init
```

**Selecionar:**
- ✅ **Hosting** - Para frontend
- ✅ **Functions** - Para backend (ou Cloud Run, ver passo 4)
- ✅ **Firestore** - Opcional (se não usar Cloud SQL)

**Configurações:**
- **Project:** Escolher o projeto criado
- **Public directory:** `.` (raiz)
- **Single-page app:** Não
- **GitHub Actions:** Sim (para deploy automático)

---

### 4️⃣ Configurar Backend no Cloud Run (Recomendado para Python)

**Por quê Cloud Run em vez de Functions?**
- ✅ Melhor para Python/FastAPI
- ✅ Suporta containers Docker
- ✅ Mais fácil de migrar
- ✅ Melhor performance

#### 4.1 Criar Dockerfile para Backend

Criar `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Expor porta (Cloud Run usa PORT)
ENV PORT=8080
EXPOSE 8080

# Comando de start
CMD exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

#### 4.2 Criar `.dockerignore`

Criar `backend/.dockerignore`:

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv
*.db
*.sqlite
.env
.git
.gitignore
README.md
tests/
.pytest_cache
```

#### 4.3 Criar Script de Deploy

Criar `deploy_backend_firebase.ps1`:

```powershell
# Deploy do backend para Cloud Run

$PROJECT_ID = "ifrs16-app"  # Substituir pelo seu project ID
$SERVICE_NAME = "ifrs16-backend"
$REGION = "us-central1"  # ou southamerica-east1 (São Paulo)

Write-Host "🚀 Fazendo deploy do backend para Cloud Run..." -ForegroundColor Cyan

# Build e push da imagem
Write-Host "📦 Construindo imagem Docker..." -ForegroundColor Yellow
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME --project $PROJECT_ID backend/

# Deploy no Cloud Run
Write-Host "🚀 Fazendo deploy no Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME `
    --platform managed `
    --region $REGION `
    --allow-unauthenticated `
    --project $PROJECT_ID `
    --set-env-vars "ENVIRONMENT=production,DEBUG=false"

Write-Host "✅ Deploy concluído!" -ForegroundColor Green
```

---

### 5️⃣ Configurar Cloud SQL PostgreSQL (15 min)

#### 5.1 Criar Instância Cloud SQL

1. Acesse: https://console.cloud.google.com/sql/instances
2. Clique em "Criar instância"
3. Escolha **PostgreSQL**
4. **ID da instância:** `ifrs16-database`
5. **Senha:** Gerar senha forte (salvar!)
6. **Região:** `southamerica-east1` (São Paulo) ou `us-central1`
7. **Tipo de máquina:** `db-f1-micro` (free tier) ou `db-g1-small`
8. Clique em "Criar"

**Aguarde 5-10 minutos para criação.**

#### 5.2 Configurar Conexão

1. Na instância criada, vá em "Conexões"
2. Adicionar rede autorizada: `0.0.0.0/0` (temporário, para teste)
3. Ou melhor: usar Cloud SQL Proxy (mais seguro)

#### 5.3 Obter Connection String

1. Na instância, clique em "Visão geral"
2. Copie a **String de conexão**:
   ```
   [PROJECT_ID]:[REGION]:[INSTANCE_ID]
   ```

#### 5.4 Migrar Dados (se necessário)

```bash
# Exportar do Render
pg_dump $RENDER_DATABASE_URL > backup.sql

# Importar no Cloud SQL
gcloud sql import sql ifrs16-database gs://[BUCKET]/backup.sql --database=postgres
```

---

### 6️⃣ Configurar Firebase Hosting (Frontend) (10 min)

#### 6.1 Configurar `firebase.json`

Criar/atualizar `firebase.json`:

```json
{
  "hosting": {
    "public": ".",
    "ignore": [
      "backend/**",
      "node_modules/**",
      ".git/**",
      "*.md",
      "firebase.json",
      "firebase-debug.log",
      "*.ps1",
      "*.py",
      "*.json",
      "tests/**",
      "alembic/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(html|js|css)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "max-age=3600"
          }
        ]
      }
    ]
  }
}
```

#### 6.2 Criar `index.html` (Opcional)

Se quiser redirecionar para a calculadora:

```html
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url=Calculadora_IFRS16_Deploy.html">
    <title>IFRS 16 - Calculadora</title>
</head>
<body>
    <p>Redirecionando para a calculadora...</p>
</body>
</html>
```

#### 6.3 Deploy do Frontend

```bash
firebase deploy --only hosting
```

**URL será:** `https://[seu-projeto].web.app`

---

### 7️⃣ Configurar Variáveis de Ambiente (10 min)

#### 7.1 Variáveis no Cloud Run

Após deploy do Cloud Run, adicionar variáveis:

```bash
gcloud run services update ifrs16-backend \
    --update-env-vars "DATABASE_URL=postgresql://user:pass@/db?host=/cloudsql/[CONNECTION_STRING]" \
    --update-env-vars "JWT_SECRET_KEY=..." \
    --update-env-vars "STRIPE_SECRET_KEY=..." \
    --region us-central1 \
    --project ifrs16-app
```

Ou via Console:
1. Cloud Run → Serviço → Editar e implantar nova revisão
2. Variáveis e segredos → Adicionar variável

#### 7.2 Criar Arquivo de Variáveis

Criar `firebase_env_vars.txt` com todas as variáveis (copiar de `VARIABLES_RENDER.txt` e adaptar `DATABASE_URL`).

---

### 8️⃣ Atualizar URLs no Código (10 min)

#### 8.1 Atualizar `backend/app/config.py`

```python
FRONTEND_URL: str = "https://[seu-projeto].web.app"
API_URL: str = "https://[seu-cloud-run-url].run.app"
```

#### 8.2 Atualizar `backend/app/main.py`

```python
ALLOWED_ORIGINS = [
    "https://[seu-projeto].web.app",
    "https://[seu-projeto].firebaseapp.com",
    "https://[seu-cloud-run-url].run.app",
    "http://localhost:3000",
    "http://localhost:8000",
]
```

#### 8.3 Atualizar `Calculadora_IFRS16_Deploy.html`

```javascript
const getApiUrl = () => {
    const hostname = window.location.hostname;
    
    // Firebase Hosting
    if (hostname.includes('web.app') || hostname.includes('firebaseapp.com')) {
        return 'https://[seu-cloud-run-url].run.app';
    }
    
    // Desenvolvimento local
    return 'http://localhost:8000';
};
```

---

### 9️⃣ Configurar Deploy Automático (15 min)

#### 9.1 GitHub Actions para Frontend

Criar `.github/workflows/firebase-hosting.yml`:

```yaml
name: Deploy to Firebase Hosting

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - run: npm install -g firebase-tools
      
      - run: firebase deploy --only hosting
        env:
          FIREBASE_TOKEN: ${{ secrets.FIREBASE_TOKEN }}
```

#### 9.2 GitHub Actions para Backend

Criar `.github/workflows/cloud-run-deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]
    paths:
      - 'backend/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}
      
      - name: Build and Deploy
        run: |
          gcloud builds submit --tag gcr.io/${{ secrets.GCP_PROJECT_ID }}/ifrs16-backend backend/
          gcloud run deploy ifrs16-backend \
            --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/ifrs16-backend \
            --platform managed \
            --region us-central1 \
            --allow-unauthenticated
```

#### 9.3 Configurar Secrets no GitHub

1. GitHub → Settings → Secrets and variables → Actions
2. Adicionar:
   - `FIREBASE_TOKEN` (obter com `firebase login:ci`)
   - `GCP_SA_KEY` (service account JSON)
   - `GCP_PROJECT_ID`

---

### 🔟 Testar Tudo (15 min)

- [ ] Frontend carrega: `https://[projeto].web.app`
- [ ] Backend health: `https://[cloud-run-url]/health`
- [ ] API docs: `https://[cloud-run-url]/docs`
- [ ] Login funciona
- [ ] Calculadora funciona
- [ ] Banco de dados conecta
- [ ] Stripe funciona

---

### 1️⃣1️⃣ Atualizar Webhooks Stripe (5 min)

1. Acesse: https://dashboard.stripe.com/webhooks
2. Edite o webhook
3. URL: `https://[seu-cloud-run-url]/api/payments/webhook`
4. Salvar

---

## 🎯 CHECKLIST COMPLETO

### Preparação
- [ ] Backup do banco de dados
- [ ] Exportar variáveis de ambiente
- [ ] Código no GitHub atualizado

### Firebase Setup
- [ ] Projeto Firebase criado
- [ ] Firebase CLI instalado
- [ ] `firebase init` executado
- [ ] `firebase.json` configurado

### Backend (Cloud Run)
- [ ] Dockerfile criado
- [ ] Imagem buildada
- [ ] Cloud Run service criado
- [ ] Variáveis de ambiente configuradas
- [ ] Deploy funcionando

### Banco de Dados
- [ ] Cloud SQL instância criada
- [ ] Conexão configurada
- [ ] Dados migrados (se necessário)
- [ ] Alembic migrations executadas

### Frontend (Hosting)
- [ ] `firebase.json` configurado
- [ ] Deploy feito
- [ ] URL testada

### Código
- [ ] URLs atualizadas
- [ ] CORS configurado
- [ ] `getApiUrl()` atualizado

### Automação
- [ ] GitHub Actions configurado
- [ ] Secrets configurados
- [ ] Deploy automático funcionando

### Testes
- [ ] Frontend acessível
- [ ] Backend respondendo
- [ ] Login funciona
- [ ] Calculadora funciona
- [ ] Stripe funciona
- [ ] Webhooks funcionam

---

## 💰 CUSTOS ESTIMADOS

| Serviço | Free Tier | Pago (uso moderado) |
|---------|-----------|---------------------|
| **Firebase Hosting** | 10GB storage, 360MB/day | $0.026/GB storage |
| **Cloud Run** | 2 milhões requests/mês | $0.40/milhão requests |
| **Cloud SQL** | ❌ Não tem free | $7-25/mês (db-f1-micro) |
| **Total** | **$0** (só hosting) | **$10-30/mês** |

---

## 🆘 TROUBLESHOOTING

### Backend não inicia no Cloud Run
- Verificar logs: `gcloud run services logs read ifrs16-backend`
- Verificar variáveis de ambiente
- Verificar `DATABASE_URL` está correta
- Verificar porta (Cloud Run usa `$PORT`)

### Erro de conexão com Cloud SQL
- Verificar IP autorizado
- Usar Cloud SQL Proxy (recomendado)
- Verificar connection string

### Frontend não carrega
- Verificar `firebase.json`
- Verificar arquivos na raiz
- Verificar deploy: `firebase deploy --only hosting`

### CORS errors
- Verificar `ALLOWED_ORIGINS` no código
- Verificar URL exata do Firebase Hosting

---

## 📞 LINKS ÚTEIS

- Firebase Console: https://console.firebase.google.com
- Cloud Run Console: https://console.cloud.google.com/run
- Cloud SQL Console: https://console.cloud.google.com/sql
- Firebase Docs: https://firebase.google.com/docs
- Cloud Run Docs: https://cloud.google.com/run/docs

---

## 🎉 PRONTO!

Agora você tem:
- ✅ Frontend no Firebase Hosting (CDN global)
- ✅ Backend no Cloud Run (sem sleep)
- ✅ PostgreSQL no Cloud SQL (gerenciado)
- ✅ Deploy automático
- ✅ Tudo integrado no Firebase/Google Cloud

**Próximo passo:** Desativar Render após confirmar que tudo funciona!

---

**Tempo total:** 1-2 horas  
**Dificuldade:** ⭐⭐⭐ (Médio - requer conhecimento de Docker/Cloud)
