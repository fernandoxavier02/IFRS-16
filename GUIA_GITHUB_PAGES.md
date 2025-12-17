# 📦 Guia de Migração para GitHub Pages

**GitHub Pages** é perfeito para frontend estático e é **100% GRÁTIS**!

**Limitações:**
- ✅ Apenas frontend estático (HTML/CSS/JS)
- ❌ Não suporta backend
- ❌ Não suporta banco de dados
- ✅ Deploy automático do GitHub
- ✅ HTTPS automático
- ✅ Custom domain grátis

---

## 🎯 Arquitetura Recomendada: GitHub Pages + Railway

**Por quê essa combinação?**
- ✅ **GitHub Pages:** Frontend grátis, CDN, deploy automático
- ✅ **Railway:** Backend Python/FastAPI, PostgreSQL
- ✅ **Custo total:** $5-20/mês (apenas Railway)

---

## 📋 PASSO A PASSO - GitHub Pages

### 1️⃣ Preparar Repositório

Seu repositório já está no GitHub: `fernandoxavier02/IFRS-16`

### 2️⃣ Ativar GitHub Pages

1. Acesse: https://github.com/fernandoxavier02/IFRS-16/settings/pages
2. **Source:** Deploy from a branch
3. **Branch:** `main` (ou `gh-pages`)
4. **Folder:** `/` (root)
5. Salvar

### 3️⃣ Configurar `index.html` (Opcional)

Se quiser que `index.html` seja a página inicial:

1. Renomear `Calculadora_IFRS16_Deploy.html` para `index.html`
2. Ou criar `index.html` que redireciona:

```html
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url=Calculadora_IFRS16_Deploy.html">
</head>
<body>
    <p>Redirecionando...</p>
</body>
</html>
```

### 4️⃣ Deploy Automático

GitHub Pages faz deploy automático a cada push no branch `main`!

**URL será:** `https://fernandoxavier02.github.io/IFRS-16/`

**URLs das páginas:**
- `https://fernandoxavier02.github.io/IFRS-16/Calculadora_IFRS16_Deploy.html`
- `https://fernandoxavier02.github.io/IFRS-16/login.html`
- `https://fernandoxavier02.github.io/IFRS-16/admin.html`
- `https://fernandoxavier02.github.io/IFRS-16/pricing.html`

---

## 🔧 Configurar CORS no Backend

Como GitHub Pages usa domínio diferente, precisa atualizar CORS:

### `backend/app/main.py`:

```python
ALLOWED_ORIGINS = [
    "https://fernandoxavier02.github.io",
    "https://ifrs-16-1.onrender.com",  # Manter por enquanto
    "https://[sua-url-railway]",  # Adicionar Railway
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
]
```

### Variável de Ambiente:

```
CORS_ORIGINS=https://fernandoxavier02.github.io,https://[sua-url-railway]
```

---

## 🔄 Atualizar URLs no Frontend

### `Calculadora_IFRS16_Deploy.html`:

```javascript
const getApiUrl = () => {
    const hostname = window.location.hostname;
    
    // GitHub Pages
    if (hostname.includes('github.io')) {
        return 'https://[sua-url-backend-railway]';
    }
    
    // Render (temporário)
    if (hostname.includes('onrender.com')) {
        return 'https://ifrs16-backend-fbbm.onrender.com';
    }
    
    // Desenvolvimento local
    return 'http://localhost:8000';
};
```

---

## 🌐 Custom Domain (Opcional)

Se quiser usar seu próprio domínio:

1. **Adicionar arquivo `CNAME`:**
   ```
   seu-dominio.com
   ```

2. **Configurar DNS:**
   - Tipo: `CNAME`
   - Nome: `@` ou `www`
   - Valor: `fernandoxavier02.github.io`

3. **Ativar no GitHub:**
   - Settings → Pages → Custom domain
   - Adicionar domínio
   - Habilitar HTTPS

---

## 📁 Estrutura Recomendada

```
IFRS-16/
├── backend/              # Backend (não deployado no Pages)
├── Calculadora_IFRS16_Deploy.html
├── login.html
├── admin.html
├── pricing.html
├── index.html            # Página inicial (opcional)
├── assets/               # Imagens, CSS, etc.
└── .gitignore           # Ignorar backend se necessário
```

**Nota:** GitHub Pages serve tudo na raiz, então seus arquivos HTML já estão prontos!

---

## 🚀 Deploy Automático com GitHub Actions (Opcional)

Criar `.github/workflows/deploy.yml`:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./
          exclude_assets: 'backend/**'
```

---

## ⚠️ Limitações do GitHub Pages

1. **Apenas arquivos estáticos** - Não roda PHP, Python, etc.
2. **Sem backend** - Precisa de backend separado (Railway)
3. **Sem banco de dados** - Precisa de banco separado (Railway)
4. **Limite de 1GB** - Geralmente suficiente para frontend
5. **100GB bandwidth/mês** - Grátis, geralmente suficiente

---

## 💰 Custos

**GitHub Pages:** **100% GRÁTIS** ✅

**Backend (Railway):** $5-20/mês

**Total:** $5-20/mês (apenas backend)

---

## 🎯 RECOMENDAÇÃO FINAL

**GitHub Pages + Railway:**
- ✅ Frontend grátis no GitHub Pages
- ✅ Backend no Railway ($5-20/mês)
- ✅ PostgreSQL no Railway (incluído)
- ✅ Deploy automático
- ✅ CDN global (GitHub)
- ✅ HTTPS automático

**Setup:**
1. Ativar GitHub Pages no repositório
2. Deploy backend no Railway (seguir `PLANO_MIGRACAO_RAILWAY.md`)
3. Atualizar URLs no código
4. Pronto! ✅

---

## 📋 Checklist GitHub Pages

- [ ] Repositório no GitHub (já tem)
- [ ] Ativar GitHub Pages em Settings
- [ ] Escolher branch `main`
- [ ] Testar URL: `https://fernandoxavier02.github.io/IFRS-16/`
- [ ] Atualizar CORS no backend
- [ ] Atualizar `getApiUrl()` no frontend
- [ ] Deploy backend no Railway
- [ ] Testar tudo funcionando

---

## 🔗 Links Úteis

- GitHub Pages Docs: https://docs.github.com/pages
- Seu repositório: https://github.com/fernandoxavier02/IFRS-16
- Pages Settings: https://github.com/fernandoxavier02/IFRS-16/settings/pages

---

**Última atualização:** 11/12/2025
