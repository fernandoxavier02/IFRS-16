# PLANO DE IMPLEMENTAÇÃO - ÁREA DE CLIENTES

## 📊 Status Atual
- ✅ Backend: Autenticação, User, Subscription, License, Stripe
- ✅ Frontend: auth-choice.html, login.html, register.html, dashboard.html (básico)
- ⚠️ Falta: Integração completa frontend-backend

## 🎯 Objetivo
Criar fluxo completo: Registro → Login → Dashboard → Assinatura Stripe

## 📝 Fluxo Detalhado

### 1. LANDING PAGE → AUTH-CHOICE
- Botão "Minha Conta" redireciona para `auth-choice.html`
- Verificar se já está logado (token existe) → redirecionar para dashboard

### 2. AUTH-CHOICE → REGISTRO ou LOGIN
- **Registro**: Criar conta SEM assinatura
- **Login**: Autenticar e ir para dashboard

### 3. REGISTRO (register.html)
**Campos necessários:**
- Nome completo
- Email
- Senha (mínimo 8 caracteres)
- Nome da empresa
- Aceitar termos

**Endpoint backend:** `POST /api/auth/user/register`
```json
{
  "name": "João Silva",
  "email": "joao@empresa.com",
  "password": "senha123",
  "company_name": "Empresa LTDA"
}
```

**Resposta:**
```json
{
  "message": "Conta criada com sucesso",
  "user_id": "uuid"
}
```

**Após registro:**
- Mostrar mensagem de sucesso
- Redirecionar para login.html após 2s

### 4. LOGIN (login.html)
**Endpoint backend:** `POST /api/auth/user/login`
```json
{
  "email": "joao@empresa.com",
  "password": "senha123"
}
```

