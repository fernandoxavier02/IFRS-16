# DECISIONS.md

> **Purpose:** Log architectural and implementation decisions for AI agents and developers.  
> **Format:** Each decision includes context, options considered, and rationale.

---

## Decision Log

### DEC-001: Context Pack Structure (2025-12-27)

**Context:** Need a tool-agnostic context system for AI coding assistants (Codex, Claude Code, Windsurf).

**Decision:** Create `docs/ai/` directory with:
- `PROJECT_CONTEXT.md` — High-signal project overview
- `DECISIONS.md` — This file
- `CHANGELOG_AI.md` — AI-made changes log

Plus tool-specific wiring:
- `AGENTS.md` (root) — For OpenAI Codex
- `CLAUDE.md` (root) + `.claude/rules/` — For Claude Code

**Rationale:** 
- Centralized context reduces hallucination
- Tool-specific files follow each tool's conventions
- Version-controlled alongside code

---

### DEC-002: Backend Stack (Historical)

**Context:** Backend API for license management.

**Decision:** FastAPI + SQLAlchemy async + PostgreSQL

**Rationale:**
- FastAPI: Modern, async, auto-docs
- SQLAlchemy async: Non-blocking DB operations
- PostgreSQL: Production-grade, Render free tier

---

### DEC-003: Frontend Hosting (Historical)

**Context:** Static HTML/JS frontend needs hosting.

**Decision:** Firebase Hosting

**Rationale:**
- Free tier sufficient
- Fast CDN
- Easy deployment via CLI

---

### DEC-004: Backend Hosting (Historical)

**Context:** Python backend needs container hosting.

**Decision:** Google Cloud Run

**Rationale:**
- Scales to zero (cost-effective)
- Docker-based
- Same GCP project as Firebase

---

### DEC-005: Sistema de Contexto Multi-Ambiente (2025-12-30)

**Context:** Necessidade de contexto persistente e regras padronizadas para 4 ambientes de IA: Codex, Claude, Cursor e Windsurf.

**Decision:** Criar estrutura de arquivos de contexto:
- `docs/ai/PROJECT_CONTEXT.md` — Fonte da verdade canônica
- `docs/ai/DECISIONS.md` — Log de decisões
- `docs/ai/CHANGELOG_AI.md` — Log de mudanças por AI
- `AGENTS.md` — Config para Codex
- `CLAUDE.md` + `.claude/rules/` — Config para Claude
- `.cursor/rules/` — Config para Cursor
- `.windsurf/workflows/` — Workflows para Windsurf

**Rationale:**
- Cada ferramenta tem seu próprio formato de configuração
- Fonte da verdade única evita inconsistências
- Regra das 2 tentativas reduz loops de correção
- Recuperação ativa de contexto melhora precisão

**Trade-offs:**
- Mais arquivos para manter sincronizados
- Workflow `/atualiza-contexto` criado para facilitar manutenção

---

### DEC-006: World-Class Context System Initialized (2026-01-01)

**Context:** Requirement to establish a "World-Class Context System" to prevent incorrect edits by JetBrains AI agents (Junie/AI Assistant).

**Decision:**
- Initialize `docs/ai/PROJECT_CONTEXT.md`, `DECISIONS.md`, `CHANGELOG_AI.md`, `CONTEXT_INDEX.md`.
- Establish `AGENTS.md` and `.junie/guidelines.md` for Junie.
- Configure `.aiassistant/rules/` for AI Assistant.
- Implement `.aiignore` for privacy.
- Define `docs/ai/SELF_REVIEW.md`.

**Rationale:** Standardize agent behavior across JetBrains IDE tools. Enforce active retrieval and verification rules.

**Trade-offs:** Initial overhead in setting up rules, but long-term gain in agent reliability.

---

### DEC-007: Stripe CLI and MCP Integration (2026-01-01)

**Context:** Need for direct interaction with Stripe API and local simulation of Stripe events.

