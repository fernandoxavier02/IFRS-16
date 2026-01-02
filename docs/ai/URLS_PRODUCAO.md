# 🌐 URLs DE PRODUÇÃO

> **IMPORTANTE:** Sempre use estas URLs nas documentações e comunicações

---

## 🎯 URLs PRINCIPAIS

### Frontend (Produção)
- **Domínio Principal:** `https://fxstudioai.com`
- **Firebase (Fallback):** `https://ifrs16-app.web.app`

### Backend (API)
- **Cloud Run:** `https://ifrs16-backend-1051753255664.us-central1.run.app`
- **Base Path:** `/api`

### Banco de Dados
- **Supabase:** `db.hxfqmfqfqmfqmfqm.supabase.co`
- **Pooler:** `aws-0-us-east-1.pooler.supabase.com`

---

## 📄 PÁGINAS PRINCIPAIS

| Página | URL |
|--------|-----|
| Landing | `https://fxstudioai.com/landing.html` |
| Login | `https://fxstudioai.com/login.html` |
| Cadastro | `https://fxstudioai.com/register.html` |
| Dashboard | `https://fxstudioai.com/dashboard.html` |
| Calculadora | `https://fxstudioai.com/Calculadora_IFRS16_Deploy` |
| Pricing | `https://fxstudioai.com/pricing.html` |

---

## 🔗 LINKS ESPECIAIS

### Com Parâmetros

**Login com Licença:**
```
https://fxstudioai.com/login.html?license=FX2025-IFRS16-PRO-XXXXX
```

**Verificação de Email:**
```
https://fxstudioai.com/verify-email.html?token=UUID-TOKEN
```

**Dashboard com Validação:**
```
https://fxstudioai.com/dashboard.html?validate_license=FX2025-IFRS16-PRO-XXXXX
```

---

## 📧 EMAILS

### Templates de Email

Todos os emails devem usar o domínio **fxstudioai.com**:

**Email de Boas-Vindas:**
- Link: `https://fxstudioai.com/login.html?license={license_key}`

**Email de Licença Ativada:**
- Link: `https://fxstudioai.com/login.html?license={license_key}`

**Email de Verificação:**
- Link: `https://fxstudioai.com/verify-email.html?token={token}`

**Email de Reset de Senha:**
- Link: `https://fxstudioai.com/reset-password.html?token={token}`

---

## 🚀 DEPLOY

### Firebase Hosting

**Comando:**
```bash
cd "IFRS 16-20251217T150830Z-1-001/IFRS 16"
firebase deploy --only hosting --project ifrs16-app
```

**Resultado:**
- ✅ Deploy para `ifrs16-app.web.app`
- ✅ Automático para `fxstudioai.com` (domínio customizado)

### Backend (Cloud Run)

**Comando:**
```bash
cd "IFRS 16-20251217T150830Z-1-001/IFRS 16/backend"
gcloud builds submit --tag gcr.io/ifrs16-app/ifrs16-backend
gcloud run deploy ifrs16-backend --image gcr.io/ifrs16-app/ifrs16-backend --region us-central1 --project ifrs16-app
```

---

## ⚠️ NUNCA USE

- ❌ `localhost`
- ❌ `127.0.0.1`
- ❌ URLs de desenvolvimento
- ❌ IPs diretos

---

## ✅ CHECKLIST DE DEPLOY

Antes de fazer deploy, verificar:

- [ ] Todas as URLs nos emails apontam para `fxstudioai.com`
- [ ] `config.js` tem a URL correta do backend
- [ ] Links internos usam caminhos relativos ou `fxstudioai.com`
- [ ] Documentação atualizada com URLs corretas
- [ ] `CHANGELOG_AI.md` atualizado

---

**Última Atualização:** 2026-01-02 22:45  
**Status:** ✅ Todas as URLs validadas e em produção
