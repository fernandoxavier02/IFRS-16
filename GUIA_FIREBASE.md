# 🔥 Guia de Migração para Firebase

**Firebase** é uma excelente opção, especialmente se você já usa Google Cloud. Oferece:
- ✅ Firebase Hosting (frontend estático) - **GRÁTIS**
- ✅ Cloud Functions (backend) - Free tier generoso
- ✅ Firestore (banco NoSQL) ou Cloud SQL (PostgreSQL)
- ✅ Autenticação integrada
- ✅ CDN global
- ✅ Sem sleep

---

## 📊 Firebase vs Outros

| Recurso | Firebase | Railway | Render |
|---------|----------|---------|--------|
| **Frontend Hosting** | ✅ Grátis | ⚠️ Pago | ⚠️ Free (sleep) |
| **Backend (Functions)** | ✅ Free tier | ✅ Pago | ⚠️ Free (sleep) |
| **Banco de Dados** | ✅ Firestore/Cloud SQL | ✅ PostgreSQL | ✅ PostgreSQL |
| **CDN Global** | ✅ Sim | ❌ Não | ❌ Não |
| **Setup** | ⭐⭐ Médio | ⭐⭐⭐ Fácil | ⭐⭐⭐ Fácil |
| **Custo** | $0-25/mês | $5-20/mês | $0-7/mês |

---

## 🎯 Arquitetura Recomendada Firebase

### Opção 1: Firebase Completo (Recomendado)
- **Frontend:** Firebase Hosting (HTML estático)
- **Backend:** Cloud Functions (Node.js ou Python)
- **Banco:** Cloud SQL PostgreSQL (ou Firestore se adaptar)

### Opção 2: Firebase + Railway (Híbrido)
- **Frontend:** Firebase Hosting (melhor CDN)
- **Backend:** Railway (mais fácil para Python/FastAPI)
- **Banco:** Railway PostgreSQL

---

## 📋 PASSO A PASSO - Firebase Completo

### 1️⃣ Instalar Firebase CLI

```powershell
# Windows
npm install -g firebase-tools

# Ou via Chocolatey
choco install firebase-tools
```

### 2️⃣ Login no Firebase

```bash
firebase login
```

### 3️⃣ Inicializar Projeto Firebase

```bash
cd "c:\Projetos\IFRS 16"
firebase init
```

**Selecionar:**
- ✅ Hosting
- ✅ Functions (se quiser backend no Firebase)
- ✅ Firestore (opcional, se não usar Cloud SQL)

### 4️⃣ Configurar Firebase Hosting (Frontend)

O Firebase criará `firebase.json`. Configure:

```json
{
  "hosting": {
    "public": ".",
    "ignore": [
      "backend/**",
      "node_modules/**",
      ".git/**",
      "*.md",
      "firebase.json",
      "firebase-debug.log"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(html|js|css)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "max-age=3600"
          }
        ]
      }
    ]
  }
}
```

### 5️⃣ Deploy do Frontend

```bash
firebase deploy --only hosting
```

**URL será:** `https://[seu-projeto].web.app`

---

## 🔧 Configurar Backend no Firebase

### Opção A: Cloud Functions (Node.js)

**Criar `functions/index.js`:**

```javascript
const functions = require('firebase-functions');
const admin = require('firebase-admin');
admin.initializeApp();

// Proxy para seu backend FastAPI (se quiser manter no Railway)
exports.api = functions.https.onRequest((req, res) => {
  // Redirecionar para Railway ou outro backend
  const backendUrl = 'https://[sua-url-railway]';
  // Ou implementar lógica aqui
});

// Ou criar endpoints diretos
exports.hello = functions.https.onRequest((req, res) => {
  res.json({ message: 'Hello from Firebase!' });
});
```

### Opção B: Manter Backend no Railway (Recomendado)

Manter backend FastAPI no Railway e apenas usar Firebase para frontend.

**Vantagens:**
- ✅ Mantém código Python/FastAPI
- ✅ Não precisa reescrever backend
- ✅ Firebase Hosting para frontend (melhor CDN)

---

## 🗄️ Banco de Dados no Firebase

### Opção 1: Cloud SQL (PostgreSQL) - Recomendado

1. **Criar Cloud SQL:**
   - Firebase Console → Cloud SQL
   - Criar instância PostgreSQL
   - Configurar conexão

2. **Conectar Backend:**
   - Usar connection string do Cloud SQL
   - Mesmo código funciona!

### Opção 2: Firestore (NoSQL)

Requer adaptação do código para NoSQL (não recomendado se já tem PostgreSQL).

---

## 📝 Configurar Variáveis de Ambiente

No Firebase Functions ou Cloud Run:

```bash
firebase functions:config:set stripe.secret_key="sk_live_..."
firebase functions:config:set jwt.secret_key="..."
```

Ou via Firebase Console → Functions → Config.

---

## 🔄 Atualizar URLs no Código

### `Calculadora_IFRS16_Deploy.html`:

```javascript
const getApiUrl = () => {
    const hostname = window.location.hostname;
    
    // Firebase Hosting
    if (hostname.includes('web.app') || hostname.includes('firebaseapp.com')) {
        // Backend no Railway ou Cloud Functions
        return 'https://[sua-url-backend-railway]';
    }
    
    // Desenvolvimento local
    return 'http://localhost:8000';
};
```

---

## 💰 Custos Firebase

### Blaze Plan (Pay-as-you-go) - Necessário para Cloud Functions

**Gratuito (Spark Plan):**
- ✅ Hosting: 10GB storage, 360MB/day transfer
- ✅ Functions: 2 milhões invocações/mês
- ❌ Cloud SQL: Não incluído

**Pago (Blaze Plan):**
- Hosting: $0.026/GB storage, $0.15/GB transfer (após free tier)
- Functions: $0.40/milhão invocações (após free tier)
- Cloud SQL: $7-50/mês (depende do tamanho)

**Estimativa:** $10-30/mês para uso moderado

---

## 🎯 RECOMENDAÇÃO: Firebase Hosting + Railway Backend

**Por quê?**
- ✅ Firebase Hosting: Melhor CDN, grátis para frontend
- ✅ Railway Backend: Mantém Python/FastAPI, fácil setup
- ✅ Custo: $5-20/mês (Railway) + $0 (Firebase Hosting)

**Setup:**
1. Frontend no Firebase Hosting
2. Backend no Railway
3. Banco no Railway PostgreSQL

---

## 📋 Checklist Firebase

### Frontend (Firebase Hosting)
- [ ] Instalar Firebase CLI
- [ ] `firebase init hosting`
- [ ] Configurar `firebase.json`
- [ ] `firebase deploy --only hosting`
- [ ] Testar URL

### Backend (Railway ou Cloud Functions)
- [ ] Escolher: Railway (recomendado) ou Cloud Functions
- [ ] Se Railway: seguir `PLANO_MIGRACAO_RAILWAY.md`
- [ ] Se Cloud Functions: adaptar código para Node.js

### Banco de Dados
- [ ] Escolher: Railway PostgreSQL (recomendado) ou Cloud SQL
- [ ] Configurar conexão
- [ ] Migrar dados

---

## 🔗 Links Úteis

- Firebase Console: https://console.firebase.google.com
- Firebase Docs: https://firebase.google.com/docs
- Firebase Hosting: https://firebase.google.com/docs/hosting
- Cloud Functions: https://firebase.google.com/docs/functions

---

**Última atualização:** 11/12/2025
