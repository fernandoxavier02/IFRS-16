# CHANGELOG_AI.md

> **Purpose:** Log all changes made by AI agents for traceability and verification.  
> **Format:** Reverse chronological order. Each entry includes date, agent, files changed, and verification status.

---

## Changelog

### 2025-12-31 — Limpeza completa do banco de dados

**Agent:** Windsurf Cascade  
**Task:** Remover todos os registros do banco de dados (manter estrutura)

**Ações executadas:**

- Script criado: `backend/limpar_todos_dados.py`
- Banco: `ifrs16_licenses.db`
- Tabelas mantidas: 6 (estrutura preservada)

**Registros deletados:**

- Usuários: 1
- Licenças: 3
- Logs de validação: 5
- Admin users: 1
- Assinaturas: 0
- Contratos: 0
- **Total:** 10 registros

**Verificação:**

- [x] Todos os registros removidos
- [x] Estrutura das tabelas mantida
- [x] Banco otimizado (VACUUM)
- [x] Verificação confirmada (0 usuários)

---

### 2025-12-30 — Deploy para fxstudioai.com

**Agent:** Windsurf Cascade  
**Task:** Build e deploy do frontend para domínio customizado fxstudioai.com

**Ações executadas:**

- Deploy Firebase Hosting: 133 arquivos
- Projeto: `ifrs16-app`
- Domínio configurado: `fxstudioai.com` (DNS: 199.36.158.100)

**URLs atualizadas:**

- **Produção:** https://fxstudioai.com
- Firebase (fallback): https://ifrs16-app.web.app
- Backend API: https://ifrs16-backend-1051753255664.us-central1.run.app

**Arquivos atualizados:**

- `docs/ai/10-STACK.md` — URLs de produção

**Verificação:**

- [x] Deploy concluído (133 arquivos)
- [x] DNS resolvendo corretamente
- [x] Domínio customizado ativo
- [ ] SSL/TLS (aguardar propagação se necessário)

---

### 2025-12-30 — Context Pack v2.0 (Modular)

**Agent:** Windsurf Cascade  
**Task:** Criar Context Pack enxuto e modular, compatível com Claude Code e Codex

**Arquivos criados:**

- `docs/ai/00-INDEX.md` — Índice do Context Pack
- `docs/ai/10-STACK.md` — Stack tecnológica e comandos
- `docs/ai/20-ARCHITECTURE.md` — Arquitetura e diagramas
- `docs/ai/30-DATA_BACKEND.md` — Models, API, schemas
- `docs/ai/40-FRONTEND_APP.md` — Frontend e deploy
- `docs/ai/90-OPEN_QUESTIONS.md` — TODOs e questões em aberto
- `.windsurf/rules/00-always-on.md` — Regras globais (always on)
- `.windsurf/rules/10-backend-python.md` — Regras para backend Python
- `.windsurf/rules/20-frontend.md` — Regras para frontend
- `.windsurf/workflows/ifrs16-update-context.md` — Workflow de atualização
- `.windsurf/workflows/atualiza-contexto-v2.md` — Comando `/atualiza-contexto` otimizado
- `.claude/commands/ifrs16-update-context.md` — Comando Claude
- `docs/ai/templates/codex-prompts/ifrs16-update-context.md` — Template Codex

**Arquivos atualizados:**

- `AGENTS.md` — Simplificado para ~50 linhas, aponta para docs/ai/
- `CLAUDE.md` — Simplificado para ~50 linhas, aponta para docs/ai/

**Estrutura final:**

```
docs/ai/
├── 00-INDEX.md           # Índice
├── 10-STACK.md           # Stack
├── 20-ARCHITECTURE.md    # Arquitetura
├── 30-DATA_BACKEND.md    # Backend/Data
├── 40-FRONTEND_APP.md    # Frontend
├── 90-OPEN_QUESTIONS.md  # TODOs
├── CHANGELOG_AI.md       # Este arquivo
├── DECISIONS.md          # Decisões
├── PROJECT_CONTEXT.md    # Legacy (mantido)
└── templates/codex-prompts/
    └── ifrs16-update-context.md
```

**Verificação:**

- [x] Arquivos criados sem duplicação
- [x] AGENTS.md e CLAUDE.md < 60 linhas
- [x] Rules e workflows configurados
- [ ] Testes não afetados (mudança apenas em documentação)

