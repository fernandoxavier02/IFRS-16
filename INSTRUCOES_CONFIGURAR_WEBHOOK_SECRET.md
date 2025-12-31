# Instruções: Configurar STRIPE_WEBHOOK_SECRET no Google Cloud Run

**Data:** 31/12/2025
**Problema:** Webhooks retornando HTTP 400 "Assinatura inválida"
**Causa:** STRIPE_WEBHOOK_SECRET não está configurado no ambiente de produção

---

## 🔧 Passo a Passo

### **1. Obter o Webhook Signing Secret do Stripe**

1. Acesse o Stripe Dashboard:
   ```
   https://dashboard.stripe.com/webhooks
   ```

2. Localize o webhook endpoint:
   ```
   https://ifrs16-backend-1051753255664.us-central1.run.app/api/payments/webhook
   ```

3. Clique em **"Reveal"** no campo **"Signing secret"**

4. Copie o valor (formato: `whsec_xxxxxxxxxxxxxxxxxxxxx`)

---

### **2. Configurar no Google Cloud Run**

#### **Opção A: Via Console Web**

1. Acesse: https://console.cloud.google.com/run

2. Selecione o serviço: **`ifrs16-backend`**

3. Clique em **"EDIT & DEPLOY NEW REVISION"** (no topo)

4. Na aba **"Variables & Secrets"**, role até a seção **"Environment variables"**

5. Procure pela variável `STRIPE_WEBHOOK_SECRET`

6. Cole o valor obtido do Stripe (ex: `whsec_abc123...`)

7. Clique em **"DEPLOY"** (no final da página)

8. Aguarde o deploy completar (~2-3 minutos)

#### **Opção B: Via gcloud CLI**

```bash
# Atualizar variável de ambiente
gcloud run services update ifrs16-backend \
  --region=us-central1 \
  --update-env-vars STRIPE_WEBHOOK_SECRET=whsec_SEU_SECRET_AQUI
```

---

### **3. Verificar se Funcionou**

#### **3.1 Testar com Stripe CLI (Local)**

```bash
# Instalar Stripe CLI se necessário
# https://stripe.com/docs/stripe-cli

# Fazer login
stripe login

# Enviar webhook de teste
stripe trigger checkout.session.completed
```

#### **3.2 Fazer Nova Compra de Teste**

1. Acesse: https://seu-frontend.web.app/pricing.html

2. Clique em **"Assinar"** em qualquer plano

3. Complete o pagamento com cartão de teste:
   ```
   Número: 4242 4242 4242 4242
   Validade: 12/34
   CVC: 123
   ```

4. Após pagamento, verifique no Stripe Dashboard:
   ```
   https://dashboard.stripe.com/webhooks
   ```

   **Resultado esperado:**
   - Status: **200 OK** (verde) ✅
   - Não mais "400 ERR" (vermelho) ❌

#### **3.3 Verificar Banco de Dados**

```bash
cd backend
python ver_usuarios.py
```

**Output esperado:**
```
====================================================================================================
USUÁRIOS CADASTRADOS (1)
====================================================================================================

[1] Nome do Teste
    ID: abc123...
    Email: teste@example.com
    Ativo: Sim
    Precisa trocar senha: Sim
    Criado em: 2025-12-31 XX:XX:XX

[INFO] Assinaturas no banco: 1
[INFO] Licenças no banco: 1
```

#### **3.4 Verificar Email Recebido**

O usuário deve receber email com assunto:
```
Bem-vindo ao IFRS 16 - Sua assinatura foi ativada!
```

Conteúdo:
- Senha temporária gerada
- Chave de licença (formato: FX20250131-IFRS16-ABC123)
- Instruções de acesso

---

## 🐛 Solução de Problemas

### Erro: "STRIPE_WEBHOOK_SECRET não está definido"

**Sintoma:** Logs do Cloud Run mostram:
```
WARNING: STRIPE_WEBHOOK_SECRET não está definido!
```

**Solução:**
1. Verifique se salvou a variável corretamente no Cloud Run
2. Certifique-se de que fez **DEPLOY** após adicionar a variável
3. Reinicie o serviço se necessário

---

### Erro: Ainda retorna "Assinatura inválida"

**Sintomas possíveis:**

1. **Secret incorreto:**
   - Verifique se copiou o valor completo do Stripe (incluindo `whsec_`)
   - Certifique-se de que está usando o secret do webhook CORRETO (produção vs teste)

2. **Modo Stripe incorreto:**
   ```bash
   # Verifique no .env de produção:
   STRIPE_MODE=live  # OU test
   ```
   - Se `STRIPE_MODE=live`, use webhook secret de **LIVE mode** no Stripe
   - Se `STRIPE_MODE=test`, use webhook secret de **TEST mode** no Stripe

3. **Cache do Cloud Run:**
   ```bash
   # Forçar redeploy
   gcloud run services update ifrs16-backend \
     --region=us-central1 \
     --no-traffic  # Remove tráfego

   gcloud run services update ifrs16-backend \
     --region=us-central1 \
     --traffic=latest=100  # Restaura tráfego
   ```

---

### Erro: Webhook recebido mas banco ainda vazio

**Sintoma:** Stripe mostra 200 OK, mas `ver_usuarios.py` retorna 0 usuários

**Possíveis causas:**

1. **DATABASE_URL incorreto:**
   ```bash
   # Verificar logs do Cloud Run
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ifrs16-backend" --limit=50
   ```

2. **Erro silencioso no código:**
   - Verificar logs para exceções dentro de `try/except`

3. **Transação não commitada:**
   - Código usa `await db.commit()` após criar License/Subscription

---

## 📊 Checklist de Validação

Após configurar o `STRIPE_WEBHOOK_SECRET`, verifique:

- [ ] Stripe Dashboard mostra **200 OK** nos webhooks
- [ ] `ver_usuarios.py` mostra 1 usuário criado
- [ ] Usuário recebeu email de boas-vindas
- [ ] Email contém senha temporária
- [ ] Email contém chave de licença (formato: FX20250131-...)
- [ ] Banco de dados tem 1 subscription com status ACTIVE
- [ ] Banco de dados tem 1 license com status ACTIVE
- [ ] Login com senha temporária funciona
- [ ] Sistema força troca de senha no primeiro login

---

## 🎯 Próximos Passos Após Configurar

1. **Testar fluxo completo:**
   - Registro → Pagamento → Webhook → Email → Login → Dashboard

2. **Monitorar logs por 24h:**
   ```bash
   gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=ifrs16-backend"
   ```

3. **Testar outros webhooks:**
   - `invoice.paid` (renovação)
   - `invoice.payment_failed` (falha de pagamento)
   - `customer.subscription.deleted` (cancelamento)

---

**Última atualização:** 31/12/2025 às 23:50
**Responsável:** Claude Sonnet 4.5
**Status:** ⚠️ AGUARDANDO CONFIGURAÇÃO DO SECRET
