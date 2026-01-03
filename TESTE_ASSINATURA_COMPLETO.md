# 🧪 Guia Completo de Teste de Assinatura - IFRS 16

**Data:** 2026-01-03  
**Objetivo:** Validar fluxo completo de assinatura (Frontend → Backend → Banco de Dados)

---

## 📋 Pré-requisitos

### 1. Ambiente Preparado

- [ ] Backend rodando (local ou produção)
- [ ] Frontend acessível (local ou produção)
- [ ] Stripe configurado (modo teste)
- [ ] Banco de dados limpo (opcional, mas recomendado)
- [ ] Email SMTP configurado

### 2. URLs de Teste

| Ambiente | Frontend | Backend | Stripe Dashboard |
|----------|----------|---------|-----------------|
| **Local** | http://localhost:3000 | http://localhost:8000 | https://dashboard.stripe.com/test |
| **Produção** | https://fxstudioai.com | https://ifrs16-backend-ox4zylcs5a-rj.a.run.app | https://dashboard.stripe.com |

### 3. Credenciais de Teste Stripe

```
Cartão de Teste: 4242 4242 4242 4242
Data: 12/34
CVC: 123
CEP: 12345
```

---

## 🎯 Fluxo de Teste Completo

### FASE 1: Preparação e Verificação Inicial

#### 1.1 Verificar Backend

```bash
# Verificar se backend está rodando
curl https://ifrs16-backend-ox4zylcs5a-rj.a.run.app/health

# Esperado: {"status":"healthy","environment":"production"}
```

**Verificações:**
- [ ] Backend responde 200 OK
- [ ] Health check retorna `healthy`
- [ ] Logs do backend acessíveis

#### 1.2 Verificar Frontend

```bash
# Acessar página de preços
# URL: https://fxstudioai.com/pricing.html
```

**Verificações:**
- [ ] Página carrega sem erros
- [ ] Planos exibidos corretamente
- [ ] Botões "Assinar" visíveis
- [ ] Console do navegador sem erros (F12)

#### 1.3 Verificar Banco de Dados

```sql
-- Conectar ao Supabase e verificar estado inicial
SELECT 
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM licenses) as total_licenses,
    (SELECT COUNT(*) FROM subscriptions) as total_subscriptions;
```

**Esperado (banco limpo):**
```
total_users: 0
total_licenses: 0
total_subscriptions: 0
```

---

### FASE 2: Teste de Assinatura (Fluxo Principal)

#### 2.1 Acessar Página de Preços

1. Abrir navegador em modo anônimo/privado
2. Acessar: `https://fxstudioai.com/pricing.html`
3. Verificar que planos estão visíveis

**Checklist:**
- [ ] 6 planos exibidos (Basic/Pro/Enterprise × Monthly/Yearly)
- [ ] Preços formatados corretamente (R$)
- [ ] Recursos de cada plano listados
- [ ] Botões "Assinar" funcionais

#### 2.2 Iniciar Checkout

1. Clicar em "Assinar" no plano **Basic Monthly** (R$ 299/mês)
2. Verificar redirecionamento para Stripe Checkout

**Verificações no Frontend:**
- [ ] Redirecionamento ocorre
- [ ] URL do Stripe Checkout carrega
- [ ] Formulário de pagamento aparece

**Verificações no Backend (logs):**
```bash
# Procurar por:
[INFO] Criando checkout session para user: ...
[INFO] Customer ID: cus_...
```

#### 2.3 Preencher Dados de Pagamento

**Dados do Cartão de Teste:**
```
Número: 4242 4242 4242 4242
Data: 12/34
CVC: 123
CEP: 12345
Nome: Teste Assinatura
Email: teste.assinatura+$(date +%s)@gmail.com
```

**Importante:** Use um email único para cada teste (adicione timestamp)

**Checklist:**
- [ ] Formulário aceita dados de teste
- [ ] Validação de campos funciona
- [ ] Botão "Assinar" habilitado após preenchimento

#### 2.4 Confirmar Pagamento

1. Clicar em "Assinar" ou "Subscribe"
2. Aguardar processamento

**O que deve acontecer:**
- [ ] Stripe processa pagamento
- [ ] Redirecionamento para success_url
- [ ] Webhook disparado para backend

**Verificações Imediatas:**

