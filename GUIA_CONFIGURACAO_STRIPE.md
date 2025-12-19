# 🔧 GUIA DE CONFIGURAÇÃO STRIPE

## 📋 Pré-requisitos
- ✅ Conta Stripe criada (https://dashboard.stripe.com)
- ✅ Endpoints Stripe implementados no backend
- ✅ Backend rodando

---

## 🚀 PASSO A PASSO

### 1. Acessar Stripe Dashboard
```
https://dashboard.stripe.com
```

### 2. Criar Produtos

#### Produto 1: Plano Básico
1. Ir para **Produtos** → **Adicionar produto**
2. Preencher:
   - **Nome:** IFRS 16 - Plano Básico
   - **Descrição:** Até 3 contratos, exportação Excel
   - **Preço:** R$ 299,00
   - **Tipo:** Recorrente
   - **Frequência:** Mensal
3. Clicar em **Salvar produto**
4. **Copiar o Price ID** (ex: `price_1234567890`)

#### Produto 2: Plano Pro
1. Ir para **Produtos** → **Adicionar produto**
2. Preencher:
   - **Nome:** IFRS 16 - Plano Pro
   - **Descrição:** Até 20 contratos, multi-usuário (5 usuários)
   - **Preço:** R$ 499,00
   - **Tipo:** Recorrente
   - **Frequência:** Mensal
3. Clicar em **Salvar produto**
4. **Copiar o Price ID**

#### Produto 3: Plano Enterprise
1. Ir para **Produtos** → **Adicionar produto**
2. Preencher:
   - **Nome:** IFRS 16 - Plano Enterprise
   - **Descrição:** Contratos ilimitados, usuários ilimitados
   - **Preço:** R$ 999,00
   - **Tipo:** Recorrente
   - **Frequência:** Mensal
3. Clicar em **Salvar produto**
4. **Copiar o Price ID**

---

### 3. Configurar Webhooks

#### 3.1 Criar Webhook
1. Ir para **Desenvolvedores** → **Webhooks**
2. Clicar em **Adicionar endpoint**
3. Preencher:
   - **URL do endpoint:** `https://ifrs16-backend-1051753255664.us-central1.run.app/api/webhooks/stripe`
   - **Descrição:** Webhook IFRS 16 Production
4. Selecionar eventos:
   - ✅ `checkout.session.completed`
   - ✅ `customer.subscription.created`
   - ✅ `customer.subscription.updated`
   - ✅ `customer.subscription.deleted`
   - ✅ `invoice.payment_succeeded`
   - ✅ `invoice.payment_failed`
5. Clicar em **Adicionar endpoint**
6. **Copiar o Signing Secret** (ex: `whsec_1234567890`)

---

### 4. Atualizar Variáveis de Ambiente

#### 4.1 Arquivo `.env` (Backend Local)
```env
# Stripe Keys
STRIPE_SECRET_KEY=sk_test_51...
STRIPE_PUBLISHABLE_KEY=pk_test_51...
STRIPE_WEBHOOK_SECRET=whsec_...

# Preços Básico
STRIPE_PRICE_BASIC_MONTHLY=price_1234567890
STRIPE_PRICE_BASIC_YEARLY=price_0987654321

# Preços Pro
STRIPE_PRICE_PRO_MONTHLY=price_1111111111
STRIPE_PRICE_PRO_YEARLY=price_2222222222

# Preços Enterprise
STRIPE_PRICE_ENTERPRISE_MONTHLY=price_3333333333
STRIPE_PRICE_ENTERPRISE_YEARLY=price_4444444444
```

#### 4.2 Cloud Run (Produção)
```bash
gcloud run services update ifrs16-backend \
  --update-env-vars STRIPE_SECRET_KEY=sk_live_... \
  --update-env-vars STRIPE_PUBLISHABLE_KEY=pk_live_... \
  --update-env-vars STRIPE_WEBHOOK_SECRET=whsec_... \
  --update-env-vars STRIPE_PRICE_BASIC_MONTHLY=price_... \
  --update-env-vars STRIPE_PRICE_PRO_MONTHLY=price_... \
  --update-env-vars STRIPE_PRICE_ENTERPRISE_MONTHLY=price_...
```

---

### 5. Configurar Portal do Cliente

1. Ir para **Configurações** → **Portal do cliente**
2. Ativar portal do cliente
3. Configurar:
   - ✅ Permitir cancelamento de assinatura
   - ✅ Permitir atualização de método de pagamento
   - ✅ Mostrar histórico de faturas
   - ✅ Permitir download de faturas
4. Salvar configurações

---

### 6. Testar Integração

#### 6.1 Testar Endpoint de Preços
```bash
curl http://localhost:8000/api/stripe/prices
```

**Resposta esperada:**
```json
{
  "prices": [
    {
      "id": "price_1234567890",
      "product_name": "IFRS 16 - Plano Básico",
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

#### 6.2 Testar Checkout (com usuário autenticado)
```bash
TOKEN="seu_jwt_token_aqui"

curl -X POST http://localhost:8000/api/stripe/create-checkout-session \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "price_id": "price_1234567890"
  }'
