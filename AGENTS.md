# AGENTS.md

> **For:** OpenAI Codex  
> **Project:** IFRS 16 License Management System

---

## Quick Start

1. **Read context first:** `docs/ai/PROJECT_CONTEXT.md`
2. **Check recent changes:** `docs/ai/CHANGELOG_AI.md`
3. **List files before editing**
4. **Run tests after changes**

---

## Repository Overview

- **Backend:** `backend/` — Python 3.11 + FastAPI
- **Frontend:** `*.html` files in root — Static HTML/JS/CSS
- **Tests:** `backend/tests/` — pytest + pytest-asyncio
- **Migrations:** `backend/alembic/` — Alembic migrations

---

## Commands

### Backend (from `backend/` directory)

```bash
# Install dependencies
pip install -r requirements.txt

# Run dev server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest -v

# Run tests with coverage
pytest -v --cov=app --cov-report=html

# Run migrations
alembic upgrade head
```

### Deploy (from project root)

```powershell
# Deploy frontend to Firebase
firebase deploy --only hosting --project ifrs16-app

# Full deploy script
.\deploy_firebase.ps1

# E2E tests
.\testar_sistema_completo.ps1
```

---

## Key Files

| Purpose | Path |
|---------|------|
| Backend entry | `backend/app/main.py` |
| Models | `backend/app/models.py` |
| Schemas | `backend/app/schemas.py` |
| Config | `backend/app/config.py` |
| Routes | `backend/app/routers/*.py` |
| Tests | `backend/tests/test_*.py` |
| Test fixtures | `backend/tests/conftest.py` |

---

## Constraints

1. **Never commit secrets** — `.env` files are gitignored
2. **Always run tests** before completing a task
3. **Use Alembic** for database schema changes in production
4. **Preserve existing code style** — Match indentation, naming conventions
5. **Update CHANGELOG_AI.md** after making changes

---

## Verification

After any code change, run:

```bash
cd backend
pytest -v
```

For frontend changes, run:

```powershell
.\testar_sistema_completo.ps1
```

---

## Architecture

```
Browser → Firebase Hosting (static HTML/JS)
           ↓ API calls
       Cloud Run (FastAPI)
           ↓ asyncpg + SSL
       PostgreSQL (Render)
```

---

## Stop Rules

- **After 2 failed fix attempts:** Stop and analyze root cause
- **If tests fail unexpectedly:** Read the failing test file first
- **If unsure about architecture:** Read `docs/ai/PROJECT_CONTEXT.md`

---

*See `docs/ai/PROJECT_CONTEXT.md` for complete documentation.*
