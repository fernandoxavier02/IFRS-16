# ✅ FASE 1.5 - ENDPOINTS STRIPE CONCLUÍDOS

**Data:** 19/12/2025 16:50 BRT
**Status:** Implementação completa - Aguardando testes

---

## 📋 RESUMO DAS ALTERAÇÕES

### 1. Router Stripe Criado ✅
**Arquivo:** `backend/app/routers/stripe.py`

**Endpoints implementados:**
- `POST /api/stripe/create-checkout-session` - Criar sessão de checkout
- `POST /api/stripe/create-portal-session` - Criar sessão do portal
- `GET /api/stripe/prices` - Listar preços ativos

---

### 2. Main.py Atualizado ✅
**Arquivo:** `backend/app/main.py`

**Alterações:**
- Importado `stripe_router`
- Registrado router: `app.include_router(stripe_router)`

---

## 🔌 ENDPOINTS DISPONÍVEIS

### 1. POST /api/stripe/create-checkout-session

**Descrição:** Cria uma sessão de checkout do Stripe para o usuário assinar um plano.

**Autenticação:** Bearer Token (JWT)

**Request Body:**
```json
{
  "price_id": "price_1234567890",
  "success_url": "https://fxstudioai.com/dashboard?session_id={CHECKOUT_SESSION_ID}",
  "cancel_url": "https://fxstudioai.com/dashboard?canceled=true"
}
```

**Response (200 OK):**
```json
{
  "session_id": "cs_test_1234567890",
  "url": "https://checkout.stripe.com/c/pay/cs_test_1234567890"
}
```

**Funcionalidades:**
- ✅ Cria customer no Stripe se não existir
- ✅ Salva `stripe_customer_id` no usuário
- ✅ Cria sessão de checkout com o price_id fornecido
- ✅ Permite códigos promocionais
- ✅ Coleta endereço de cobrança
- ✅ Retorna URL para redirecionar usuário

**Erros:**
- `400` - Erro do Stripe (price_id inválido, etc.)
- `401` - Token JWT inválido ou ausente
- `500` - Erro interno do servidor

---

### 2. POST /api/stripe/create-portal-session

**Descrição:** Cria uma sessão do portal do cliente Stripe para gerenciar assinatura.

**Autenticação:** Bearer Token (JWT)

**Query Parameters (opcional):**
- `return_url` - URL para retornar após gerenciar assinatura

**Request:**
```bash
POST /api/stripe/create-portal-session?return_url=https://fxstudioai.com/dashboard
```

**Response (200 OK):**
```json
{
  "url": "https://billing.stripe.com/p/session/test_1234567890"
}
```

**Funcionalidades:**
- ✅ Verifica se usuário tem `stripe_customer_id`
- ✅ Cria sessão do portal do cliente
- ✅ Permite gerenciar método de pagamento
- ✅ Permite ver histórico de faturas
- ✅ Permite cancelar assinatura
- ✅ Retorna URL para redirecionar usuário

**Erros:**
- `400` - Usuário não possui conta no Stripe
- `401` - Token JWT inválido ou ausente
- `500` - Erro interno do servidor

---

### 3. GET /api/stripe/prices

**Descrição:** Lista todos os preços ativos configurados no Stripe.

**Autenticação:** Não requerida (público)

**Response (200 OK):**
```json
{
  "prices": [
    {
      "id": "price_basic_monthly",
      "product_id": "prod_basic",
      "product_name": "Plano Básico",
      "unit_amount": 29900,
      "currency": "brl",
      "recurring": {
        "interval": "month",
        "interval_count": 1
      }
    },
    {
      "id": "price_pro_yearly",
      "product_id": "prod_pro",
      "product_name": "Plano Pro",
      "unit_amount": 499900,
      "currency": "brl",
      "recurring": {
        "interval": "year",
        "interval_count": 1
      }
    }
  ]
}
```

**Funcionalidades:**
- ✅ Lista preços ativos do Stripe
- ✅ Expande informações do produto
- ✅ Útil para frontend exibir planos

---

## 🧪 PLANO DE TESTES

### Pré-requisitos:
1. ✅ Backend rodando: `uvicorn app.main:app --reload`
2. ✅ Stripe API Key configurada no `.env`
3. ✅ Usuário registrado e autenticado (JWT token)

---

### Teste 1: Criar Checkout Session

**1.1 Fazer login e obter token:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "joao@empresa.com",
    "password": "Senha123!"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user_type": "user"
}
```

**1.2 Criar sessão de checkout:**
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X POST http://localhost:8000/api/stripe/create-checkout-session \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "price_id": "price_1234567890"
  }'
```

**Response Esperada (200 OK):**
```json
{
  "session_id": "cs_test_...",
  "url": "https://checkout.stripe.com/c/pay/cs_test_..."
}
```

**Validações:**
- ✅ Status 200 OK
- ✅ `session_id` presente
- ✅ `url` presente e válida
- ✅ Customer criado no Stripe
- ✅ `stripe_customer_id` salvo no usuário

---

### Teste 2: Criar Portal Session

**Request:**
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X POST http://localhost:8000/api/stripe/create-portal-session \
  -H "Authorization: Bearer $TOKEN"
