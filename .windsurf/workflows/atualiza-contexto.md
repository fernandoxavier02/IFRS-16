---
description: Atualiza o contexto do projeto para Claude e Codex
---

# Workflow: Atualização de Contexto do Projeto

> **Frequência recomendada:** Semanal ou após mudanças significativas  
> **Objetivo:** Manter os arquivos de contexto sincronizados com o estado atual do código

---

## Passo 1: Verificar Estado Atual do Repositório

Listar arquivos modificados recentemente para identificar mudanças não documentadas:

```powershell
git log --oneline -20
git status
```

---

## Passo 2: Atualizar Estrutura de Diretórios

Verificar se a estrutura em `docs/ai/PROJECT_CONTEXT.md` (seção 2) ainda reflete a realidade:

1. Listar diretórios principais:
   ```powershell
   Get-ChildItem -Directory | Select-Object Name
   Get-ChildItem backend/app -Directory | Select-Object Name
   Get-ChildItem backend/app/routers | Select-Object Name
   Get-ChildItem backend/app/services | Select-Object Name
   ```

2. Se houver novos diretórios ou arquivos importantes, atualizar:
   - `docs/ai/PROJECT_CONTEXT.md` → Seção "Repository Structure"
   - `.claude/rules/10-repo-map.md` → Seção "Directory Structure"

---

## Passo 3: Atualizar Lista de Routers/Endpoints

Verificar routers existentes e comparar com documentação:

```powershell
Get-ChildItem backend/app/routers/*.py | Select-Object Name
```

Atualizar `docs/ai/PROJECT_CONTEXT.md` se houver novos routers.

---

## Passo 4: Atualizar Lista de Models

Verificar models em `backend/app/models.py` e comparar com seção "Core Domain Models":

1. Ler arquivo de models e extrair classes
2. Atualizar tabela em `docs/ai/PROJECT_CONTEXT.md` → Seção "Core Domain Models"

---

## Passo 5: Verificar Dependências

Comparar `backend/requirements.txt` com documentação:

```powershell
Get-Content backend/requirements.txt
```

Se houver novas dependências críticas (ex: novo ORM, novo framework), documentar em `docs/ai/DECISIONS.md`.

---

## Passo 6: Atualizar Páginas Frontend

Listar arquivos HTML na raiz e verificar se estão documentados:

```powershell
Get-ChildItem *.html | Select-Object Name
```

Atualizar tabela "Key Entry Points" em `docs/ai/PROJECT_CONTEXT.md` se necessário.

---

## Passo 7: Verificar Scripts de Deploy/Test

Listar scripts PowerShell e verificar se estão documentados:

```powershell
Get-ChildItem *.ps1 | Select-Object Name
```

Atualizar seção "Commands Reference" se houver novos scripts.

---

## Passo 8: Atualizar Variáveis de Ambiente

Verificar `.env.example` ou `backend/app/config.py` para novas variáveis:

1. Ler `backend/app/config.py` → classe `Settings`
2. Comparar com seção "Environment Variables" em `docs/ai/PROJECT_CONTEXT.md`
3. Adicionar novas variáveis documentadas

---

## Passo 9: Verificar Testes

Listar arquivos de teste e verificar cobertura:

```powershell
Get-ChildItem backend/tests/test_*.py | Select-Object Name
```

Se houver novos módulos sem testes correspondentes, documentar em `docs/ai/DECISIONS.md` como pendência.

---

## Passo 10: Atualizar Data de Última Atualização

Atualizar o header de `docs/ai/PROJECT_CONTEXT.md`:

```markdown
> **Last updated:** [DATA ATUAL]
```

---

## Passo 11: Registrar no Changelog

Adicionar entrada em `docs/ai/CHANGELOG_AI.md`:

```markdown
### YYYY-MM-DD — Context Update

**Agent:** [Nome do agente]  
**Task:** Periodic context synchronization

**Files Updated:**
- `docs/ai/PROJECT_CONTEXT.md` — [descrição das mudanças]
- `.claude/rules/10-repo-map.md` — [se atualizado]
- `docs/ai/DECISIONS.md` — [se novas decisões]

**Verification:**
- [x] Structure matches actual repository
- [x] All new files documented
```

---

## Passo 12: Validar Consistência

Verificar que não há conflitos entre os arquivos de contexto:

1. `AGENTS.md` deve referenciar corretamente `docs/ai/PROJECT_CONTEXT.md`
2. `CLAUDE.md` deve referenciar corretamente `.claude/rules/`
3. `.claude/rules/10-repo-map.md` deve ser consistente com `docs/ai/PROJECT_CONTEXT.md`

---

## Checklist Final

- [ ] Estrutura de diretórios atualizada
- [ ] Lista de routers/endpoints atualizada
- [ ] Lista de models atualizada
- [ ] Dependências críticas documentadas
- [ ] Páginas frontend listadas
- [ ] Scripts de deploy/test documentados
- [ ] Variáveis de ambiente atualizadas
- [ ] Data de última atualização corrigida
- [ ] Changelog atualizado
- [ ] Consistência entre arquivos verificada

---

## Informações Que Devem Ser Atualizadas Periodicamente

| Informação | Arquivo | Frequência |
|------------|---------|------------|
| Estrutura de diretórios | `PROJECT_CONTEXT.md`, `10-repo-map.md` | Semanal |
| Lista de routers | `PROJECT_CONTEXT.md` | Após criar novo router |
| Lista de models | `PROJECT_CONTEXT.md` | Após criar novo model |
| Variáveis de ambiente | `PROJECT_CONTEXT.md` | Após adicionar nova var |
| Decisões arquiteturais | `DECISIONS.md` | Após decisão importante |
| Mudanças feitas por AI | `CHANGELOG_AI.md` | Após cada sessão AI |
| URLs de produção | `PROJECT_CONTEXT.md` | Após mudança de infra |
| Comandos de deploy | `PROJECT_CONTEXT.md`, `AGENTS.md` | Após novo script |

---

*Este workflow garante que Claude Code e OpenAI Codex sempre tenham contexto atualizado para execução precisa.*
