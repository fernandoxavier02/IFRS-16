# Guia para Testar Assinatura Real - IFRS 16

**Data:** 31/12/2025
**Status do Banco:** ✅ LIMPO E PRONTO PARA TESTE

---

## ✅ Banco de Dados Limpo

```
Users: 0
Licenses: 0
Subscriptions: 0
Contracts: 0
Validation Logs: 0
```

**Tudo pronto para um teste limpo!**

---

## 🎯 Passo a Passo para Testar

### **1. Verificar Backend Rodando**

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Ou verificar se já está rodando:**
- Local: http://localhost:8000/docs
- Produção: https://ifrs16-backend-1051753255664.us-central1.run.app/docs

### **2. Acessar Landing Page**

- Local: http://localhost:3000/landing.html
- Produção: https://ifrs16.fxstudioai.com/landing.html

### **3. Ir para Seção de Preços**

Role até a seção **"Escolha seu Plano"** ou clique em **"Ver Planos"**

### **4. Escolher um Plano de Teste**

Recomendo testar com o **Básico Mensal** (R$ 299):
- Mais barato para teste
- Ciclo mensal (renovação rápida para testar)
- Limite de 5 contratos (fácil de testar limites)

### **5. Clicar em "Assinar"**

Isso irá:
1. Redirecionar para o Stripe Checkout
2. Exibir formulário de pagamento

### **6. Preencher Dados no Stripe**

**Email:** Use um email real que você tenha acesso
- Exemplo: `seu-email@gmail.com`

**Dados do Cartão de Teste:**
```
Número do Cartão: 4242 4242 4242 4242
Data de Validade: 12/34 (qualquer data futura)
CVC: 123
CEP: 12345
```

**Nome:** Seu nome ou nome de teste

### **7. Confirmar Pagamento**

Clique em **"Assinar"** ou **"Subscribe"**

---

## 🔍 O Que Esperar Após Assinatura

### **Imediatamente:**

1. **Redirecionamento para Success Page**
   - URL: `/success.html`
   - Mensagem: "Assinatura realizada com sucesso!"

2. **Webhook Processado pelo Backend**
   - Stripe envia `checkout.session.completed`
   - Backend cria: User, License, Subscription
   - Você verá nos logs do backend:
   ```
   [OK] Novo usuario criado via Pricing Table: seu-email@gmail.com
   [OK] Licenca criada: FX20251231-IFRS16-XXXXXXXX
   [EMAIL] Email de boas-vindas enviado
   ```

### **Em 1-2 minutos:**

3. **Emails Recebidos**
   - **Para você:** Email de boas-vindas com senha temporária
   - **Para admin:** Email de notificação de nova assinatura

   **Assunto:** "Bem-vindo ao IFRS 16!"

   **Conteúdo:**
   ```
   Olá [Seu Nome],

   Sua assinatura foi confirmada!

   CREDENCIAIS DE ACESSO:
   Email: seu-email@gmail.com
   Senha temporária: XXXXXXXX

   Chave de Licença: FX20251231-IFRS16-XXXXXXXX

   [Botão: Acessar Dashboard]
   ```

---

## 🧪 Testes a Realizar

### **Teste 1: Login com Senha Temporária**

1. Acesse: http://localhost:3000/login.html
2. Email: `seu-email@gmail.com`
3. Senha: `XXXXXXXX` (do email)
4. **Esperado:** Deve pedir para trocar a senha

### **Teste 2: Trocar Senha**

1. Digite nova senha forte
2. Confirme nova senha
3. Clique em "Atualizar Senha"
4. **Esperado:** Redirecionado para o dashboard

### **Teste 3: Verificar Dashboard**

1. **Informações da Conta:**
   - Nome: [Seu Nome]
   - Email: seu-email@gmail.com

2. **Status da Assinatura:**
   - Status: [Badge Verde] Ativa
   - Plano: Básico Mensal
   - Próxima Renovação: [Data daqui 30 dias]

3. **Limites do Plano:**
   - Contratos: 0/5
   - Barra de progresso: 0%

4. **Detalhes da Assinatura:**
   - Plano Atual: Básico Mensal
   - Período: [Data início] - [Data fim]
   - ID da Assinatura: sub_XXXX
   - Criada em: [Hoje]

5. **Recursos Incluídos:**
   - ✓ Excel Export
   - ✓ CSV Export
   - ✓ PDF Export
   - ✓ Relatórios
   - ✓ Suporte Email

6. **Chave de Licença:**
   - Licença: FX20251231-IFRS16-XXXXXXXX
   - Tipo: Licença BASIC
   - Válida até: [Data daqui 30 dias]

