# 🚂 Plano de Migração para Railway

**Objetivo:** Migrar completamente do Render para Railway  
**Prazo estimado:** 1-2 horas  
**Dificuldade:** Fácil

---

## ✅ PRÉ-REQUISITOS

- [ ] Conta no GitHub (já tem)
- [ ] Código no repositório GitHub (já tem)
- [ ] Backup do banco de dados (fazer antes)

---

## 📋 PASSO A PASSO

### 1️⃣ Preparar Backup (15 min)

#### 1.1 Exportar Variáveis de Ambiente
```powershell
.\exportar_variaveis_render.ps1
```

Isso criará:
- `variaveis_render_exportadas.csv`
- `variaveis_render.env`
- `variaveis_render.json`

#### 1.2 Fazer Backup do Banco de Dados

**Opção A: Via Render Dashboard**
1. Acesse Render Dashboard
2. Vá no banco de dados
3. Settings → Download Backup

**Opção B: Via Script (se tiver acesso)**
```bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

---

### 2️⃣ Criar Conta Railway (5 min)

1. Acesse: https://railway.app
2. Clique em "Start a New Project"
3. Faça login com GitHub
4. Autorize o Railway a acessar seus repositórios

---

### 3️⃣ Criar Projeto Railway (5 min)

1. No Railway, clique em "New Project"
2. Selecione "Deploy from GitHub repo"
3. Escolha: `fernandoxavier02/IFRS-16`
4. Railway detectará automaticamente o projeto

---

### 4️⃣ Configurar PostgreSQL (10 min)

1. No projeto Railway, clique em "+ New"
2. Selecione "Database" → "PostgreSQL"
3. Railway criará automaticamente:
   - Banco de dados PostgreSQL
   - Variável `DATABASE_URL` (automaticamente conectada)

**Importar Dados (se necessário):**
```bash
# Via Railway CLI
railway connect
railway run psql $DATABASE_URL < backup_YYYYMMDD.sql
```

---

### 5️⃣ Configurar Backend (15 min)

1. **Adicionar Serviço:**
   - No projeto Railway, clique em "+ New"
   - Selecione "GitHub Repo"
   - Escolha o repositório `IFRS-16`

2. **Configurar Root Directory:**
   - Vá em Settings → Source
   - Root Directory: `backend`

3. **Configurar Build:**
   - Settings → Build
   - Build Command: `pip install -r requirements.txt`
   - (Railway detecta automaticamente Python)

4. **Configurar Deploy:**
   - Settings → Deploy
   - Start Command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

5. **Adicionar Variáveis de Ambiente:**
   - Settings → Variables
   - Clique em "Raw Editor"
   - Cole o conteúdo de `variaveis_render.env` (remova `DATABASE_URL` pois Railway já cria)
   - Ou adicione manualmente:
     ```
     JWT_SECRET_KEY=...
     STRIPE_SECRET_KEY=...
     FRONTEND_URL=... (atualizar depois)
     API_URL=... (atualizar depois)
     ```

6. **Conectar ao Banco:**
   - Settings → Variables
   - Railway já criou `DATABASE_URL` automaticamente
   - Não precisa fazer nada!

---

### 6️⃣ Fazer Deploy (10 min)

1. Railway fará deploy automático após configurar
2. Aguarde o build completar (2-5 minutos)
3. Railway fornecerá uma URL como: `https://ifrs16-backend-production.up.railway.app`

**Verificar Deploy:**
```bash
# Testar health check
curl https://[sua-url-railway]/health
```

---

### 7️⃣ Configurar Frontend (15 min)

**Opção A: Railway (Recomendado para simplicidade)**

1. No mesmo projeto Railway, clique em "+ New"
2. Selecione "GitHub Repo" novamente
3. Escolha o mesmo repositório
4. Settings → Source → Root Directory: `.` (raiz)
5. Settings → Deploy → Start Command: (deixe vazio ou `echo "Static site"`)
6. Railway detectará que é um site estático

