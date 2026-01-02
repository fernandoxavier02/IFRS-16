"""
Configurações da aplicação usando Pydantic Settings
"""

from functools import lru_cache
from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configurações carregadas de variáveis de ambiente"""
    
    # Banco de dados
    # O Render fornece no formato postgresql://, mas precisamos postgresql+asyncpg://
    # A conversão é feita automaticamente em database.py
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ifrs16_licenses"
    
    # JWT
    JWT_SECRET_KEY: str = "sua-chave-secreta-super-complexa-aqui-mude-isso-em-producao"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 horas
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # Admin
    ADMIN_TOKEN: str = "admin-token-super-secreto-mude-isso"
    
    # Stripe
    STRIPE_SECRET_KEY: str = "sk_test_..."
    STRIPE_PUBLISHABLE_KEY: str = "pk_test_..."
    STRIPE_WEBHOOK_SECRET: str = "whsec_..."
    STRIPE_PRICING_TABLE_ID: Optional[str] = None  # ID da Pricing Table do Stripe (usado no frontend)

    # Preços por plano - Básico (até 5 contratos, 1 usuário)
    STRIPE_PRICE_BASIC_MONTHLY: Optional[str] = None
    STRIPE_PRICE_BASIC_YEARLY: Optional[str] = None

    # Preços por plano - Pro (até 20 contratos, 1 usuário)
    STRIPE_PRICE_PRO_MONTHLY: Optional[str] = None
    STRIPE_PRICE_PRO_YEARLY: Optional[str] = None

    # Preços por plano - Enterprise (ilimitado, 1 usuário)
    # Multi-usuário: cada usuário adicional precisa de assinatura própria
    STRIPE_PRICE_ENTERPRISE_MONTHLY: Optional[str] = None
    STRIPE_PRICE_ENTERPRISE_YEARLY: Optional[str] = None
    
    # URLs
    FRONTEND_URL: str = "http://localhost:3000"
    API_URL: str = "http://localhost:8000"
    
    # Cloud SQL (Produção)
    CLOUD_SQL_USER: Optional[str] = None
    CLOUD_SQL_PASSWORD: Optional[str] = None
    DATABASE_URL_PROD: Optional[str] = None
    
    # Firebase Storage
    FIREBASE_STORAGE_BUCKET: str = "ifrs16-app.firebasestorage.app"
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None  # Caminho para service account JSON

    # Limites de upload
    MAX_FILE_SIZE_MB: int = 10  # Tamanho máximo de arquivo em MB
    ALLOWED_MIME_TYPES: str = "application/pdf,image/jpeg,image/png,image/gif"

    @property
    def allowed_mime_types_list(self) -> List[str]:
        """Retorna lista de tipos MIME permitidos"""
        return [mt.strip() for mt in self.ALLOWED_MIME_TYPES.split(",")]

    # Email SMTP
    SMTP_HOST: str = "smtp.zoho.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""  # Senha de App do Gmail
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "IFRS 16 - Sistema de Gestão"
    SMTP_USE_SSL: bool = False
    SMTP_USE_STARTTLS: bool = True
    SMTP_TIMEOUT_SECONDS: int = 30
    
    # Ambiente
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # CORS
    CORS_ORIGINS: str = "http://localhost,http://127.0.0.1,http://localhost:3000,file://"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Retorna lista de origens CORS"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def async_database_url(self) -> str:
        """Retorna DATABASE_URL convertida para asyncpg"""
        url = self.DATABASE_URL
        if url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# =============================================================================
# LIMITES DE LICENÇA (Fonte única de verdade)
# =============================================================================
LICENSE_LIMITS = {
    "trial": {
        "max_contracts": 1,  # Trial: apenas visualização, sem criar contratos
        "max_activations": 1,
        "duration_hours": 24,  # Trial válido por 24 horas
        "export_excel": False,  # SEM download
        "export_csv": False,  # SEM download
        "export_pdf": False,  # SEM download
        "consolidation_reports": False,  # SEM emissão de relatórios na consolidação
        "support": False,
        "multi_user": False,
    },
    "basic": {
        "max_contracts": 5,  # Atualizado: 3 → 5 contratos
        "max_activations": 1,  # Cada usuário = 1 assinatura (sem multi-user)
        "export_excel": True,
        "export_csv": True,
        "export_pdf": True,
        "consolidation_reports": True,
        "support": True,
        "multi_user": False,  # Cada usuário precisa de assinatura própria
    },
    "pro": {
        "max_contracts": 20,
        "max_activations": 1,  # Cada usuário = 1 assinatura (sem multi-user)
        "export_excel": True,
        "export_csv": True,
        "export_pdf": True,
        "consolidation_reports": True,
        "support": True,
        "multi_user": False,  # Cada usuário precisa de assinatura própria
    },
    "enterprise": {
        "max_contracts": -1,  # Ilimitado
        "max_activations": 1,  # Cada usuário = 1 assinatura (sem multi-user)
        "export_excel": True,
        "export_csv": True,
        "export_pdf": True,
        "consolidation_reports": True,
        "support": True,
        "multi_user": False,  # Cada usuário precisa de assinatura própria
    },
}


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna instância cacheada das configurações.
    Use esta função para acessar configurações em toda a aplicação.
    """
    return Settings()


