"""
FastAPI Application Principal
API de Gerenciamento de Licenças IFRS 16
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .config import Settings, get_settings
from .database import (
    init_db,
    close_db,
    ensure_user_sessions_table,
    ensure_economic_indexes_table,
    ensure_reajuste_periodicidade_column,
    ensure_notifications_table,
)
from .routers import (
    licenses_router,
    admin_router,
    auth_router,
    payments_router,
    user_dashboard_router,
    economic_indexes_router,
    notifications_router,
    jobs_router,
)
from .routers.contracts import router as contracts_router

settings = get_settings()


def validate_critical_settings(current_settings: Settings) -> tuple[list[str], list[str]]:
    """
    Retorna tupla (erros_criticos, warnings) de configuração.
    Erros críticos bloqueiam o startup, warnings são apenas logados.
    """
    errors = []
    warnings = []

    stripe_key = (getattr(current_settings, "STRIPE_SECRET_KEY", "") or "").strip()
    webhook_secret = (getattr(current_settings, "STRIPE_WEBHOOK_SECRET", "") or "").strip()

    smtp_user = (getattr(current_settings, "SMTP_USER", "") or "").strip()
    smtp_pass = (getattr(current_settings, "SMTP_PASSWORD", "") or "").strip()
    smtp_host = (getattr(current_settings, "SMTP_HOST", "") or "").strip()
    smtp_port = getattr(current_settings, "SMTP_PORT", None)

    jwt_secret = (getattr(current_settings, "JWT_SECRET_KEY", "") or "").strip()
    admin_token = (getattr(current_settings, "ADMIN_TOKEN", "") or "").strip()

    # Erros críticos - bloqueiam startup
    if not stripe_key or stripe_key.endswith("...") or stripe_key.startswith("sk_test_"):
        errors.append("STRIPE_SECRET_KEY inválida/placeholder")

    if not jwt_secret or "sua-chave-secreta" in jwt_secret:
        errors.append("JWT_SECRET_KEY fraca/placeholder")

    # Warnings - não bloqueiam mas são logados
    if not webhook_secret or webhook_secret.endswith("...") or not webhook_secret.startswith("whsec_"):
        warnings.append("STRIPE_WEBHOOK_SECRET não configurada (webhooks não funcionarão)")

    if not smtp_host:
        warnings.append("SMTP_HOST ausente (emails não serão enviados)")
    if not smtp_port:
        warnings.append("SMTP_PORT ausente (emails não serão enviados)")
    if not smtp_user:
        warnings.append("SMTP_USER ausente (emails não serão enviados)")
    if not smtp_pass:
        warnings.append("SMTP_PASSWORD ausente (emails não serão enviados)")

    if not admin_token or "admin-token-super-secreto" in admin_token:
        warnings.append("ADMIN_TOKEN fraco/placeholder (use um token seguro)")

    return errors, warnings


def validate_stripe_config() -> None:
    """
    Valida que todos os price IDs do Stripe estão configurados.
    Fail-fast: lança RuntimeError se algum estiver ausente.

    Valida os 6 planos:
    - STRIPE_PRICE_BASIC_MONTHLY
    - STRIPE_PRICE_BASIC_YEARLY
    - STRIPE_PRICE_PRO_MONTHLY
    - STRIPE_PRICE_PRO_YEARLY
    - STRIPE_PRICE_ENTERPRISE_MONTHLY
    - STRIPE_PRICE_ENTERPRISE_YEARLY
    """
    current_settings = get_settings()

    required_prices = [
        "STRIPE_PRICE_BASIC_MONTHLY",
        "STRIPE_PRICE_BASIC_YEARLY",
        "STRIPE_PRICE_PRO_MONTHLY",
        "STRIPE_PRICE_PRO_YEARLY",
        "STRIPE_PRICE_ENTERPRISE_MONTHLY",
        "STRIPE_PRICE_ENTERPRISE_YEARLY",
    ]

    missing = []
    for price_var in required_prices:
        value = getattr(current_settings, price_var, None)
        if not value or not value.strip():
            missing.append(price_var)

    if missing:
        error_msg = (
            f"[ERROR] Configuracao Stripe incompleta! Faltam variaveis de ambiente:\n"
            + "\n".join(f"  - {var}" for var in missing)
        )
        print(error_msg)
        raise RuntimeError(f"Price IDs não configurados: {', '.join(missing)}")

    print("[OK] Configuracao Stripe validada com sucesso (6 price IDs)")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Gerencia o ciclo de vida da aplicação.
    - Inicializa conexões ao iniciar
    - Fecha conexões ao encerrar
    """
    # Startup
    print("[STARTUP] Iniciando API de Licenciamento IFRS 16...")
    print(f"[INFO] Ambiente: {settings.ENVIRONMENT}")

    # Validar configuração Stripe (6 price IDs obrigatórios)
    try:
        validate_stripe_config()
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        raise

    # Fail-fast em produção: evita deploy com placeholders críticos
    if settings.ENVIRONMENT == "production":
        errors, warnings = validate_critical_settings(settings)
        # Logar warnings (não bloqueiam)
        for warn in warnings:
            print(f"[WARN] {warn}")
        # Erros críticos bloqueiam startup
        if errors:
            msg = " | ".join(errors)
            print(f"[ERROR CRITICO] Configuracao incompleta em producao: {msg}")
            raise RuntimeError(f"Secrets inválidos em produção: {msg}")

    # Criar tabelas automaticamente apenas em desenvolvimento
    # Em produção, usar Alembic migrations para evitar drift
    if settings.ENVIRONMENT != "production":
        print("[INFO] Inicializando banco de dados (dev mode)...")
        try:
            await init_db()
            print("[OK] Banco de dados inicializado com sucesso!")
        except Exception as e:
            print(f"[WARN] Erro ao inicializar banco: {e}")
    else:
        print("[INFO] Producao: init_db desabilitado (use Alembic migrations)")

    # IMPORTANTE: Garantir que tabelas e colunas necessárias existem
    try:
        await ensure_user_sessions_table()
        await ensure_economic_indexes_table()
        await ensure_notifications_table()
        await ensure_reajuste_periodicidade_column()
    except Exception as e:
        print(f"[WARN] Erro ao criar tabelas/colunas: {e}")

    yield
    
    # Shutdown
    print("[SHUTDOWN] Encerrando API...")
    await close_db()