**Opção B: Vercel (Melhor performance para frontend)**

1. Acesse: https://vercel.com
2. Login com GitHub
3. "Add New Project"
4. Escolha repositório `IFRS-16`
5. Framework Preset: "Other"
6. Root Directory: `.`
7. Deploy!

---

### 8️⃣ Atualizar URLs (10 min)

Após ter as URLs do Railway:

1. **Atualizar `backend/app/config.py`:**
```python
FRONTEND_URL: str = "https://[sua-url-frontend]"
API_URL: str = "https://[sua-url-backend-railway]"
```

2. **Atualizar `backend/app/main.py`:**
```python
ALLOWED_ORIGINS = [
    "https://[sua-url-frontend]",
    # ... outras origens
]
```

3. **Atualizar `Calculadora_IFRS16_Deploy.html`:**
```javascript
const getApiUrl = () => {
    const hostname = window.location.hostname;
    if (hostname.includes('railway.app') || hostname.includes('vercel.app')) {
        return 'https://[sua-url-backend-railway]';
    }
    return 'http://localhost:8000';
};
```

4. **Atualizar Variáveis no Railway:**
   - Settings → Variables
   - Atualizar `FRONTEND_URL` e `API_URL`
   - Atualizar `CORS_ORIGINS`

5. **Fazer novo deploy** (Railway faz automaticamente ao commitar)

---

### 9️⃣ Atualizar Webhooks Stripe (5 min)

Se você tem webhooks do Stripe configurados:

1. Acesse: https://dashboard.stripe.com/webhooks
2. Edite o webhook
3. Atualize a URL para: `https://[sua-url-backend-railway]/api/payments/webhook`
4. Salve

---

### 🔟 Testar Tudo (15 min)

- [ ] Backend health check funciona
- [ ] API docs acessível (`/docs`)
- [ ] Frontend carrega
- [ ] Login funciona
- [ ] Calculadora funciona
- [ ] Stripe funciona (testar checkout)
- [ ] Webhooks funcionam

---

### 1️⃣1️⃣ Limpar Render (5 min)

**APENAS APÓS CONFIRMAR QUE TUDO FUNCIONA:**

1. Render Dashboard → Services
2. Pausar/Deletar serviços (não deletar ainda, apenas pausar)
3. Aguardar 1 semana para garantir
4. Depois deletar definitivamente

---

## 🎯 CHECKLIST COMPLETO

### Antes
- [ ] Backup do banco de dados
- [ ] Exportar variáveis de ambiente
- [ ] Código no GitHub atualizado

### Durante
- [ ] Conta Railway criada
- [ ] Projeto Railway criado
- [ ] PostgreSQL configurado
- [ ] Backend configurado e deployado
- [ ] Frontend configurado e deployado
- [ ] URLs atualizadas
- [ ] Variáveis de ambiente configuradas

### Depois
- [ ] Tudo testado e funcionando
- [ ] Webhooks atualizados
- [ ] Render pausado (não deletado ainda)
- [ ] Documentação atualizada

---

## 🆘 TROUBLESHOOTING

### Backend não inicia
- Verificar logs no Railway
- Verificar se `DATABASE_URL` está configurada
- Verificar se `PORT` está sendo usado corretamente

### Erro de migração do banco
```bash
# Conectar ao banco Railway
railway connect
railway run alembic upgrade head
```

### CORS errors
- Verificar `CORS_ORIGINS` nas variáveis
- Verificar `ALLOWED_ORIGINS` no código

### Frontend não encontra API
- Verificar função `getApiUrl()` no HTML
- Verificar se `API_URL` está correta

---

## 📞 AJUDA

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Railway Status: https://status.railway.app

---

**Tempo total estimado:** 1-2 horas  
**Dificuldade:** ⭐⭐ (Fácil)
