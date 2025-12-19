# 🏗️ ARQUITETURA E INTEGRAÇÃO - SISTEMA ÁREA DE CLIENTES

## 📊 VISÃO GERAL DA ARQUITETURA

```
┌─────────────────────────────────────────────────────────────────┐
│                         USUÁRIO FINAL                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FIREBASE HOSTING                              │
│  URL: https://fxstudioai.com                                    │
│       https://ifrs16-app.web.app                                │
│                                                                  │
│  Arquivos Servidos:                                             │
│  ├─ landing.html (página inicial)                               │
│  ├─ auth-choice.html (escolha login/registro) ✅ NOVO           │
│  ├─ login.html (autenticação)                                   │
│  ├─ register.html (cadastro)                                    │
│  ├─ dashboard.html (área do cliente)                            │
│  ├─ Calculadora_IFRS16_Deploy.html (sistema principal)          │
│  └─ assets/ (CSS, JS, imagens)                                  │
│      ├─ js/config.js (configuração API)                         │
│      ├─ js/auth.js (funções de autenticação)                    │
│      └─ css/theme-neon.css (tema visual)                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTPS Requests
                         │ (JWT Token no Header)
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GOOGLE CLOUD RUN                              │
│  URL: https://ifrs16-backend-1051753255664.us-central1.run.app  │
│                                                                  │
│  Backend FastAPI:                                               │
│  ├─ /api/auth/register (POST) - Criar conta                    │
│  ├─ /api/auth/login (POST) - Autenticar                        │
│  ├─ /api/auth/me (GET) - Dados do usuário                      │
│  ├─ /api/user/profile (GET) - Perfil completo                  │
│  ├─ /api/user/subscription (GET) - Assinatura ativa            │
│  ├─ /api/stripe/create-checkout-session (POST) - Pagamento     │
│  └─ /api/stripe/create-portal-session (POST) - Gerenciar       │
│                                                                  │
│  Autenticação: JWT (Bearer Token)                               │
│  CORS: fxstudioai.com, ifrs16-app.web.app                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ├─────────────────┬──────────────────┐
                         │                 │                  │
                         ▼                 ▼                  ▼
              ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
              │  PostgreSQL  │  │    Stripe    │  │   SMTP/Email │
              │   Database   │  │   Payments   │  │   Service    │
              │              │  │              │  │              │
              │ • Users      │  │ • Checkout   │  │ • Welcome    │
              │ • Licenses   │  │ • Billing    │  │ • Invoices   │
              │ • Subscript. │  │ • Webhooks   │  │ • Alerts     │
              └──────────────┘  └──────────────┘  └──────────────┘
```

## 🔄 FLUXO DE DADOS DETALHADO

### 1️⃣ LANDING PAGE → AUTH-CHOICE

**Arquivo:** `landing.html`
**Ação:** Usuário clica em "Minha Conta"

```javascript
// landing.html - Atualizar link do botão
<a href="auth-choice.html" class="btn-nav btn-nav-outline">Minha Conta</a>
```

**Arquivo:** `auth-choice.html` ✅ **JÁ CRIADO**
**Verificação automática:**
```javascript
const token = localStorage.getItem('ifrs16_auth_token');
if (token) {
    window.location.href = 'dashboard.html'; // Já logado
}
```

---

### 2️⃣ REGISTRO DE NOVO USUÁRIO

**Arquivo:** `register.html`
**Campos do formulário:**
- Nome completo
- Email
- Senha (mínimo 8 caracteres)
- Nome da empresa
- Aceitar termos

