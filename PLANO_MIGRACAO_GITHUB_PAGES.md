# 📦 Plano de Migração: GitHub Pages + Railway

**Objetivo:** Frontend grátis no GitHub Pages + Backend no Railway  
**Prazo:** 30-60 minutos  
**Custo:** $5-20/mês (apenas backend)

---

## ✅ VANTAGENS DESTA COMBINAÇÃO

- ✅ **Frontend 100% grátis** (GitHub Pages)
- ✅ **CDN global** (GitHub)
- ✅ **Deploy automático** (a cada push)
- ✅ **HTTPS automático**
- ✅ **Backend confiável** (Railway, sem sleep)
- ✅ **PostgreSQL incluído** (Railway)
- ✅ **Custo baixo** ($5-20/mês apenas backend)

---

## 📋 PASSO A PASSO

### 1️⃣ Ativar GitHub Pages (5 min)

1. Acesse: https://github.com/fernandoxavier02/IFRS-16/settings/pages
2. **Source:** Deploy from a branch
3. **Branch:** `main`
4. **Folder:** `/` (root)
5. Clique em **Save**

**URL será:** `https://fernandoxavier02.github.io/IFRS-16/`

**Teste:** Aguarde 1-2 minutos e acesse a URL acima.

---

### 2️⃣ Configurar Backend no Railway (30 min)

Seguir `PLANO_MIGRACAO_RAILWAY.md` - Passos 2 a 6.

**Resumo:**
1. Criar conta Railway
2. Criar projeto
3. Adicionar PostgreSQL
4. Configurar backend (Root: `backend`)
5. Adicionar variáveis de ambiente
6. Deploy

**URL backend será:** `https://[seu-projeto].up.railway.app`

---

### 3️⃣ Atualizar CORS no Backend (5 min)

#### 3.1 Atualizar `backend/app/main.py`:

```python
ALLOWED_ORIGINS = [
    "https://fernandoxavier02.github.io",  # GitHub Pages
    "https://ifrs-16-1.onrender.com",  # Manter temporariamente
    "https://[sua-url-railway].up.railway.app",  # Railway
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]
```

#### 3.2 Atualizar Variável de Ambiente no Railway:

```
CORS_ORIGINS=https://fernandoxavier02.github.io,https://[sua-url-railway].up.railway.app
```

---

### 4️⃣ Atualizar Frontend (10 min)

#### 4.1 Atualizar `Calculadora_IFRS16_Deploy.html`:

Encontrar função `getApiUrl()` (por volta da linha 730) e atualizar:

```javascript
const getApiUrl = () => {
    const hostname = window.location.hostname;
    
    // GitHub Pages
    if (hostname.includes('github.io')) {
        return 'https://[sua-url-backend-railway].up.railway.app';
    }
    
    // Render (temporário, remover depois)
    if (hostname.includes('onrender.com')) {
        return 'https://ifrs16-backend-fbbm.onrender.com';
    }
    
    // Railway direto
    if (hostname.includes('railway.app')) {
        return 'https://[sua-url-backend-railway].up.railway.app';
    }
    
    // Desenvolvimento local
    return 'http://localhost:8000';
};
```

#### 4.2 Fazer Commit e Push:

```bash
git add Calculadora_IFRS16_Deploy.html backend/app/main.py
git commit -m "Atualizar URLs para GitHub Pages + Railway"
git push origin main
```

GitHub Pages fará deploy automático em 1-2 minutos!

---

### 5️⃣ Atualizar Variáveis de Ambiente (5 min)

No Railway Dashboard → Settings → Variables:

Atualizar:
```
FRONTEND_URL=https://fernandoxavier02.github.io/IFRS-16
API_URL=https://[sua-url-backend-railway].up.railway.app
CORS_ORIGINS=https://fernandoxavier02.github.io,https://[sua-url-backend-railway].up.railway.app
```

---

### 6️⃣ Testar Tudo (10 min)

- [ ] Frontend carrega: `https://fernandoxavier02.github.io/IFRS-16/Calculadora_IFRS16_Deploy.html`
- [ ] Backend health: `https://[sua-url-railway]/health`
- [ ] API docs: `https://[sua-url-railway]/docs`
- [ ] Login funciona
- [ ] Calculadora funciona
- [ ] CORS não dá erro (verificar console do navegador)

---

### 7️⃣ Atualizar Webhooks Stripe (5 min)

Se tiver webhooks configurados:

1. Acesse: https://dashboard.stripe.com/webhooks
2. Edite o webhook
3. URL: `https://[sua-url-backend-railway]/api/payments/webhook`
4. Salvar

---

## 🎯 CHECKLIST COMPLETO

### Frontend (GitHub Pages)
- [ ] GitHub Pages ativado
- [ ] URL testada e funcionando
- [ ] `getApiUrl()` atualizado
- [ ] Commit e push feito
- [ ] Deploy automático funcionando

### Backend (Railway)
- [ ] Conta Railway criada
- [ ] Projeto criado
- [ ] PostgreSQL configurado
- [ ] Backend deployado
- [ ] Variáveis de ambiente configuradas
- [ ] CORS atualizado
- [ ] Health check funcionando

### Testes
- [ ] Frontend acessível
- [ ] Backend respondendo
- [ ] Login funciona
- [ ] Calculadora funciona
- [ ] Stripe funciona
- [ ] Sem erros de CORS

---

## 🆘 TROUBLESHOOTING

### Frontend não carrega no GitHub Pages
- Verificar se GitHub Pages está ativado
- Aguardar 1-2 minutos após ativar
- Verificar branch correto (`main`)
- Verificar se arquivos estão no repositório

### CORS errors
- Verificar `ALLOWED_ORIGINS` no código
- Verificar `CORS_ORIGINS` nas variáveis
- Verificar URL exata do GitHub Pages (com `/IFRS-16/`)

### Frontend não encontra API
- Verificar função `getApiUrl()` no HTML
- Verificar console do navegador para erros
- Verificar se URL do Railway está correta

### Backend não inicia
- Verificar logs no Railway
- Verificar variáveis de ambiente
- Verificar `DATABASE_URL` está configurada

---

## 📊 COMPARAÇÃO DE CUSTOS

| Item | GitHub Pages | Railway | Total |
|------|--------------|---------|-------|
| **Frontend** | ✅ Grátis | - | $0 |
| **Backend** | - | $5-20/mês | $5-20 |
| **PostgreSQL** | - | Incluído | $0 |
| **CDN** | ✅ Incluído | - | $0 |
| **HTTPS** | ✅ Grátis | ✅ Grátis | $0 |
| **TOTAL** | | | **$5-20/mês** |

---

## 🎉 PRONTO!

Agora você tem:
- ✅ Frontend grátis no GitHub Pages
- ✅ Backend confiável no Railway
- ✅ Deploy automático
- ✅ Sem problemas de sleep
- ✅ Custo baixo

**Próximo passo:** Desativar Render após confirmar que tudo funciona!

---

**Tempo total:** 30-60 minutos  
**Dificuldade:** ⭐⭐ (Fácil)
