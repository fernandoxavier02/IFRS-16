-- Script para criar usuário master no Cloud SQL
-- Execute via: gcloud sql connect ifrs16-database --user=postgres --project=ifrs16-app

-- Verificar se tabela admin_users existe, se não, criar
CREATE TABLE IF NOT EXISTS admin_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'admin',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Inserir ou atualizar usuário master
INSERT INTO admin_users (username, email, password_hash, role, is_active)
VALUES (
    'master',
    'fernandocostaxavier@gmail.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5K5K5K5K5K5K', -- Master@2025! hash
    'superadmin',
    true
)
ON CONFLICT (username) 
DO UPDATE SET 
    email = EXCLUDED.email,
    password_hash = EXCLUDED.password_hash,
    role = EXCLUDED.role,
    is_active = true;