**Decision:**
- Installed Stripe CLI via `npm install -g stripe-cli`.
- Configured/Verified Stripe MCP server (both official `@stripe/mcp` and local Python version).
- Integrated Stripe commands into the project documentation.

**Rationale:**
- Stripe CLI allows testing webhooks locally and managing Stripe resources without the dashboard.
- MCP (Model Context Protocol) provides the AI agent with direct tools to interact with the Stripe ecosystem safely.

---

### DEC-008: Google Cloud SQL MCP Integration (2026-01-01)

**Context:** Requirement to enable direct database interaction and monitoring for AI agents on the Cloud SQL PostgreSQL instance.

**Decision:**
- Configured documentation for both the official `@modelcontextprotocol/server-postgres` and the local `mcp/cloudsql_mcp_server.py`.
- Verified database dependencies (`asyncpg`, `psycopg2-binary`) are present in `mcp/requirements.txt`.
- Added connection and execution commands to `PROJECT_CONTEXT.md`.

**Rationale:** Enabling the GCloud SQL MCP allows the agent to verify database states, run diagnostic queries, and manage schema migrations more effectively without manual intervention.

---

### DEC-010: API de Índices Econômicos do Banco Central (2026-01-01)

**Context:** Necessidade de fornecer índices econômicos (SELIC, IGPM, IPCA, CDI, INPC, TR) atualizados automaticamente para cálculos de reajuste de contratos IFRS 16.

**Decision:**
- Criar modelo `EconomicIndex` para armazenar índices no banco de dados
- Implementar `BCBService` para buscar dados da API do Banco Central do Brasil (BCB)
- Criar router `/api/economic-indexes` com endpoints para listagem, busca do último valor e sincronização
- Endpoints de sincronização requerem autenticação admin
- Endpoints de consulta são públicos (para facilitar integração)

**Rationale:**
- Integração com API oficial do BCB garante dados atualizados e confiáveis
- Armazenamento local reduz dependência de APIs externas e melhora performance
- Sincronização manual via admin permite controle sobre atualizações
- Endpoints públicos facilitam uso pelo frontend sem autenticação obrigatória

**Trade-offs:**
- Dados não atualizados automaticamente (requer ação admin para sincronizar)
- Dependência da disponibilidade da API do BCB para sincronização
- Armazenamento adicional no banco de dados (trade-off aceitável pela performance)

**Files Created:**
- `backend/app/models.py` — Modelo `EconomicIndex`
- `backend/app/services/bcb_service.py` — Service para integração com BCB
- `backend/app/routers/economic_indexes.py` — Router com endpoints
- `backend/alembic/versions/20260101_add_economic_indexes_table.py` — Migration

**Files Modified:**
- `backend/app/main.py` — Registro do router
- `backend/app/schemas.py` — Schemas Pydantic para índices

---

### DEC-009: Firebase CLI and MCP Integration (2026-01-01)

**Context:** Need to manage Firebase Hosting and provide the AI agent with tools to interact with Firebase services (Auth, Firestore, Storage).

**Decision:**
- Installed Firebase CLI via `npm install -g firebase-tools`.
- Verified the local `mcp/firebase_mcp_server.py` and its dependencies (`firebase-admin`).
- Added Firebase management and MCP execution commands to `PROJECT_CONTEXT.md`.

**Rationale:** Firebase is the primary hosting for the frontend and handles authentication. Direct integration via CLI and MCP allows the agent to automate deployments and verify user/project states.

---

### DEC-010: MCP Functionality Status and Testing (2026-01-01)

**Context:** Verify if the newly installed MCP servers are actually operational.

**Decision:**
- Performed dry-runs of the local MCP servers using their built-in test routines.
- Identified that while the core logic is sound, external connectivity depends on specific project states (Firebase database initialization) and network/credential access (Cloud SQL).

**Rationale:** Immediate verification ensures the installation was correct and identifies environmental blockers early.

**Status:**
- **Stripe:** Fully Operational.
- **Firebase/Cloud SQL:** Framework Operational, Environmental connection pending.

---

