"""
Pydantic Schemas para validação de dados da API
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, EmailStr, Field, field_validator
import re


# ============================================================
# Enums
# ============================================================

class LicenseStatusEnum(str, Enum):
    """Status possíveis de uma licença"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class LicenseTypeEnum(str, Enum):
    """Tipos de licença disponíveis"""
    TRIAL = "trial"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class AdminRoleEnum(str, Enum):
    """Roles de administradores"""
    SUPERADMIN = "superadmin"
    ADMIN = "admin"


class SubscriptionStatusEnum(str, Enum):
    """Status de assinatura"""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    INCOMPLETE = "incomplete"
    TRIALING = "trialing"


class PlanTypeEnum(str, Enum):
    """Tipos de plano"""
    MONTHLY = "monthly"
    YEARLY = "yearly"
    LIFETIME = "lifetime"


# ============================================================
# Schemas de Autenticação
# ============================================================

class LoginRequest(BaseModel):
    """Request de login"""
    email: EmailStr = Field(..., description="Email do usuário")
    password: str = Field(..., min_length=6, description="Senha")


class RegisterRequest(BaseModel):
    """Request de registro de usuário"""
    name: str = Field(..., min_length=2, max_length=255, description="Nome completo")
    email: EmailStr = Field(..., description="Email do usuário")
    password: str = Field(..., min_length=8, description="Senha (mínimo 8 caracteres)")
    company_name: Optional[str] = Field(None, max_length=255, description="Nome da empresa (opcional)")
    
    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Senha deve conter pelo menos uma letra maiúscula')
        if not re.search(r'[a-z]', v):
            raise ValueError('Senha deve conter pelo menos uma letra minúscula')
        if not re.search(r'[0-9]', v):
            raise ValueError('Senha deve conter pelo menos um número')
        return v


class TokenResponse(BaseModel):
    """Response com token JWT"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Tempo de expiração em segundos")
    user_type: str = Field(description="Tipo: admin ou user")


class ChangePasswordRequest(BaseModel):
    """Request para alterar senha"""
    current_password: str = Field(..., description="Senha atual")
    new_password: str = Field(..., min_length=8, description="Nova senha")


class ForgotPasswordRequest(BaseModel):
    """Request para recuperar senha"""
    email: EmailStr = Field(..., description="Email do usuário")


class ResetPasswordRequest(BaseModel):
    """Request para resetar senha"""
    token: str = Field(..., description="Token de reset")
    new_password: str = Field(..., min_length=8, description="Nova senha")


# ============================================================
# Schemas de Admin User
# ============================================================

class AdminUserCreate(BaseModel):
    """Request para criar admin"""
    username: str = Field(..., min_length=3, max_length=50, description="Username único")
    email: EmailStr = Field(..., description="Email do admin")
    password: str = Field(..., min_length=8, description="Senha")
    role: AdminRoleEnum = Field(default=AdminRoleEnum.ADMIN, description="Role do admin")


class AdminUserUpdate(BaseModel):
    """Request para atualizar admin"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    role: Optional[AdminRoleEnum] = None
    is_active: Optional[bool] = None


class AdminUserResponse(BaseModel):
    """Response de admin user"""
    id: UUID
    username: str
    email: str
    role: AdminRoleEnum
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============================================================
# Schemas de User (Cliente)
# ============================================================

