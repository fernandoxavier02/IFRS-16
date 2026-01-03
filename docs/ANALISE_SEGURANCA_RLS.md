# 🔒 Análise de Segurança: RLS Disabled in Public

**Data:** 2026-01-03  
**Status:** ⚠️ **CRÍTICO - REQUER AÇÃO IMEDIATA**

---

## 🚨 Resumo Executivo

O Supabase Security Advisor detectou **13 erros críticos** de segurança: **RLS (Row Level Security) desabilitado** em todas as tabelas públicas do banco de dados em **PRODUÇÃO**.

**Severidade:** 🔴 **CRÍTICA**

---

## 📊 O que é RLS (Row Level Security)?

**RLS** é uma funcionalidade do PostgreSQL que permite controlar quais **linhas** (registros) um usuário pode visualizar ou modificar no nível do banco de dados, independente da aplicação.

### Por que é Importante?

Mesmo que sua aplicação tenha autenticação e autorização no backend (FastAPI), **RLS fornece uma camada adicional de segurança** no próprio banco de dados.

### Cenários de Risco SEM RLS:

1. **Acesso Direto ao Banco:**
   - Se alguém conseguir as credenciais do banco (vazamento, engenharia social, etc.)
   - Pode acessar **TODOS** os dados de **TODOS** os usuários diretamente

2. **Vulnerabilidade no Backend:**
   - SQL Injection (mesmo que raro, ainda é possível)
   - Bug de autorização no código
   - Comprometimento do servidor backend

3. **Acesso via Supabase Dashboard:**
   - Se alguém conseguir acesso ao dashboard do Supabase
   - Pode visualizar/modificar dados sem passar pelo backend

4. **Conformidade (LGPD/GDPR):**
   - Violação de privacidade de dados
   - Multas e problemas legais

---

## 🎯 Situação Atual da Aplicação

### Arquitetura de Segurança Atual:

✅ **Backend (FastAPI) tem autenticação:**
- JWT tokens para usuários
- Verificação de permissões nos endpoints
- `get_current_user()` garante que apenas usuários autenticados acessem dados

✅ **Autorização no Backend:**
- Usuários só veem seus próprios dados (filtro por `user_id`)
- Admins têm acesso especial através de `get_current_admin()`

❌ **RLS Desabilitado no Banco:**
- Se alguém conseguir acesso direto ao banco, pode ver tudo
- Sem proteção adicional no nível do banco de dados

---

## 📋 Tabelas Afetadas (13 tabelas)

### Tabelas Críticas (Alto Risco):

1. **`users`** - Dados pessoais, emails, senhas (hashed)
2. **`admin_users`** - Credenciais de administradores
3. **`licenses`** - Chaves de licença (propriedade intelectual)
4. **`subscriptions`** - Dados de assinatura Stripe
5. **`contracts`** - Contratos IFRS 16 (dados comerciais sensíveis)
6. **`documents`** - Documentos anexados
7. **`validation_logs`** - Histórico de validações

### Tabelas Moderadas:

8. **`contract_versions`** - Versões de contratos
9. **`user_sessions`** - Sessões ativas de usuários
10. **`notifications`** - Notificações pessoais
11. **`email_verification_tokens`** - Tokens de verificação
12. **`economic_indexes`** - Índices econômicos (público, mas melhor proteger)
13. **`alembic_version`** - Versão do Alembic (baixo risco)

---

## ✅ Recomendação: Implementar RLS

### Estratégia Recomendada:

#### 1. **Habilitar RLS em Todas as Tabelas**

```sql
-- Exemplo para tabela 'users'
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Exemplo para tabela 'licenses'
ALTER TABLE licenses ENABLE ROW LEVEL SECURITY;

-- Repetir para todas as 13 tabelas
```

#### 2. **Criar Políticas RLS por Tabela**

A estratégia depende de **como a aplicação se conecta ao banco**:

##### Opção A: Backend usa um usuário único (atual - recomendado manter)

Se o backend usa **uma única conta de banco** (como `postgres.[PROJECT_REF]`), as políticas RLS precisam ser **baseadas em função do PostgreSQL** que identifica o usuário da aplicação.

**Problema:** Com conexão única, não há como o banco saber qual "user_id" da aplicação está fazendo a query.

**Solução:** Criar políticas que permitam o acesso baseado em **contexto da aplicação** OU usar **Service Role** apenas para o backend (bypass de RLS para operações do backend).

##### Opção B: Service Role para Backend (Recomendado)

**Recomendação para esta aplicação:**

1. **Backend usa Service Role** (bypass RLS) - porque já tem autenticação/autorização no código
2. **Habilitar RLS** para proteger contra acesso direto não autorizado
3. **Políticas RLS** para qualquer acesso que NÃO seja via Service Role

---

## 🔧 Implementação Prática

