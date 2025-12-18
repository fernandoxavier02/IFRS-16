"""
FastAPI Application Principal
API de Gerenciamento de Licenças IFRS 16
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .database import init_db, close_db
from .routers import (
    licenses_router,
    admin_router,
    auth_router,
    payments_router,
    user_dashboard_router
)
from .routers.contracts import router as contracts_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Gerencia o ciclo de vida da aplicação.
    - Inicializa conexões ao iniciar
    - Fecha conexões ao encerrar
    """
    # Startup
    print("🚀 Iniciando API de Licenciamento IFRS 16...")
    print(f"📊 Ambiente: {settings.ENVIRONMENT}")

    # Fail-fast em produção: evita deploy com placeholders (sk_live_...) e SMTP incompleto
    if settings.ENVIRONMENT == "production":
        stripe_key = (getattr(settings, "STRIPE_SECRET_KEY", "") or "").strip()
        webhook_secret = (getattr(settings, "STRIPE_WEBHOOK_SECRET", "") or "").strip()

        smtp_user = (getattr(settings, "SMTP_USER", "") or "").strip()
        smtp_pass = (getattr(settings, "SMTP_PASSWORD", "") or "").strip()
        smtp_host = (getattr(settings, "SMTP_HOST", "") or "").strip()
        smtp_port = getattr(settings, "SMTP_PORT", None)

        errors = []

        if not stripe_key or stripe_key.endswith("...") or not stripe_key.startswith("sk_"):
            errors.append("STRIPE_SECRET_KEY inválida/placeholder")
        if not webhook_secret or webhook_secret.endswith("...") or not webhook_secret.startswith("whsec_"):
            errors.append("STRIPE_WEBHOOK_SECRET inválida/placeholder")

        if not smtp_host:
            errors.append("SMTP_HOST ausente")
        if not smtp_port:
            errors.append("SMTP_PORT ausente")
        if not smtp_user:
            errors.append("SMTP_USER ausente")
        if not smtp_pass:
            errors.append("SMTP_PASSWORD ausente")

        if errors:
            msg = " | ".join(errors)
            print(f"❌ Configuração inválida em produção: {msg}")
            raise RuntimeError(f"Configuração inválida em produção: {msg}")
    
    # Criar tabelas automaticamente se não existirem
    print("📦 Inicializando banco de dados...")
    try:
        await init_db()
        print("✅ Banco de dados inicializado com sucesso!")
    except Exception as e:
        print(f"⚠️ Erro ao inicializar banco: {e}")
        # Continuar mesmo com erro - tabelas podem já existir
    
    yield
    
    # Shutdown
    print("🛑 Encerrando API...")
    await close_db()


# Criar aplicação FastAPI
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
| Trial | 1 | Grátis | ❌ | ❌ |
| Basic | 3 | R$ 299 | ✅ | ❌ |
| Pro | 20 | R$ 499 | ✅ | ✅ (5) |
| Enterprise | ∞ | R$ 999 | ✅ | ✅ (∞) |

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
    print(f"❌ Erro não tratado: {exc}")
    print(f"📋 Traceback:\n{error_trace}")
    # Mostrar erro detalhado sempre para debug (remover em produção final)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Erro interno do servidor",
            "error": str(exc),
            "type": type(exc).__name__
        }
    )


# Incluir routers
app.include_router(auth_router)
app.include_router(licenses_router)
app.include_router(admin_router)
app.include_router(payments_router)
app.include_router(user_dashboard_router)
app.include_router(contracts_router)


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

