# 20-ARCHITECTURE.md
> **Arquitetura — IFRS 16**

---

## Diagrama de Arquitetura

```
┌─────────────────┐     HTTPS      ┌─────────────────┐
│  Firebase       │◄──────────────►│  Browser        │
│  Hosting        │                │  (HTML/JS)      │
│  (Static)       │                └────────┬────────┘
└─────────────────┘                         │
                                            │ API calls
                                            ▼
┌─────────────────┐     HTTPS      ┌─────────────────┐
│  Stripe         │◄──────────────►│  Cloud Run      │
│  (Webhooks)     │                │  (FastAPI)      │
└─────────────────┘                └────────┬────────┘
                                            │
                                            │ asyncpg + SSL
                                            ▼
                                   ┌─────────────────┐
                                   │  PostgreSQL     │
                                   │  (Render)       │
                                   └─────────────────┘
```

---

## Estrutura de Diretórios

```
IFRS 16/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py             # Entry point
│   │   ├── config.py           # Pydantic Settings
│   │   ├── database.py         # SQLAlchemy async
│   │   ├── models.py           # ORM models
│   │   ├── schemas.py          # Pydantic schemas
│   │   ├── crud.py             # DB operations
│   │   ├── auth.py             # JWT auth
│   │   ├── routers/            # API routes
│   │   │   ├── admin.py
│   │   │   ├── auth.py
│   │   │   ├── contracts.py
│   │   │   ├── licenses.py
│   │   │   ├── payments.py
│   │   │   ├── stripe.py
│   │   │   └── user_dashboard.py
│   │   └── services/           # Business logic
│   ├── tests/                  # pytest tests
│   │   ├── conftest.py         # Fixtures
│   │   └── test_*.py           # Test modules
│   ├── alembic/                # Migrations
│   ├── requirements.txt
│   └── Dockerfile
├── docs/ai/                    # Context Pack
├── .windsurf/                  # Windsurf config
├── .claude/                    # Claude config
├── *.html                      # Frontend pages
├── firebase.json               # Firebase config
├── AGENTS.md                   # Codex config
└── CLAUDE.md                   # Claude config
```

---

## Entry Points

| Propósito | Arquivo |
|-----------|---------|
| Backend app | `backend/app/main.py` |
| Frontend principal | `Calculadora_IFRS16_Deploy.html` |
| Landing page | `landing.html` |
| Login | `login.html` |
| Admin panel | `admin.html` |
| Pricing | `pricing.html` |

---

## Fluxo de Autenticação

```
1. User → POST /auth/login (email, password)
2. Backend → Verifica credenciais no PostgreSQL
3. Backend → Gera JWT token
4. User ← Recebe { access_token, token_type }
5. User → Requests com header: Authorization: Bearer <token>
```

---

## Fluxo de Pagamento (Stripe)

```
1. User → Seleciona plano em pricing.html
2. Frontend → Cria checkout session via API
3. User → Redirecionado para Stripe Checkout
4. User → Completa pagamento
5. Stripe → Webhook para /stripe/webhook
6. Backend → Cria/atualiza Subscription e License
7. User → Redirecionado para success page
```

---

## Invariantes

1. **License validation** — Sempre checar propriedade `is_valid`
2. **CORS** — Origins explícitas; sem wildcards com credentials
3. **SSL** — PostgreSQL usa `ssl='require'`
4. **Migrations** — Usar Alembic em produção
5. **Secrets** — Nunca logar ou expor em responses

---

*Ver `30-DATA_BACKEND.md` para models e schemas.*