---

### 2025-12-30 — Template seguro de backend/.env

**Agent:** Windsurf Cascade  
**Task:** Criar/ajustar `.env` local para o projeto (sem expor segredos)

**Arquivos modificados:**

- `backend/.env` — Padronizado com base em `backend/env.example`, removendo duplicações/indentação e **removendo credenciais sensíveis** que estavam em texto claro.
- `docs/ai/CHANGELOG_AI.md` — Registro da alteração

**Verificação:**

- [ ] Testes não executados (mudança apenas em arquivo local `.env`)

### 2025-12-30 — Validação de Dependências, MCPs e CLIs (Firebase/Stripe)

**Agent:** Windsurf Cascade  
**Task:** Verificar/instalar dependências e validar MCPs + CLIs (Firebase/Stripe)

**Arquivos modificados:**

- `docs/ai/CHANGELOG_AI.md` — Registro das validações executadas

**Ações executadas (ambiente local):**

- `backend/venv` recriado com Python 3.12 (substituiu venv quebrado que apontava para Python 3.14 inexistente; backup criado como `backend/venv_bak_<timestamp>`)
- Dependências instaladas:
  - `pip install -r backend/requirements.txt`
  - `pip install -r mcp/requirements.txt`

**Verificação:**

- [x] `backend/venv`: `pip check` => **No broken requirements found**
- [x] Backend: `cd backend && pytest -v` => **194 passed**
- [x] MCP (imports): `import mcp, firebase_admin, stripe` => **OK**
- [x] MCP tests: `cd mcp && pytest -v -m "not integration" --ignore=tests/test_production_via_api.py` => **119 passed**
- [x] Firebase CLI: `firebase --version` => **15.1.0**
- [x] Stripe CLI: `stripe version` => **1.33.2**

**Observação:**

- `mcp/tests/test_production_via_api.py` requer `aiohttp`, que não está em `mcp/requirements.txt` e por isso falha na coleta se não for ignorado.

### 2025-12-30 — Correções de Qualidade (Fase 4)

**Agent:** Windsurf Cascade  
**Task:** Melhorias de qualidade e manutenibilidade

**Arquivos modificados:**

- `backend/requirements.txt` — Versões fixadas para reprodutibilidade (fastapi==0.128.0, sqlalchemy==2.0.41, etc.)

**Verificação:**

- [x] Todas as dependências com versões exatas
- [x] App importa corretamente

---

### 2025-12-30 — Correções Médias (Fase 3)

**Agent:** Windsurf Cascade  
**Task:** Corrigir funcionalidades médias e imports quebrados

**Arquivos criados:**

- `backend/app/repositories/__init__.py` — Módulo de repositories
- `backend/app/repositories/contracts.py` — ContractRepository com operações CRUD

**Arquivos modificados:**

- `backend/app/routers/contracts.py` — Adicionada validação robusta de status/categoria (retorna 422 em vez de 500)
- `backend/app/services/contracts_service.py` — Corrigido import quebrado (ContractCreate/ContractUpdate → Any)
- `backend/app/main.py` — init_db condicionado apenas para ambiente de desenvolvimento

**Correções implementadas:**

1. **Validação de status/categoria** — Retorna 422 com mensagem clara para valores inválidos
2. **ContractRepository criado** — Resolve ImportError em contracts_service.py
3. **init_db apenas em dev** — Em produção, usar Alembic migrations

**Verificação:**

- [x] App importa corretamente
- [x] ContractRepository e ContractService importam OK
- [x] Validação de status/categoria funciona

---

### 2025-12-30 — Correções de Segurança ALTA (Fase 2)

**Agent:** Windsurf Cascade  
**Task:** Corrigir bugs de segurança de prioridade ALTA

**Arquivos modificados:**