### Passo 1: Criar Políticas RLS Básicas

```sql
-- Exemplo: Tabela 'users'
-- Política: Usuários só veem seus próprios registros
CREATE POLICY "Users can view own data"
ON users FOR SELECT
USING (auth.uid()::text = id::text);

-- Mas isso só funciona se usar Supabase Auth
-- Como você usa JWT próprio, precisa de abordagem diferente
```

### Passo 2: Para Backend com JWT Próprio

Como sua aplicação usa **JWT próprio** (não Supabase Auth), a melhor abordagem é:

```sql
-- Habilitar RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE licenses ENABLE ROW LEVEL SECURITY;
-- ... repetir para todas as tabelas

-- Criar políticas que PERMITEM acesso via Service Role
-- Service Role bypassa RLS automaticamente
-- Então você só precisa proteger acesso direto

-- Política padrão: DENY tudo (exceto via Service Role)
CREATE POLICY "Deny all direct access"
ON users FOR ALL
USING (false);  -- Bloqueia tudo

-- Service Role (postgres superuser) bypassa isso automaticamente
```

### Passo 3: Configurar Backend para usar Service Role

**Arquivo:** `backend/app/database.py`

Você já usa uma connection string que provavelmente é o Service Role. O Service Role **bypassa RLS automaticamente**, então:

1. ✅ Backend continua funcionando normalmente
2. ✅ RLS protege acesso direto ao banco
3. ✅ Qualquer tentativa de acesso direto é bloqueada

---

## 🎯 Plano de Ação Recomendado

### Fase 1: Preparação (Imediato)

1. ✅ **Verificar connection string atual:**
   - Se usa Service Role: RLS pode ser habilitado sem quebrar nada
   - Service Role sempre bypassa RLS

2. ✅ **Documentar impacto:**
   - Identificar quais tabelas são mais críticas
   - Priorizar proteção

### Fase 2: Implementação (Esta Semana)

1. **Habilitar RLS em todas as tabelas:**
   ```sql
   ALTER TABLE users ENABLE ROW LEVEL SECURITY;
   ALTER TABLE licenses ENABLE ROW LEVEL SECURITY;
   ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
   ALTER TABLE contracts ENABLE ROW LEVEL SECURITY;
   ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
   -- ... todas as outras
   ```

2. **Criar políticas básicas de DENY:**
   ```sql
   -- Para cada tabela, criar política que bloqueia acesso direto
   -- Service Role (usado pelo backend) bypassa automaticamente
   CREATE POLICY "block_direct_access" ON users FOR ALL USING (false);
   ```

3. **Testar backend:**
   - Verificar se todas as operações funcionam
   - Service Role deve bypassar RLS normalmente

### Fase 3: Refinamento (Opcional, Futuro)

Se quiser proteção mais granular:

1. Criar políticas específicas por role/tipo de acesso
2. Usar funções do PostgreSQL para verificar contexto
3. Implementar audit logging de acesso ao banco

---

## ⚠️ AVISO IMPORTANTE

**ANTES de habilitar RLS:**

1. ✅ **Backup completo do banco**
2. ✅ **Testar em ambiente de desenvolvimento primeiro**
3. ✅ **Confirmar que connection string usa Service Role**
4. ✅ **Ter plano de rollback**

**Se o backend NÃO usar Service Role:**
- RLS pode **quebrar toda a aplicação**
- Será necessário criar políticas específicas para cada operação
- Muito mais complexo de implementar

---

## 🔍 Como Verificar se usa Service Role

**Connection string do Service Role geralmente tem:**
- Usuário: `postgres.[PROJECT_REF]` ou `postgres` (superuser)
- Senha: Password do projeto Supabase
- Localização: Settings → Database → Connection string

**Service Role** tem permissões de superuser e **sempre bypassa RLS**.

---

## ✅ Conclusão

### Resposta Direta:

**SIM, esses erros são EXTREMAMENTE IMPORTANTES** porque:

1. ⚠️ **Risco de exposição de dados** se credenciais vazarem
2. ⚠️ **Violação de privacidade** (LGPD/GDPR)
3. ⚠️ **Acesso direto ao banco** não protegido
4. ⚠️ **Conformidade** - RLS é best practice para produção

### Próximos Passos:

1. **Imediato:** Verificar se backend usa Service Role
2. **Esta semana:** Habilitar RLS em todas as tabelas
3. **Testar:** Garantir que backend continua funcionando
4. **Monitorar:** Verificar se Security Advisor mostra 0 erros

---

## 📚 Referências

- [Supabase RLS Documentation](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL RLS Documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Supabase Service Role](https://supabase.com/docs/guides/auth/service-role-key)

---

**Status:** ⚠️ **AÇÃO REQUERIDA**  
**Prioridade:** 🔴 **ALTA**  
**Prazo Recomendado:** Esta semana
