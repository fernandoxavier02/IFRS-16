-- IFRS 16 Database Schema Migration for Supabase
-- Generated: 2026-01-02
-- This migration creates all tables, enums, and indexes for the IFRS 16 application

-- =============================================================================
-- ENUMS
-- =============================================================================

-- License Status
DO $$ BEGIN
    CREATE TYPE licensestatus AS ENUM ('active', 'suspended', 'expired', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- License Type
DO $$ BEGIN
    CREATE TYPE licensetype AS ENUM ('trial', 'basic', 'pro', 'enterprise');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Admin Role
DO $$ BEGIN
    CREATE TYPE adminrole AS ENUM ('superadmin', 'admin');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Subscription Status
DO $$ BEGIN
    CREATE TYPE subscriptionstatus AS ENUM ('active', 'past_due', 'cancelled', 'incomplete', 'trialing');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Plan Type
DO $$ BEGIN
    CREATE TYPE plantype AS ENUM ('basic_monthly', 'basic_yearly', 'pro_monthly', 'pro_yearly', 'enterprise_monthly', 'enterprise_yearly', 'monthly', 'yearly', 'lifetime');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Contract Status
DO $$ BEGIN
    CREATE TYPE contractstatus AS ENUM ('draft', 'active', 'archived');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Notification Type
DO $$ BEGIN
    CREATE TYPE notificationtype AS ENUM ('contract_expiring', 'contract_expired', 'remeasurement_done', 'index_updated', 'license_expiring', 'system_alert');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- =============================================================================
-- TABLES
-- =============================================================================

-- Admin Users
CREATE TABLE IF NOT EXISTS admin_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role adminrole DEFAULT 'admin' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    last_login TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users (username);
CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users (email);

-- Users (Clientes)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    company_name VARCHAR(255),
    stripe_customer_id VARCHAR(100) UNIQUE,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE NOT NULL,
    password_must_change BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    last_login TIMESTAMP,
    password_changed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- Licenses
CREATE TABLE IF NOT EXISTS licenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(50) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    customer_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    status licensestatus DEFAULT 'active' NOT NULL,
    license_type licensetype DEFAULT 'trial' NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMP,
    revoked BOOLEAN DEFAULT FALSE NOT NULL,
    revoked_at TIMESTAMP,
    revoke_reason TEXT,
    machine_id VARCHAR(64),
    max_activations INTEGER DEFAULT 1 NOT NULL,
    current_activations INTEGER DEFAULT 0 NOT NULL,
    last_validation TIMESTAMP,
    last_validation_ip VARCHAR(45)
);

CREATE INDEX IF NOT EXISTS idx_license_key ON licenses (key);
CREATE INDEX IF NOT EXISTS idx_license_user_id ON licenses (user_id);
CREATE INDEX IF NOT EXISTS idx_license_status_type ON licenses (status, license_type);
CREATE INDEX IF NOT EXISTS idx_license_email ON licenses (email);

-- Subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    license_id UUID REFERENCES licenses(id) ON DELETE SET NULL,
    stripe_subscription_id VARCHAR(100) UNIQUE,
    stripe_session_id VARCHAR(100) UNIQUE,
    stripe_price_id VARCHAR(100),
    plan_type plantype NOT NULL,
    status subscriptionstatus DEFAULT 'incomplete' NOT NULL,
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    cancelled_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_subscription_user_id ON subscriptions (user_id);
CREATE INDEX IF NOT EXISTS idx_subscription_status ON subscriptions (status);
CREATE INDEX IF NOT EXISTS idx_subscription_user_status ON subscriptions (user_id, status);
CREATE INDEX IF NOT EXISTS ix_subscriptions_stripe_session_id ON subscriptions (stripe_session_id);

-- Validation Logs
CREATE TABLE IF NOT EXISTS validation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_key VARCHAR(50) NOT NULL REFERENCES licenses(key) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT NOW() NOT NULL,
    success BOOLEAN NOT NULL,
    message VARCHAR(255),
    machine_id VARCHAR(64),
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    app_version VARCHAR(20)
);

CREATE INDEX IF NOT EXISTS idx_validation_license_key ON validation_logs (license_key);
CREATE INDEX IF NOT EXISTS idx_validation_timestamp ON validation_logs (timestamp);

-- Contracts
CREATE TABLE IF NOT EXISTS contracts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    contract_code VARCHAR(100),
    categoria VARCHAR(2) DEFAULT 'OT' NOT NULL,
    status contractstatus DEFAULT 'draft' NOT NULL,
    numero_sequencial INTEGER,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_contract_user_id ON contracts (user_id);
CREATE INDEX IF NOT EXISTS idx_contract_user_status ON contracts (user_id, status);
CREATE INDEX IF NOT EXISTS idx_contract_deleted ON contracts (deleted_at, is_deleted);

-- User Sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(500) UNIQUE NOT NULL,
    device_fingerprint VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    device_name VARCHAR(255),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions (session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions (user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions (expires_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_last_activity ON user_sessions (last_activity);

-- Economic Indexes
CREATE TABLE IF NOT EXISTS economic_indexes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    index_type VARCHAR(20) NOT NULL,
    reference_date TIMESTAMP NOT NULL,
    value VARCHAR(50) NOT NULL,
    source VARCHAR(50) DEFAULT 'BCB' NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_economic_index_type_date ON economic_indexes (index_type, reference_date);
CREATE INDEX IF NOT EXISTS idx_economic_index_type_date ON economic_indexes (index_type, reference_date);

-- Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_type notificationtype NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    extra_data TEXT,
    read BOOLEAN DEFAULT FALSE NOT NULL,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_notification_user_id ON notifications (user_id);
CREATE INDEX IF NOT EXISTS idx_notification_user_read ON notifications (user_id, read);
CREATE INDEX IF NOT EXISTS idx_notification_user_type ON notifications (user_id, notification_type);
CREATE INDEX IF NOT EXISTS idx_notification_created_at ON notifications (created_at);

-- Documents
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id UUID NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    version INTEGER DEFAULT 1 NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_document_contract ON documents (contract_id);
CREATE INDEX IF NOT EXISTS idx_document_user ON documents (user_id);
CREATE INDEX IF NOT EXISTS idx_document_deleted ON documents (is_deleted);

-- =============================================================================
-- ALEMBIC VERSION TABLE (para compatibilidade com Alembic)
-- =============================================================================

CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) PRIMARY KEY NOT NULL
);

-- Inserir versao mais recente do Alembic
INSERT INTO alembic_version (version_num) VALUES ('reajuste_periodicidade')
ON CONFLICT (version_num) DO NOTHING;