class UserResponse(BaseModel):
    """Response de usuário cliente"""
    id: UUID
    email: str
    name: str
    company_name: Optional[str] = None
    is_active: bool
    email_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    stripe_customer_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """Request para atualizar usuário"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None


class UserListResponse(BaseModel):
    """Response de listagem de usuários"""
    total: int
    users: List[UserResponse]


# ============================================================
# Schemas de Subscription
# ============================================================

class SubscriptionResponse(BaseModel):
    """Response de assinatura"""
    id: UUID
    plan_type: PlanTypeEnum
    status: SubscriptionStatusEnum
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class SubscriptionWithLicenseResponse(BaseModel):
    """Response de assinatura com licença"""
    subscription: SubscriptionResponse
    license_key: Optional[str]
    license_type: Optional[LicenseTypeEnum]
    license_expires_at: Optional[datetime]


# ============================================================
# Schemas de Stripe/Pagamento
# ============================================================

class CreateCheckoutRequest(BaseModel):
    """Request para criar checkout Stripe"""
    plan_type: PlanTypeEnum = Field(..., description="Tipo do plano")
    success_url: Optional[str] = Field(None, description="URL de sucesso")
    cancel_url: Optional[str] = Field(None, description="URL de cancelamento")


class CheckoutResponse(BaseModel):
    """Response de criação de checkout"""
    checkout_url: str
    session_id: str


class PortalResponse(BaseModel):
    """Response do portal do cliente"""
    portal_url: str


class InvoiceResponse(BaseModel):
    """Response de fatura"""
    id: str
    amount: int
    currency: str
    status: str
    created: datetime
    invoice_pdf: Optional[str]
    hosted_invoice_url: Optional[str]


# ============================================================
# Schemas de Licença - Request
# ============================================================

class LicenseValidateRequest(BaseModel):
    """Request para validar uma licença"""
    key: str = Field(..., min_length=10, max_length=50, description="Chave da licença")
    machine_id: Optional[str] = Field(None, max_length=64, description="ID único da máquina")
    app_version: Optional[str] = Field(None, max_length=20, description="Versão da aplicação")


class LicenseCreateRequest(BaseModel):
    """Request para criar uma nova licença (admin)"""
    customer_name: str = Field(..., min_length=2, max_length=255, description="Nome do cliente")
    email: EmailStr = Field(..., description="Email do cliente")
    license_type: LicenseTypeEnum = Field(default=LicenseTypeEnum.TRIAL, description="Tipo da licença")
    duration_months: Optional[int] = Field(None, ge=1, le=120, description="Duração em meses (null = permanente)")
    max_activations: int = Field(default=1, ge=1, le=100, description="Máximo de ativações permitidas")


class LicenseRevokeRequest(BaseModel):
    """Request para revogar uma licença (admin)"""
    key: str = Field(..., min_length=10, max_length=50, description="Chave da licença")
    reason: Optional[str] = Field(None, max_length=500, description="Motivo da revogação")


class LicenseReactivateRequest(BaseModel):
    """Request para reativar uma licença (admin)"""
    key: str = Field(..., min_length=10, max_length=50, description="Chave da licença")


# ============================================================
# Schemas de Licença - Response
# ============================================================

class LicenseFeatures(BaseModel):
    """Features disponíveis na licença"""
    max_contracts: int = Field(description="Máximo de contratos (-1 = ilimitado)")
    export_excel: bool = Field(description="Pode exportar Excel")
    export_csv: bool = Field(description="Pode exportar CSV")
    support: bool = Field(description="Tem suporte técnico")
    multi_user: bool = Field(description="Permite múltiplos usuários")


class LicenseData(BaseModel):
    """Dados da licença retornados após validação"""
    customer_name: str
    license_type: LicenseTypeEnum
    expires_at: Optional[datetime]
    features: LicenseFeatures

    class Config:
        from_attributes = True


class ValidationSuccessResponse(BaseModel):
    """Response de validação bem-sucedida"""
    valid: bool = True
    token: str = Field(description="Token JWT para autenticação")
    data: LicenseData


class ValidationErrorResponse(BaseModel):
    """Response de validação com erro"""
    valid: bool = False
    message: str = Field(description="Mensagem de erro")


class CheckLicenseResponse(BaseModel):
    """Response de verificação de token"""
    valid: bool
    status: Optional[LicenseStatusEnum] = None
    expires_at: Optional[datetime] = None
    message: Optional[str] = None


class LicenseFullResponse(BaseModel):
    """Response completa de licença (admin)"""
    id: UUID
    key: str
    customer_name: str
    email: str
    status: LicenseStatusEnum
    license_type: LicenseTypeEnum
    created_at: datetime
    expires_at: Optional[datetime]
    revoked: bool
    revoked_at: Optional[datetime]
    revoke_reason: Optional[str]
    machine_id: Optional[str]
    max_activations: int
    current_activations: int
    last_validation: Optional[datetime]

    class Config:
        from_attributes = True


class LicenseListResponse(BaseModel):
    """Response de listagem de licenças"""
    total: int
    licenses: List[LicenseFullResponse]


class UserLicenseResponse(BaseModel):
    """Response da licença do usuário logado"""
    has_license: bool = Field(description="Se o usuário possui licença ativa")
    license_key: Optional[str] = Field(None, description="Chave da licença")
    customer_name: Optional[str] = Field(None, description="Nome do cliente")
    license_type: Optional[LicenseTypeEnum] = Field(None, description="Tipo da licença")
    status: Optional[LicenseStatusEnum] = Field(None, description="Status da licença")
    expires_at: Optional[datetime] = Field(None, description="Data de expiração")
    features: Optional[LicenseFeatures] = Field(None, description="Features da licença")
    token: Optional[str] = Field(None, description="Token JWT para autenticação de licença")


# ============================================================
# Schemas Admin - Response
# ============================================================

class AdminActionResponse(BaseModel):
    """Response genérica de ação administrativa"""
    success: bool
    message: str
    key: Optional[str] = None


class GenerateLicenseResponse(BaseModel):
    """Response de geração de licença"""
    success: bool
    message: str
    license: Optional[LicenseFullResponse] = None


# ============================================================
# Schemas de Log
# ============================================================

class ValidationLogResponse(BaseModel):
    """Response de log de validação"""
    id: UUID
    license_key: str
    timestamp: datetime
    success: bool
    message: Optional[str]
    machine_id: Optional[str]
    ip_address: Optional[str]

    class Config:
        from_attributes = True


# ============================================================
# Schemas de Erro
# ============================================================

class HTTPError(BaseModel):
    """Schema padrão de erro HTTP"""
    detail: str


class ValidationError(BaseModel):
    """Schema de erro de validação"""
    loc: List[str]
    msg: str
    type: str