# Criar aplicação FastAPI
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="IFRS 16 License API",
    description="""
## API de Gerenciamento de Licenças

Sistema de controle de licenças para a Calculadora IFRS 16.

### Funcionalidades

- **Validação de Licenças**: Valide chaves de licença e obtenha tokens JWT
- **Verificação de Status**: Verifique se uma licença ainda está válida
- **Gerenciamento Admin**: Crie, revogue e reative licenças

### Autenticação

- **Endpoints públicos**: Use o header `Authorization: Bearer <token>`
- **Endpoints admin**: Use o header `X-Admin-Token`

### Tipos de Licença

| Tipo | Contratos/CNPJ | Preço/mês | Excel | Multi-usuário |
|------|----------------|-----------|-------|---------------|
| Trial | 1 | Grátis | [ERROR] | [ERROR] |
| Basic | 3 | R$ 299 | [OK] | [ERROR] |
| Pro | 20 | R$ 499 | [OK] | [OK] (5) |
| Enterprise | ∞ | R$ 999 | [OK] | [OK] (∞) |

---
© 2025 Fernando Xavier - Todos os direitos reservados
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configurar CORS - origens explícitas (wildcard não funciona com credentials)
ALLOWED_ORIGINS = [
    # Firebase Hosting
    "https://ifrs16-app.web.app",
    "https://ifrs16-app.firebaseapp.com",
    # Domínio customizado
    "https://fxstudioai.com",
    "https://www.fxstudioai.com",
    # GitHub Pages
    "https://fernandoxavier02.github.io",
    # Local
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:5173",
]
# Adicionar origens da config se existirem
ALLOWED_ORIGINS.extend([o for o in settings.cors_origins_list if o not in ALLOWED_ORIGINS])

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Exception handler global
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global para exceções não tratadas"""
    import traceback
    error_trace = traceback.format_exc()
    print(f"[ERROR] Erro nao tratado: {exc}")
    print(f"[TRACEBACK] {error_trace}")

    content = {"detail": "Erro interno do servidor"}
    if settings.DEBUG or settings.ENVIRONMENT != "production":
        content.update({
            "error": str(exc),
            "type": type(exc).__name__
        })

    # Adicionar headers CORS para evitar erro de CORS em exceções
    origin = request.headers.get("origin", "")
    headers = {}
    if origin in ALLOWED_ORIGINS:
        headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }

    return JSONResponse(status_code=500, content=content, headers=headers)


# Incluir routers
app.include_router(auth_router)
app.include_router(licenses_router)
app.include_router(admin_router)
app.include_router(payments_router)
app.include_router(user_dashboard_router)
app.include_router(contracts_router)
app.include_router(economic_indexes_router)
app.include_router(notifications_router)
app.include_router(jobs_router)
# stripe_router removido - funcionalidade consolidada em payments_router


# Rota raiz
@app.get("/", tags=["Root"])
async def root():
    """
    Rota raiz - informações básicas da API
    """
    return {
        "name": "IFRS 16 License API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint para monitoramento
    """
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
