-- Script SQL para criar usuario Master/Admin
-- Deve ser executado no banco Google Cloud SQL connected via 'gcloud sql connect'

-- 1. Inserir na tabela admin_users (se existir, senao usar users)
-- Vamos tentar inserir na tabela 'users' com is_admin = true (ou similar)
-- Mas o script python original referenciava 'admin_users'. Vamos manter isso.

-- Senha hashada para 'Fcxv020781@' (gerada via bcrypt)
-- Exemplo de hash bcrypt válido: $2b$12$lxC/kXk5kXk5kXk5kXk5kOf/d.Xk5kXk5kXk5kXk5kXk5kXk5kXk (placeholder)
-- Como nao conseguimos gerar hash bcrypt valido em SQL puro facilmente sem extensao pgcrypto com formato especifico,
-- eh melhor inserir um usuario com senha temporaria conhecida ou usar pgcrypto se disponivel.

-- Melhor abordagem: Vamos usar o Python localmente para gerar o HASH e o SQL,
-- e depois executar esse SQL no Cloud SQL.

-- Veja o script 'criar_master_cloud_sql.ps1' que fara isso.
