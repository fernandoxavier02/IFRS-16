"""
Modelos SQLAlchemy para o banco de dados
"""

import uuid
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, 
    Enum as SQLEnum, ForeignKey, Text, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


# =============================================================================
# ENUMS
# =============================================================================

class LicenseStatus(str, enum.Enum):
    """Status possíveis de uma licença"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class LicenseType(str, enum.Enum):
    """Tipos de licença disponíveis"""
    TRIAL = "trial"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class AdminRole(str, enum.Enum):
    """Roles de administradores"""
    SUPERADMIN = "superadmin"
    ADMIN = "admin"


class SubscriptionStatus(str, enum.Enum):
    """Status de assinatura"""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    INCOMPLETE = "incomplete"
    TRIALING = "trialing"


class PlanType(str, enum.Enum):
    """Tipos de plano - Refatorado para refletir 6 planos reais"""
    # Novos valores (fonte da verdade)
    BASIC_MONTHLY = "basic_monthly"
    BASIC_YEARLY = "basic_yearly"
    PRO_MONTHLY = "pro_monthly"
    PRO_YEARLY = "pro_yearly"
    ENTERPRISE_MONTHLY = "enterprise_monthly"
    ENTERPRISE_YEARLY = "enterprise_yearly"

    # Deprecated (mantidos para retrocompatibilidade)
    MONTHLY = "monthly"  # Alias para BASIC_MONTHLY
    YEARLY = "yearly"    # Alias para PRO_YEARLY
    LIFETIME = "lifetime"  # Alias para ENTERPRISE_YEARLY


# =============================================================================
# ADMIN USERS
# =============================================================================

class AdminUser(Base):
    """
    Modelo de Usuário Administrador
    Gerencia acesso ao painel administrativo
    """
    __tablename__ = "admin_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Role e status
    role = Column(
        SQLEnum(AdminRole),
        default=AdminRole.ADMIN,
        nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Datas
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<AdminUser(username='{self.username}', role='{self.role}')>"


# =============================================================================
# USERS (CLIENTES)
# =============================================================================

class User(Base):
    """
    Modelo de Usuário Cliente
    Usuários que compram licenças
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=True)
    
    # Stripe
    stripe_customer_id = Column(String(100), unique=True, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    password_must_change = Column(Boolean, default=False, nullable=False)

    # Datas
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    
    # Relacionamentos
    subscriptions = relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    licenses = relationship(
        "License",
        back_populates="user",
        foreign_keys="License.user_id"
    )
    contracts = relationship(
        "Contract",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    sessions = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User(email='{self.email}', name='{self.name}')>"


# =============================================================================
# SUBSCRIPTIONS
# =============================================================================

class Subscription(Base):
    """
    Modelo de Assinatura
    Vincula usuário a uma licença via Stripe
    """
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relacionamentos
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    license_id = Column(
        UUID(as_uuid=True),
        ForeignKey("licenses.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Stripe
    stripe_subscription_id = Column(String(100), unique=True, nullable=True)
    stripe_session_id = Column(String(100), unique=True, nullable=True, index=True)  # Para idempotência de webhooks
    stripe_price_id = Column(String(100), nullable=True)
    
    # Tipo e status
    plan_type = Column(
        SQLEnum(PlanType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False
    )
    status = Column(
        SQLEnum(SubscriptionStatus),
        default=SubscriptionStatus.INCOMPLETE,
        nullable=False
    )
    
    # Período
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)
    
    # Datas
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Relacionamentos
    user = relationship("User", back_populates="subscriptions")
    license = relationship("License", back_populates="subscription")
    
    __table_args__ = (
        Index('idx_subscription_status', 'status'),
        Index('idx_subscription_user_status', 'user_id', 'status'),
    )
    
    def __repr__(self):
        return f"<Subscription(user_id='{self.user_id}', plan='{self.plan_type}', status='{self.status}')>"


# =============================================================================
# LICENSES
# =============================================================================

class License(Base):
    """
    Modelo de Licença
    Armazena informações sobre licenças dos usuários
    """
    __tablename__ = "licenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(50), unique=True, nullable=False, index=True)
    
    # Relacionamento com usuário (opcional - pode ser licença manual)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Dados do cliente
    customer_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    
    # Status e tipo
    status = Column(
        SQLEnum(LicenseStatus), 
        default=LicenseStatus.ACTIVE, 
        nullable=False
    )
    license_type = Column(
        SQLEnum(LicenseType), 
        default=LicenseType.TRIAL, 
        nullable=False
    )
    
    # Datas
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # NULL = sem expiração
    
    # Revogação
    revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    revoke_reason = Column(Text, nullable=True)
    
    # Controle de ativações
    machine_id = Column(String(64), nullable=True)
    max_activations = Column(Integer, default=1, nullable=False)
    current_activations = Column(Integer, default=0, nullable=False)
    
    # Última validação
    last_validation = Column(DateTime, nullable=True)
    last_validation_ip = Column(String(45), nullable=True)
    
    # Relacionamentos
    validation_logs = relationship(
        "ValidationLog", 
        back_populates="license",
        cascade="all, delete-orphan"
    )
    user = relationship(
        "User",
        back_populates="licenses",
        foreign_keys=[user_id]
    )
    subscription = relationship(
        "Subscription",
        back_populates="license",
        uselist=False
    )

    # Índices compostos
    __table_args__ = (
        Index('idx_license_status_type', 'status', 'license_type'),
        Index('idx_license_email', 'email'),
    )

    def __repr__(self):
        return f"<License(key='{self.key}', customer='{self.customer_name}', status='{self.status}')>"
    
    @property
    def is_valid(self) -> bool:
        """Verifica se a licença está válida"""
        if self.revoked:
            return False
        if self.status != LicenseStatus.ACTIVE:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True
    
    @property
    def features(self) -> dict:
        """Retorna features baseadas no tipo de licença (usa LICENSE_LIMITS como fonte única)"""
        from .config import LICENSE_LIMITS
        
        license_key = self.license_type.value if self.license_type else "trial"
        return LICENSE_LIMITS.get(license_key, LICENSE_LIMITS["trial"])


class ValidationLog(Base):
    """
    Log de validações de licença
    Registra todas as tentativas de validação
    """
    __tablename__ = "validation_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    license_key = Column(
        String(50), 
        ForeignKey("licenses.key", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Dados da validação
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    success = Column(Boolean, nullable=False)
    message = Column(String(255), nullable=True)
    
    # Informações do cliente
    machine_id = Column(String(64), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    app_version = Column(String(20), nullable=True)
    
    # Relacionamento
    license = relationship("License", back_populates="validation_logs")

    # Índice para consultas por período
    __table_args__ = (
        Index('idx_validation_timestamp', 'timestamp'),
    )

    def __repr__(self):
        return f"<ValidationLog(key='{self.license_key}', success={self.success}, time='{self.timestamp}')>"


# =============================================================================
# CONTRACTS
# =============================================================================

class ContractStatus(str, enum.Enum):
    """Status possíveis de um contrato"""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Contract(Base):
    """Modelo de Contrato IFRS 16"""
    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    contract_code = Column(String(100), nullable=True)
    categoria = Column(String(2), nullable=False, default="OT")

    status = Column(SQLEnum(ContractStatus), nullable=False, default=ContractStatus.DRAFT)

    numero_sequencial = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="contracts")

    __table_args__ = (
        Index("idx_contract_user_status", "user_id", "status"),
        Index("idx_contract_deleted", "deleted_at", "is_deleted"),
    )

    def mark_deleted(self):
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()

    def __repr__(self):
        return f"<Contract(name='{self.name}', status='{self.status}')>"


# =============================================================================
# USER SESSIONS (CONTROLE DE ACESSO SIMULTÂNEO)
# =============================================================================

class UserSession(Base):
    """
    Sessões ativas de usuários para controle de acesso simultâneo.
    Evita compartilhamento de licença entre múltiplos dispositivos.
    """
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Identificação da sessão
    session_token = Column(String(500), nullable=False, unique=True, index=True)
    device_fingerprint = Column(String(255), nullable=True)

    # Informações do dispositivo
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_name = Column(String(255), nullable=True)

    # Controle de atividade
    last_activity = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Relacionamento
    user = relationship("User", back_populates="sessions")

    __table_args__ = (
        Index("idx_user_sessions_active", "user_id", "is_active"),
        Index("idx_user_sessions_expires", "expires_at"),
    )

    def __repr__(self):
        return f"<UserSession(user_id='{self.user_id}', device='{self.device_name}', active={self.is_active})>"