**Resposta:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user_type": "user"
}
```

**Após login:**
- Salvar token no localStorage: `ifrs16_auth_token`
- Salvar user_type: `ifrs16_user_type = "user"`
- Redirecionar para dashboard.html

### 5. DASHBOARD (dashboard.html)

**Ao carregar:**
1. Verificar se tem token
   - Se NÃO → redirecionar para auth-choice.html
   - Se SIM → continuar

2. Buscar dados do usuário: `GET /api/user/profile`
   ```
   Headers: Authorization: Bearer {token}
   ```
   
   **Resposta:**
   ```json
   {
     "id": "uuid",
     "name": "João Silva",
     "email": "joao@empresa.com",
     "company_name": "Empresa LTDA",
     "created_at": "2025-01-01T00:00:00",
     "is_active": true
   }
   ```

3. Buscar assinatura: `GET /api/user/subscription`
   ```
   Headers: Authorization: Bearer {token}
   ```
   
   **Resposta (COM assinatura):**
   ```json
   {
     "id": "uuid",
     "status": "active",
     "plan_type": "monthly",
     "stripe_subscription_id": "sub_xxx",
     "current_period_start": "2025-01-01",
     "current_period_end": "2025-02-01",
     "license": {
       "license_type": "pro",
       "status": "active",
       "key": "IFRS16-XXXX-XXXX",
       "expires_at": "2025-02-01"
     }
   }
   ```
   
   **Resposta (SEM assinatura):**
   ```json
   null
   ```

**Exibição no Dashboard:**

#### A. SEM ASSINATURA ATIVA:
```
┌─────────────────────────────────────┐
│ 👤 Bem-vindo, João Silva            │
│ 📧 joao@empresa.com                 │
│ 🏢 Empresa LTDA                     │
├─────────────────────────────────────┤
│ ⚠️ NENHUMA ASSINATURA ATIVA         │
│                                     │
│ Para acessar o Engine IFRS 16,     │
│ você precisa de uma assinatura.    │
│                                     │
│ [🚀 ASSINAR AGORA]                  │
│                                     │
│ Planos disponíveis:                │
│ • Basic: R$ 99/mês                 │
│ • Pro: R$ 199/mês                  │
│ • Enterprise: Sob consulta         │
└─────────────────────────────────────┘
```

#### B. COM ASSINATURA ATIVA:
```
┌─────────────────────────────────────┐
│ 👤 João Silva                       │
│ 📧 joao@empresa.com                 │
│ 🏢 Empresa LTDA                     │
├─────────────────────────────────────┤
│ ✅ ASSINATURA ATIVA                 │
│                                     │
│ 📦 Plano: Pro                       │
│ 💳 Status: Ativo                    │
│ 📅 Início: 01/01/2025              │
│ 🔄 Próxima cobrança: 01/02/2025    │
│ 🔑 Licença: IFRS16-XXXX-XXXX       │
│                                     │
│ [🎯 ACESSAR SISTEMA]                │
│ [⚙️ GERENCIAR ASSINATURA]          │
└─────────────────────────────────────┘
```

### 6. BOTÃO "ASSINAR AGORA"

**Endpoint:** `POST /api/stripe/create-checkout-session`
```json
{
  "price_id": "price_xxx",
  "success_url": "https://fxstudioai.com/dashboard?success=true",
  "cancel_url": "https://fxstudioai.com/dashboard?canceled=true"
}
```

**Resposta:**
```json
{
  "checkout_url": "https://checkout.stripe.com/xxx"
}
```

**Ação:**
- Redirecionar para checkout_url
- Stripe processa pagamento
- Webhook atualiza assinatura no banco
- Usuário retorna para dashboard com assinatura ativa

### 7. BOTÃO "GERENCIAR ASSINATURA"

**Endpoint:** `POST /api/stripe/create-portal-session`
```
Headers: Authorization: Bearer {token}
```

**Resposta:**
```json
{
  "portal_url": "https://billing.stripe.com/xxx"
}
```

**Ação:**
- Redirecionar para portal_url
- Cliente pode:
  - Atualizar forma de pagamento
  - Cancelar assinatura
  - Ver histórico de faturas

## 🔒 PROTEÇÃO DE ROTAS

**Arquivo:** `assets/js/route-protection.js`

```javascript
// Verificar autenticação em todas as páginas protegidas
function checkAuth() {
    const token = localStorage.getItem('ifrs16_auth_token');
    const protectedPages = ['dashboard.html', 'Calculadora_IFRS16_Deploy.html'];
    const currentPage = window.location.pathname.split('/').pop();
    
    if (protectedPages.includes(currentPage) && !token) {
        window.location.href = 'auth-choice.html';
        return false;
    }
    return true;
}

// Executar ao carregar página
checkAuth();
```

## 📋 CHECKLIST DE IMPLEMENTAÇÃO

### Backend (Verificar se existe):
- [x] POST /api/auth/user/register
- [x] POST /api/auth/user/login
- [x] GET /api/user/profile
- [x] GET /api/user/subscription
- [x] POST /api/stripe/create-checkout-session
- [x] POST /api/stripe/create-portal-session

### Frontend:
- [x] auth-choice.html (criado)
- [ ] Atualizar register.html com campo empresa
- [ ] Atualizar login.html com integração backend
- [ ] Atualizar dashboard.html com dados reais
- [ ] Criar route-protection.js
- [ ] Atualizar landing.html (botão Minha Conta)

### Testes:
- [ ] Registro de novo usuário
- [ ] Login com credenciais válidas
- [ ] Dashboard sem assinatura
- [ ] Fluxo de checkout Stripe
- [ ] Dashboard com assinatura ativa
- [ ] Gerenciar assinatura no Stripe Portal
- [ ] Logout e limpeza de sessão

## 🚀 PRÓXIMOS PASSOS

1. Verificar endpoints do backend
2. Atualizar register.html
3. Atualizar login.html
4. Atualizar dashboard.html
5. Criar route-protection.js
6. Atualizar landing.html
7. Testar fluxo completo
8. Deploy

## 📞 SUPORTE

Em caso de dúvidas sobre a implementação, consultar:
- Backend: `backend/app/routers/auth.py`
- Backend: `backend/app/routers/user_dashboard.py`
- Backend: `backend/app/services/stripe_service.py`