**JavaScript (a implementar):**
```javascript
async function handleRegister(event) {
    event.preventDefault();
    
    const data = {
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        password: document.getElementById('password').value,
        company_name: document.getElementById('company').value
    };
    
    const response = await fetch(`${CONFIG.API_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    
    if (response.ok) {
        alert('Conta criada com sucesso! Faça login.');
        window.location.href = 'login.html';
    }
}
```

**Backend Endpoint:** `POST /api/auth/register`
**Status:** ✅ **JÁ EXISTE** (`backend/app/routers/auth.py:181-222`)

**Request:**
```json
{
  "name": "João Silva",
  "email": "joao@empresa.com",
  "password": "Senha123!",
  "company_name": "Empresa LTDA"
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "name": "João Silva",
  "email": "joao@empresa.com",
  "is_active": true,
  "email_verified": false,
  "created_at": "2025-12-19T19:00:00Z"
}
```

**⚠️ ATENÇÃO:** Backend atual NÃO tem campo `company_name` no modelo User!
**AÇÃO NECESSÁRIA:** Adicionar campo `company_name` ao modelo User

---

### 3️⃣ LOGIN DE USUÁRIO

**Arquivo:** `login.html`
**Campos do formulário:**
- Email
- Senha

**JavaScript (a implementar):**
```javascript
async function handleLogin(event) {
    event.preventDefault();
    
    const data = {
        email: document.getElementById('email').value,
        password: document.getElementById('password').value
    };
    
    const response = await fetch(`${CONFIG.API_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    
    if (response.ok) {
        const result = await response.json();
        
        // Salvar token e tipo de usuário
        localStorage.setItem('ifrs16_auth_token', result.access_token);
        localStorage.setItem('ifrs16_user_type', result.user_type);
        
        // Redirecionar para dashboard
        window.location.href = 'dashboard.html';
    }
}
```

**Backend Endpoint:** `POST /api/auth/login`
**Status:** ✅ **JÁ EXISTE** (`backend/app/routers/auth.py:225-276`)

**Request:**
```json
{
  "email": "joao@empresa.com",
  "password": "Senha123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user_type": "user"
}
```

---

### 4️⃣ DASHBOARD - ÁREA DO CLIENTE

**Arquivo:** `dashboard.html`
**Proteção de Rota:**
```javascript
// Executar ao carregar a página
window.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('ifrs16_auth_token');
    
    if (!token) {
        window.location.href = 'auth-choice.html';
        return;
    }
    
    await loadUserData();
    await loadSubscriptionData();
});
```

#### 4.1 Carregar Dados do Usuário

**JavaScript:**
```javascript
async function loadUserData() {
    const token = localStorage.getItem('ifrs16_auth_token');
    
    const response = await fetch(`${CONFIG.API_URL}/api/user/profile`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.ok) {
        const user = await response.json();
        
        // Exibir dados na tela
        document.getElementById('userName').textContent = user.name;
        document.getElementById('userEmail').textContent = user.email;
        document.getElementById('userCompany').textContent = user.company_name || 'Não informado';
        document.getElementById('userSince').textContent = formatDate(user.created_at);
    } else if (response.status === 401) {
        // Token inválido - fazer logout
        localStorage.clear();
        window.location.href = 'auth-choice.html';
    }
}
```

**Backend Endpoint:** `GET /api/user/profile`
**Status:** ✅ **JÁ EXISTE** (`backend/app/routers/user_dashboard.py:32-45`)

**Response (200 OK):**
```json
{
  "id": "uuid",
  "name": "João Silva",
  "email": "joao@empresa.com",
  "company_name": "Empresa LTDA",
  "is_active": true,
  "email_verified": false,
  "created_at": "2025-12-19T19:00:00Z"
}
```

#### 4.2 Carregar Dados da Assinatura

**JavaScript:**
```javascript
async function loadSubscriptionData() {
    const token = localStorage.getItem('ifrs16_auth_token');
    
    const response = await fetch(`${CONFIG.API_URL}/api/user/subscription`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.ok) {
        const subscription = await response.json();
        
        if (subscription) {
            // TEM ASSINATURA ATIVA
            showActiveSubscription(subscription);
        } else {
            // SEM ASSINATURA
            showNoSubscription();
        }
    }
}

function showActiveSubscription(sub) {
    document.getElementById('noSubscription').classList.add('hidden');
    document.getElementById('activeSubscription').classList.remove('hidden');
    
    document.getElementById('planName').textContent = sub.license.license_type.toUpperCase();
    document.getElementById('planStatus').textContent = sub.status;
    document.getElementById('planStart').textContent = formatDate(sub.current_period_start);
    document.getElementById('planNext').textContent = formatDate(sub.current_period_end);
    document.getElementById('licenseKey').textContent = sub.license.key;
}

function showNoSubscription() {
    document.getElementById('activeSubscription').classList.add('hidden');
    document.getElementById('noSubscription').classList.remove('hidden');
}
```

**Backend Endpoint:** `GET /api/user/subscription`
**Status:** ✅ **JÁ EXISTE** (`backend/app/routers/user_dashboard.py:88-127`)

**Response COM assinatura (200 OK):**
```json
{
  "id": "uuid",
  "status": "active",
  "plan_type": "monthly",
  "stripe_subscription_id": "sub_xxx",
  "current_period_start": "2025-12-19T00:00:00Z",
  "current_period_end": "2026-01-19T00:00:00Z",
  "license": {
    "id": "uuid",
    "key": "IFRS16-XXXX-XXXX-XXXX",
    "license_type": "pro",
    "status": "active",
    "expires_at": "2026-01-19T00:00:00Z",
    "max_contracts": 20
  }
}
```

**Response SEM assinatura (200 OK):**
```json
null
```

---

### 5️⃣ CRIAR ASSINATURA (STRIPE CHECKOUT)

**Botão no Dashboard:**
```html
<button onclick="createCheckoutSession('price_basic_monthly')" class="btn btn-primary">
    Assinar Plano Basic - R$ 99/mês
</button>
```

**JavaScript:**
```javascript
async function createCheckoutSession(priceId) {
    const token = localStorage.getItem('ifrs16_auth_token');
    
    const response = await fetch(`${CONFIG.API_URL}/api/stripe/create-checkout-session`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
            price_id: priceId,
            success_url: `${window.location.origin}/dashboard?success=true`,
            cancel_url: `${window.location.origin}/dashboard?canceled=true`
        })
    });
    
    if (response.ok) {
        const result = await response.json();
        window.location.href = result.checkout_url;
    }
}
```

**Backend Endpoint:** `POST /api/stripe/create-checkout-session`
**Status:** ⚠️ **VERIFICAR SE EXISTE**

**Request:**
```json
{
  "price_id": "price_1234567890",
  "success_url": "https://fxstudioai.com/dashboard?success=true",
  "cancel_url": "https://fxstudioai.com/dashboard?canceled=true"
}
```

**Response (200 OK):**
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_xxx"
}
```

**Fluxo Stripe:**
1. Usuário é redirecionado para Stripe Checkout
2. Preenche dados de pagamento
3. Stripe processa pagamento
4. Stripe envia webhook para backend
5. Backend cria/atualiza Subscription e License
6. Usuário retorna para `dashboard?success=true`

---

### 6️⃣ GERENCIAR ASSINATURA (STRIPE PORTAL)

**Botão no Dashboard:**
```html
<button onclick="openBillingPortal()" class="btn btn-secondary">
    Gerenciar Assinatura
</button>
```

**JavaScript:**
```javascript
async function openBillingPortal() {
    const token = localStorage.getItem('ifrs16_auth_token');
    
    const response = await fetch(`${CONFIG.API_URL}/api/stripe/create-portal-session`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    
    if (response.ok) {
        const result = await response.json();
        window.location.href = result.portal_url;
    }
}
```

**Backend Endpoint:** `POST /api/stripe/create-portal-session`
**Status:** ⚠️ **VERIFICAR SE EXISTE**

**Response (200 OK):**
```json
{
  "portal_url": "https://billing.stripe.com/p/session/xxx"
}
```

---

## 🔐 AUTENTICAÇÃO E SEGURANÇA

### JWT Token Flow

1. **Login bem-sucedido:**
   - Backend gera JWT token
   - Token contém: `user_id`, `email`, `user_type`, `exp` (expiração)
   - Frontend salva em `localStorage.setItem('ifrs16_auth_token', token)`

2. **Requisições autenticadas:**
   ```javascript
   headers: {
       'Authorization': `Bearer ${token}`
   }
   ```

3. **Verificação no backend:**
   - Middleware `get_current_user` valida token
   - Extrai dados do usuário
   - Retorna 401 se inválido/expirado

4. **Logout:**
   ```javascript
   localStorage.clear();
   window.location.href = 'auth-choice.html';
   ```

### CORS Configuration

**Backend (`config.py`):**
```python
CORS_ORIGINS = "https://fxstudioai.com,https://ifrs16-app.web.app,https://ifrs16-app.firebaseapp.com"
```

**Frontend (`config.js`):**
```javascript
const getApiUrl = () => {
    if (hostname.includes('fxstudioai.com') || 
        hostname.includes('web.app')) {
        return 'https://ifrs16-backend-1051753255664.us-central1.run.app';
    }
    return 'http://localhost:8000'; // Desenvolvimento
};
```

---

## 📦 MODELO DE DADOS

### User (PostgreSQL)
```python
class User(Base):
    id: UUID
    email: str (unique)
    name: str
    password_hash: str
    company_name: str  # ⚠️ ADICIONAR
    stripe_customer_id: str (nullable)
    is_active: bool
    email_verified: bool
    created_at: datetime
    last_login: datetime (nullable)
```

### Subscription (PostgreSQL)
```python
class Subscription(Base):
    id: UUID
    user_id: UUID (FK → User)
    license_id: UUID (FK → License)
    stripe_subscription_id: str
    status: SubscriptionStatus (active, past_due, cancelled, etc.)
    plan_type: PlanType (monthly, yearly, lifetime)
    current_period_start: datetime
    current_period_end: datetime
    created_at: datetime
```

### License (PostgreSQL)
```python
class License(Base):
    id: UUID
    key: str (unique, formato: IFRS16-XXXX-XXXX-XXXX)
    license_type: LicenseType (trial, basic, pro, enterprise)
    status: LicenseStatus (active, suspended, expired, cancelled)
    user_id: UUID (FK → User)
    max_contracts: int
    expires_at: datetime (nullable)
    created_at: datetime
```

---

## 🚀 CHECKLIST DE IMPLEMENTAÇÃO

### Backend:
- [x] POST /api/auth/register
- [x] POST /api/auth/login
- [x] GET /api/user/profile
- [x] GET /api/user/subscription
- [ ] ⚠️ Adicionar campo `company_name` ao modelo User
- [ ] ⚠️ Verificar POST /api/stripe/create-checkout-session
- [ ] ⚠️ Verificar POST /api/stripe/create-portal-session
- [ ] ⚠️ Atualizar RegisterRequest schema para incluir company_name

### Frontend:
- [x] auth-choice.html (criado)
- [ ] Atualizar register.html com campo empresa e integração
- [ ] Atualizar login.html com JWT e redirecionamento
- [ ] Reescrever dashboard.html completo com dados reais
- [ ] Atualizar landing.html (botão Minha Conta → auth-choice.html)
- [ ] Criar route-protection.js (verificação automática)

### Deploy:
- [ ] Atualizar variáveis de ambiente no Cloud Run
- [ ] Deploy backend no Cloud Run
- [ ] Deploy frontend no Firebase Hosting
- [ ] Testar fluxo completo em produção

---

## 🔧 PRÓXIMOS PASSOS IMEDIATOS

### 1. Adicionar campo company_name ao backend
**Arquivo:** `backend/app/models.py`
```python
class User(Base):
    # ... campos existentes ...
    company_name = Column(String(255), nullable=True)
```

**Criar migração Alembic:**
```bash
cd backend
alembic revision --autogenerate -m "add_company_name_to_users"
alembic upgrade head
```

### 2. Atualizar RegisterRequest schema
**Arquivo:** `backend/app/schemas.py`
```python
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    company_name: Optional[str] = None
```

### 3. Atualizar register.html
- Adicionar campo "Nome da Empresa"
- Implementar função handleRegister()
- Conectar com API

### 4. Atualizar login.html
- Implementar função handleLogin()
- Salvar token JWT
- Redirecionar para dashboard

### 5. Reescrever dashboard.html
- Verificar autenticação
- Carregar dados do usuário
- Carregar dados da assinatura
- Exibir interface adequada (com/sem assinatura)
- Botões de ação (Assinar/Gerenciar/Acessar Sistema)

---

## 📞 CONTATOS E URLS

- **Frontend Produção:** https://fxstudioai.com
- **Frontend Firebase:** https://ifrs16-app.web.app
- **Backend Cloud Run:** https://ifrs16-backend-1051753255664.us-central1.run.app
- **Firebase Project:** ifrs16-app
- **Stripe Dashboard:** https://dashboard.stripe.com

---

**Última Atualização:** 19/12/2025 16:30 BRT
**Status:** Arquitetura mapeada, pronta para implementação
