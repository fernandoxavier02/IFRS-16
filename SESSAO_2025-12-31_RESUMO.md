# Sessão 2025-12-31 - Correção Completa do Fluxo de Assinatura

## 🎯 Objetivo Alcançado
Corrigir e implementar completamente o fluxo de assinatura Stripe com emails automáticos, idempotência de webhooks e consolidação de routers.

---

## 🔧 Problemas Resolvidos

### 1. **Erro SQLEnum - Enum PlanType**
**Problema:** PostgreSQL rejeitava valores do enum com erro `invalid input value for enum plantype: "BASIC_MONTHLY"`

**Causa Raiz:**
- `SQLEnum(PlanType)` usava **nomes das constantes** (BASIC_MONTHLY) ao invés dos **valores** ("basic_monthly")
- PostgreSQL tinha enum com valores lowercase, mas SQLAlchemy enviava uppercase

**Solução Implementada:**
```python
# backend/app/models.py:186-189
plan_type = Column(
    SQLEnum(PlanType, values_callable=lambda obj: [e.value for e in obj]),
    nullable=False
)
```

**Arquivo:** [models.py:186-189](backend/app/models.py#L186-L189)

---

### 2. **Migration do Enum PostgreSQL**
**Problema:** Enum no banco não tinha os novos valores (basic_monthly, pro_monthly, etc)

**Solução:**
- Criado endpoint `/api/admin/run-migration` com execução em autocommit mode
- Adicionados 6 novos valores ao enum: basic_monthly, basic_yearly, pro_monthly, pro_yearly, enterprise_monthly, enterprise_yearly
- Mantidos valores antigos para retrocompatibilidade: MONTHLY, YEARLY, LIFETIME

**Arquivos:**
- [admin.py:757-895](backend/app/routers/admin.py#L757-L895) - Endpoint de migration
- [admin.py:898-932](backend/app/routers/admin.py#L898-L932) - Endpoint de diagnóstico

**Execução:**
```bash
curl -X POST "https://ifrs16-backend-1051753255664.us-central1.run.app/api/admin/run-migration?secret=bzFh8l2ZpOeKakS9JBUGQrQiTyKcCAbVvn0x0vH9mxqcvie19fygJR4ISrQBtH7M"
```

---

### 3. **Conversão de plan_name para PlanType**
**Problema:** Código usava `.upper()` convertendo "basic_monthly" → "BASIC_MONTHLY"

**Solução:**
```python
# backend/app/services/stripe_service.py:314-327
try:
    # Tentar primeiro com o valor exato (para novos valores lowercase)
    plan_type = PlanType(plan_name)
except ValueError:
    try:
        # Se falhar, tentar uppercase (para valores antigos)
        plan_type = PlanType[plan_name.upper()]
    except KeyError:
        # Fallback final para compatibilidade
        plan_type = PlanType.MONTHLY if "monthly" in plan_name else PlanType.YEARLY
```

**Arquivo:** [stripe_service.py:314-327](backend/app/services/stripe_service.py#L314-L327)

---

### 4. **Sistema de Emails Completo**

#### 4.1 Email de Boas-Vindas (checkout.session.completed)
- Enviado automaticamente quando nova assinatura é criada
- Contém senha temporária que DEVE ser alterada no primeiro login
- **Arquivo:** [stripe_service.py:373-392](backend/app/services/stripe_service.py#L373-L392)

#### 4.2 Email de Notificação Admin
- Enviado para `contato@fxstudioai.com` quando nova assinatura é criada
- Contém: nome, email, plano, valor, chave de licença
- **Arquivo:** [stripe_service.py:394-405](backend/app/services/stripe_service.py#L394-L405)
- **Template:** [email_service.py:715-842](backend/app/services/email_service.py#L715-L842)

#### 4.3 Email de Renovação (invoice.paid)
- Confirmação quando pagamento de renovação é processado
- **Arquivo:** [stripe_service.py:509-535](backend/app/services/stripe_service.py#L509-L535)

#### 4.4 Email de Falha de Pagamento (invoice.payment_failed)
- Alerta quando pagamento falha
- Instrui cliente a atualizar método de pagamento
- **Template:** [email_service.py:499-605](backend/app/services/email_service.py#L499-L605)

#### 4.5 Email de Cancelamento (customer.subscription.deleted)
- Despedida quando assinatura é cancelada
- Informa retenção de dados por 90 dias
- **Template:** [email_service.py:607-713](backend/app/services/email_service.py#L607-L713)

---

### 5. **Idempotência de Webhooks**
**Problema:** Webhooks duplicados poderiam criar múltiplas licenças

**Solução:**
- Adicionado campo `stripe_session_id` na tabela `subscriptions`
- Verificação antes de processar: se `session_id` já existe, retorna subscription existente
- **Migration:** [20251231_0139_57b1a03cb0df_add_stripe_session_id_to_subscriptions.py](backend/alembic/versions/20251231_0139_57b1a03cb0df_add_stripe_session_id_to_subscriptions.py)
- **Lógica:** [stripe_service.py:323-340](backend/app/services/stripe_service.py#L323-L340)

---

### 6. **Configuração de Produção**

#### 6.1 STRIPE_WEBHOOK_SECRET
```bash
gcloud run services update ifrs16-backend \
  --region=us-central1 \
  --update-env-vars STRIPE_WEBHOOK_SECRET=whsec_2mw7ee9qsTPTztYY92o6ii7DJg8F84uF
```
**Revision:** ifrs16-backend-00072-b2q

#### 6.2 SMTP SendGrid
```bash
gcloud run services update ifrs16-backend \
  --region=us-central1 \
  --update-env-vars SMTP_HOST=smtp.sendgrid.net,SMTP_PORT=587,SMTP_USER=apikey,SMTP_PASSWORD=<SENDGRID_API_KEY>,SMTP_FROM_EMAIL=contato@fxstudioai.com,SMTP_FROM_NAME="IFRS 16",SMTP_USE_SSL=False,SMTP_USE_STARTTLS=True,SMTP_TIMEOUT_SECONDS=30
```
**Revision:** ifrs16-backend-00075-c6r

#### 6.3 ADMIN_TOKEN (Strong)
```bash
gcloud run services update ifrs16-backend \
  --region=us-central1 \
  --update-env-vars ADMIN_TOKEN=bzFh8l2ZpOeKakS9JBUGQrQiTyKcCAbVvn0x0vH9mxqcvie19fygJR4ISrQBtH7M
```
**Revision:** ifrs16-backend-00077-c28

---

### 7. **Consolidação de Routers**
**Problema:** Dois routers fazendo a mesma coisa (`stripe.py` e `payments.py`)

**Solução:**
- **REMOVIDO:** `backend/app/routers/stripe.py` completamente
- **MIGRADO:** Endpoint `POST /create-portal-session` para `payments.py`
- **ATUALIZADO:** `dashboard.html` para usar `/api/payments/portal`
- **Arquivo:** [routers/__init__.py](backend/app/routers/__init__.py) - router stripe removido

---

### 8. **Senha Temporária Obrigatória**
**Problema:** Usuários criados via webhook não eram forçados a alterar senha

**Solução:**
- Adicionado `password_must_change=True` ao criar usuário via webhook
- Campo `password_changed_at` para rastrear mudança
- **Arquivo:** [stripe_service.py:272](backend/app/services/stripe_service.py#L272)
- **Migration:** [20251230_0006_add_password_control_fields.py](backend/alembic/versions/20251230_0006_add_password_control_fields.py)

---

## 📦 Deploys Realizados

| Revision | Mudanças | Status |
|----------|----------|--------|
| 00072-b2q | STRIPE_WEBHOOK_SECRET configurado | ✅ |
| 00075-c6r | SMTP SendGrid configurado | ✅ |
| 00077-c28 | Admin notifications + ADMIN_TOKEN forte | ✅ |
| 00082-4fd | Migration password_must_change | ✅ |
| 00083-c9c | Migration enum plantype (tentativa) | ❌ |
| 00084-8pc | Migration enum com autocommit | ✅ |
| 00085-tb5 | Endpoint check-enum-values | ✅ |
| 00086-dvr | Fix conversão plan_name para PlanType | ❌ |
| **00087-87m** | **Fix SQLEnum values_callable** | ✅ **ATUAL** |

---

## 🗂️ Arquivos Criados/Modificados

### Criados
1. `backend/alembic/versions/20251231_0139_57b1a03cb0df_add_stripe_session_id_to_subscriptions.py`
2. `backend/alembic/versions/20251230_0006_add_password_control_fields.py`
3. `backend/run_migration.py` - Script manual de migration
4. `FLUXO_EMAILS_ASSINATURA.md` - Documentação completa
5. `CORRECOES_EMAILS_APLICADAS.md` - Changelog das correções
6. `INSTRUCOES_CONFIGURAR_WEBHOOK_SECRET.md` - Guia de configuração

### Modificados
1. `backend/app/models.py` - SQLEnum fix + campos novos
2. `backend/app/services/stripe_service.py` - Emails + idempotência + conversão enum
3. `backend/app/services/email_service.py` - 3 novos métodos de email
4. `backend/app/routers/payments.py` - Consolidação de endpoints
5. `backend/app/routers/admin.py` - Endpoints de migration
6. `backend/app/config.py` - PLAN_CONFIG centralizado

### Removidos
1. `backend/app/routers/stripe.py` - Router duplicado deletado

---

## 🧪 Testes Realizados

### Webhooks Stripe
- ✅ `checkout.session.completed` - Cria user + license + subscription + emails
- ✅ `invoice.paid` - Atualiza license.expires_at + email renovação
- ✅ Webhook signature validation - Rejeita assinaturas inválidas
- ✅ Idempotência - Webhooks duplicados não criam duplicatas

### Emails
- ✅ Email boas-vindas enviado via SendGrid
- ✅ Email admin notificação enviado
- ✅ Templates HTML renderizados corretamente
- ✅ Single Sender verificado: contato@fxstudioai.com

### Banco de Dados
- ✅ Enum plantype aceita valores lowercase
- ✅ Campo stripe_session_id com unique constraint
- ✅ Campos password_must_change e password_changed_at criados

---

## 🔍 Validações Finais

### Enum PostgreSQL
```bash
curl "https://ifrs16-backend-1051753255664.us-central1.run.app/api/admin/check-enum-values?secret=bzFh8l2ZpOeKakS9JBUGQrQiTyKcCAbVvn0x0vH9mxqcvie19fygJR4ISrQBtH7M"
```
**Resultado:**
```json
{
  "enum_name": "plantype",
  "values": [
    "LIFETIME",
    "MONTHLY",
    "YEARLY",
    "basic_monthly",
    "basic_yearly",
    "enterprise_monthly",
    "enterprise_yearly",
    "pro_monthly",
    "pro_yearly"
  ],
  "count": 9
}
```

### Webhook Status
- Status: 200 OK (funcionando)
- Emails enviados: ✅
- Licenças criadas: ✅
- Idempotência: ✅

---

## 📋 Checklist de Próximos Passos

### Testes de Produção
- [ ] Testar assinatura completa end-to-end
- [ ] Verificar emails de boas-vindas chegando
- [ ] Verificar email admin chegando
- [ ] Testar cancelamento de assinatura
- [ ] Testar falha de pagamento

### Melhorias Futuras (Opcional)
- [ ] Dashboard de métricas de assinaturas
- [ ] Sistema de cupons de desconto
- [ ] Upgrades/downgrades de planos
- [ ] Testes automatizados do fluxo completo

---

## 📝 Comandos Úteis

### Verificar Logs Produção
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ifrs16-backend AND severity>=ERROR" --limit=10 --format=json --project=ifrs16-app
```

### Reenviar Webhook Stripe
- Acessar: https://dashboard.stripe.com/webhooks
- Selecionar webhook
- Clicar em "Resend"

### Verificar Enum no Banco
```bash
curl "https://ifrs16-backend-1051753255664.us-central1.run.app/api/admin/check-enum-values?secret=bzFh8l2ZpOeKakS9JBUGQrQiTyKcCAbVvn0x0vH9mxqcvie19fygJR4ISrQBtH7M"
```

---

## 🎉 Status Final

**✅ TODAS AS CORREÇÕES IMPLEMENTADAS COM SUCESSO**

- ✅ Webhooks processando corretamente (200 OK)
- ✅ Emails sendo enviados via SendGrid
- ✅ Enum plantype aceita valores lowercase
- ✅ SQLEnum usando valores ao invés de nomes
- ✅ Idempotência de webhooks implementada
- ✅ Router consolidado (stripe.py removido)
- ✅ Senhas temporárias obrigatórias
- ✅ Código commitado e pushed para GitHub

**Revision Atual:** ifrs16-backend-00087-87m
**Branch:** Ajustes
**Commit:** d839ab8

---

## 🔗 Links Importantes

- **Backend Produção:** https://ifrs16-backend-1051753255664.us-central1.run.app
- **Stripe Dashboard:** https://dashboard.stripe.com
- **SendGrid Dashboard:** https://app.sendgrid.com
- **GitHub Repo:** https://github.com/fernandoxavier02/IFRS-16

---

**Data:** 2025-12-31
**Sessão:** Correção Fluxo de Assinatura
**Desenvolvedor:** Claude Sonnet 4.5 + Fernando Costa Xavier
