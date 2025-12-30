# PROJECT_CONTEXT.md
> **Last updated:** 2025-12-30  
> **Version:** 1.1.0  
> **Maintainer:** AI Context Pack

---

## 1. Project Overview

**IFRS 16 License Management System** — A SaaS application for IFRS 16 lease accounting calculations with a license/subscription management backend.

| Layer | Technology | Hosting |
|-------|------------|---------|
| **Frontend** | Static HTML/JS/CSS | Firebase Hosting |
| **Backend** | Python 3.11 + FastAPI | Google Cloud Run |
| **Database** | PostgreSQL 14+ | Render (external) |
| **Payments** | Stripe (webhooks) | — |
| **Auth** | JWT (python-jose) | — |

---

## 2. Repository Structure

```
IFRS 16/
├── backend/                    # FastAPI backend (Python)
│   ├── app/
│   │   ├── main.py             # FastAPI app entry point
│   │   ├── config.py           # Pydantic Settings (env vars)
│   │   ├── database.py         # SQLAlchemy async engine
│   │   ├── models.py           # SQLAlchemy ORM models
│   │   ├── schemas.py          # Pydantic request/response schemas
│   │   ├── crud.py             # Database operations
│   │   ├── auth.py             # JWT authentication
│   │   ├── routers/            # API route modules
│   │   │   ├── admin.py
│   │   │   ├── auth.py
│   │   │   ├── contracts.py
│   │   │   ├── licenses.py
│   │   │   ├── payments.py
│   │   │   ├── stripe.py
│   │   │   └── user_dashboard.py
│   │   └── services/           # Business logic services
│   ├── tests/                  # Pytest test suite
│   │   ├── conftest.py         # Fixtures (SQLite in-memory)
│   │   └── test_*.py           # Test modules
│   ├── alembic/                # Database migrations
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Cloud Run container
│   ├── pytest.ini              # Pytest configuration
│   └── .env                    # Local env vars (gitignored)
├── assets/                     # Static assets (CSS, JS, images)
├── mcp/                        # MCP server integrations
├── *.html                      # Frontend pages (landing, login, admin, etc.)
├── firebase.json               # Firebase Hosting config
├── deploy_firebase.ps1         # Deployment script
└── testar_sistema_completo.ps1 # E2E test script
```

---

## 3. Key Entry Points

| Purpose | File |
|---------|------|
| Backend app | `backend/app/main.py` |
| Frontend main | `Calculadora_IFRS16_Deploy.html` |
| Landing page | `landing.html` |
| Login page | `login.html` |
| Admin panel | `admin.html` |
| Pricing page | `pricing.html` |

---

## 4. Commands Reference

### Backend (run from `backend/` directory)

| Action | Command |
|--------|---------|
| **Install deps** | `pip install -r requirements.txt` |
| **Run dev server** | `uvicorn app.main:app --reload --port 8000` |
| **Run prod server** | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| **Run tests** | `pytest -v` |
| **Run tests + coverage** | `pytest -v --cov=app --cov-report=html` |
| **Run specific test** | `pytest tests/test_licenses.py -v` |
| **Run migrations** | `alembic upgrade head` |
| **Create migration** | `alembic revision --autogenerate -m "description"` |

### Frontend / Deploy (run from project root)

| Action | Command |
|--------|---------|
| **Deploy Firebase** | `firebase deploy --only hosting --project ifrs16-app` |
| **Full deploy** | `.\deploy_firebase.ps1` |
| **E2E tests** | `.\testar_sistema_completo.ps1` |

### Docker (backend)

| Action | Command |
|--------|---------|
| **Build image** | `docker build -t ifrs16-backend backend/` |
| **Run container** | `docker run -p 8080:8080 ifrs16-backend` |

---

## 5. Architecture & Data Flow

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

### Core Domain Models

| Model | Purpose |
|-------|---------|
| `User` | Customer accounts (email, password, Stripe customer ID) |
| `AdminUser` | Admin panel users (superadmin/admin roles) |
| `License` | License keys with type (Trial/Basic/Pro/Enterprise) |
| `Subscription` | Stripe subscription tracking |
| `Contract` | IFRS 16 lease contracts |
| `ValidationLog` | License validation audit trail |

### License Types & Features

| Type | Max Contracts | Excel Export | Multi-user |
|------|---------------|--------------|------------|
| Trial | 5 | ❌ | ❌ |
| Basic | 50 | ✅ | ❌ |
| Pro | 500 | ✅ | ✅ (5) |
| Enterprise | ∞ | ✅ | ✅ (∞) |

---

## 6. API Authentication

| Endpoint Type | Auth Method |
|---------------|-------------|
| Public | None |
| User endpoints | `Authorization: Bearer <JWT>` |
| Admin endpoints | `X-Admin-Token` header OR Admin JWT |

---

## 7. Environment Variables

**Required in production** (set in Cloud Run):

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string |
| `JWT_SECRET_KEY` | JWT signing key |
| `ADMIN_TOKEN` | Admin API token |
| `STRIPE_SECRET_KEY` | Stripe API key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signing secret |
| `SMTP_*` | Email configuration |
| `ENVIRONMENT` | `development` or `production` |

> ⚠️ **Never commit secrets.** Use `.env` locally (gitignored).

---

## 8. Testing Strategy

- **Framework:** pytest + pytest-asyncio
- **Database:** SQLite in-memory (via `aiosqlite`)
- **Client:** `httpx.AsyncClient` with ASGI transport
- **Fixtures:** See `backend/tests/conftest.py`

### Test Categories

| Marker | Purpose |
|--------|---------|
| `@pytest.mark.asyncio` | Async tests |
| `@pytest.mark.slow` | Long-running tests |
| `@pytest.mark.integration` | Integration tests |

---

## 9. Invariants & Constraints

1. **License validation** — Always check `is_valid` property (status + expiry + revoked)
2. **CORS** — Explicit origins only; no wildcards with credentials
3. **SSL required** — PostgreSQL connections use `ssl='require'`
4. **Migrations** — Always use Alembic in production; `init_db()` only for dev
5. **Secrets** — Never log or expose in responses; validate at startup in production

---

## 10. Production URLs

| Service | URL |
|---------|-----|
| Frontend | https://ifrs16-app.web.app |
| Backend API | https://ifrs16-backend-1051753255664.us-central1.run.app |
| API Docs | https://ifrs16-backend-1051753255664.us-central1.run.app/docs |

---

## 11. Session Start Checklist

Before making any changes, AI agents MUST:

1. [ ] **Read this file** (`docs/ai/PROJECT_CONTEXT.md`)
2. [ ] **Read latest changelog** (`docs/ai/CHANGELOG_AI.md`)
3. [ ] **List files to modify** before editing
4. [ ] **Select verification command:**
   - Backend changes: `pytest -v` (from `backend/`)
   - Frontend changes: Manual browser test or `.\testar_sistema_completo.ps1`
   - Full stack: `.\testar_sistema_completo.ps1`
5. [ ] **Run verification** after changes
6. [ ] **Update CHANGELOG_AI.md** with changes made

---

## 12. File Modification Protocol

1. **Read first** — Always read the file before editing
2. **Minimal edits** — Prefer small, focused changes
3. **Preserve style** — Match existing code conventions
4. **No orphan imports** — Imports at top of file only
5. **Test before commit** — Run relevant tests
6. **Document changes** — Update CHANGELOG_AI.md

---

*This context pack is tool-agnostic and designed for use with OpenAI Codex, Claude Code, and Windsurf Cascade.*
