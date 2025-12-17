# 🌐 URLs do Sistema - Firebase

**Data:** 11 de Dezembro de 2025  
**Ambiente:** Produção (Firebase)

---

## 📍 URLs DO FIREBASE

### Frontend (Firebase Hosting)

| Descrição | URL |
|-----------|-----|
| **URL Principal** | https://ifrs16-app.web.app |
| **URL Alternativa** | https://ifrs16-app.firebaseapp.com |
| **Calculadora** | https://ifrs16-app.web.app/Calculadora_IFRS16_Deploy.html |
| **Login Admin** | https://ifrs16-app.web.app/login.html |
| **Painel Admin** | https://ifrs16-app.web.app/admin.html |
| **Página de Preços** | https://ifrs16-app.web.app/pricing.html |

### Backend (Cloud Run)

**URL será configurada após deploy:**
```
https://ifrs16-backend-[hash].run.app
```

**Endpoints:**
- Health: `https://[cloud-run-url]/health`
- API Docs: `https://[cloud-run-url]/docs`
- API Root: `https://[cloud-run-url]/`

---

## 🔐 CREDENCIAIS DE ACESSO

### Usuário Master (Admin)

| Campo | Valor |
|------|-------|
| **Email** | `fernandocostaxavier@gmail.com` |
| **Senha** | `Master@2025!` |
| **Role** | `SUPERADMIN` |

**Como fazer login:**
1. Acesse: https://ifrs16-app.web.app/login.html
2. Clique na aba "Administrador"
3. Use o email (não username)
4. Digite a senha

---

## 🔄 MIGRAÇÃO DO RENDER

### URLs Antigas (Render) - Manter temporariamente

- Frontend: https://ifrs-16-1.onrender.com
- Backend: https://ifrs-16.onrender.com

**Status:** Manter ativo durante migração, depois desativar.

---

## 📊 STATUS DA MIGRAÇÃO

- [x] Projeto Firebase criado
- [x] Firebase CLI instalado
- [x] Frontend deployado no Firebase Hosting
- [ ] Cloud SQL PostgreSQL configurado
- [ ] Backend deployado no Cloud Run
- [ ] URLs atualizadas no código
- [ ] Variáveis de ambiente configuradas
- [ ] Webhooks Stripe atualizados
- [ ] Testes completos realizados

---

**Última atualização:** 11/12/2025
