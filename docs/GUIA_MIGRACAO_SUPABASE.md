# Guia Completo: Migração do Backend para Supabase

> **Data:** 2026-01-02
> **Projeto:** IFRS 16 SaaS
> **Status:** Migração Concluída com Sucesso
> **Autor:** Claude Code (Opus 4.5)

---

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Pré-requisitos](#2-pré-requisitos)
3. [Configuração do Projeto Supabase](#3-configuração-do-projeto-supabase)
4. [Alterações no Código](#4-alterações-no-código)
5. [Criação do Schema](#5-criação-do-schema)
6. [Deploy no Cloud Run](#6-deploy-no-cloud-run)
7. [Sincronização de Dados](#7-sincronização-de-dados)
8. [Verificação](#8-verificação)
9. [Troubleshooting](#9-troubleshooting)
10. [Rollback](#10-rollback)

---

## 1. Visão Geral

### 1.1 Arquitetura Antes/Depois

```
ANTES (Cloud SQL/Render):              DEPOIS (Supabase):
┌──────────────────────┐               ┌──────────────────────┐
│  Firebase Hosting    │               │  Firebase Hosting    │
│  (fxstudioai.com)    │               │  (fxstudioai.com)    │
└──────────┬───────────┘               └──────────┬───────────┘
           │                                      │
┌──────────▼───────────┐               ┌──────────▼───────────┐
│  Google Cloud Run    │               │  Google Cloud Run    │
│  (FastAPI Backend)   │               │  (FastAPI Backend)   │
└──────────┬───────────┘               └──────────┬───────────┘
           │                                      │
┌──────────▼───────────┐               ┌──────────▼───────────┐
│  Cloud SQL / Render  │      →        │  Supabase PostgreSQL │
│  PostgreSQL 14       │               │  + PgBouncer Pooler  │
└──────────────────────┘               └──────────────────────┘
```

### 1.2 Compatibilidade Técnica

| Aspecto | Avaliação |
|---------|-----------|
| **Compatibilidade** | 95% |
| **Mudanças de Código** | Mínimas (2 arquivos) |
| **Tempo de Migração** | 2-4 horas |
| **Risco** | Baixo |

### 1.3 O Que Muda

| Componente | Antes | Depois |
|------------|-------|--------|
| Banco de Dados | Cloud SQL / Render | Supabase PostgreSQL |
| Connection Pooling | Não ou externo | PgBouncer incluído |
| SSL | Configurável | Obrigatório |
| Dashboard SQL | pgAdmin externo | UI integrada |

### 1.4 O Que NÃO Muda

- Framework backend (FastAPI)
- ORM (SQLAlchemy async)
- Driver (asyncpg)
- Autenticação JWT
- Stripe integration
- Firebase Storage
- Cloud Run hosting

---

## 2. Pré-requisitos

### 2.1 Ferramentas Necessárias

```bash
# Supabase CLI
npm install -g supabase

# Verificar instalação
supabase --version
```

### 2.2 Acesso Necessário

- [ ] Conta Supabase (https://supabase.com)
- [ ] Acesso ao Google Cloud Console
- [ ] Acesso ao repositório Git

### 2.3 Backup do Banco Atual

```bash
# Se tiver dados importantes, fazer backup primeiro
pg_dump "$OLD_DATABASE_URL" --data-only > backup_data.sql
```

---

## 3. Configuração do Projeto Supabase

### 3.1 Criar Projeto

1. Acesse https://supabase.com/dashboard
2. Clique em "New Project"
3. Configure:
   - **Organization:** Selecione ou crie
   - **Name:** IFRS 16 (ou nome desejado)
   - **Database Password:** Crie uma senha forte
   - **Region:** South America (São Paulo) - `sa-east-1`
4. Clique em "Create new project"
5. Aguarde ~2 minutos para provisionar

### 3.2 Obter Credenciais

1. No dashboard do projeto, vá em **Settings → Database**
2. Copie a **Connection string (URI)** na seção "Connection Pooling"
3. Formato:
   ```
   postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```

### 3.3 Linkar Projeto Local (Opcional)

```bash
cd backend

# Login no Supabase
supabase login

# Linkar projeto existente
supabase link --project-ref [PROJECT_REF]
```

---

## 4. Alterações no Código

### 4.1 Atualizar DATABASE_URL

**Arquivo:** `backend/.env`

```bash
# ANTES (Cloud SQL)
DATABASE_URL=postgresql+asyncpg://user:pass@/db?host=/cloudsql/project:region:instance

# ANTES (Render)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?sslmode=require

# DEPOIS (Supabase Pooler)
DATABASE_URL=postgresql+asyncpg://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
```

> **IMPORTANTE:** Use a URL do **Pooler** (porta 6543), não a conexão direta (porta 5432).

### 4.2 Fix Crítico: PgBouncer (statement_cache_size=0)

**Arquivo:** `backend/app/database.py`

O Supabase usa PgBouncer em **Transaction Mode**, que não suporta prepared statements. Adicione `statement_cache_size=0`:

```python
# PostgreSQL com SSL para Supabase
engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    pool_size=1,
    max_overflow=2,
    pool_recycle=300,
    pool_timeout=30,
    connect_args={
        "ssl": "require",              # SSL obrigatório
        "command_timeout": 60,
        "statement_cache_size": 0,     # CRÍTICO: Desabilita cache para PgBouncer
    },
)
```

### 4.3 Fix Crítico: ENUMs SQLAlchemy (values_callable)

**Arquivo:** `backend/app/models.py`

O asyncpg envia o **nome do enum** (`"ACTIVE"`) por padrão, mas o PostgreSQL espera o **valor** (`"active"`). Adicione `values_callable` em todos os campos ENUM:

```python
# ANTES (causa erro)
status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.INCOMPLETE)

# DEPOIS (correto)
status = Column(
    SQLEnum(SubscriptionStatus, values_callable=lambda obj: [e.value for e in obj]),
    default=SubscriptionStatus.INCOMPLETE,
    nullable=False
)
```

**Campos que precisam dessa correção:**
- `AdminUser.role`
- `Subscription.status`
- `Subscription.plan_type`
- `License.status`
- `License.license_type`
- `Contract.status`
- `Notification.notification_type`

### 4.4 Fix: Cast JSONB em Queries

Se você tem campos TEXT que armazenam JSON e usa operadores `->` ou `->>`, adicione cast explícito:

```python
# ANTES (erro se campo é TEXT)
cv.resultados_json->>'total_vp'

# DEPOIS (funciona)
cv.resultados_json::jsonb->>'total_vp'
```

---

## 5. Criação do Schema

### 5.1 Opção A: Via Supabase CLI (Recomendado)

```bash
cd backend

# Criar arquivo de migration
mkdir -p supabase/migrations

# Copiar o schema completo (ver arquivo de exemplo abaixo)
# Executar migration
supabase db push --linked --include-all
```

### 5.2 Opção B: Via SQL Editor no Dashboard

1. Acesse **SQL Editor** no dashboard Supabase
2. Cole o conteúdo do arquivo de migration
3. Execute

### 5.3 Schema Completo

**Arquivo:** `backend/supabase/migrations/20260102181620_remote_commit.sql`

```sql
-- =============================================================================
-- ENUMS
-- =============================================================================

DO $$ BEGIN
    CREATE TYPE licensestatus AS ENUM ('active', 'suspended', 'expired', 'cancelled');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE licensetype AS ENUM ('trial', 'basic', 'pro', 'enterprise');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE adminrole AS ENUM ('superadmin', 'admin');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE subscriptionstatus AS ENUM ('active', 'past_due', 'cancelled', 'incomplete', 'trialing');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE plantype AS ENUM ('basic_monthly', 'basic_yearly', 'pro_monthly', 'pro_yearly', 'enterprise_monthly', 'enterprise_yearly', 'monthly', 'yearly', 'lifetime');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE contractstatus AS ENUM ('draft', 'active', 'archived');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE notificationtype AS ENUM ('contract_expiring', 'contract_expired', 'remeasurement_done', 'index_updated', 'license_expiring', 'system_alert');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- =============================================================================
-- TABELAS
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

-- Contract Versions (SCD Type 2)
CREATE TABLE IF NOT EXISTS contract_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id UUID NOT NULL REFERENCES contracts(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL DEFAULT 1,
    version_id VARCHAR(50),
    data_inicio DATE NOT NULL,
    prazo_meses INTEGER NOT NULL,
    carencia_meses INTEGER DEFAULT 0,
    parcela_inicial DECIMAL(15, 2) NOT NULL,
    taxa_desconto_anual DECIMAL(8, 4) NOT NULL,
    reajuste_tipo VARCHAR(20) DEFAULT 'nenhum',
    reajuste_periodicidade VARCHAR(20) DEFAULT 'anual',
    reajuste_valor DECIMAL(8, 4),
    mes_reajuste INTEGER,
    resultados_json TEXT,
    total_vp DECIMAL(15, 2),
    total_nominal DECIMAL(15, 2),
    avp DECIMAL(15, 2),
    notas TEXT,
    archived_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- Economic Indexes
CREATE TABLE IF NOT EXISTS economic_indexes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    index_type VARCHAR(20) NOT NULL,
    reference_date TIMESTAMP NOT NULL,
    value VARCHAR(50) NOT NULL,
    source VARCHAR(50) DEFAULT 'BCB' NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

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

-- =============================================================================
-- ÍNDICES
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_admin_users_username ON admin_users (username);
CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users (email);
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_license_key ON licenses (key);
CREATE INDEX IF NOT EXISTS idx_license_user_id ON licenses (user_id);
CREATE INDEX IF NOT EXISTS idx_subscription_user_id ON subscriptions (user_id);
CREATE INDEX IF NOT EXISTS idx_subscription_status ON subscriptions (status);
CREATE INDEX IF NOT EXISTS idx_contract_user_id ON contracts (user_id);
CREATE INDEX IF NOT EXISTS idx_contract_versions_contract_id ON contract_versions (contract_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_contract_version_number ON contract_versions (contract_id, version_number);
CREATE UNIQUE INDEX IF NOT EXISTS uq_economic_index_type_date ON economic_indexes (index_type, reference_date);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions (session_token);
CREATE INDEX IF NOT EXISTS idx_notification_user_id ON notifications (user_id);
CREATE INDEX IF NOT EXISTS idx_document_contract ON documents (contract_id);
CREATE INDEX IF NOT EXISTS idx_validation_license_key ON validation_logs (license_key);

-- Alembic version (compatibilidade)
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) PRIMARY KEY NOT NULL
);
INSERT INTO alembic_version (version_num) VALUES ('reajuste_periodicidade')
ON CONFLICT (version_num) DO NOTHING;
```

### 5.4 Verificar Tabelas Criadas

```bash
# Via Supabase CLI
supabase db execute "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"

# Esperado: 12 tabelas
```

---

## 6. Deploy no Cloud Run

### 6.1 Build Docker

```bash
cd backend

# Build
docker build -t gcr.io/[PROJECT_ID]/ifrs16-backend:latest .

# Push
docker push gcr.io/[PROJECT_ID]/ifrs16-backend:latest
```

### 6.2 Atualizar Cloud Run

```bash
# Atualizar variáveis de ambiente
gcloud run services update ifrs16-backend \
  --region us-central1 \
  --project [PROJECT_ID] \
  --set-env-vars DATABASE_URL="postgresql+asyncpg://postgres.[REF]:[PASS]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres"
```

> **IMPORTANTE:** Use `--set-env-vars` com TODAS as variáveis necessárias, pois esse comando substitui as existentes.

### 6.3 Variáveis de Ambiente Completas

```bash
gcloud run services update ifrs16-backend \
  --region us-central1 \
  --set-env-vars "\
DATABASE_URL=postgresql+asyncpg://postgres.[REF]:[PASS]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres,\
JWT_SECRET_KEY=sua-chave-jwt-secreta,\
JWT_ALGORITHM=HS256,\
ACCESS_TOKEN_EXPIRE_MINUTES=1440,\
REFRESH_TOKEN_EXPIRE_DAYS=30,\
ADMIN_TOKEN=seu-token-admin,\
STRIPE_PUBLISHABLE_KEY=pk_...,\
STRIPE_PRICING_TABLE_ID=prctbl_...,\
STRIPE_WEBHOOK_SECRET=whsec_...,\
STRIPE_PRICE_BASIC_MONTHLY=price_...,\
STRIPE_PRICE_BASIC_YEARLY=price_...,\
STRIPE_PRICE_PRO_MONTHLY=price_...,\
STRIPE_PRICE_PRO_YEARLY=price_...,\
STRIPE_PRICE_ENTERPRISE_MONTHLY=price_...,\
STRIPE_PRICE_ENTERPRISE_YEARLY=price_...,\
FRONTEND_URL=https://fxstudioai.com,\
ENVIRONMENT=production,\
DEBUG=False,\
CORS_ORIGINS=https://fxstudioai.com,\
SMTP_HOST=smtp.sendgrid.net,\
SMTP_PORT=587,\
SMTP_USER=apikey,\
SMTP_PASSWORD=SG...,\
SMTP_FROM_EMAIL=contato@fxstudioai.com,\
SMTP_FROM_NAME=IFRS 16"
```

---

## 7. Sincronização de Dados

### 7.1 Índices Econômicos

Sincronizar índices econômicos do Banco Central via API:

```bash
# SELIC
curl -X POST "https://[BACKEND_URL]/api/economic-indexes/sync/selic" \
  -H "X-Admin-Token: [ADMIN_TOKEN]"

# IGPM
curl -X POST "https://[BACKEND_URL]/api/economic-indexes/sync/igpm" \
  -H "X-Admin-Token: [ADMIN_TOKEN]"

# IPCA
curl -X POST "https://[BACKEND_URL]/api/economic-indexes/sync/ipca" \
  -H "X-Admin-Token: [ADMIN_TOKEN]"

# CDI
curl -X POST "https://[BACKEND_URL]/api/economic-indexes/sync/cdi" \
  -H "X-Admin-Token: [ADMIN_TOKEN]"

# INPC
curl -X POST "https://[BACKEND_URL]/api/economic-indexes/sync/inpc" \
  -H "X-Admin-Token: [ADMIN_TOKEN]"
```

### 7.2 Resultado Esperado

| Índice | Registros | Status |
|--------|-----------|--------|
| SELIC | ~473 | OK |
| IGPM | ~438 | OK |
| IPCA | ~550 | OK |
| CDI | ~473 | OK |
| INPC | ~559 | OK |
| TR | - | Erro API BCB (406) |

> **Nota:** O índice TR pode falhar devido a limitações da API do Banco Central.

### 7.3 Migrar Dados Existentes (Se Necessário)

```bash
# Restaurar backup de dados
psql "$SUPABASE_URL" < backup_data.sql
```

---

## 8. Verificação

### 8.1 Health Check

```bash
curl -s "https://[BACKEND_URL]/health"
# Esperado: {"status":"healthy","environment":"production"}
```

### 8.2 Testar Endpoints

```bash
# Índices econômicos
curl -s "https://[BACKEND_URL]/api/economic-indexes?index_type=selic&limit=5"

# Tipos de índices
curl -s "https://[BACKEND_URL]/api/economic-indexes/types"
```

### 8.3 Verificar Logs

```bash
gcloud run services logs read ifrs16-backend \
  --region us-central1 \
  --limit 50
```

### 8.4 Testar Frontend

1. Acesse https://fxstudioai.com
2. Tente fazer login
3. Verifique se o dashboard carrega
4. Teste criar um contrato

---

## 9. Troubleshooting

### 9.1 Erro: InvalidSQLStatementNameError (Prepared Statements)

```
asyncpg.exceptions.InvalidSQLStatementNameError:
prepared statement "..." does not exist
```

**Causa:** PgBouncer não suporta prepared statements em Transaction Mode.

**Solução:** Adicionar `statement_cache_size=0` em `database.py`:

```python
connect_args={
    "statement_cache_size": 0,
}
```

### 9.2 Erro: InvalidTextRepresentationError (ENUMs)

```
asyncpg.exceptions.InvalidTextRepresentationError:
invalid input value for enum subscriptionstatus: "ACTIVE"
```

**Causa:** SQLAlchemy envia nome do enum (`"ACTIVE"`) em vez do valor (`"active"`).

**Solução:** Adicionar `values_callable` em todos os campos ENUM:

```python
status = Column(
    SQLEnum(SubscriptionStatus, values_callable=lambda obj: [e.value for e in obj]),
    ...
)
```

### 9.3 Erro: UndefinedFunctionError (JSONB)

```
asyncpg.exceptions.UndefinedFunctionError:
operator does not exist: text -> unknown
```

**Causa:** Usando operadores JSONB (`->`, `->>`) em campo TEXT.

**Solução:** Adicionar cast explícito:

```python
# ANTES
resultados_json->>'total_vp'

# DEPOIS
resultados_json::jsonb->>'total_vp'
```

### 9.4 Erro: SSL Connection Required

```
asyncpg.exceptions.ConnectionError:
SSL connection is required
```

**Solução:** Confirmar `ssl: "require"` em `connect_args`:

```python
connect_args={
    "ssl": "require",
}
```

### 9.5 Verificar Conexão Manualmente

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

async def test():
    engine = create_async_engine(
        "postgresql+asyncpg://postgres.[REF]:[PASS]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres",
        connect_args={"ssl": "require", "statement_cache_size": 0}
    )
    async with engine.connect() as conn:
        result = await conn.execute("SELECT version()")
        print(result.fetchone())
    await engine.dispose()

asyncio.run(test())
```

---

## 10. Rollback

### 10.1 Reverter para Banco Anterior

Se houver problemas críticos, reverter a variável DATABASE_URL:

```bash
gcloud run services update ifrs16-backend \
  --region us-central1 \
  --set-env-vars DATABASE_URL="[OLD_DATABASE_URL]"
```

### 10.2 Verificar Funcionamento

```bash
curl -s "https://[BACKEND_URL]/health"
```

### 10.3 Manter Banco Antigo Ativo

Recomendação: manter o banco antigo ativo por 7 dias após migração bem-sucedida.

---

## Anexos

### A. Arquivos Modificados na Migração

| Arquivo | Alteração |
|---------|-----------|
| `backend/.env` | DATABASE_URL atualizada |
| `backend/app/database.py` | `statement_cache_size=0` |
| `backend/app/models.py` | `values_callable` em 7 ENUMs |
| `backend/app/services/dashboard_service.py` | Cast `::jsonb` |

### B. Tabelas Criadas

1. `admin_users`
2. `users`
3. `licenses`
4. `subscriptions`
5. `contracts`
6. `contract_versions`
7. `economic_indexes`
8. `user_sessions`
9. `notifications`
10. `documents`
11. `validation_logs`
12. `alembic_version`

### C. ENUMs Criados

1. `licensestatus`
2. `licensetype`
3. `adminrole`
4. `subscriptionstatus`
5. `plantype`
6. `contractstatus`
7. `notificationtype`

### D. Connection String Final

```
postgresql+asyncpg://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-sa-east-1.pooler.supabase.com:6543/postgres
```

---

*Documento gerado por Claude Code (Opus 4.5) em 2026-01-02*
