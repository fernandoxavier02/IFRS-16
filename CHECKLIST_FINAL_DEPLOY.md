# ✅ CHECKLIST FINAL - DEPLOY E TESTES

## 🎯 OBJETIVO
Validar e deployar o sistema completo de área de clientes com integração Stripe.

---

## 📋 FASE 1: PREPARAÇÃO LOCAL

### 1.1 Banco de Dados
- [ ] PostgreSQL rodando localmente
- [ ] Aplicar migração:
  ```bash
  cd backend
  alembic upgrade head
  ```
- [ ] Verificar tabela users tem coluna company_name:
  ```sql
  \d users
  ```

### 1.2 Backend
- [ ] Instalar dependências:
  ```bash
  cd backend
  pip install -r requirements.txt
  ```
- [ ] Configurar `.env` com variáveis corretas
- [ ] Iniciar backend:
  ```bash
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```
- [ ] Verificar backend respondendo:
  ```bash
  curl http://localhost:8000/health
  ```

### 1.3 Frontend
- [ ] Abrir `landing.html` no navegador
- [ ] Verificar console do navegador (sem erros)

---

## 🧪 FASE 2: TESTES FUNCIONAIS

### 2.1 Teste de Registro
1. [ ] Abrir `landing.html`
2. [ ] Clicar em "Minha Conta"
3. [ ] Clicar em "Criar Conta"
4. [ ] Preencher formulário:
   - Nome: Teste Usuario
   - Email: teste@email.com
   - Empresa: Empresa Teste LTDA
   - Senha: Teste123!
   - Confirmar Senha: Teste123!
5. [ ] Clicar em "Criar Conta"
6. [ ] Verificar mensagem de sucesso
7. [ ] Aguardar redirecionamento para login

**Validação Backend:**
```bash
# Verificar usuário criado
curl http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"teste@email.com","password":"Teste123!"}'
```

### 2.2 Teste de Login
1. [ ] Na página de login
2. [ ] Preencher:
   - Email: teste@email.com
   - Senha: Teste123!
3. [ ] Clicar em "Entrar"
4. [ ] Verificar redirecionamento para dashboard
5. [ ] Verificar token salvo no localStorage:
   ```javascript
   localStorage.getItem('ifrs16_auth_token')
   ```

### 2.3 Teste de Dashboard
1. [ ] Dashboard carregou corretamente
2. [ ] Dados do usuário exibidos:
   - [ ] Nome: Teste Usuario
   - [ ] Email: teste@email.com
   - [ ] Empresa: Empresa Teste LTDA
3. [ ] Status da assinatura: "Inativa"
4. [ ] Botão "Assinar Plano" visível
5. [ ] Botão "Gerenciar Pagamento" oculto

### 2.4 Teste de Proteção de Rotas
1. [ ] Fazer logout
2. [ ] Tentar acessar `dashboard.html` diretamente
3. [ ] Verificar redirecionamento para login
4. [ ] Fazer login novamente
5. [ ] Dashboard deve carregar normalmente

### 2.5 Teste de Endpoints Stripe
```bash
# 1. Obter token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"teste@email.com","password":"Teste123!"}' \
  | jq -r '.access_token')

# 2. Listar preços
curl http://localhost:8000/api/stripe/prices

# 3. Criar checkout session (requer price_id configurado)
curl -X POST http://localhost:8000/api/stripe/create-checkout-session \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"price_id":"price_1234567890"}'

# 4. Criar portal session (requer stripe_customer_id)
curl -X POST http://localhost:8000/api/stripe/create-portal-session \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔧 FASE 3: CONFIGURAÇÃO STRIPE

### 3.1 Produtos e Preços
- [ ] Acessar Stripe Dashboard
- [ ] Criar produto "Plano Básico" (R$ 299/mês)
- [ ] Criar produto "Plano Pro" (R$ 499/mês)
- [ ] Criar produto "Plano Enterprise" (R$ 999/mês)
- [ ] Copiar todos os Price IDs

### 3.2 Webhooks
- [ ] Criar webhook endpoint
- [ ] URL: `https://ifrs16-backend-1051753255664.us-central1.run.app/api/webhooks/stripe`
- [ ] Eventos selecionados:
  - checkout.session.completed
  - customer.subscription.created
  - customer.subscription.updated
  - customer.subscription.deleted
- [ ] Copiar Webhook Secret

### 3.3 Atualizar Variáveis
- [ ] Atualizar `.env` local com price_ids
- [ ] Atualizar Cloud Run com price_ids (produção)

### 3.4 Testar Checkout (Modo Teste)
1. [ ] No dashboard, clicar em "Assinar Plano"
2. [ ] Selecionar um plano
3. [ ] Usar cartão de teste: 4242 4242 4242 4242
4. [ ] Completar pagamento
5. [ ] Verificar webhook recebido no Stripe
6. [ ] Verificar assinatura criada no banco
7. [ ] Dashboard deve mostrar assinatura ativa

---

## 🚀 FASE 4: DEPLOY PRODUÇÃO

### 4.1 Preparar Backend
```bash
cd backend

# 1. Verificar requirements.txt atualizado
pip freeze > requirements.txt

# 2. Testar build local
docker build -t ifrs16-backend .

# 3. Testar container local
docker run -p 8000:8000 ifrs16-backend
```