**Frontend:**
- [ ] Redirecionado para `/dashboard.html?success=true`
- [ ] Mensagem de sucesso exibida (se houver)

**Backend (logs):**
```bash
# Procurar por:
📥 Webhook recebido: checkout.session.completed
🔄 Processando checkout.session.completed...
✅ Novo usuario criado via Pricing Table: teste.assinatura+...
✅ Licenca criada: FX20260103-IFRS16-XXXXXXXX
✅ Subscription criada: sub_...
[EMAIL] Email de boas-vindas enviado
```

---

### FASE 3: Validação no Banco de Dados

#### 3.1 Verificar Criação de Usuário

```sql
-- Verificar usuário criado
SELECT 
    id,
    email,
    name,
    stripe_customer_id,
    password_must_change,
    created_at
FROM users
WHERE email LIKE 'teste.assinatura%'
ORDER BY created_at DESC
LIMIT 1;
```

**Esperado:**
- [ ] 1 usuário criado
- [ ] `stripe_customer_id` preenchido (cus_...)
- [ ] `password_must_change = true`
- [ ] `created_at` = timestamp atual

#### 3.2 Verificar Criação de Licença

```sql
-- Verificar licença criada
SELECT 
    l.id,
    l.license_key,
    l.license_type,
    l.status,
    l.expires_at,
    l.user_id,
    u.email
FROM licenses l
JOIN users u ON l.user_id = u.id
WHERE u.email LIKE 'teste.assinatura%'
ORDER BY l.created_at DESC
LIMIT 1;
```

**Esperado:**
- [ ] 1 licença criada
- [ ] `license_key` no formato: `FX20260103-IFRS16-XXXXXXXX`
- [ ] `license_type = 'basic'`
- [ ] `status = 'active'`
- [ ] `expires_at` = data atual + 30 dias
- [ ] `user_id` vinculado ao usuário criado

#### 3.3 Verificar Criação de Subscription

```sql
-- Verificar subscription criada
SELECT 
    s.id,
    s.stripe_subscription_id,
    s.stripe_customer_id,
    s.plan_type,
    s.status,
    s.current_period_start,
    s.current_period_end,
    s.user_id,
    u.email
FROM subscriptions s
JOIN users u ON s.user_id = u.id
WHERE u.email LIKE 'teste.assinatura%'
ORDER BY s.created_at DESC
LIMIT 1;
```

**Esperado:**
- [ ] 1 subscription criada
- [ ] `stripe_subscription_id` preenchido (sub_...)
- [ ] `stripe_customer_id` = mesmo do usuário
- [ ] `plan_type = 'basic_monthly'`
- [ ] `status = 'active'`
- [ ] `current_period_start` = hoje
- [ ] `current_period_end` = hoje + 30 dias

#### 3.4 Verificar Relacionamentos

```sql
-- Verificar integridade dos relacionamentos
SELECT 
    u.email,
    u.stripe_customer_id,
    l.license_key,
    l.license_type,
    s.stripe_subscription_id,
    s.plan_type,
    s.status
FROM users u
LEFT JOIN licenses l ON l.user_id = u.id
LEFT JOIN subscriptions s ON s.user_id = u.id
WHERE u.email LIKE 'teste.assinatura%'
ORDER BY u.created_at DESC
LIMIT 1;
```

**Esperado:**
- [ ] Todos os relacionamentos corretos
- [ ] User → License (1:1)
- [ ] User → Subscription (1:1)
- [ ] License e Subscription vinculados ao mesmo user_id

---

### FASE 4: Validação de Emails

#### 4.1 Verificar Email de Boas-Vindas

**Destinatário:** Email usado no checkout

**Conteúdo Esperado:**
- [ ] Assunto: "Bem-vindo ao IFRS 16!"
- [ ] Nome do usuário correto
- [ ] Email de login correto
- [ ] Senha temporária (8 caracteres hex)
- [ ] Chave de licença (FX20260103-IFRS16-XXXXXXXX)
- [ ] Link para login: `https://fxstudioai.com/login.html?license=...`
- [ ] Instruções de acesso

**Verificações:**
- [ ] Email recebido em 1-2 minutos
- [ ] Não está em spam
- [ ] Links funcionais
- [ ] Formatação correta

#### 4.2 Verificar Email de Admin (Opcional)

**Destinatário:** Email configurado em `SMTP_FROM_EMAIL` ou admin