# =============================================================================
# CONFIGURAÇÃO CENTRALIZADA DE PLANOS (Fonte única de verdade)
# =============================================================================
PLAN_CONFIG: Dict[str, Dict[str, Any]] = {
    "basic_monthly": {
        "price_id_env": "STRIPE_PRICE_BASIC_MONTHLY",
        "license_type": "basic",
        "duration_months": 1,
        "max_contracts": 5,  # Atualizado: 3 → 5
        "max_activations": 1,  # Cada usuário = 1 assinatura
        "display_name": "Básico - Mensal",
        "amount": Decimal("299.00"),
        "currency": "brl",
        "features": {
            "export_excel": True,
            "export_csv": True,
            "export_pdf": True,
            "consolidation_reports": True,
            "support": "email",
            "multi_user": False,  # Sem multi-user, cada usuário precisa assinar
        }
    },
    "basic_yearly": {
        "price_id_env": "STRIPE_PRICE_BASIC_YEARLY",
        "license_type": "basic",
        "duration_months": 12,
        "max_contracts": 5,  # Atualizado: 3 → 5
        "max_activations": 1,  # Cada usuário = 1 assinatura
        "display_name": "Básico - Anual",
        "amount": Decimal("3229.20"),
        "currency": "brl",
        "features": {
            "export_excel": True,
            "export_csv": True,
            "export_pdf": True,
            "consolidation_reports": True,
            "support": "email",
            "multi_user": False,  # Sem multi-user, cada usuário precisa assinar
        }
    },
    "pro_monthly": {
        "price_id_env": "STRIPE_PRICE_PRO_MONTHLY",
        "license_type": "pro",
        "duration_months": 1,
        "max_contracts": 20,
        "max_activations": 1,  # Cada usuário = 1 assinatura
        "display_name": "Pro - Mensal",
        "amount": Decimal("499.00"),
        "currency": "brl",
        "features": {
            "export_excel": True,
            "export_csv": True,
            "export_pdf": True,
            "consolidation_reports": True,
            "support": "priority",
            "multi_user": False,  # Sem multi-user, cada usuário precisa assinar
            "api_access": True,
        }
    },
    "pro_yearly": {
        "price_id_env": "STRIPE_PRICE_PRO_YEARLY",
        "license_type": "pro",
        "duration_months": 12,
        "max_contracts": 20,
        "max_activations": 1,  # Cada usuário = 1 assinatura
        "display_name": "Pro - Anual",
        "amount": Decimal("5389.20"),
        "currency": "brl",
        "features": {
            "export_excel": True,
            "export_csv": True,
            "export_pdf": True,
            "consolidation_reports": True,
            "support": "priority",
            "multi_user": False,  # Sem multi-user, cada usuário precisa assinar
            "api_access": True,
        }
    },
    "enterprise_monthly": {
        "price_id_env": "STRIPE_PRICE_ENTERPRISE_MONTHLY",
        "license_type": "enterprise",
        "duration_months": 1,
        "max_contracts": -1,  # ilimitado
        "max_activations": 1,  # Cada usuário = 1 assinatura
        "display_name": "Enterprise - Mensal",
        "amount": Decimal("999.00"),
        "currency": "brl",
        "features": {
            "export_excel": True,
            "export_csv": True,
            "export_pdf": True,
            "consolidation_reports": True,
            "support": "dedicated",
            "multi_user": False,  # Sem multi-user, cada usuário precisa assinar
            "api_access": True,
            "training": True,
            "sla": True,
        }
    },
    "enterprise_yearly": {
        "price_id_env": "STRIPE_PRICE_ENTERPRISE_YEARLY",
        "license_type": "enterprise",
        "duration_months": 12,
        "max_contracts": -1,  # ilimitado
        "max_activations": 1,  # Cada usuário = 1 assinatura
        "display_name": "Enterprise - Anual",
        "amount": Decimal("10789.20"),
        "currency": "brl",
        "features": {
            "export_excel": True,
            "export_csv": True,
            "export_pdf": True,
            "consolidation_reports": True,
            "support": "dedicated",
            "multi_user": False,  # Sem multi-user, cada usuário precisa assinar
            "api_access": True,
            "training": True,
            "sla": True,
        }
    },
}


def get_plan_config(plan_key: str) -> Dict[str, Any]:
    """
    Retorna configuração completa do plano com price_id resolvido do ambiente.

    Args:
        plan_key: Chave do plano (ex: "basic_monthly", "pro_yearly")

    Returns:
        Dict com configuração do plano incluindo price_id do .env

    Raises:
        ValueError: Se plano não existe ou price_id não está configurado
    """
    config = PLAN_CONFIG.get(plan_key)
    if not config:
        raise ValueError(f"Plano desconhecido: {plan_key}")

    # Resolver price_id do ambiente
    settings = get_settings()
    price_id = getattr(settings, config["price_id_env"], None)
    if not price_id:
        raise ValueError(
            f"Price ID não configurado no .env: {config['price_id_env']}"
        )

    # Retornar config com price_id resolvido
    return {**config, "price_id": price_id}


def get_plan_by_price_id(price_id: str) -> tuple[str, Dict[str, Any]]:
    """
    Retorna plano baseado no price_id do Stripe.

    Args:
        price_id: ID do preço do Stripe (ex: "price_1Sbs0oGEyVmwHCe6P9IylBWe")

    Returns:
        Tupla (plan_key, config) com a chave e configuração do plano

    Note:
        Se price_id não for encontrado, retorna fallback para "basic_monthly"
    """
    settings = get_settings()

    # Procurar plano por price_id
    for plan_key, config in PLAN_CONFIG.items():
        env_var = config["price_id_env"]
        if getattr(settings, env_var, None) == price_id:
            return plan_key, get_plan_config(plan_key)

    # Fallback para evitar crash
    print(f"⚠️ Price ID desconhecido: {price_id}, usando fallback: basic_monthly")
    return "basic_monthly", get_plan_config("basic_monthly")