### 4.2 Deploy Backend (Cloud Run)
```bash
# 1. Autenticar
gcloud auth login

# 2. Configurar projeto
gcloud config set project ifrs16-app

# 3. Build e deploy
gcloud run deploy ifrs16-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=$DATABASE_URL_PROD \
  --set-env-vars STRIPE_SECRET_KEY=$STRIPE_SECRET_KEY \
  --set-env-vars STRIPE_WEBHOOK_SECRET=$STRIPE_WEBHOOK_SECRET

# 4. Verificar deploy
gcloud run services describe ifrs16-backend --region us-central1
```

### 4.3 Aplicar Migração (Produção)
```bash
# Conectar ao Cloud SQL
gcloud sql connect ifrs16-database --user=ifrs16_user

# Aplicar migração
cd backend
alembic upgrade head
```

### 4.4 Deploy Frontend (Firebase)
```bash
# 1. Instalar Firebase CLI (se necessário)
npm install -g firebase-tools

# 2. Login
firebase login

# 3. Deploy
firebase deploy --only hosting

# 4. Verificar
# Acessar: https://fxstudioai.com
```

### 4.5 Verificar Produção
- [ ] Backend respondendo: https://ifrs16-backend-1051753255664.us-central1.run.app/health
- [ ] Frontend carregando: https://fxstudioai.com
- [ ] Registro funcionando
- [ ] Login funcionando
- [ ] Dashboard funcionando
- [ ] Stripe checkout funcionando (modo teste)

---

## 🔄 FASE 5: ATIVAR MODO PRODUÇÃO

### 5.1 Stripe Live Mode
- [ ] Ativar conta Stripe (verificar identidade)
- [ ] Trocar para chaves Live:
  - sk_live_...
  - pk_live_...
- [ ] Atualizar webhook para produção
- [ ] Copiar novo webhook secret (live)

### 5.2 Atualizar Variáveis (Live)
```bash
gcloud run services update ifrs16-backend \
  --update-env-vars STRIPE_SECRET_KEY=sk_live_... \
  --update-env-vars STRIPE_PUBLISHABLE_KEY=pk_live_... \
  --update-env-vars STRIPE_WEBHOOK_SECRET=whsec_live_...
```

### 5.3 Teste Final (Produção Real)
1. [ ] Criar conta real
2. [ ] Fazer login
3. [ ] Assinar plano com cartão real (valor pequeno)
4. [ ] Verificar cobrança no Stripe
5. [ ] Verificar assinatura no dashboard
6. [ ] Testar portal do cliente
7. [ ] Cancelar assinatura de teste

---

## 📊 FASE 6: MONITORAMENTO

### 6.1 Logs
```bash
# Backend logs
gcloud run services logs read ifrs16-backend --limit 100

# Filtrar erros
gcloud run services logs read ifrs16-backend --limit 100 | grep ERROR

# Filtrar Stripe
gcloud run services logs read ifrs16-backend --limit 100 | grep stripe
```

### 6.2 Métricas
- [ ] Stripe Dashboard: Verificar transações
- [ ] Cloud Run: Verificar requests/errors
- [ ] Firebase: Verificar acessos

### 6.3 Alertas
- [ ] Configurar alerta de erro no Cloud Run
- [ ] Configurar alerta de falha de pagamento no Stripe
- [ ] Configurar alerta de downtime

---

## ✅ CHECKLIST FINAL

### Desenvolvimento
- [x] Backend implementado
- [x] Frontend implementado
- [x] Endpoints Stripe criados
- [x] Migração criada
- [x] Documentação completa
- [ ] Testes locais executados
- [ ] Migração aplicada localmente

### Stripe
- [ ] Conta criada
- [ ] Produtos criados
- [ ] Webhooks configurados
- [ ] Modo teste validado
- [ ] Modo live ativado (quando pronto)

### Deploy
- [ ] Backend deployado (Cloud Run)
- [ ] Frontend deployado (Firebase)
- [ ] Migração aplicada (produção)
- [ ] Variáveis configuradas
- [ ] SSL/HTTPS funcionando

### Validação
- [ ] Registro funcionando
- [ ] Login funcionando
- [ ] Dashboard funcionando
- [ ] Checkout funcionando
- [ ] Portal funcionando
- [ ] Webhooks funcionando

---

## 🎉 SISTEMA PRONTO!

Quando todos os itens estiverem marcados, o sistema estará 100% funcional e pronto para uso em produção.

---

## 📞 TROUBLESHOOTING

### Erro: Migração falha
```bash
# Verificar versão atual
alembic current

# Ver histórico
alembic history

# Forçar versão
alembic stamp head
```

### Erro: Deploy Cloud Run falha
```bash
# Ver logs de build
gcloud builds list --limit 5

# Ver detalhes do erro
gcloud builds log [BUILD_ID]
```

### Erro: Frontend não carrega
```bash
# Verificar deploy
firebase hosting:channel:list

# Ver logs
firebase hosting:channel:open live
```

---

**Data de criação:** 19/12/2025  
**Versão:** 1.0  
**Status:** Pronto para execução
