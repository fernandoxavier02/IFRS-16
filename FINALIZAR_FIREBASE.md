# 🎯 Finalizar Configuração Firebase - Passo a Passo

**Status Atual:** Frontend deployado ✅ | Backend pendente ⏳

---

## ✅ JÁ CONCLUÍDO

1. ✅ Projeto Firebase criado: `ifrs16-app`
2. ✅ Firebase CLI instalado e configurado
3. ✅ Frontend deployado no Firebase Hosting
4. ✅ URLs atualizadas no código (parcialmente)
5. ✅ CORS atualizado no backend

**Frontend funcionando em:**
- https://ifrs16-app.web.app
- https://ifrs16-app.firebaseapp.com

---

## 📋 PRÓXIMOS PASSOS

### 1️⃣ Instalar Google Cloud SDK (se não tiver)

**Windows:**
1. Baixar: https://cloud.google.com/sdk/docs/install
2. Instalar o instalador
3. Ou via PowerShell:
   ```powershell
   (New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
   & $env:Temp\GoogleCloudSDKInstaller.exe
   ```

---

### 2️⃣ Autenticar no Google Cloud

```bash
gcloud auth login
```

Siga as instruções na tela para autenticar.

---

### 3️⃣ Configurar Projeto

```bash
gcloud config set project ifrs16-app
```

---

### 4️⃣ Habilitar APIs Necessárias

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
```

Ou tudo de uma vez:
```bash
gcloud services enable cloudbuild.googleapis.com run.googleapis.com sqladmin.googleapis.com
```

---

### 5️⃣ Criar Cloud SQL PostgreSQL

**Opção A: Via Script (Recomendado)**

```powershell
.\configurar_cloud_sql.ps1
```

**Opção B: Manual**

```bash
gcloud sql instances create ifrs16-database \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=us-central1 \
    --root-password=[SENHA_FORTE_AQUI]
```

**Aguarde 5-10 minutos para criação.**

Depois:
```bash
# Criar database
gcloud sql databases create ifrs16_licenses --instance=ifrs16-database

# Criar usuário
gcloud sql users create ifrs16_user \
    --instance=ifrs16-database \
    --password=[SENHA_FORTE]
```

**Obter Connection String:**
```bash
gcloud sql instances describe ifrs16-database --format="value(connectionName)"
```

---

### 6️⃣ Deploy do Backend no Cloud Run

**Opção A: Via Script**

```powershell
.\deploy_firebase.ps1
```

**Opção B: Manual**

```bash
# Build da imagem
gcloud builds submit --tag gcr.io/ifrs16-app/ifrs16-backend backend/

# Deploy no Cloud Run
gcloud run deploy ifrs16-backend \
    --image gcr.io/ifrs16-app/ifrs16-backend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --project ifrs16-app
```

**Aguarde 2-5 minutos para deploy.**

**URL será:** `https://ifrs16-backend-[hash].run.app`

---

### 7️⃣ Configurar Variáveis de Ambiente no Cloud Run

Após obter a URL do Cloud Run, configure as variáveis:

```bash
gcloud run services update ifrs16-backend \
    --update-env-vars "DATABASE_URL=postgresql://user:pass@/db?host=/cloudsql/[CONNECTION_STRING]" \
    --update-env-vars "JWT_SECRET_KEY=vj7s-Zlyd4OYlejHDC22UEmCSSblzH1Pn7mowJulEAk" \
    --update-env-vars "STRIPE_SECRET_KEY=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" \
    --update-env-vars "FRONTEND_URL=https://ifrs16-app.web.app" \
    --update-env-vars "API_URL=https://[SUA-URL-CLOUD-RUN]" \
    --update-env-vars "CORS_ORIGINS=https://ifrs16-app.web.app,https://ifrs16-app.firebaseapp.com" \
    --region us-central1 \
    --project ifrs16-app
```

**Ou via Console:**
1. Acesse: https://console.cloud.google.com/run
2. Clique no serviço `ifrs16-backend`
3. Editar e implantar nova revisão
4. Variáveis e segredos → Adicionar variável
5. Adicione todas as variáveis de `FIREBASE_ENV_VARS.txt`

---

### 8️⃣ Executar Migrations

```bash
# Conectar ao Cloud Run e executar migrations
gcloud run services update ifrs16-backend \
    --update-env-vars "RUN_MIGRATIONS=true" \
    --region us-central1

# Ou executar localmente apontando para Cloud SQL
# (requer Cloud SQL Proxy)
```

---

### 9️⃣ Atualizar URLs Finais no Código

Após obter a URL do Cloud Run:

**Atualizar `Calculadora_IFRS16_Deploy.html`:**

```javascript
const getApiUrl = () => {
    const hostname = window.location.hostname;
    
    // Firebase Hosting
    if (hostname.includes('web.app') || hostname.includes('firebaseapp.com')) {
        return 'https://[SUA-URL-CLOUD-RUN].run.app';
    }
    
    // Render (temporário)
    if (hostname.includes('onrender.com')) {
        return 'https://ifrs-16.onrender.com';
    }
    
    // Desenvolvimento local
    return 'http://localhost:8000';
};
```

**Atualizar `backend/app/config.py`:**

```python
FRONTEND_URL: str = "https://ifrs16-app.web.app"
API_URL: str = "https://[SUA-URL-CLOUD-RUN].run.app"
```

**Fazer commit e push:**
```bash
git add .
git commit -m "Atualizar URLs para Firebase"
git push origin main
```

**Fazer novo deploy do frontend:**
```bash
firebase deploy --only hosting
```

---

### 🔟 Atualizar Webhooks Stripe

1. Acesse: https://dashboard.stripe.com/webhooks
2. Edite o webhook
3. URL: `https://[SUA-URL-CLOUD-RUN]/api/payments/webhook`
4. Salvar

---

### 1️⃣1️⃣ Testar Tudo

- [ ] Frontend carrega: https://ifrs16-app.web.app
- [ ] Backend health: https://[cloud-run-url]/health
- [ ] API docs: https://[cloud-run-url]/docs
- [ ] Login funciona
- [ ] Calculadora funciona
- [ ] Banco de dados conecta
- [ ] Stripe funciona

---

## 🎯 RESUMO RÁPIDO

**Comandos principais:**

```bash
# 1. Login
gcloud auth login

# 2. Projeto
gcloud config set project ifrs16-app

# 3. APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com sqladmin.googleapis.com

# 4. Cloud SQL (via script)
.\configurar_cloud_sql.ps1

# 5. Deploy backend
.\deploy_firebase.ps1

# 6. Configurar variáveis
# (via console ou gcloud run services update)
```

---

## 📞 AJUDA

- Firebase Console: https://console.firebase.google.com/project/ifrs16-app
- Cloud Console: https://console.cloud.google.com
- Documentação completa: `PLANO_MIGRACAO_FIREBASE_COMPLETO.md`

---

**Status:** Frontend ✅ | Backend ⏳ | Database ⏳
