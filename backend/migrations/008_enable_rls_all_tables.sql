-- ============================================================================
-- MIGRATION: Habilitar RLS em Todas as Tabelas
-- Data: 2026-01-03
-- Descrição: Habilita Row Level Security para proteção adicional do banco
--
-- IMPORTANTE: Execute este script no Supabase SQL Editor
-- O backend usa postgres (superuser) que BYPASSA RLS automaticamente
-- Isso protege contra acesso direto não autorizado ao banco
-- ============================================================================

-- ============================================================================
-- PASSO 1: Verificar status atual do RLS
-- ============================================================================
-- Execute primeiro para ver o estado atual:
/*
SELECT
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
*/

-- ============================================================================
-- PASSO 2: Habilitar RLS em todas as tabelas
-- ============================================================================

-- Tabelas críticas (dados sensíveis)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE licenses ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE contracts ENABLE ROW LEVEL SECURITY;
ALTER TABLE contract_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE validation_logs ENABLE ROW LEVEL SECURITY;

-- Tabelas de sessão e notificações
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- Tabelas auxiliares
ALTER TABLE economic_indexes ENABLE ROW LEVEL SECURITY;

-- Tabela de tokens de verificação de email (se existir)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'email_verification_tokens') THEN
        EXECUTE 'ALTER TABLE email_verification_tokens ENABLE ROW LEVEL SECURITY';
    END IF;
END $$;

-- Tabela alembic_version (baixo risco, mas melhor proteger)
ALTER TABLE alembic_version ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- PASSO 3: Criar políticas de segurança básicas
--
-- IMPORTANTE: O usuário postgres (superuser) BYPASSA todas estas políticas
-- Estas políticas só bloqueiam acesso de usuários não-superuser
-- ============================================================================

-- Política para users: bloquear acesso direto
DROP POLICY IF EXISTS "block_direct_access" ON users;
CREATE POLICY "block_direct_access" ON users
    FOR ALL
    USING (false)
    WITH CHECK (false);

-- Política para admin_users: bloquear acesso direto
DROP POLICY IF EXISTS "block_direct_access" ON admin_users;
CREATE POLICY "block_direct_access" ON admin_users
    FOR ALL
    USING (false)
    WITH CHECK (false);

-- Política para licenses: bloquear acesso direto
DROP POLICY IF EXISTS "block_direct_access" ON licenses;
CREATE POLICY "block_direct_access" ON licenses
    FOR ALL
    USING (false)
    WITH CHECK (false);

-- Política para subscriptions: bloquear acesso direto
DROP POLICY IF EXISTS "block_direct_access" ON subscriptions;
CREATE POLICY "block_direct_access" ON subscriptions
    FOR ALL
    USING (false)
    WITH CHECK (false);

-- Política para contracts: bloquear acesso direto
DROP POLICY IF EXISTS "block_direct_access" ON contracts;
CREATE POLICY "block_direct_access" ON contracts
    FOR ALL
    USING (false)
    WITH CHECK (false);

-- Política para contract_versions: bloquear acesso direto
DROP POLICY IF EXISTS "block_direct_access" ON contract_versions;
CREATE POLICY "block_direct_access" ON contract_versions
    FOR ALL
    USING (false)
    WITH CHECK (false);

-- Política para documents: bloquear acesso direto
DROP POLICY IF EXISTS "block_direct_access" ON documents;
CREATE POLICY "block_direct_access" ON documents
    FOR ALL
    USING (false)
    WITH CHECK (false);

-- Política para validation_logs: bloquear acesso direto
DROP POLICY IF EXISTS "block_direct_access" ON validation_logs;
CREATE POLICY "block_direct_access" ON validation_logs
    FOR ALL
    USING (false)
    WITH CHECK (false);

-- Política para user_sessions: bloquear acesso direto
DROP POLICY IF EXISTS "block_direct_access" ON user_sessions;
CREATE POLICY "block_direct_access" ON user_sessions
    FOR ALL
    USING (false)
    WITH CHECK (false);

