# 10-repo-map.md — Repository Map

## Stack

| Layer | Technology |
|-------|------------|
| Frontend | Static HTML/JS/CSS |
| Backend | Python 3.11 + FastAPI |
| Database | PostgreSQL 14+ (async) |
| Auth | JWT (python-jose) |
| Payments | Stripe |
| Hosting FE | Firebase Hosting |
| Hosting BE | Google Cloud Run |

## Directory Structure

```text
IFRS 16/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entry
│   │   ├── config.py        # Settings
│   │   ├── database.py      # SQLAlchemy async
│   │   ├── models.py        # ORM models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── crud.py          # DB operations
│   │   ├── auth.py          # JWT auth
│   │   ├── routers/         # API routes
│   │   └── services/        # Business logic
│   ├── tests/               # pytest tests
│   ├── alembic/             # Migrations
│   └── requirements.txt
├── assets/                  # CSS, JS, images
├── mcp/                     # MCP integrations
├── docs/ai/                 # AI context files
├── *.html                   # Frontend pages
├── firebase.json            # Firebase config
├── AGENTS.md                # Codex config
└── CLAUDE.md                # Claude config
```

## Key Files

| Purpose | Path |
|---------|------|
| Backend entry | `backend/app/main.py` |
| Models | `backend/app/models.py` |
| Config | `backend/app/config.py` |
| Test fixtures | `backend/tests/conftest.py` |
| Main calculator | `Calculadora_IFRS16_Deploy.html` |
