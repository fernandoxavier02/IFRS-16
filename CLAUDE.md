# CLAUDE.md

> **For:** Claude Code  
> **Project:** IFRS 16 License Management System

---

## Session Protocol

1. **Read first:**
   - `docs/ai/PROJECT_CONTEXT.md` — Full context
   - `docs/ai/CHANGELOG_AI.md` — Recent changes

2. **Before editing:** List all files you will modify

3. **After editing:** Run verification command

4. **Log changes:** Update `docs/ai/CHANGELOG_AI.md`

---

## Project Structure

```
IFRS 16/
├── backend/                 # FastAPI backend (Python 3.11)
│   ├── app/                 # Application code
│   │   ├── main.py          # Entry point
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── routers/         # API routes
│   │   └── services/        # Business logic
│   ├── tests/               # pytest tests
│   └── alembic/             # DB migrations
├── *.html                   # Frontend pages
├── firebase.json            # Firebase config
└── docs/ai/                 # AI context files
```

---

## Commands

| Action | Command | Directory |
|--------|---------|-----------|
| Run backend | `uvicorn app.main:app --reload --port 8000` | `backend/` |
| Run tests | `pytest -v` | `backend/` |
| Run tests + coverage | `pytest -v --cov=app` | `backend/` |
| Run migrations | `alembic upgrade head` | `backend/` |
| Deploy frontend | `firebase deploy --only hosting` | root |
| E2E tests | `.\testar_sistema_completo.ps1` | root |

---

## Rules

See `.claude/rules/` for detailed rules:

- `00-core.md` — Core behavior rules
- `10-repo-map.md` — Repository structure
- `20-quality.md` — Quality standards

---

## Key Invariants

1. **License validation:** Always check `is_valid` property
2. **CORS:** Explicit origins only (no wildcards with credentials)
3. **SSL:** PostgreSQL requires `ssl='require'`
4. **Secrets:** Never log or expose; validate at startup
5. **Migrations:** Use Alembic in production

---

## Verification Commands

**Backend changes:**
```bash
cd backend && pytest -v
```

**Frontend changes:**
```powershell
.\testar_sistema_completo.ps1
```

---

## Stop Rules

- After 2 failed fixes → deeper root cause analysis
- If tests fail → read the test file first
- If architecture unclear → read PROJECT_CONTEXT.md

---

*Full documentation: `docs/ai/PROJECT_CONTEXT.md`*