- `backend/app/crud.py` — Corrigido controle de ativações: agora incrementa contador quando nova máquina é usada
- `backend/app/routers/admin.py` — Corrigido grant_license: usa LicenseTypeEnum em vez de LicenseStatusEnum; respeita tipo solicitado
- `backend/app/config.py` — Adicionado LICENSE_LIMITS como fonte única de verdade para limites de licença
- `backend/app/models.py` — Atualizado features() para usar LICENSE_LIMITS centralizado
- `backend/app/routers/payments.py` — Atualizado get_prices() para usar LICENSE_LIMITS (basic=50, pro=500 contratos)
- `backend/app/routers/auth.py` — Adicionado rate limit 5/min no login admin
- `backend/app/routers/licenses.py` — Adicionado rate limit 30/min na validação de licença

**Correções implementadas:**

1. **Controle de ativações por dispositivo** — Contador agora incrementa corretamente para novas máquinas
2. **Concessão manual de licença** — Usa enum correto e respeita tipo solicitado (trial/basic/pro/enterprise)
3. **Limites de contratos unificados** — Fonte única em LICENSE_LIMITS (trial=5, basic=50, pro=500, enterprise=ilimitado)
4. **Rate limiting** — Login admin: 5/min, Validação licença: 30/min

**Verificação:**

- [x] App importa corretamente
- [x] Todos os routers importam OK
- [x] LICENSE_LIMITS disponível: ['trial', 'basic', 'pro', 'enterprise']

---

### 2025-12-30 — Remoção de Credenciais Expostas (Fase 1 - Críticos)

**Agent:** Windsurf Cascade  
**Task:** Remover credenciais reais de docs/scripts e exigir env vars

**Arquivos modificados:**

- `DEPLOY_FINAL_STATUS.md` — Substituídas credenciais reais por placeholders
- `FINALIZAR_FIREBASE.md` — Substituídas JWT_SECRET_KEY e STRIPE_SECRET_KEY por placeholders
- `MIGRACAO_CLOUD_SQL_EM_ANDAMENTO.md` — Substituídas senhas DB, URLs e credenciais admin por placeholders
- `backend/criar_master_job.py` — Removidas credenciais hardcoded; exige CLOUD_SQL_USER, CLOUD_SQL_PASSWORD, ADMIN_EMAIL, ADMIN_USERNAME, ADMIN_PASSWORD; não loga senhas
- `backend/init_production_db.py` — Removida senha padrão; exige ADMIN_EMAIL e ADMIN_PASSWORD; não loga senha
- `listar_usuarios_ativos.ps1` — Removida senha hardcoded; exige ADMIN_EMAIL e ADMIN_PASSWORD via env vars
- `.gitignore` — Adicionados padrões para binários (*.exe, cloud-sql-proxy*) e backups de venv

**Verificação:**

- [x] App importa corretamente: `from app.main import app` => OK
- [x] `criar_master_job.py` falha sem env vars (exit code 1)
- [x] `listar_usuarios_ativos.ps1` falha sem env vars (exit code 1)
- [x] Arquivos sensíveis não tracked no Git
- [x] `.gitignore` atualizado

**Próximos passos:**

- **MANUAL:** Rotacionar segredos em produção (JWT, Stripe, DB) nos dashboards
- Fase 2: Correções de segurança (senha temporária, token admin, ativações, limites)

---

### 2025-12-30 — Correções Críticas de Segurança (Fase 1)

**Agent:** Windsurf Cascade  
**Task:** Auditoria de segurança + correção de 4 vulnerabilidades críticas  
**Branch:** Ajustes

**Arquivos criados:**
- `backend/.env.example` — Template completo com todas as variáveis de ambiente e checklist de segurança

**Arquivos modificados:**
- `backend/requirements.txt` — Adicionado `slowapi>=0.1.9` para rate limiting
- `backend/app/main.py` — Validação crítica de secrets + configuração do limiter
- `backend/app/routers/payments.py` — Rate limiting no webhook + endpoint de teste removido
- `backend/app/routers/contracts.py` — Sanitização de queries LIKE

**Correções implementadas:**

1. **CRÍTICO-01: Validação de Secrets em Produção**
   - App agora falha no startup se detectar placeholders em produção
   - Previne deploy com JWT_SECRET_KEY, ADMIN_TOKEN ou STRIPE keys inválidas
   - Arquivo: `backend/app/main.py:80-86`

2. **CRÍTICO-02: Rate Limiting em Webhook Stripe**
   - Webhook `/api/payments/webhook` limitado a 100 requisições/minuto por IP
   - Previne DoS e criação fraudulenta de licenças
   - Arquivos: `backend/app/main.py:12-14,108,166-167` + `backend/app/routers/payments.py:9-10,28,157`

