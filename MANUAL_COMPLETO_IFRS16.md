# 📚 Manual Completo - Calculadora IFRS 16

**Versão:** 1.0  
**Data:** 11 de Dezembro de 2025  
**Autor:** Fernando Xavier

---

## 📑 Índice

1. [Visão Geral do Sistema](#1-visão-geral-do-sistema)
2. [Arquitetura](#2-arquitetura)
3. [URLs e Acessos](#3-urls-e-acessos)
4. [Firebase - Console e CLI](#4-firebase---console-e-cli)
5. [Google Cloud - Cloud Run](#5-google-cloud---cloud-run)
6. [Stripe - Pagamentos](#6-stripe---pagamentos)
7. [Sistema de Licenças](#7-sistema-de-licenças)
8. [Painel Administrativo](#8-painel-administrativo)
9. [Deploy e Manutenção](#9-deploy-e-manutenção)
10. [MCP (Model Context Protocol)](#10-mcp-model-context-protocol)
11. [Troubleshooting](#11-troubleshooting)
12. [Referência de APIs](#12-referência-de-apis)

---

## 1. Visão Geral do Sistema

### O que é a Calculadora IFRS 16?

Uma aplicação web para cálculo de arrendamentos conforme a norma IFRS 16/CPC 06 (R2), que inclui:

- **Calculadora de Leasing**: Cálculo de parcelas, valor presente, direito de uso, passivo de arrendamento
- **Sistema de Licenciamento**: Controle de acesso por chaves de licença
- **Assinaturas via Stripe**: Planos Basic, Pro e Enterprise
- **Painel Admin**: Gerenciamento de usuários e licenças

### Stack Tecnológico

| Componente | Tecnologia |
|------------|------------|
| Frontend | HTML5, CSS3 (Tailwind), JavaScript |
| Backend | Python 3.11, FastAPI |
| Database | PostgreSQL (Render) |
| Hosting Frontend | Firebase Hosting |
| Hosting Backend | Google Cloud Run |
| Pagamentos | Stripe |
| Autenticação | JWT (JSON Web Tokens) |

---

## 2. Arquitetura

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ARQUITETURA DO SISTEMA                       │
└─────────────────────────────────────────────────────────────────────┘

                    ┌──────────────────┐
                    │     USUÁRIO      │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  Firebase Hosting │
                    │  (Frontend)       │
                    │  ifrs16-app.web.app│
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼────────┐    │    ┌────────▼────────┐
     │   Cloud Run     │    │    │     Stripe      │
     │   (Backend)     │◄───┼───►│   (Pagamentos)  │
     │   FastAPI       │    │    │                 │
     └────────┬────────┘    │    └─────────────────┘
              │             │
     ┌────────▼────────┐    │
     │   PostgreSQL    │    │
     │   (Database)    │    │
     │   Render        │    │
     └─────────────────┘    │
                            │
              ┌─────────────▼─────────────┐
              │      WEBHOOKS             │
              │  Stripe → Backend         │
              │  (Assinaturas, Pagamentos)│
              └───────────────────────────┘
```

### Fluxo de Dados

1. **Usuário acessa** → Firebase Hosting serve HTML/CSS/JS
2. **Autenticação** → Frontend envia credenciais → Backend valida → JWT retornado
3. **Validação de Licença** → Frontend envia chave → Backend verifica → Token de licença
4. **Assinatura** → Stripe checkout → Webhook → Backend cria usuário/licença
5. **Uso do App** → Verificação periódica da licença (5 min)

---

## 3. URLs e Acessos

### URLs de Produção

| Descrição | URL |
|-----------|-----|
| **Frontend Principal** | https://ifrs16-app.web.app |
| **Calculadora** | https://ifrs16-app.web.app/Calculadora_IFRS16_Deploy.html |
| **Login** | https://ifrs16-app.web.app/login.html |
| **Admin** | https://ifrs16-app.web.app/admin.html |
| **Pricing** | https://ifrs16-app.web.app/pricing.html |
| **Backend API** | https://ifrs16-backend-1051753255664.us-central1.run.app |
| **API Docs (Swagger)** | https://ifrs16-backend-1051753255664.us-central1.run.app/docs |
| **API Docs (ReDoc)** | https://ifrs16-backend-1051753255664.us-central1.run.app/redoc |

### Credenciais Admin

```
Email:    fernandocostaxavier@gmail.com
Senha:    (NÃO VERSIONAR — armazene em cofre/gerenciador de senhas)
```

### Licença Master

```
Chave:    (NÃO VERSIONAR — consulte no painel Admin)
Tipo:     Enterprise
Cliente:  Master User
Ativações: 0/999
```

### Consoles de Gerenciamento

| Serviço | URL |
|---------|-----|
| Firebase Console | https://console.firebase.google.com/project/ifrs16-app |
| Google Cloud Console | https://console.cloud.google.com/home/dashboard?project=ifrs16-app |
| Cloud Run | https://console.cloud.google.com/run?project=ifrs16-app |
| Stripe Dashboard | https://dashboard.stripe.com |

---

## 4. Firebase - Console e CLI

### 4.1 Acessar o Console Firebase

1. Acesse: https://console.firebase.google.com
2. Selecione o projeto: **ifrs16-app**
3. Navegue pelas seções:
   - **Hosting**: Ver deploys, domínios, histórico
   - **Authentication**: Usuários (se configurado)
   - **Project Settings**: Configurações gerais

### 4.2 Firebase CLI - Instalação

```powershell
# Instalar via npm (Node.js necessário)
npm install -g firebase-tools

# Verificar instalação
firebase --version
```

### 4.3 Firebase CLI - Comandos Principais

```powershell
# Login no Firebase
firebase login

# Listar projetos
firebase projects:list

# Selecionar projeto
firebase use ifrs16-app

# Deploy do frontend
firebase deploy --only hosting

# Ver status do hosting
firebase hosting:sites:list

# Ver histórico de deploys
firebase hosting:channel:list

# Criar preview channel (para testes)
firebase hosting:channel:create preview
firebase hosting:channel:deploy preview

# Abrir console no navegador
firebase open
```

### 4.4 Estrutura do firebase.json

```json
{
  "hosting": {
    "public": ".",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**",
      "backend/**",
      "**/*.py",
      "**/*.md"
    ],
    "headers": [
      {
        "source": "**/*.@(js|css|html)",
        "headers": [
          { "key": "Cache-Control", "value": "max-age=3600" }
        ]
      }
    ]
  }
}
```

### 4.5 Deploy do Frontend

```powershell
# Navegue até a pasta do projeto
cd "c:\Projetos\IFRS 16"

# Deploy completo
firebase deploy --only hosting --project ifrs16-app

# Deploy com mensagem
firebase deploy --only hosting -m "Atualizacao de seguranca"
```

---

## 5. Google Cloud - Cloud Run

### 5.1 Google Cloud CLI - Instalação

```powershell
# Baixar instalador
# https://cloud.google.com/sdk/docs/install

# Após instalação, inicializar
gcloud init

# Login
gcloud auth login

# Configurar projeto
gcloud config set project ifrs16-app
```

### 5.2 Comandos Cloud Run

```powershell
# Listar serviços
gcloud run services list --region=us-central1

# Ver detalhes do serviço
gcloud run services describe ifrs16-backend --region=us-central1

# Ver logs
gcloud run services logs read ifrs16-backend --region=us-central1 --limit=100

# Ver logs em tempo real
gcloud run services logs tail ifrs16-backend --region=us-central1

# Atualizar variáveis de ambiente
gcloud run services update ifrs16-backend \
    --env-vars-file=cloud_run_env.yaml \
    --region=us-central1

# Forçar novo deploy
gcloud run deploy ifrs16-backend \
    --image gcr.io/ifrs16-app/ifrs16-backend \
    --region=us-central1 \
    --platform managed
```

### 5.3 Build e Deploy do Backend

```powershell
# Navegar para pasta do backend
cd "c:\Projetos\IFRS 16\backend"

# Build da imagem Docker
gcloud builds submit --tag gcr.io/ifrs16-app/ifrs16-backend

# Deploy para Cloud Run
gcloud run deploy ifrs16-backend \
    --image gcr.io/ifrs16-app/ifrs16-backend \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --project ifrs16-app

# Atualizar com variáveis de ambiente
cd "c:\Projetos\IFRS 16"
gcloud run services update ifrs16-backend \
    --env-vars-file=cloud_run_env.yaml \
    --region=us-central1 \
    --project=ifrs16-app
```

### 5.4 Variáveis de Ambiente (cloud_run_env.yaml)

```yaml
DATABASE_URL: "postgresql://..."
JWT_SECRET_KEY: "..."
JWT_ALGORITHM: "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: "1440"
ENVIRONMENT: "production"
DEBUG: "false"
FRONTEND_URL: "https://ifrs16-app.web.app"
API_URL: "https://ifrs16-backend-1051753255664.us-central1.run.app"
CORS_ORIGINS: "https://ifrs16-app.web.app,https://ifrs16-app.firebaseapp.com"
STRIPE_SECRET_KEY: "sk_live_..."
STRIPE_PUBLISHABLE_KEY: "pk_live_..."
STRIPE_WEBHOOK_SECRET: "whsec_..."
```

### 5.5 Dockerfile do Backend

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Expor porta
EXPOSE 8080

# Comando para iniciar
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

---

## 6. Stripe - Pagamentos

### 6.1 Dashboard Stripe

- **URL**: https://dashboard.stripe.com
- **Modo**: Live (Produção)

### 6.2 Webhook Configurado

| Campo | Valor |
|-------|-------|
| **ID** | `we_1SdGpHGEyVmwHCe67UywwDnQ` |
| **URL** | `https://ifrs16-backend-1051753255664.us-central1.run.app/api/payments/webhook` |
| **Secret** | `whsec_2mw7ee9qsTPTztYY92o6ii7DJg8F84uF` |
| **Status** | Ativo |

### 6.3 Eventos Monitorados

- `checkout.session.completed` - Assinatura concluída
- `invoice.paid` - Fatura paga
- `invoice.payment_failed` - Pagamento falhou
- `customer.subscription.created` - Nova assinatura
- `customer.subscription.updated` - Assinatura atualizada
- `customer.subscription.deleted` - Assinatura cancelada
- `customer.subscription.paused` - Assinatura pausada
- `customer.subscription.resumed` - Assinatura retomada
- `payment_intent.succeeded` - Pagamento bem-sucedido
- `payment_intent.payment_failed` - Pagamento falhou

### 6.4 Planos de Preço

| Plano | Mensal | Anual | Price ID |
|-------|--------|-------|----------|
| Basic | R$ X | R$ Y | price_1Sbs0o... |
| Pro | R$ X | R$ Y | price_1Sbs0p... |
| Enterprise | R$ X | R$ Y | price_1Sbs0s... |

### 6.5 Gerenciar Webhook via API

```powershell
$STRIPE_KEY = "sk_live_..."

# Listar webhooks
Invoke-RestMethod -Uri "https://api.stripe.com/v1/webhook_endpoints" `
    -Headers @{ "Authorization" = "Bearer $STRIPE_KEY" }

# Criar webhook
$body = @{
    url = "https://seu-backend/api/payments/webhook"
    "enabled_events[0]" = "checkout.session.completed"
    "enabled_events[1]" = "invoice.paid"
}
Invoke-RestMethod -Uri "https://api.stripe.com/v1/webhook_endpoints" `
    -Method Post -Headers @{ "Authorization" = "Bearer $STRIPE_KEY" } -Body $body

# Desabilitar webhook
Invoke-RestMethod -Uri "https://api.stripe.com/v1/webhook_endpoints/we_XXXXX" `
    -Method Post -Headers @{ "Authorization" = "Bearer $STRIPE_KEY" } `
    -Body @{ disabled = "true" }
```

---

## 7. Sistema de Licenças

### 7.1 Tipos de Licença

| Tipo | Contratos | Export | Suporte |
|------|-----------|--------|---------|
| Trial | 5 | Não | Não |
| Basic | 50 | Excel | Email |
| Pro | 500 | Excel, CSV | Prioritário |
| Enterprise | Ilimitado | Todos | Dedicado |

### 7.2 Fluxo de Validação

```
1. Usuário insere chave
   ↓
2. Frontend envia POST /api/validate-license
   ↓
3. Backend verifica:
   - Chave existe?
   - Status = active?
   - Revoked = false?
   - Não expirada?
   - Limite de ativações OK?
   ↓
4. Se válido: Retorna token JWT
   Se inválido: Retorna erro 403
   ↓
5. Frontend armazena token
   ↓
6. A cada 5 min: POST /api/check-license
   ↓
7. Se inválido: Bloqueia sistema
```

### 7.3 Endpoints de Licença

```
POST /api/validate-license
  Body: { "key": "XXXXX", "machine_id": "...", "app_version": "1.0.0" }
  Response: { "valid": true, "token": "...", "data": {...} }

POST /api/check-license
  Headers: Authorization: Bearer <token>
  Response: { "valid": true, "status": "active", "expires_at": "..." }
```

### 7.4 Gerar Licença via API

```powershell
$BACKEND = "https://ifrs16-backend-1051753255664.us-central1.run.app"

# Login admin
$login = Invoke-RestMethod -Uri "$BACKEND/api/auth/admin/login" -Method Post `
    -ContentType "application/json" `
    -Body '{"email":"fernandocostaxavier@gmail.com","password":"Master@2025!"}'

$token = $login.access_token

# Gerar licença
$body = @{
    customer_name = "Novo Cliente"
    email = "cliente@email.com"
    license_type = "basic"
    duration_months = 12
} | ConvertTo-Json

Invoke-RestMethod -Uri "$BACKEND/api/admin/generate-license" -Method Post `
    -Headers @{ "Authorization" = "Bearer $token" } `
    -ContentType "application/json" -Body $body
```

---

## 8. Painel Administrativo

### 8.1 Acessar o Admin

1. Acesse: https://ifrs16-app.web.app/admin.html
2. Login com credenciais admin
3. Funções disponíveis:
   - Gerar licenças
   - Revogar licenças
   - Reativar licenças
   - Buscar detalhes
   - Listar todas as licenças

### 8.2 Funcionalidades

#### Gerar Licença
- Nome do cliente
- Email
- Tipo (trial, basic, pro, enterprise)
- Duração em meses

#### Revogar Licença
- Insira a chave
- (Opcional) Motivo da revogação
- Clique em "Revogar"
- **Efeito**: Usuário é bloqueado em até 5 minutos

#### Reativar Licença
- Insira a chave de uma licença revogada
- Clique em "Reativar"
- **Efeito**: Usuário pode usar novamente

#### Buscar Licença
- Insira a chave
- Veja todos os detalhes:
  - Status, cliente, email
  - Data de criação e expiração
  - Número de ativações
  - Se está revogada

### 8.3 Endpoints Admin

```
POST /api/auth/admin/login
POST /api/admin/generate-license
POST /api/admin/revoke-license
POST /api/admin/reactivate-license
GET  /api/admin/license/{key}
GET  /api/admin/licenses
GET  /api/admin/users
```

---

## 9. Deploy e Manutenção

### 9.1 Deploy Frontend (Firebase)

```powershell
cd "c:\Projetos\IFRS 16"

# 1. Fazer alterações nos arquivos HTML/JS/CSS

# 2. Testar localmente (opcional)
# Abrir index.html no navegador

# 3. Deploy
firebase deploy --only hosting --project ifrs16-app

# 4. Verificar
# Acesse https://ifrs16-app.web.app
```

### 9.2 Deploy Backend (Cloud Run)

```powershell
cd "c:\Projetos\IFRS 16"

# 1. Fazer alterações no código Python

# 2. Build da imagem
cd backend
gcloud builds submit --tag gcr.io/ifrs16-app/ifrs16-backend --project ifrs16-app

# 3. Deploy
gcloud run deploy ifrs16-backend \
    --image gcr.io/ifrs16-app/ifrs16-backend \
    --platform managed \
    --region us-central1 \
    --project ifrs16-app

# 4. Atualizar variáveis (se necessário)
cd ..
gcloud run services update ifrs16-backend \
    --env-vars-file=cloud_run_env.yaml \
    --region=us-central1 \
    --project=ifrs16-app

# 5. Verificar
# Acesse https://ifrs16-backend-1051753255664.us-central1.run.app/health
```

### 9.3 Script de Deploy Completo

```powershell
# deploy_firebase.ps1

param(
    [string]$ProjectId = "ifrs16-app",
    [string]$Region = "us-central1",
    [string]$ServiceName = "ifrs16-backend",
    [switch]$SkipBuild = $false
)

Write-Host "=== DEPLOY IFRS16 ===" -ForegroundColor Cyan

# Backend
if (-not $SkipBuild) {
    Write-Host "Building backend..." -ForegroundColor Yellow
    Push-Location backend
    gcloud builds submit --tag gcr.io/$ProjectId/$ServiceName --project $ProjectId
    Pop-Location
}

Write-Host "Deploying backend..." -ForegroundColor Yellow
gcloud run deploy $ServiceName `
    --image gcr.io/$ProjectId/$ServiceName `
    --platform managed `
    --region $Region `
    --project $ProjectId

# Frontend
Write-Host "Deploying frontend..." -ForegroundColor Yellow
firebase deploy --only hosting --project $ProjectId

Write-Host "=== DEPLOY COMPLETE ===" -ForegroundColor Green
```

### 9.4 Manutenção de Rotina

#### Diária
- Verificar logs de erro no Cloud Run
- Monitorar métricas de uso

#### Semanal
- Verificar licenças expirando
- Analisar relatórios do Stripe

#### Mensal
- Atualizar dependências (pip, npm)
- Backup do banco de dados
- Revisar segurança

### 9.5 Comandos Úteis

```powershell
# Ver logs do backend
gcloud run services logs read ifrs16-backend --region=us-central1 --limit=50

# Ver logs em tempo real
gcloud run services logs tail ifrs16-backend --region=us-central1

# Verificar saúde do backend
Invoke-RestMethod https://ifrs16-backend-1051753255664.us-central1.run.app/health

# Testar endpoint de preços
Invoke-RestMethod https://ifrs16-backend-1051753255664.us-central1.run.app/api/payments/prices

# Listar licenças
$token = "..." # Obtenha via login admin
Invoke-RestMethod -Uri "https://ifrs16-backend-1051753255664.us-central1.run.app/api/admin/licenses" `
    -Headers @{ "Authorization" = "Bearer $token" }
```

---

## 10. MCP (Model Context Protocol)

### 10.1 O que é MCP?

MCP é um protocolo que permite que assistentes de IA (como o Cursor/Claude) interajam com serviços externos como Stripe, Firebase, etc.

### 10.2 MCPs Instalados

#### Stripe MCP
Permite interagir com a API do Stripe diretamente via comandos:
- Listar clientes, produtos, preços
- Criar pagamentos, invoices
- Gerenciar assinaturas
- Consultar documentação

### 10.3 Configuração do Stripe MCP

Localização: Configurado no Cursor IDE

Funcionalidades disponíveis:
- `list_customers` - Listar clientes
- `create_customer` - Criar cliente
- `list_products` - Listar produtos
- `create_product` - Criar produto
- `list_prices` - Listar preços
- `create_price` - Criar preço
- `list_invoices` - Listar faturas
- `create_invoice` - Criar fatura
- `list_subscriptions` - Listar assinaturas
- `cancel_subscription` - Cancelar assinatura
- `search_stripe_documentation` - Buscar na documentação

### 10.4 Usando MCP no Cursor

Os MCPs são usados automaticamente quando você pede ao assistente para interagir com Stripe. Exemplos:

- "Liste os clientes do Stripe"
- "Crie um produto no Stripe chamado X"
- "Verifique as assinaturas ativas"
- "Configure um webhook no Stripe"

---

## 11. Troubleshooting

### 11.1 Frontend não carrega

```powershell
# Verificar se o deploy foi feito
firebase hosting:channel:list

# Verificar DNS
nslookup ifrs16-app.web.app

# Forçar novo deploy
firebase deploy --only hosting --project ifrs16-app
```

### 11.2 Backend retorna erro 500

```powershell
# Ver logs
gcloud run services logs read ifrs16-backend --region=us-central1 --limit=100

# Verificar variáveis de ambiente
gcloud run services describe ifrs16-backend --region=us-central1

# Reiniciar (forçar novo deploy)
gcloud run deploy ifrs16-backend --image gcr.io/ifrs16-app/ifrs16-backend --region=us-central1
```

### 11.3 Licença não valida

Verificar no admin:
1. A licença existe?
2. Status é "active"?
3. Não está revogada?
4. Não expirou?
5. Limite de ativações não excedido?

```powershell
# Via API
$BACKEND = "https://ifrs16-backend-1051753255664.us-central1.run.app"
$token = "..." # Login admin primeiro

Invoke-RestMethod -Uri "$BACKEND/api/admin/license/CHAVE-AQUI" `
    -Headers @{ "Authorization" = "Bearer $token" }
```

### 11.4 Webhook não funciona

```powershell
# Verificar no Stripe Dashboard
# https://dashboard.stripe.com/webhooks

# Testar endpoint
Invoke-WebRequest -Uri "https://ifrs16-backend-1051753255664.us-central1.run.app/api/payments/webhook" `
    -Method Post -ContentType "application/json" -Body '{}'
# Deve retornar 400 (esperado sem assinatura válida)

# Verificar logs
gcloud run services logs read ifrs16-backend --region=us-central1 | Select-String "webhook"
```

### 11.5 CORS Error

```powershell
# Verificar se a origem está na lista de CORS
# Arquivo: backend/app/main.py

# Atualizar CORS_ORIGINS no cloud_run_env.yaml
# Exemplo: "https://ifrs16-app.web.app,https://ifrs16-app.firebaseapp.com"

# Redeployar
gcloud run services update ifrs16-backend --env-vars-file=cloud_run_env.yaml --region=us-central1
```

---

## 12. Referência de APIs

### 12.1 Autenticação

```
POST /api/auth/login
  Body: { "email": "...", "password": "..." }
  Response: { "access_token": "...", "token_type": "bearer" }

POST /api/auth/admin/login
  Body: { "email": "...", "password": "..." }
  Response: { "access_token": "...", "token_type": "bearer" }

GET /api/auth/me
  Headers: Authorization: Bearer <token>
  Response: { "id": "...", "email": "...", "name": "...", "is_admin": true }
```

### 12.2 Licenças (Público)

```
POST /api/validate-license
  Body: { "key": "XXXXX", "machine_id": "...", "app_version": "1.0.0" }
  Response: { "valid": true, "token": "...", "data": {...} }

POST /api/check-license
  Headers: Authorization: Bearer <license_token>
  Response: { "valid": true, "status": "active", "expires_at": "..." }
```

### 12.3 Admin

```
POST /api/admin/generate-license
  Headers: Authorization: Bearer <admin_token>
  Body: { "customer_name": "...", "email": "...", "license_type": "basic", "duration_months": 12 }

POST /api/admin/revoke-license
  Headers: Authorization: Bearer <admin_token>
  Body: { "key": "XXXXX", "reason": "..." }

POST /api/admin/reactivate-license
  Headers: Authorization: Bearer <admin_token>
  Body: { "key": "XXXXX" }

GET /api/admin/license/{key}
  Headers: Authorization: Bearer <admin_token>

GET /api/admin/licenses
  Headers: Authorization: Bearer <admin_token>
  Response: { "total": 5, "licenses": [...] }

GET /api/admin/users
  Headers: Authorization: Bearer <admin_token>
```

### 12.4 Pagamentos

```
GET /api/payments/prices
  Response: { "plans": [...] }

POST /api/payments/create-checkout
  Headers: Authorization: Bearer <user_token>
  Body: { "plan_type": "basic_monthly", "success_url": "...", "cancel_url": "..." }
  Response: { "checkout_url": "https://checkout.stripe.com/..." }

POST /api/payments/webhook
  (Chamado pelo Stripe)
```

### 12.5 Health Check

```
GET /health
  Response: { "status": "healthy", "timestamp": "..." }
```

---

## 📎 Arquivos de Referência

| Arquivo | Descrição |
|---------|-----------|
| `firebase.json` | Configuração do Firebase Hosting |
| `cloud_run_env.yaml` | Variáveis de ambiente do Cloud Run |
| `backend/Dockerfile` | Imagem Docker do backend |
| `deploy_firebase.ps1` | Script de deploy automatizado |
| `testar_sistema_completo.ps1` | Script de testes |

---

## 🔗 Links do Projeto

| Serviço | Link |
|---------|------|
| **Firebase Console** | https://console.firebase.google.com/project/ifrs16-app |
| **Google Cloud Console** | https://console.cloud.google.com/home/dashboard?project=ifrs16-app |
| **Cloud Run** | https://console.cloud.google.com/run?project=ifrs16-app |
| **Stripe Dashboard** | https://dashboard.stripe.com |
| **GitHub** | https://github.com/FernandoXavier02/IFRS-16 |

---

## 13. Controle de Gastos (Firebase / Google Cloud Billing)

### 13.1 Onde o custo do Firebase aparece?

O Firebase **cobra via Google Cloud Billing** do mesmo projeto (`ifrs16-app`).  
Ou seja: o local oficial para controlar custos é o **Billing do Google Cloud**.

- **Billing do projeto**: https://console.cloud.google.com/billing?project=ifrs16-app

### 13.2 Budget mensal + alertas (recomendado)

O jeito mais seguro é criar um **Budget** com alertas (ex.: 50%, 80%, 100% e previsão).

Você pode fazer isso de 2 formas:

- **Pelo Console**: Billing → Budgets & alerts  
- **Pelo script** (automático): `CONTROLAR_GASTOS_FIREBASE.ps1`

### 13.3 Script automático (1 clique)

Arquivo: `CONTROLAR_GASTOS_FIREBASE.ps1`

Exemplo (orçamento mensal de 50 na moeda do billing e limite de escala no Cloud Run):

```powershell
cd "C:\Projetos\IFRS 16"
.\CONTROLAR_GASTOS_FIREBASE.ps1 -BudgetAmount 50 -MaxInstances 2
```

O script faz:

- Cria **Budget mensal** para o projeto `ifrs16-app`
- Configura alertas: **50%**, **80%**, **100%** e **90% previsto**
- Aplica limite no Cloud Run: `max-instances` (evita picos)

### 13.4 Recomendação de limites no Cloud Run

Para “segurar” custo em caso de pico/abuso:

- **max-instances**: 1–2 (conforme necessidade)
- **min-instances**: 0 (scale-to-zero, custo ~0 sem tráfego)

### 13.5 Acompanhar consumo (caminho no console)

1. Abra o Firebase: https://console.firebase.google.com/project/ifrs16-app/overview  
2. Clique no ícone de engrenagem (⚙️) → **Usage and billing**
3. Para detalhamento por serviço: https://console.cloud.google.com/billing?project=ifrs16-app

---

**Documento gerado em:** 11 de Dezembro de 2025  
**Versão:** 1.0