**Conteúdo Esperado:**
- [ ] Assunto: "Nova Assinatura Criada"
- [ ] Email do cliente
- [ ] Plano adquirido
- [ ] Valor pago
- [ ] Data/hora

---

### FASE 5: Validação no Frontend (Dashboard)

#### 5.1 Login com Senha Temporária

1. Acessar: `https://fxstudioai.com/login.html`
2. Preencher:
   - Email: email usado no checkout
   - Senha: senha temporária do email

**Esperado:**
- [ ] Login bloqueado (403 Forbidden)
- [ ] Mensagem: "Você deve alterar sua senha antes de fazer login"
- [ ] Redirecionamento para página de troca de senha (se houver)

#### 5.2 Trocar Senha

1. Preencher:
   - Senha atual: senha temporária
   - Nova senha: `NovaSenha123!`
   - Confirmar senha: `NovaSenha123!`

**Esperado:**
- [ ] Troca de senha bem-sucedida
- [ ] Redirecionamento para dashboard
- [ ] Token JWT recebido

#### 5.3 Verificar Dashboard

**Endpoint:** `GET /api/user/subscription`

**Resposta Esperada:**
```json
{
  "id": "...",
  "plan_type": "basic_monthly",
  "status": "active",
  "current_period_start": "2026-01-03T...",
  "current_period_end": "2026-02-03T...",
  "stripe_subscription_id": "sub_...",
  "license": {
    "license_key": "FX20260103-IFRS16-XXXXXXXX",
    "license_type": "basic",
    "status": "active",
    "expires_at": "2026-02-03T..."
  }
}
```

**Checklist no Dashboard:**
- [ ] Status da assinatura: "Ativa" (badge verde)
- [ ] Plano: "Básico Mensal"
- [ ] Próxima renovação: data correta (+30 dias)
- [ ] Limites: "0/50 contratos"
- [ ] Chave de licença exibida
- [ ] Botão "Gerenciar Pagamento" visível
- [ ] Recursos do plano listados

---

### FASE 6: Validação de Endpoints da API

#### 6.1 Endpoint: GET /api/payments/prices

```bash
curl -X GET "https://ifrs16-backend-ox4zylcs5a-rj.a.run.app/api/payments/prices"
```

**Esperado:**
```json
{
  "prices": [
    {
      "plan_type": "basic_monthly",
      "price_id": "price_...",
      "amount": 29900,
      "currency": "brl",
      "interval": "month"
    },
    ...
  ]
}
```

**Verificações:**
- [ ] 6 preços retornados
- [ ] Todos os planos presentes
- [ ] Valores corretos

#### 6.2 Endpoint: GET /api/user/subscription

```bash
curl -X GET "https://ifrs16-backend-ox4zylcs5a-rj.a.run.app/api/user/subscription" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

**Verificações:**
- [ ] Status 200 OK
- [ ] Subscription retornada
- [ ] License incluída
- [ ] Dados corretos

#### 6.3 Endpoint: GET /api/user/profile

```bash
curl -X GET "https://ifrs16-backend-ox4zylcs5a-rj.a.run.app/api/user/profile" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

**Verificações:**
- [ ] Status 200 OK
- [ ] Dados do usuário corretos
- [ ] Email corresponde ao usado no checkout

---

### FASE 7: Validação de Webhooks

#### 7.1 Verificar Webhook no Stripe Dashboard

1. Acessar: https://dashboard.stripe.com/test/webhooks
2. Verificar eventos recebidos

**Eventos Esperados:**
- [ ] `checkout.session.completed` - Status: Sucesso
- [ ] `customer.subscription.created` - Status: Sucesso (opcional)
- [ ] `invoice.paid` - Status: Sucesso

**Verificações:**
- [ ] Todos os eventos com status 200 OK
- [ ] Sem tentativas de retry
- [ ] Payload correto

#### 7.2 Testar Idempotência

**Cenário:** Enviar mesmo webhook duas vezes

```bash
# Via Stripe CLI (se configurado)
stripe events resend evt_...
```

**Esperado:**
- [ ] Segunda tentativa não cria duplicatas
- [ ] Mesma subscription retornada
- [ ] Log: "Session já processada"

---

## 📊 Checklist Final de Validação