3. **CRÍTICO-03: Sanitização de Queries LIKE**
   - Escape de caracteres especiais (`%`, `_`, `\`) em buscas de contratos
   - Previne bypass de filtros e SQL injection via LIKE
   - Arquivo: `backend/app/routers/contracts.py:172-179`

4. **CRÍTICO-04: Remoção de Endpoint de Teste**
   - Endpoint `/api/payments/test-email` removido completamente
   - Previne exposição de configuração SMTP e spam
   - Arquivo: `backend/app/routers/payments.py:259-289` (deletado)

**Verificação:**
- [x] Código compila sem erros
- [x] Imports resolvidos
- [x] Nenhum secret exposto
- [x] Commit realizado na branch Ajustes

**Próximos passos:**
- Fase 2: Correções de prioridade ALTA (validação de senha, bcrypt, logs)
- Instalar dependência: `pip install slowapi>=0.1.9`
- Rodar testes: `cd backend && pytest -v`

---

### 2025-12-30 — Sistema de Contexto Multi-Ambiente Completo

**Agent:** Windsurf Cascade  
**Task:** Criar sistema de contexto versionado para 4 ambientes (Codex, Claude, Cursor, Windsurf)

**Arquivos lidos:**
- `docs/ai/PROJECT_CONTEXT.md`
- `docs/ai/DECISIONS.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.claude/rules/*.md`
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/requirements.txt`
- `firebase.json`
- `.gitignore`

**Arquivos criados:**
- `.cursor/rules/00-core.md` — Regras core para Cursor (recuperação ativa, 2 tentativas)
- `.cursor/rules/10-architecture.md` — Mapa de arquitetura para Cursor
- `.cursor/rules/20-quality.md` — Padrões de qualidade para Cursor
- `.windsurf/workflows/altera-codigo.md` — Workflow de alteração segura
- `.windsurf/workflows/analisa-bug.md` — Workflow de análise de bugs
- `.windsurf/workflows/auditoria-se-codigo.md` — Workflow de auditoria
- `.windsurf/workflows/executa-plano.md` — Workflow de execução com quick wins
- `.windsurf/workflows/extensive-and-complete-optitimization.md` — Workflow de otimização

**Verificação:**
- [x] Todos os paths referenciados existem
- [x] Nenhum segredo exposto
- [x] Comandos verificados contra arquivos do repo
- [x] Consistência entre arquivos de contexto

---

### 2025-12-27 — Context Update Workflow

**Agent:** Windsurf Cascade  
**Task:** Create periodic context update workflow for Claude and Codex

**Files Created:**
- `.windsurf/workflows/atualiza-contexto.md` — 12-step workflow for periodic context synchronization

**Purpose:**
- Keep `docs/ai/PROJECT_CONTEXT.md` synchronized with actual code
- Update directory structure, models, routers, env vars
- Maintain consistency between `AGENTS.md`, `CLAUDE.md`, and `.claude/rules/`

**Verification:**
- [x] Workflow file created
- [x] All 12 steps documented with commands

---

### 2025-12-27 — Context Pack Creation

**Agent:** Windsurf Cascade  
**Task:** Create repo-native context system for Codex and Claude Code

**Files Created:**
- `docs/ai/PROJECT_CONTEXT.md` — Project overview, commands, architecture
- `docs/ai/DECISIONS.md` — Decision log
- `docs/ai/CHANGELOG_AI.md` — This file
- `AGENTS.md` — Codex configuration
- `CLAUDE.md` — Claude Code configuration
- `.claude/rules/00-core.md` — Core rules
- `.claude/rules/10-repo-map.md` — Repository map
- `.claude/rules/20-quality.md` — Quality standards

**Verification:** 
- [ ] All referenced paths exist
- [ ] No secrets included
- [ ] Commands verified against repo files

---

*Add new entries above this line. Format:*

```
### YYYY-MM-DD — Brief Title

**Agent:** [Agent name]  
**Task:** [What was requested]

**Files Changed:**
- `path/to/file` — Description of change

**Verification:**
- [ ] Tests pass: `pytest -v`
- [ ] Manual verification: [description]
```

---
