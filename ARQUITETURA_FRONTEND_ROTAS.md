# Arquitetura Frontend - Sistema de Rotas e Autenticação

> **Última atualização:** 2026-01-01
> **Versão do sistema:** 1.1.0 (Build 2025.12.18)

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Estrutura de Páginas](#estrutura-de-páginas)
3. [Sistema de Rotas](#sistema-de-rotas)
4. [Autenticação e Autorização](#autenticação-e-autorização)
5. [Configuração de API](#configuração-de-api)
6. [LocalStorage Keys](#localstorage-keys)
7. [Fluxos de Navegação](#fluxos-de-navegação)
8. [Proteção de Rotas](#proteção-de-rotas)

---

## 🎯 Visão Geral

**Arquitetura:** Multi-Page Application (MPA) com HTML estático
**Framework:** Nenhum (Vanilla JavaScript)
**Autenticação:** JWT Bearer Token + localStorage
**API Backend:** Google Cloud Run (Python/FastAPI)
**Hosting:** Firebase Hosting

### Tecnologias Principais

- **Frontend:** HTML5, CSS3 (Tailwind inline), Vanilla JavaScript
- **Autenticação:** JWT (JSON Web Tokens)
- **Storage:** localStorage (client-side)
- **Navegação:** `window.location.href` (sem SPA router)

---

## 📄 Estrutura de Páginas

### Páginas Públicas (Sem Autenticação)

| Arquivo | Descrição | Rota |
|---------|-----------|------|
| `index.html` | Página inicial (redirect) | `/` |
| `landing.html` | Landing page principal | `/landing.html` |
| `landing-new.html` | Landing page alternativa | `/landing-new.html` |
| `pricing.html` | Página de preços/planos | `/pricing.html` |
| `auth-choice.html` | Escolha Login/Registro | `/auth-choice.html` |
| `login.html` | Login de usuários | `/login.html` |
| `register.html` | Cadastro de novos usuários | `/register.html` |
| `reset-password.html` | Recuperação de senha | `/reset-password.html` |
| `admin.html` | Login administrativo | `/admin.html` |
| `teste-assinatura.html` | Teste de assinatura Stripe | `/teste-assinatura.html` |

### Páginas Protegidas (Requer Autenticação)

| Arquivo | Descrição | Requisitos | Rota |
|---------|-----------|------------|------|
| `dashboard.html` | Dashboard do usuário | Token JWT | `/dashboard.html` |
| `Calculadora_IFRS16_Deploy.html` | Calculadora IFRS 16 | Token JWT + Licença | `/Calculadora_IFRS16_Deploy.html` |
| `relatorios.html` | Relatórios consolidados | Token JWT | `/relatorios.html` |

---

## 🛣️ Sistema de Rotas

### Navegação (Sem Framework de SPA)

O sistema **não utiliza** React Router, Vue Router ou similar. A navegação é implementada via:

1. **JavaScript redirect:**
   ```javascript
   window.location.href = 'pagina.html';
   ```

2. **Links HTML diretos:**
   ```html
   <a href="pagina.html">Link</a>
   ```

3. **Meta refresh:**
   ```html
   <meta http-equiv="refresh" content="0; url=landing.html">
   ```

### Fluxo de Navegação Principal

```
┌─────────────┐
│ index.html  │ (auto redirect)
└──────┬──────┘
       ↓
┌──────────────┐
│ landing.html │ (público)
└──────┬───────┘
       ↓
┌──────────────────┐
│ auth-choice.html │
└────┬────────┬────┘
     ↓        ↓
┌─────────┐ ┌──────────────┐
│login.html│ │register.html │
└────┬─────┘ └──────┬───────┘
     └────────┬─────┘
              ↓
     ┌────────────────┐
     │ dashboard.html │ (protegido)
     └────────┬───────┘
              ↓
     ┌──────────────────────────────┐
     │ Calculadora_IFRS16_Deploy.html│ (protegido + licença)
     └──────────────────────────────┘
```

---

## 🔐 Autenticação e Autorização

### Arquivos JavaScript Core

| Arquivo | Localização | Responsabilidade |
|---------|-------------|------------------|
| `config.js` | `assets/js/` | Configuração da API e detecção de ambiente |
| `auth.js` | `assets/js/` | Lógica de login, registro e licenciamento |
| `route-protection.js` | `assets/js/` | Proteção de rotas e validação JWT |
| `session-manager.js` | `assets/js/` | Gerenciamento de sessões simultâneas |

### Fluxo de Autenticação

**Referência:** `assets/js/auth.js` (linhas 5-87)

#### 1. Login do Usuário

```javascript
// Função: fazerLogin()
POST /api/auth/login
Body: { email, password }

Response: {
  access_token: "jwt_token",
  session_token: "session_uuid",
  user_type: "user" | "admin"
}
```

**Dados salvos no localStorage:**
- `ifrs16_user_token` → Token de acesso
- `ifrs16_auth_token` → Token alternativo (compatibilidade)
- `ifrs16_session_token` → ID da sessão ativa
- `ifrs16_user_type` → Tipo de usuário (admin/user)

#### 2. Buscar Dados do Usuário

```javascript
GET /api/auth/me
Headers: { Authorization: "Bearer {token}" }

Response: { id, email, name, ... }
```

**Salvo em:** `ifrs16_user_data` (JSON stringificado)

#### 3. Validação de Licença

**Referência:** `assets/js/auth.js` (linhas 89-137)

```javascript
// Função: validarLicenca()
POST /api/validate-license
Body: {
  key: "LICENSE-KEY",
  machine_id: "fingerprint",
  app_version: "1.1.0"
}

Response: {
  valid: true,
  token: "license_token",
  data: {
    customer_name: "Nome",
    expires_at: "2026-12-31",
    license_type: "pro_monthly",
    features: [...]
  }
}
```

**Dados salvos:**
- `ifrs16_license` → Chave da licença
- `ifrs16_token` → Token de licenciamento
- `ifrs16_customer_name` → Nome do cliente

---

## 🛡️ Proteção de Rotas

**Arquivo:** `assets/js/route-protection.js`

### Páginas Protegidas

```javascript
protectedPages: [
  'dashboard.html',
  'Calculadora_IFRS16_Deploy.html'
]
```

### Fluxo de Verificação

```javascript
// 1. Verificar se é página protegida
isProtectedPage() → true/false

// 2. Verificar se está autenticado
isAuthenticated() → Checa localStorage.getItem('ifrs16_auth_token')

// 3. Validar formato do token JWT
isValidTokenFormat(token) → {
  - Verificar 3 partes (header.payload.signature)
  - Decodificar payload (base64)
  - Verificar expiração (exp claim)
}

// 4. Se falhar → Redirecionar
redirectToLogin() → window.location.href = 'auth-choice.html'
```

### Validação JWT (Cliente)

**Referência:** `route-protection.js` (linhas 55-80)

```javascript
function isValidTokenFormat(token) {
  const parts = token.split('.');
  if (parts.length !== 3) return false;

  const payload = JSON.parse(atob(parts[1]));

  // Verificar expiração
  if (payload.exp) {
    const now = Math.floor(Date.now() / 1000);
    if (payload.exp < now) return false;
  }

  return true;
}
```

**⚠️ Nota:** Esta é uma validação **básica** no cliente. A validação real de assinatura é feita no backend.

---

## ⚙️ Configuração de API

**Arquivo:** `assets/js/config.js`

### Detecção Automática de Ambiente

```javascript
const getApiUrl = () => {
  const hostname = window.location.hostname;

  // Produção (Firebase Hosting)
  if (
    hostname.includes('fxstudioai.com') ||
    hostname.includes('web.app') ||
    hostname.includes('firebaseapp.com')
  ) {
    return 'https://ifrs16-backend-1051753255664.us-central1.run.app';
  }

  // Desenvolvimento Local
  return 'http://localhost:8000';
};
```

### Configurações Globais

```javascript
const CONFIG = {
  VERSION: '1.1.0',
  BUILD: '2025.12.18',
  API_URL: getApiUrl(),
  URL_COMPRA: window.location.origin + '/pricing.html',
  CHECK_INTERVAL: 300000, // 5 minutos
};
```

---

## 💾 LocalStorage Keys

### Autenticação

| Key | Tipo | Descrição | Exemplo |
|-----|------|-----------|---------|
| `ifrs16_auth_token` | String (JWT) | Token de autenticação principal | `eyJhbGciOiJIUzI1NiIs...` |
| `ifrs16_user_token` | String (JWT) | Token alternativo (compatibilidade) | `eyJhbGciOiJIUzI1NiIs...` |
| `ifrs16_session_token` | String (UUID) | ID da sessão ativa | `550e8400-e29b-41d4-a716...` |
| `ifrs16_user_type` | String | Tipo de usuário | `"admin"` ou `"user"` |
| `ifrs16_user_data` | JSON String | Dados completos do usuário | `{"id":"uuid","email":"..."}` |

### Licenciamento

| Key | Tipo | Descrição | Exemplo |
|-----|------|-----------|---------|
| `ifrs16_license` | String | Chave de licença | `IFRS16-XXXX-YYYY-ZZZZ` |
| `ifrs16_token` | String | Token de licença validado | `license_token_hash` |
| `ifrs16_customer_name` | String | Nome do cliente | `"João Silva"` |

### Sessões Simultâneas

| Key | Tipo | Descrição |
|-----|------|-----------|
| `ifrs16_session_token` | String (UUID) | Identificador único da sessão |
| `ifrs16_device_fingerprint` | String | Fingerprint do dispositivo |
| `ifrs16_last_activity` | Timestamp | Última atividade registrada |

---

## 🔄 Fluxos de Navegação Detalhados

### 1. Primeiro Acesso (Usuário Novo)

```
landing.html
  → Clicar "Começar"
    → auth-choice.html
      → Escolher "Criar Conta"
        → register.html
          → POST /api/auth/register
            → Retorna { user_id, requires_subscription: true }
              → Redireciona para Stripe Checkout
                → Retorna para dashboard.html?session_id=xxx
                  → Webhook cria licença automaticamente
                    → Dashboard exibe status "Ativo"
```

### 2. Login Existente

```
landing.html
  → Clicar "Login"
    → auth-choice.html
      → Escolher "Já tenho conta"
        → login.html
          → POST /api/auth/login
            → Salva tokens no localStorage
              → Verifica licença (GET /api/auth/me/license)
                → Se ativo: dashboard.html
                → Se sem licença: mostra tela de ativação
```

### 3. Acesso à Calculadora

```
dashboard.html (autenticado)
  → Verificar subscription_status
    → Se "active":
      → Botão "Usar Calculadora" habilitado
        → window.location.href = 'Calculadora_IFRS16_Deploy.html'
          → route-protection.js valida token
            → auth.js valida licença
              → Exibe calculadora
    → Se "inactive" ou "canceled":
      → Botão desabilitado
        → Exibir "Assinar Plano" (link para pricing)
```

### 4. Logout

```
dashboard.html ou Calculadora
  → Clicar "Sair"
    → Executar logout()
      → localStorage.clear() (limpa todos os tokens)
        → window.location.href = 'login.html'
```

---

## 📍 Principais Redirecionamentos

### Dashboard (`dashboard.html`)

| Linha | Condição | Destino |
|-------|----------|---------|
| 441, 453 | Sem token válido | `login.html` |
| 730 | Botão "Usar Calculadora" | `Calculadora_IFRS16_Deploy.html` |
| 663, 748 | Botão "Ver Planos" | `landing.html#pricing` |
| 651 | Portal de Assinatura Stripe | `data.portal_url` (externo) |
| 669 | Logout | `login.html` |

### Auth Choice (`auth-choice.html`)

| Linha | Ação | Destino |
|-------|------|---------|
| 139 | Click "Já tenho conta" | `login.html` |
| 157 | Click "Criar conta" | `register.html` |
| 174 | Link "Voltar" | `landing.html` |
| 185 | Token válido encontrado | `dashboard.html` |

### Calculadora (`Calculadora_IFRS16_Deploy.html`)

| Linha | Link | Destino |
|-------|------|---------|
| 416 | Painel Administrativo | `admin.html` |
| 430 | Relatórios | `relatorios.html` |
| 341, 382 | Voltar | `landing.html` |

---

## 🔒 Controle de Sessões Simultâneas

**Arquivo:** `assets/js/session-manager.js`

### Implementação

1. **No Login:**
   - Backend gera `session_token` único (UUID)
   - Salva em `user_sessions` table com:
     - `user_id`
     - `session_token`
     - `device_fingerprint`
     - `ip_address`
     - `user_agent`
     - `last_activity`

2. **Verificação Periódica:**
   ```javascript
   setInterval(() => {
     // Verifica se sessão ainda é válida
     GET /api/auth/validate-session
     Headers: {
       Authorization: Bearer {token},
       X-Session-Token: {session_token}
     }
   }, 300000); // 5 minutos
   ```

3. **Detecção de Conflito:**
   - Backend detecta múltiplas sessões ativas
   - Retorna erro 401 com `session_conflict: true`
   - Frontend exibe modal: "Sua conta está em uso em outro dispositivo"

---

## 🚀 Boas Práticas

### Segurança

✅ **Tokens JWT armazenados em localStorage** (não sessionStorage para persistência)
✅ **Validação de expiração no cliente** (validação completa no backend)
✅ **HTTPS obrigatório em produção** (Firebase Hosting)
✅ **CORS configurado** no backend para domínios específicos
✅ **Session tokens** para controle de dispositivos

⚠️ **Importante:** localStorage é vulnerável a XSS. Certifique-se de sanitizar todos os inputs.

### Performance

✅ **Detecção automática de ambiente** (sem rebuild)
✅ **Verificação de sessão a cada 5min** (não a cada request)
✅ **Cache de dados do usuário** (reduz chamadas à API)

### Manutenção

✅ **Versionamento no config.js** para tracking
✅ **Logs em desenvolvimento** (`console.log` apenas se localhost)
✅ **Fallbacks para compatibilidade** (múltiplas chaves de token)

---

## 🐛 Troubleshooting

### Usuário Não Consegue Logar

1. Verificar console do browser (F12):
   - Erro de CORS? → Verificar backend CORS config
   - 401 Unauthorized? → Credenciais inválidas
   - 500 Server Error? → Verificar logs do Cloud Run

2. Verificar localStorage:
   ```javascript
   console.log(localStorage.getItem('ifrs16_auth_token'));
   ```

3. Testar endpoint manualmente:
   ```bash
   curl -X POST https://ifrs16-backend-1051753255664.us-central1.run.app/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"teste@exemplo.com","password":"senha123"}'
   ```

### Página Protegida Não Carrega

1. Verificar `route-protection.js` está carregado:
   ```html
   <script src="assets/js/route-protection.js"></script>
   ```

2. Verificar token no localStorage

3. Verificar console: mensagens de erro do route-protection

### API URL Errada

1. Verificar `window.location.hostname` no console
2. Verificar lógica em `config.js` (linhas 6-20)
3. Forçar ambiente (temporário):
   ```javascript
   localStorage.setItem('__force_api_url', 'https://...');
   ```

---

## 📚 Referências

- **Backend API:** Cloud Run - `ifrs16-backend-1051753255664.us-central1.run.app`
- **Frontend Hosting:** Firebase Hosting - `fxstudioai.com`
- **Documentação Backend:** `backend/README.md`
- **Fluxo de Assinatura:** `FLUXO_ASSINATURA.md`
- **Deploy:** `DEPLOY_FINAL_CONCLUIDO.md`

---

## 📝 Histórico de Alterações

| Data | Versão | Mudanças |
|------|--------|----------|
| 2026-01-01 | 1.0 | Documentação inicial completa |
| 2025-12-31 | - | Implementação de sessões simultâneas |
| 2025-12-19 | - | Sistema de licenciamento dual |
| 2025-12-17 | - | Migração para Cloud SQL |

---

**Mantido por:** FX Studio AI
**Contato:** contato@fxstudioai.com
