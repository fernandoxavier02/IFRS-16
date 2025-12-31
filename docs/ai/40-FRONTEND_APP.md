# 40-FRONTEND_APP.md
> **Frontend & App — IFRS 16**

---

## Páginas Principais

| Arquivo | URL | Propósito |
|---------|-----|-----------|
| `landing.html` | `/` | Landing page (redirect) |
| `login.html` | `/login` | Página de login |
| `register.html` | `/register` | Registro de usuário |
| `pricing.html` | `/pricing` | Planos e preços |
| `dashboard.html` | `/dashboard` | Dashboard do usuário |
| `admin.html` | `/admin` | Painel administrativo |
| `Calculadora_IFRS16_Deploy.html` | `/Calculadora_IFRS16_Deploy` | Calculadora IFRS 16 |
| `relatorios.html` | `/relatorios` | Relatórios |

---

## Assets

```
assets/
├── css/
│   └── styles.css        # Estilos globais
├── js/
│   ├── auth.js           # Funções de autenticação
│   ├── api.js            # Chamadas API
│   └── calculator.js     # Lógica calculadora
├── images/
│   └── logo.png          # Logo
└── fonts/                # Fontes customizadas
```

---

## Configuração Firebase Hosting

```json
// firebase.json
{
  "hosting": {
    "public": ".",
    "redirects": [
      { "source": "/", "destination": "/landing.html", "type": 302 }
    ],
    "ignore": ["backend/**", "*.md", "*.json", "*.ps1"],
    "cleanUrls": true,
    "headers": [
      {
        "source": "**/*.html",
        "headers": [{ "key": "Cache-Control", "value": "no-cache" }]
      }
    ]
  }
}
```

---

## Integração com Backend

### API Base URL
```javascript
// Produção
const API_URL = 'https://ifrs16-backend-1051753255664.us-central1.run.app';

// Desenvolvimento
const API_URL = 'http://localhost:8000';
```

### Autenticação Frontend
```javascript
// Salvar token após login
localStorage.setItem('access_token', response.access_token);

// Usar token em requests
fetch(`${API_URL}/auth/me`, {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
});
```

---

## Deploy Frontend

```powershell
# Deploy simples
firebase deploy --only hosting --project ifrs16-app

# Deploy com script completo
.\deploy_firebase.ps1
```

### Verificação pós-deploy
1. Acessar https://ifrs16-app.web.app
2. Verificar console para erros JS
3. Testar login e calculadora

---

## Responsividade

- **Breakpoints:** 768px (tablet), 1024px (desktop)
- **Mobile-first:** Estilos base para mobile
- **Flexbox/Grid:** Layout responsivo

---

## Segurança Frontend

1. **Tokens:** Armazenar em `localStorage` (não cookies)
2. **HTTPS:** Sempre em produção
3. **CSP:** Configurado no Firebase
4. **XSS:** Input sanitization

---

*Ver `90-OPEN_QUESTIONS.md` para questões em aberto.*
