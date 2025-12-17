# 🌐 URLs do Sistema IFRS 16

**Data:** 11 de Dezembro de 2025  
**Ambiente:** Produção (Render)

---

## 📍 Mapa de URLs

### 👥 Para Usuários Finais

| Descrição | URL | Uso |
|-----------|-----|-----|
| **Calculadora IFRS 16** | https://ifrs-16-1.onrender.com/Calculadora_IFRS16_Deploy.html | Aplicação principal para cálculos |
| **Login de Usuários** | https://ifrs-16-1.onrender.com/Calculadora_IFRS16_Deploy.html | Login integrado na calculadora |
| **Página de Preços** | https://ifrs-16-1.onrender.com/pricing.html | Planos e assinaturas |

### 🔧 Para Administradores

| Descrição | URL | Uso |
|-----------|-----|-----|
| **Login Admin** | https://ifrs-16-1.onrender.com/login.html | Login exclusivo para admins (aba "Administrador") |
| **Painel Admin** | https://ifrs-16-1.onrender.com/admin.html | Gerenciamento do sistema |

### 🔌 Backend / API

| Descrição | URL | Uso |
|-----------|-----|-----|
| **API Backend** | https://ifrs-16.onrender.com | Servidor de API |
| **Documentação API** | https://ifrs-16.onrender.com/docs | Swagger/OpenAPI docs |
| **Health Check** | https://ifrs-16.onrender.com/health | Status da API |

---

## 🎯 Fluxo de Acesso

### Para Usuários Comuns

```
1. Acessa: Calculadora_IFRS16_Deploy.html
2. Faz login com email/senha OU ativa licença
3. Usa a calculadora IFRS 16
```

### Para Administradores

```
1. Acessa: login.html
2. Clica na aba "Administrador"
3. Login com: fernandocostaxavier@gmail.com / Master@2025!
4. É redirecionado para: admin.html
5. Gerencia usuários, licenças, etc.
```

---

## ⚠️ IMPORTANTE - Diferenças

### ❌ NÃO CONFUNDA!

| O que | URL Errada | URL Correta |
|-------|------------|-------------|
| **Login Admin** | ~~Calculadora_IFRS16_Deploy.html~~ | **login.html** (aba Admin) |
| **Login Usuário** | ~~login.html~~ | **Calculadora_IFRS16_Deploy.html** |

### 🔑 Tipos de Login

**1. Login de Usuário (Calculadora)**
- URL: `Calculadora_IFRS16_Deploy.html`
- Acesso: Usuários com licença
- Credenciais: Email + senha do usuário OU chave de licença
- Destino: Calculadora IFRS 16

**2. Login de Administrador**
- URL: `login.html` (aba "Administrador")
- Acesso: Apenas administradores
- Credenciais: `fernandocostaxavier@gmail.com` / `Master@2025!`
- Destino: Painel administrativo

---

## 🗺️ Estrutura do Site

```
https://ifrs-16-1.onrender.com/
│
├── Calculadora_IFRS16_Deploy.html  ← Aplicação principal (usuários)
├── login.html                       ← Login admin (aba "Administrador")
├── admin.html                       ← Painel administrativo
├── pricing.html                     ← Página de preços
├── register.html                    ← Registro de usuários
└── index.html                       ← Página inicial (se existir)
```

---

## 🔗 Links Rápidos

### Acesso Direto - Administrador

**Login Admin:**
```
https://ifrs-16-1.onrender.com/login.html
```
👉 Clique na aba "Administrador" e use:
- Email: `fernandocostaxavier@gmail.com`
- Senha: `Master@2025!`

### Acesso Direto - Usuário

**Calculadora:**
```
https://ifrs-16-1.onrender.com/Calculadora_IFRS16_Deploy.html
```
👉 Faça login com suas credenciais de usuário ou ative sua licença

---

## 🔌 Endpoints da API

### Autenticação

```
POST /api/auth/login              - Login de usuário
POST /api/auth/admin/login        - Login de admin
POST /api/auth/register           - Registro de usuário
GET  /api/auth/me                 - Dados do usuário logado
GET  /api/auth/admin/me           - Dados do admin logado
```

### Licenças

```
GET  /api/licenses                - Listar licenças (admin)
POST /api/licenses/generate       - Gerar licença (admin)
POST /api/licenses/activate       - Ativar licença (usuário)
GET  /api/licenses/validate       - Validar licença
```

### Administração

```
GET  /api/admin/users             - Listar usuários
GET  /api/admin/subscriptions     - Listar assinaturas
GET  /api/admin/stats             - Estatísticas do sistema
```

---

## 📊 Status dos Serviços

| Serviço | URL Base | Status |
|---------|----------|--------|
| **Frontend** | https://ifrs-16-1.onrender.com | ✅ Ativo |
| **Backend** | https://ifrs-16.onrender.com | ✅ Ativo |
| **Database** | PostgreSQL (Virginia) | ✅ Ativo |

---

## 🧪 Testar Conectividade

### Frontend
```bash
curl https://ifrs-16-1.onrender.com/Calculadora_IFRS16_Deploy.html
```

### Backend
```bash
curl https://ifrs-16.onrender.com/health
```

### API Docs
```bash
# Abra no navegador:
https://ifrs-16.onrender.com/docs
```

---

## 📝 Notas

1. **CORS configurado** para:
   - `https://ifrs-16-1.onrender.com`
   - `https://fernandoxavier02.github.io`

2. **SSL/TLS** habilitado em todas as URLs

3. **Auto-deploy** ativo em ambos os serviços

4. **Região:** Virginia (US East)

---

**Última atualização:** 11/12/2025  
**Versão:** 1.0