### DEC-011: World-Class Context System Initialized (2026-01-01)

**Context:** Requirement to build an exceptional, repo-native context system for both OpenAI Codex and Claude Code agents to operate with maximum accuracy.

**Decision:**
- Updated and consolidated `docs/ai/PROJECT_CONTEXT.md` with comprehensive project overview, exact commands, architecture map, conventions, invariants, and known pitfalls
- Enhanced `DECISIONS.md` with this initialization entry
- Verified and updated `AGENTS.md` (Codex entry point) and `CLAUDE.md` (Claude entry point)
- Updated `.claude/rules/` files (00-core.md, 10-repo-map.md, 20-quality.md)
- Created `.cursor/rules/000-foundation.mdc` for Cursor IDE

**Rationale:**
- Single source of truth (`PROJECT_CONTEXT.md`) prevents inconsistencies
- Tool-specific entry points (AGENTS.md, CLAUDE.md, .cursor/rules/) follow each tool's conventions
- Active retrieval protocol ensures agents read files before making changes
- Stop rule (2 failed attempts) prevents infinite correction loops
- All commands verified against actual repo files

**Trade-offs:**
- Initial overhead in maintaining context files, but significant long-term gain in agent reliability and accuracy
- Multiple files to keep synchronized, but tool-specific formats improve adoption

**Risks:**
- Context files may become outdated if not maintained
- Mitigation: Periodic context update workflow (see `.windsurf/workflows/atualiza-contexto.md`)

---

### DEC-012: Migracao do Banco de Dados para Supabase (2026-01-02)

**Context:** Avaliacao de viabilidade para migrar o banco de dados PostgreSQL de Cloud SQL/Render para Supabase.

**Decision:** APROVADO - Migrar para Supabase

**Analise de Viabilidade:**
- Viabilidade: 95% (Alta)
- Mudancas de codigo: Zero
- Tempo estimado: 2-3 dias
- Risco: Baixo

**Razoes para Migracao:**
1. Zero mudancas de codigo - Backend 100% compativel (SQLAlchemy + asyncpg)
2. Todas as funcoes PostgreSQL suportadas (generate_series, LATERAL, JSONB)
3. Menor custo operacional - Backups, logs, dashboard incluidos
4. Escalabilidade simples - Upgrade de plano sem downtime
5. Recursos extras - REST API, Realtime, Auth (opcional futuro)

**Compatibilidade Verificada:**
- 12 tabelas com UUID primary keys
- 8 Foreign Keys com CASCADE/SET NULL
- 18 indices (3 UNIQUE, 15 regulares)
- 6 ENUMs PostgreSQL
- Queries complexas com generate_series(), LATERAL, jsonb_array_elements()

**Mudancas Necessarias:**
- Apenas variavel de ambiente DATABASE_URL
- Formato: `postgresql+asyncpg://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres`

**Plano de Migracao:**
1. Fase 1: Preparacao (2-4h) - Criar projeto Supabase, obter credenciais
2. Fase 2: Schema (1-2h) - Executar migrations Alembic
3. Fase 3: Dados (1-2h) - pg_dump/pg_restore
4. Fase 4: Testes (2-3h) - pytest completo
5. Fase 5: Deploy (1h) - Atualizar Cloud Run
6. Fase 6: Monitoramento (24-48h)

**Riscos e Mitigacoes:**
- Limite de conexoes (100 free): Pool atual usa 3 max - OK
- Latencia PgBouncer: pool_pre_ping=True ja configurado - OK
- Migracao de dados: pg_dump/pg_restore padrao - OK

**Documentacao:**
- `docs/AVALIACAO_MIGRACAO_SUPABASE.md` - Documento completo de avaliacao

**Trade-offs:**
- Dependencia de vendor (Supabase) vs flexibilidade (Cloud SQL)
- Custo fixo ($25/mes Pro) vs pay-per-use (Cloud SQL)

---

*Add new decisions below this line. Use format: DEC-XXX: Title (YYYY-MM-DD)*

---
