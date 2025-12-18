"""
Configurações da aplicação usando Pydantic Settings
"""

from functools import lru_cache
from typing import List, Optional
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
    
    # Preços por plano - Básico (até 3 contratos)
    STRIPE_PRICE_BASIC_MONTHLY: Optional[str] = None
    STRIPE_PRICE_BASIC_YEARLY: Optional[str] = None
    
    # Preços por plano - Pro (até 20 contratos)
    STRIPE_PRICE_PRO_MONTHLY: Optional[str] = None
    STRIPE_PRICE_PRO_YEARLY: Optional[str] = None
    
    # Preços por plano - Enterprise (ilimitado)
    STRIPE_PRICE_ENTERPRISE_MONTHLY: Optional[str] = None
    STRIPE_PRICE_ENTERPRISE_YEARLY: Optional[str] = None
    
    # URLs
    FRONTEND_URL: str = "http://localhost:3000"
    API_URL: str = "http://localhost:8000"
    
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


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna instância cacheada das configurações.
    Use esta função para acessar configurações em toda a aplicação.
    """
    return Settings()