```

**Response Esperada (200 OK):**
```json
{
  "url": "https://billing.stripe.com/p/session/test_..."
}
```

**Validações:**
- ✅ Status 200 OK
- ✅ `url` presente e válida
- ✅ Portal acessível pelo usuário

---

### Teste 3: Listar Preços

**Request:**
```bash
curl -X GET http://localhost:8000/api/stripe/prices
```

**Response Esperada (200 OK):**
```json
{
  "prices": [
    {
      "id": "price_...",
      "product_id": "prod_...",
      "product_name": "Plano Básico",
      "unit_amount": 29900,
      "currency": "brl",
      "recurring": {
        "interval": "month",
        "interval_count": 1
      }
    }
  ]
}
```

**Validações:**
- ✅ Status 200 OK
- ✅ Lista de preços retornada
- ✅ Informações completas de cada preço

---

### Teste 4: Erro - Portal sem Customer

**Cenário:** Usuário novo sem `stripe_customer_id`

**Request:**
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X POST http://localhost:8000/api/stripe/create-portal-session \
  -H "Authorization: Bearer $TOKEN"
```

**Response Esperada (400 Bad Request):**
```json
{
  "detail": "Usuário não possui conta no Stripe. Assine um plano primeiro."
}
```

**Validações:**
- ✅ Status 400
- ✅ Mensagem de erro clara

---

### Teste 5: Erro - Token Inválido

**Request:**
```bash
curl -X POST http://localhost:8000/api/stripe/create-checkout-session \
  -H "Authorization: Bearer token_invalido" \
  -H "Content-Type: application/json" \
  -d '{
    "price_id": "price_1234567890"
  }'
```

**Response Esperada (401 Unauthorized):**
```json
{
  "detail": "Token inválido ou expirado"
}
```

**Validações:**
- ✅ Status 401
- ✅ Autenticação bloqueada

---

## 🔗 INTEGRAÇÃO COM FRONTEND

### Dashboard - Botão "Assinar Plano"

```javascript
async function subscribeToPlan(priceId) {
  const token = localStorage.getItem('ifrs16_auth_token');
  
  const response = await fetch(`${API_URL}/api/stripe/create-checkout-session`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      price_id: priceId,
      success_url: `${window.location.origin}/dashboard?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${window.location.origin}/dashboard?canceled=true`
    })
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Redirecionar para checkout
    window.location.href = data.url;
  } else {
    alert('Erro ao criar sessão de checkout: ' + data.detail);
  }
}
```

---

### Dashboard - Botão "Gerenciar Assinatura"

```javascript
async function manageSubscription() {
  const token = localStorage.getItem('ifrs16_auth_token');
  
  const response = await fetch(`${API_URL}/api/stripe/create-portal-session`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Redirecionar para portal
    window.location.href = data.url;
  } else {
    alert('Erro ao abrir portal: ' + data.detail);
  }
}
```

---

### Landing Page - Listar Planos

```javascript
async function loadPrices() {
  const response = await fetch(`${API_URL}/api/stripe/prices`);
  const data = await response.json();
  
  if (response.ok) {
    data.prices.forEach(price => {
      console.log(`${price.product_name}: R$ ${price.unit_amount / 100}`);
    });
  }
}
```

---

## 📊 CHECKLIST DE VALIDAÇÃO

### Backend:
- [x] Router Stripe criado
- [x] Endpoint `create-checkout-session` implementado
- [x] Endpoint `create-portal-session` implementado
- [x] Endpoint `prices` implementado
- [x] Router registrado no `main.py`
- [ ] ⚠️ Testes executados (aguardando backend online)

### Funcionalidades:
- [x] Criação de customer no Stripe
- [x] Salvamento de `stripe_customer_id`
- [x] Validação de autenticação JWT
- [x] Tratamento de erros Stripe
- [x] URLs de sucesso/cancelamento configuráveis
- [x] Códigos promocionais habilitados
- [x] Coleta de endereço de cobrança

---

## 🚀 PRÓXIMOS PASSOS

### Testar Endpoints (quando backend estiver online):
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Configurar Stripe (se necessário):
1. Criar produtos no Stripe Dashboard
2. Criar preços para cada produto
3. Copiar price_ids para usar nos testes
4. Configurar webhook para eventos de assinatura

### Partir para Frontend (Fase 2):
1. Atualizar `landing.html` → link para `auth-choice.html`
2. Atualizar `register.html` → campo empresa + integração
3. Atualizar `login.html` → JWT + redirecionamento
4. Criar `dashboard.html` → botões Stripe funcionais

---

## 📞 COMANDOS ÚTEIS

### Testar endpoint de checkout:
```bash
# Obter token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test123!"}' \
  | jq -r '.access_token')

# Criar checkout session
curl -X POST http://localhost:8000/api/stripe/create-checkout-session \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"price_id":"price_1234567890"}'
```

### Verificar documentação da API:
```
http://localhost:8000/docs
```

### Ver logs do Stripe:
```
https://dashboard.stripe.com/test/logs
```

---

**Fase 1.5 Stripe: ✅ CONCLUÍDA**
**Endpoints:** 3 endpoints criados e registrados
**Próximo:** Fase 2 - Frontend (register.html, login.html, dashboard.html)
