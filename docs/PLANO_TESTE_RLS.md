# 🔒 Plano de Teste: Habilitação de RLS

**Data:** 2026-01-03
**Objetivo:** Testar que o backend continua funcionando após habilitar RLS

---

## 📋 Pré-requisitos

1. ✅ Backup do banco (via Supabase Dashboard)
2. ✅ Script SQL preparado: `backend/migrations/008_enable_rls_all_tables.sql`
3. ✅ Acesso ao Supabase SQL Editor

---

## 🧪 Plano de Teste

### Fase 1: Verificação Pré-RLS

Execute no Supabase SQL Editor:

```sql
-- Verificar status atual do RLS
SELECT
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

**Resultado esperado:** Todas as tabelas com `rls_enabled = false`

---

### Fase 2: Backup

1. Acesse: Supabase Dashboard → Settings → Database
2. Clique em "Download Backup" (se disponível)
3. Ou anote os dados críticos manualmente

---

### Fase 3: Aplicar RLS

1. Acesse: Supabase Dashboard → SQL Editor
2. Cole o conteúdo de `backend/migrations/008_enable_rls_all_tables.sql`
3. Execute o script

**Resultado esperado:** "RLS habilitado com sucesso em todas as tabelas!"

---

### Fase 4: Verificação Pós-RLS

Execute no SQL Editor:

```sql
-- Verificar se RLS foi habilitado
SELECT
    schemaname,
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

**Resultado esperado:** Todas as tabelas com `rls_enabled = true`

---

### Fase 5: Teste do Backend

**IMPORTANTE:** O backend usa conexão postgres (superuser) que BYPASSA RLS automaticamente.

#### 5.1. Teste de Login

```bash
curl -X POST https://ifrs16-backend-ox4zylcs5a-rj.a.run.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "seu@email.com", "password": "sua_senha"}'
```

**Resultado esperado:** Token JWT retornado

#### 5.2. Teste de Perfil

```bash
curl -X GET https://ifrs16-backend-ox4zylcs5a-rj.a.run.app/api/user/profile \
  -H "Authorization: Bearer SEU_TOKEN_JWT"
```

**Resultado esperado:** Dados do usuário retornados

#### 5.3. Teste de Contratos

```bash
curl -X GET https://ifrs16-backend-ox4zylcs5a-rj.a.run.app/api/contracts \
  -H "Authorization: Bearer SEU_TOKEN_JWT"
```

**Resultado esperado:** Lista de contratos retornada

#### 5.4. Teste no Frontend

1. Acesse: https://fxstudioai.com
2. Faça login
3. Verifique se o dashboard carrega
4. Tente acessar a calculadora
5. Crie um contrato de teste

**Resultado esperado:** Todas as operações funcionam normalmente

---

### Fase 6: Teste de Segurança (Opcional)

Para verificar que RLS está bloqueando acesso direto:

1. Crie um novo usuário no Supabase (não superuser)
2. Tente acessar dados via SQL Editor com esse usuário
3. Deve receber erro de permissão

```sql
-- Conectado como usuário não-superuser
SELECT * FROM users; -- Deve retornar 0 linhas ou erro
```

---

## 🚨 Rollback (Se Necessário)

Se algo der errado, execute:

```sql
-- ROLLBACK COMPLETO
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

-- Dropar políticas
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
```

---

## ✅ Checklist Final

- [ ] Backup realizado
- [ ] RLS habilitado em todas as tabelas
- [ ] Políticas criadas
- [ ] Login funcionando
- [ ] Dashboard carregando
- [ ] Contratos listando
- [ ] Calculadora acessível
- [ ] Sem erros no console do navegador
- [ ] Sem erros nos logs do Cloud Run

---

## 📊 Resultado

| Teste | Status | Observações |
|-------|--------|-------------|
| RLS habilitado | ⏳ | Pendente |
| Login | ⏳ | Pendente |
| Dashboard | ⏳ | Pendente |
| Contratos | ⏳ | Pendente |
| Calculadora | ⏳ | Pendente |

---

**Próximo passo:** Executar o script SQL no Supabase Dashboard e seguir o plano de teste.
