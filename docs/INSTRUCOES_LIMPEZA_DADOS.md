# 🧹 INSTRUÇÕES: LIMPEZA DE DADOS E APLICAÇÃO DE MIGRATIONS

> **Data:** 2026-01-02  
> **Objetivo:** Preparar o sistema para novos testes

---

## 📋 ORDEM DE EXECUÇÃO

### 1️⃣ Aplicar Migration da Tabela `email_verification_tokens`

**Arquivo:** `backend/migrations/007_add_email_verification_tokens.sql`

#### Via Supabase SQL Editor:

1. Acesse o Supabase Dashboard
2. Vá em **SQL Editor**
3. Clique em **New Query**
4. Copie e cole o conteúdo do arquivo `007_add_email_verification_tokens.sql`
5. Clique em **Run**
6. Verifique se a tabela foi criada:

```sql
SELECT * FROM information_schema.tables 
WHERE table_name = 'email_verification_tokens';
```

#### Via psql (CLI):

```bash
psql "postgresql://postgres.jafdinvixrfxtvoagrsf:***@aws-1-sa-east-1.pooler.supabase.com:6543/postgres?sslmode=require" -f backend/migrations/007_add_email_verification_tokens.sql
```

---

### 2️⃣ Limpar Dados de Teste

**Arquivo:** `backend/migrations/999_limpar_dados_teste.sql`

⚠️ **ATENÇÃO:** Este script remove **TODOS** os dados de teste!

#### Via Supabase SQL Editor:

1. Acesse o Supabase Dashboard
2. Vá em **SQL Editor**
3. Clique em **New Query**
4. Copie e cole o conteúdo do arquivo `999_limpar_dados_teste.sql`
5. Clique em **Run**
6. Verifique o resultado da query de verificação (deve mostrar 0 registros)

#### Via psql (CLI):

```bash
psql "postgresql://postgres.jafdinvixrfxtvoagrsf:***@aws-1-sa-east-1.pooler.supabase.com:6543/postgres?sslmode=require" -f backend/migrations/999_limpar_dados_teste.sql
```

---

## ✅ VERIFICAÇÃO

Após executar os scripts, verifique:

### 1. Tabela `email_verification_tokens` foi criada:

```sql
\d email_verification_tokens
```

Ou:

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'email_verification_tokens';
```

### 2. Dados foram limpos:

```sql
SELECT 
    'users' as tabela, COUNT(*) as registros FROM users
UNION ALL
SELECT 'subscriptions', COUNT(*) FROM subscriptions
UNION ALL
SELECT 'licenses', COUNT(*) FROM licenses
UNION ALL
SELECT 'contracts', COUNT(*) FROM contracts
UNION ALL
SELECT 'validation_logs', COUNT(*) FROM validation_logs
UNION ALL
SELECT 'email_verification_tokens', COUNT(*) FROM email_verification_tokens
ORDER BY tabela;
```

**Resultado esperado:** Todas as tabelas com 0 registros.

---

## 🔄 FLUXO DE TESTE APÓS LIMPEZA

### 1. Cadastro de Novo Usuário

1. Acesse `https://fxstudioai.com/register.html` (ou página de cadastro)
2. Preencha os dados
3. Clique em "Cadastrar"
4. ✅ **Verificar:** Modal de sucesso aparece
5. ✅ **Verificar:** Email de verificação foi enviado

### 2. Confirmação de Email

1. Abra o email recebido
2. Clique no link de confirmação
3. ✅ **Verificar:** Página mostra "Email confirmado com sucesso"
4. ✅ **Verificar:** No banco, `users.email_verified = true`

### 3. Login

1. Acesse `https://fxstudioai.com/login.html`
2. Digite email e senha
3. Clique em "Entrar"
4. ✅ **Verificar:** Login bem-sucedido
5. ✅ **Verificar:** Redirecionado para dashboard

### 4. Compra de Assinatura

1. No dashboard, clique em "Assinar Plano"
2. Escolha um plano
3. Complete o pagamento no Stripe (use cartão de teste)
4. ✅ **Verificar:** Webhook processado
5. ✅ **Verificar:** Email de licença enviado
6. ✅ **Verificar:** No banco:
   - `subscriptions` criada
   - `licenses` criada com status ACTIVE

### 5. Validação de Licença

1. Abra o email de licença
2. Clique no link "🚀 Fazer Login e Ativar Licença"
3. ✅ **Verificar:** Redirecionado para login com `?license=XXX` na URL
4. Faça login
5. ✅ **Verificar:** Redirecionado para validação de licença
6. ✅ **Verificar:** Chave de licença pré-preenchida
7. Clique em "Validar Licença"
8. ✅ **Verificar:** Acesso à calculadora liberado

---

## 🗄️ ESTRUTURA DO BANCO APÓS LIMPEZA

```
✅ Tabelas mantidas (estrutura):
- users
- subscriptions
- licenses
- contracts
- contract_versions
- documents
- validation_logs
- email_verification_tokens (NOVA)
- user_sessions
- notifications
- admin_users (não limpo)
- economic_indexes (não limpo)

❌ Dados removidos:
- Todos os usuários de teste
- Todas as assinaturas de teste
- Todas as licenças de teste
- Todos os contratos de teste
- Todos os logs de teste
```

---

## 🚨 TROUBLESHOOTING

### Erro: "relation email_verification_tokens does not exist"

**Solução:** Execute a migration `007_add_email_verification_tokens.sql` primeiro.

### Erro: "permission denied"

**Solução:** Verifique se está usando o usuário correto do Supabase com permissões de escrita.

### Dados não foram limpos

**Solução:** Verifique se o script foi executado completamente. Execute a query de verificação para confirmar.

---

## 📝 NOTAS IMPORTANTES

1. **Admin users não são limpos** - Os administradores são mantidos
2. **Índices econômicos não são limpos** - Dados do BCB são mantidos
3. **Estrutura das tabelas é mantida** - Apenas os dados são removidos
4. **Triggers são desabilitados temporariamente** - Para evitar erros de cascata

---

**Status:** ✅ **PRONTO PARA TESTES**