-- Política para notifications: bloquear acesso direto
DROP POLICY IF EXISTS "block_direct_access" ON notifications;
CREATE POLICY "block_direct_access" ON notifications
    FOR ALL
    USING (false)
    WITH CHECK (false);

-- Política para economic_indexes: permitir leitura pública (dados públicos do BCB)
DROP POLICY IF EXISTS "allow_public_read" ON economic_indexes;
CREATE POLICY "allow_public_read" ON economic_indexes
    FOR SELECT
    USING (true);

DROP POLICY IF EXISTS "block_direct_write" ON economic_indexes;
CREATE POLICY "block_direct_write" ON economic_indexes
    FOR INSERT
    WITH CHECK (false);

DROP POLICY IF EXISTS "block_direct_update" ON economic_indexes;
CREATE POLICY "block_direct_update" ON economic_indexes
    FOR UPDATE
    USING (false)
    WITH CHECK (false);

DROP POLICY IF EXISTS "block_direct_delete" ON economic_indexes;
CREATE POLICY "block_direct_delete" ON economic_indexes
    FOR DELETE
    USING (false);

-- Política para alembic_version: bloquear acesso direto
DROP POLICY IF EXISTS "block_direct_access" ON alembic_version;
CREATE POLICY "block_direct_access" ON alembic_version
    FOR ALL
    USING (false)
    WITH CHECK (false);

-- Política para email_verification_tokens (se existir)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'email_verification_tokens') THEN
        EXECUTE 'DROP POLICY IF EXISTS "block_direct_access" ON email_verification_tokens';
        EXECUTE 'CREATE POLICY "block_direct_access" ON email_verification_tokens FOR ALL USING (false) WITH CHECK (false)';
    END IF;
END $$;

-- ============================================================================
-- PASSO 4: Verificar se RLS foi habilitado
-- ============================================================================
-- Execute para confirmar:
/*
SELECT
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
*/

-- ============================================================================
-- PASSO 5: Verificar políticas criadas
-- ============================================================================
-- Execute para ver as políticas:
/*
SELECT
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;
*/

-- ============================================================================
-- ROLLBACK (se necessário)
-- ============================================================================
-- Para reverter TUDO (use apenas em emergência):
/*
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE admin_users DISABLE ROW LEVEL SECURITY;
ALTER TABLE licenses DISABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions DISABLE ROW LEVEL SECURITY;
ALTER TABLE contracts DISABLE ROW LEVEL SECURITY;
ALTER TABLE contract_versions DISABLE ROW LEVEL SECURITY;
ALTER TABLE documents DISABLE ROW LEVEL SECURITY;
ALTER TABLE validation_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions DISABLE ROW LEVEL SECURITY;
ALTER TABLE notifications DISABLE ROW LEVEL SECURITY;
ALTER TABLE economic_indexes DISABLE ROW LEVEL SECURITY;
ALTER TABLE alembic_version DISABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "block_direct_access" ON users;
DROP POLICY IF EXISTS "block_direct_access" ON admin_users;
DROP POLICY IF EXISTS "block_direct_access" ON licenses;
DROP POLICY IF EXISTS "block_direct_access" ON subscriptions;
DROP POLICY IF EXISTS "block_direct_access" ON contracts;
DROP POLICY IF EXISTS "block_direct_access" ON contract_versions;
DROP POLICY IF EXISTS "block_direct_access" ON documents;
DROP POLICY IF EXISTS "block_direct_access" ON validation_logs;
DROP POLICY IF EXISTS "block_direct_access" ON user_sessions;
DROP POLICY IF EXISTS "block_direct_access" ON notifications;
DROP POLICY IF EXISTS "allow_public_read" ON economic_indexes;
DROP POLICY IF EXISTS "block_direct_write" ON economic_indexes;
DROP POLICY IF EXISTS "block_direct_update" ON economic_indexes;
DROP POLICY IF EXISTS "block_direct_delete" ON economic_indexes;
DROP POLICY IF EXISTS "block_direct_access" ON alembic_version;
*/

-- ============================================================================
-- FIM DA MIGRATION
-- ============================================================================
SELECT 'RLS habilitado com sucesso em todas as tabelas!' as status;
