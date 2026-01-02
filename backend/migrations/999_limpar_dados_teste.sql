-- ============================================================================
-- SCRIPT DE LIMPEZA DE DADOS DE TESTE
-- ============================================================================
-- Data: 2026-01-02
-- Descrição: Remove todos os dados de teste para permitir novos testes
-- 
-- ⚠️ ATENÇÃO: Este script remove TODOS os dados das tabelas principais!
-- Use apenas em ambiente de desenvolvimento/teste.
-- NÃO EXECUTE EM PRODUÇÃO!
-- ============================================================================

-- Desabilitar triggers temporariamente (se houver)
SET session_replication_role = 'replica';

-- ============================================================================
-- 1. LIMPAR DADOS DE VALIDAÇÃO E LOGS
-- ============================================================================

-- Limpar logs de validação de licenças
DELETE FROM validation_logs;
COMMENT ON TABLE validation_logs IS 'Logs de validação de licenças - LIMPO';

-- Limpar tokens de verificação de email
DELETE FROM email_verification_tokens;
COMMENT ON TABLE email_verification_tokens IS 'Tokens de verificação de email - LIMPO';

-- ============================================================================
-- 2. LIMPAR DADOS DE CONTRATOS E DOCUMENTOS
-- ============================================================================

-- Limpar versões de contratos
DELETE FROM contract_versions;
COMMENT ON TABLE contract_versions IS 'Versões de contratos - LIMPO';

-- Limpar contratos
DELETE FROM contracts;
COMMENT ON TABLE contracts IS 'Contratos - LIMPO';

-- Limpar documentos
DELETE FROM documents;
COMMENT ON TABLE documents IS 'Documentos - LIMPO';

-- ============================================================================
-- 3. LIMPAR DADOS DE LICENÇAS E ASSINATURAS
-- ============================================================================

-- Limpar licenças
DELETE FROM licenses;
COMMENT ON TABLE licenses IS 'Licenças - LIMPO';

-- Limpar assinaturas
DELETE FROM subscriptions;
COMMENT ON TABLE subscriptions IS 'Assinaturas - LIMPO';

-- ============================================================================
-- 4. LIMPAR DADOS DE USUÁRIOS
-- ============================================================================

-- Limpar sessões de usuários
DELETE FROM user_sessions;
COMMENT ON TABLE user_sessions IS 'Sessões de usuários - LIMPO';

-- Limpar notificações
DELETE FROM notifications;
COMMENT ON TABLE notifications IS 'Notificações - LIMPO';

-- Limpar usuários (clientes)
DELETE FROM users;
COMMENT ON TABLE users IS 'Usuários (clientes) - LIMPO';

-- ============================================================================
-- 5. LIMPAR ÍNDICES ECONÔMICOS (OPCIONAL)
-- ============================================================================

-- Descomentar a linha abaixo se quiser limpar os índices econômicos também
-- DELETE FROM economic_indexes;
-- COMMENT ON TABLE economic_indexes IS 'Índices econômicos - LIMPO';

-- ============================================================================
-- 6. RESETAR SEQUÊNCIAS (se houver)
-- ============================================================================

-- Não há sequências explícitas pois usamos UUID
-- Mas se houver, adicione aqui

-- ============================================================================
-- 7. REABILITAR TRIGGERS
-- ============================================================================

SET session_replication_role = 'origin';

-- ============================================================================
-- 8. VERIFICAÇÃO
-- ============================================================================

-- Contar registros em cada tabela
SELECT 
    'users' as tabela, 
    COUNT(*) as registros 
FROM users
UNION ALL
SELECT 'subscriptions', COUNT(*) FROM subscriptions
UNION ALL
SELECT 'licenses', COUNT(*) FROM licenses
UNION ALL
SELECT 'contracts', COUNT(*) FROM contracts
UNION ALL
SELECT 'contract_versions', COUNT(*) FROM contract_versions
UNION ALL
SELECT 'documents', COUNT(*) FROM documents
UNION ALL
SELECT 'validation_logs', COUNT(*) FROM validation_logs
UNION ALL
SELECT 'email_verification_tokens', COUNT(*) FROM email_verification_tokens
UNION ALL
SELECT 'user_sessions', COUNT(*) FROM user_sessions
UNION ALL
SELECT 'notifications', COUNT(*) FROM notifications
ORDER BY tabela;

-- ============================================================================
-- RESULTADO ESPERADO
-- ============================================================================
-- Todas as tabelas devem ter 0 registros (exceto economic_indexes se não foi limpo)
-- ============================================================================

COMMENT ON DATABASE postgres IS 'Dados de teste limpos - Pronto para novos testes';
