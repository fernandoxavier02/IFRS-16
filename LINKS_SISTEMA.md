# 🔗 Links do Sistema IFRS 16

**Última atualização:** 15 de Dezembro de 2025

---

## 🌐 Frontend (Firebase Hosting)

### Aplicação Principal
- **Calculadora IFRS 16:** https://ifrs16-app.web.app/Calculadora_IFRS16_Deploy.html
- **Página Inicial:** https://ifrs16-app.web.app/
- **Login:** https://ifrs16-app.web.app/login.html
- **Painel Admin:** https://ifrs16-app.web.app/admin.html

### URLs Alternativas (Firebase)
- **Web App:** https://ifrs16-app.firebaseapp.com
- **Calculadora:** https://ifrs16-app.firebaseapp.com/Calculadora_IFRS16_Deploy.html

---

## 🔧 Backend API (Google Cloud Run)

### API Principal
- **Base URL:** https://ifrs16-backend-1051753255664.us-central1.run.app
- **Documentação Swagger:** https://ifrs16-backend-1051753255664.us-central1.run.app/docs
- **ReDoc:** https://ifrs16-backend-1051753255664.us-central1.run.app/redoc

### Endpoints Principais

#### Autenticação
- **Login Admin:** `POST /api/auth/admin/login`
- **Verificar Admin:** `GET /api/auth/admin/me`
- **Login Usuário:** `POST /api/auth/login`
- **Validar Token:** `GET /api/auth/validate`

#### Licenças (Admin)
- **Listar Licenças:** `GET /api/admin/licenses`
- **Criar Licença:** `POST /api/admin/generate-license`
- **Revogar Licença:** `POST /api/admin/revoke-license`
- **Reativar Licença:** `POST /api/admin/reactivate-license`

#### Licenças (Público)
- **Validar Licença:** `POST /api/licenses/validate`
- **Verificar Status:** `GET /api/licenses/{license_key}/status`

#### Pagamentos (Stripe)
- **Listar Preços:** `GET /api/payments/prices`
- **Criar Checkout:** `POST /api/payments/create-checkout`
- **Webhook Stripe:** `POST /api/payments/webhook`

---

## 🗄️ Banco de Dados (Cloud SQL)

### Informações de Conexão
- **Connection Name:** `ifrs16-app:us-central1:ifrs16-database`
- **IP Público:** `136.112.221.225`
- **Database:** `ifrs16_licenses`
- **Porta:** `5432`

### Console Google Cloud
- **Cloud SQL Console:** https://console.cloud.google.com/sql/instances?project=ifrs16-app
- **Cloud Run Console:** https://console.cloud.google.com/run?project=ifrs16-app
- **Cloud Build:** https://console.cloud.google.com/cloud-build/builds?project=ifrs16-app

---

## 🔐 Credenciais de Acesso

### Usuário Master (Admin)
- **Email:** `fernandocostaxavier@gmail.com`
- **Senha:** `Master@2025!`
- **Role:** `SUPERADMIN`

### Login
- **URL:** https://ifrs16-app.web.app/login.html
- **Aba:** "Administrador"

---

## 📊 Dashboards e Monitoramento

### Google Cloud Console
- **Projeto:** https://console.cloud.google.com/home/dashboard?project=ifrs16-app
- **Cloud Run Services:** https://console.cloud.google.com/run?project=ifrs16-app
- **Cloud SQL Instances:** https://console.cloud.google.com/sql/instances?project=ifrs16-app
- **Logs Explorer:** https://console.cloud.google.com/logs/query?project=ifrs16-app

### Firebase Console
- **Firebase Console:** https://console.firebase.google.com/project/ifrs16-app
- **Hosting:** https://console.firebase.google.com/project/ifrs16-app/hosting

---

## 🔗 Links Úteis

### Documentação
- **API Docs (Swagger):** https://ifrs16-backend-1051753255664.us-central1.run.app/docs
- **API Docs (ReDoc):** https://ifrs16-backend-1051753255664.us-central1.run.app/redoc

### Stripe
- **Stripe Dashboard:** https://dashboard.stripe.com
- **Webhooks:** https://dashboard.stripe.com/webhooks

---

## 📱 Acesso Rápido

### Para Usuários
1. **Acessar Calculadora:** https://ifrs16-app.web.app/Calculadora_IFRS16_Deploy.html
2. **Fazer Login:** https://ifrs16-app.web.app/login.html

### Para Administradores
1. **Login Admin:** https://ifrs16-app.web.app/login.html (aba Administrador)
2. **Painel Admin:** https://ifrs16-app.web.app/admin.html
3. **API Docs:** https://ifrs16-backend-1051753255664.us-central1.run.app/docs

---

## ⚠️ IMPORTANTE

- Todos os links estão funcionando após a migração para Cloud SQL
- O sistema está 100% operacional
- Credenciais do usuário master foram validadas nos testes

---

**Status:** ✅ Sistema Operacional  
**Última verificação:** 15 de Dezembro de 2025, 21:10