```

**Resposta esperada:**
```json
{
  "session_id": "cs_test_...",
  "url": "https://checkout.stripe.com/c/pay/cs_test_..."
}
```

#### 6.3 Testar Portal
```bash
TOKEN="seu_jwt_token_aqui"

curl -X POST http://localhost:8000/api/stripe/create-portal-session \
  -H "Authorization: Bearer $TOKEN"
```

**Resposta esperada:**
```json
{
  "url": "https://billing.stripe.com/p/session/test_..."
}
```

---

### 7. Modo Teste vs Produção

#### Modo Teste (Desenvolvimento)
- Usar chaves `sk_test_...` e `pk_test_...`
- Cartões de teste: https://stripe.com/docs/testing
- Exemplo: `4242 4242 4242 4242` (Visa)

#### Modo Produção
1. Ativar conta Stripe (verificar identidade)
2. Trocar para chaves `sk_live_...` e `pk_live_...`
3. Configurar webhooks para URL de produção
4. Testar com cartão real (pequeno valor)

---

## 🧪 CARTÕES DE TESTE

### Sucesso
- **Visa:** 4242 4242 4242 4242
- **Mastercard:** 5555 5555 5555 4444
- **American Express:** 3782 822463 10005

### Falha
- **Cartão recusado:** 4000 0000 0000 0002
- **Saldo insuficiente:** 4000 0000 0000 9995

**Dados adicionais:**
- **Data de validade:** Qualquer data futura
- **CVC:** Qualquer 3 dígitos
- **CEP:** Qualquer CEP válido

---

## 📊 MONITORAMENTO

### Dashboard Stripe
- **Pagamentos:** Ver todas as transações
- **Assinaturas:** Gerenciar assinaturas ativas
- **Clientes:** Ver lista de clientes
- **Eventos:** Log de webhooks

### Logs do Backend
```bash
# Ver logs do Cloud Run
gcloud run services logs read ifrs16-backend --limit 50

# Filtrar por Stripe
gcloud run services logs read ifrs16-backend --limit 50 | grep stripe
```

---

## ⚠️ TROUBLESHOOTING

### Erro: "No such price"
**Causa:** Price ID inválido ou não existe
**Solução:** Verificar price_id no Stripe Dashboard

### Erro: "Customer not found"
**Causa:** Usuário não tem stripe_customer_id
**Solução:** Endpoint create-checkout-session cria automaticamente

### Webhook não recebe eventos
**Causa:** URL incorreta ou endpoint não acessível
**Solução:** 
1. Verificar URL do webhook
2. Testar endpoint manualmente
3. Ver logs de tentativas no Stripe Dashboard

### Portal não abre
**Causa:** Usuário não tem stripe_customer_id
**Solução:** Usuário precisa fazer checkout primeiro

---

## 📞 SUPORTE

- **Documentação Stripe:** https://stripe.com/docs
- **Suporte Stripe:** https://support.stripe.com
- **Status Stripe:** https://status.stripe.com

---

## ✅ CHECKLIST DE CONFIGURAÇÃO

- [ ] Conta Stripe criada e verificada
- [ ] Produtos criados (Básico, Pro, Enterprise)
- [ ] Price IDs copiados
- [ ] Webhook configurado
- [ ] Webhook secret copiado
- [ ] Variáveis de ambiente atualizadas (.env)
- [ ] Portal do cliente ativado
- [ ] Teste de endpoint /prices funcionando
- [ ] Teste de checkout funcionando
- [ ] Teste de portal funcionando
- [ ] Modo produção ativado (quando pronto)

---

**Configuração Stripe: Pronta para uso! 🎉**
