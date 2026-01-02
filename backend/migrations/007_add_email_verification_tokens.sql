-- Migration: Add email_verification_tokens table
-- Date: 2026-01-02
-- Description: Adiciona tabela para tokens de verificação de email

-- Criar tabela de tokens de verificação
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_token ON email_verification_tokens(token);
CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_user_id ON email_verification_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_expires_at ON email_verification_tokens(expires_at);

-- Comentários
COMMENT ON TABLE email_verification_tokens IS 'Tokens de verificação de email para novos usuários';
COMMENT ON COLUMN email_verification_tokens.id IS 'ID único do token';
COMMENT ON COLUMN email_verification_tokens.user_id IS 'ID do usuário associado';
COMMENT ON COLUMN email_verification_tokens.token IS 'Token único de verificação (UUID)';
COMMENT ON COLUMN email_verification_tokens.expires_at IS 'Data/hora de expiração do token (24h)';
COMMENT ON COLUMN email_verification_tokens.used_at IS 'Data/hora em que o token foi usado (NULL se não usado)';
COMMENT ON COLUMN email_verification_tokens.created_at IS 'Data/hora de criação do token';