### **Teste 4: Criar Contratos**

1. Clique em "Calculadora"
2. Crie um contrato de teste
3. Volte ao dashboard
4. **Esperado:** Limites atualizados (1/5)

### **Teste 5: Portal do Stripe**

1. No dashboard, clique em "Gerenciar Pagamento"
2. **Esperado:** Redirecionado para Stripe Customer Portal
3. Verifique:
   - Detalhes da assinatura
   - Histórico de pagamentos
   - Método de pagamento
   - Opção de cancelar

### **Teste 6: Cancelamento (Opcional)**

1. No Stripe Portal, clique em "Cancelar assinatura"
2. Confirme cancelamento
3. Volte ao dashboard
4. **Esperado:**
   - Status ainda "Ativa"
   - Aviso: "⚠️ Será cancelada ao fim do período"
   - Data de renovação mostra quando expira

---

## 📊 Verificações no Backend

### **Verificar Banco de Dados:**

```bash
cd backend
python -c "
import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text('SELECT COUNT(*) FROM users'))
        print(f'Users: {result.scalar()}')
        result = await db.execute(text('SELECT COUNT(*) FROM subscriptions'))
        print(f'Subscriptions: {result.scalar()}')
        result = await db.execute(text('SELECT COUNT(*) FROM licenses'))
        print(f'Licenses: {result.scalar()}')

asyncio.run(check())
"
```

**Esperado:**
```
Users: 1
Subscriptions: 1
Licenses: 1
```

### **Verificar Logs do Backend:**

Procure por:
```
[OK] Novo usuario criado via Pricing Table
[OK] Licenca criada
[EMAIL] Email de boas-vindas enviado
[EMAIL] Notificacao de admin enviada
```

---

## 🐛 Troubleshooting

### **Problema: Email não chegou**

1. Verifique spam/lixo eletrônico
2. Verifique logs do backend para erros SMTP
3. Confirme `SMTP_PASSWORD` no `.env`

### **Problema: Login diz "Credenciais inválidas"**

1. Aguarde 1-2 minutos (webhook pode estar processando)
2. Verifique se usuário foi criado no banco
3. Verifique logs do backend

### **Problema: Dashboard não carrega dados**

1. Abra DevTools (F12) → Console
2. Verifique erros de API
3. Confirme que `/api/user/subscription` retorna 200 OK

### **Problema: Webhook não processou**

1. Verifique `STRIPE_WEBHOOK_SECRET` no `.env`
2. Teste webhook manualmente via Stripe Dashboard
3. Use `stripe listen --forward-to localhost:8000/api/payments/webhook`

---

## ✅ Checklist de Validação

Após completar os testes, confirme:

- [ ] Usuário criado automaticamente
- [ ] Licença gerada com chave única
- [ ] Subscription com status "active"
- [ ] Email de boas-vindas recebido
- [ ] Email de admin recebido
- [ ] Login com senha temporária funcionou
- [ ] Troca de senha obrigatória funcionou
- [ ] Dashboard exibe dados corretamente
- [ ] Badge de status "Ativa" verde
- [ ] Plano formatado corretamente
- [ ] Limites exibidos (0/5)
- [ ] Detalhes da assinatura visíveis
- [ ] Recursos do plano listados
- [ ] Chave de licença exibida
- [ ] Botão "Gerenciar Pagamento" funciona
- [ ] Stripe Portal abre corretamente
- [ ] Criar contrato atualiza limite (1/5)
- [ ] Cancelamento marca aviso no dashboard

---

## 📝 Notas Importantes

1. **Stripe Test Mode:** Certifique-se de estar usando chaves de teste
2. **Emails SendGrid:** Podem levar 1-2 minutos para chegar
3. **Webhooks:** Devem processar em segundos, mas podem ter delay
4. **Dashboard:** Faz 3 chamadas API (perfil, subscription, contracts)

---

## 🎉 Sucesso!

Se todos os testes passaram, você validou:
- ✅ Fluxo completo de assinatura
- ✅ Criação automática de usuário
- ✅ Envio de emails
- ✅ Dashboard com informações completas
- ✅ Portal do Stripe
- ✅ Sistema de licenças

**Está pronto para produção!** 🚀

---

**Próximos Passos:**
1. Testar com outros planos (Pro, Enterprise)
2. Testar renovação automática (aguardar 30 dias ou simular)
3. Testar falha de pagamento
4. Testar upgrade/downgrade de plano

---

**Última atualização:** 31/12/2025 às 14:35
**Status:** ✅ PRONTO PARA TESTE