### Frontend ✅
- [ ] Página de preços carrega corretamente
- [ ] Checkout redireciona para Stripe
- [ ] Success page exibida após pagamento
- [ ] Login bloqueado com senha temporária
- [ ] Troca de senha funciona
- [ ] Dashboard exibe dados corretos
- [ ] Status da assinatura visível
- [ ] Chave de licença exibida
- [ ] Botão "Gerenciar Pagamento" funciona

### Backend ✅
- [ ] Health check retorna healthy
- [ ] Endpoint `/api/payments/prices` funciona
- [ ] Endpoint `/api/user/subscription` funciona
- [ ] Endpoint `/api/user/profile` funciona
- [ ] Webhook `/api/payments/webhook` processa eventos
- [ ] Validação de signature funciona
- [ ] Idempotência implementada
- [ ] Logs detalhados disponíveis

### Banco de Dados ✅
- [ ] Usuário criado corretamente
- [ ] Licença criada com chave única
- [ ] Subscription criada com status active
- [ ] Relacionamentos corretos (User → License → Subscription)
- [ ] `stripe_customer_id` vinculado
- [ ] `password_must_change = true` no usuário
- [ ] Datas de expiração corretas

### Emails ✅
- [ ] Email de boas-vindas enviado
- [ ] Senha temporária incluída
- [ ] Chave de licença incluída
- [ ] Links funcionais
- [ ] Formatação correta
- [ ] Email de admin enviado (se configurado)

### Integração Stripe ✅
- [ ] Checkout session criada
- [ ] Customer criado no Stripe
- [ ] Subscription criada no Stripe
- [ ] Webhooks recebidos e processados
- [ ] Status sincronizado (Stripe ↔ Backend)

---

## 🐛 Troubleshooting

### Problema: Webhook não processado

**Sintomas:**
- Usuário não criado após pagamento
- Logs não mostram processamento

**Soluções:**
1. Verificar `STRIPE_WEBHOOK_SECRET` no backend
2. Verificar URL do webhook no Stripe Dashboard
3. Testar webhook manualmente via Stripe CLI:
   ```bash
   stripe listen --forward-to localhost:8000/api/payments/webhook
   stripe trigger checkout.session.completed
   ```

### Problema: Email não recebido

**Sintomas:**
- Pagamento processado mas email não chega

**Soluções:**
1. Verificar spam/lixo eletrônico
2. Verificar logs do backend para erros SMTP
3. Verificar credenciais SMTP no `.env`
4. Testar envio manual:
   ```python
   from app.services.email_service import EmailService
   await EmailService.send_welcome_email(...)
   ```

### Problema: Login não funciona

**Sintomas:**
- Senha temporária não aceita
- Erro 403 mesmo após troca de senha

**Soluções:**
1. Verificar se usuário foi criado no banco
2. Verificar hash da senha no banco
3. Verificar logs do backend
4. Testar login via API diretamente:
   ```bash
   curl -X POST "https://ifrs16-backend-.../api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email":"...","password":"..."}'
   ```

### Problema: Dashboard não carrega dados

**Sintomas:**
- Dashboard vazio ou com erros

**Soluções:**
1. Abrir DevTools (F12) → Console
2. Verificar erros de API
3. Verificar token JWT válido
4. Testar endpoints diretamente:
   ```bash
   curl -X GET "https://ifrs16-backend-.../api/user/subscription" \
     -H "Authorization: Bearer <TOKEN>"
   ```

---

## 📝 Relatório de Teste

Após completar todos os testes, preencher:

**Data do Teste:** _______________

**Ambiente:** [ ] Local [ ] Produção

**Resultado Geral:** [ ] ✅ PASSOU [ ] ❌ FALHOU [ ] ⚠️ PARCIAL

**Problemas Encontrados:**
1. _________________________________
2. _________________________________
3. _________________________________

**Observações:**
_________________________________
_________________________________
_________________________________

---

## 🎯 Próximos Testes Recomendados

1. **Teste de Renovação:** Aguardar período de teste ou simular
2. **Teste de Falha de Pagamento:** Usar cartão de teste que falha
3. **Teste de Cancelamento:** Cancelar via Stripe Portal
4. **Teste de Upgrade/Downgrade:** Alterar plano
5. **Teste com Outros Planos:** Pro e Enterprise

---

**Última atualização:** 2026-01-03  
**Versão:** 1.0
