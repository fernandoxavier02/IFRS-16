# 10-STACK.md
> **Stack Tecnológica — IFRS 16**

---

## Camadas

| Camada | Tecnologia | Hospedagem |
|--------|------------|------------|
| **Frontend** | HTML/JS/CSS estático | Firebase Hosting |
| **Backend** | Python 3.11 + FastAPI | Google Cloud Run |
| **Database** | PostgreSQL 14+ (async) | Render |
| **Payments** | Stripe (webhooks) | — |
| **Auth** | JWT (python-jose) | — |

---

## Dependências Backend

```txt
# Core
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4

# Database
sqlalchemy>=2.0.25
asyncpg>=0.29.0
aiosqlite>=0.19.0
alembic>=1.13.1

# HTTP/Validation
httpx>=0.26.0
pydantic>=2.5.3
pydantic-settings>=2.1.0
email-validator>=2.1.0

# Payments
stripe>=7.10.0

# Testing
pytest>=7.4.4
pytest-asyncio>=0.23.3
pytest-cov>=4.1.0
```

---

## Comandos Essenciais

### Backend (executar em `backend/`)

| Ação | Comando |
|------|---------|
| Instalar deps | `pip install -r requirements.txt` |
| Dev server | `uvicorn app.main:app --reload --port 8000` |
| Testes | `pytest -v` |
| Testes + coverage | `pytest -v --cov=app --cov-report=html` |
| Migrations | `alembic upgrade head` |
| Nova migration | `alembic revision --autogenerate -m "desc"` |

### Frontend/Deploy (executar na raiz)

| Ação | Comando |
|------|---------|
| Deploy Firebase | `firebase deploy --only hosting --project ifrs16-app` |
| Deploy script | `.\deploy_firebase.ps1` |
| Testes E2E | `.\testar_sistema_completo.ps1` |

### Docker

| Ação | Comando |
|------|---------|
| Build | `docker build -t ifrs16-backend backend/` |
| Run | `docker run -p 8080:8080 ifrs16-backend` |

---

## URLs Produção

| Serviço | URL |
|---------|-----|
| **Frontend (Produção)** | https://fxstudioai.com |
| Frontend (Firebase) | https://ifrs16-app.web.app |
| Backend API | https://ifrs16-backend-1051753255664.us-central1.run.app |
| API Docs | https://ifrs16-backend-1051753255664.us-central1.run.app/docs |
| Firebase Console | https://console.firebase.google.com/project/ifrs16-app |

---

## Variáveis de Ambiente (Produção)

| Variável | Propósito |
|----------|-----------|
| `DATABASE_URL` | Connection string PostgreSQL |
| `JWT_SECRET_KEY` | Chave JWT |
| `ADMIN_TOKEN` | Token API admin |
| `STRIPE_SECRET_KEY` | Chave Stripe |
| `STRIPE_WEBHOOK_SECRET` | Secret webhook Stripe |
| `SMTP_*` | Configuração email |
| `ENVIRONMENT` | `development` ou `production` |

> ⚠️ **Nunca commitar segredos.** Use `.env` local (gitignored).

---

*Ver `20-ARCHITECTURE.md` para diagramas e fluxos.*
