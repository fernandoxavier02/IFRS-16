# Comando: Atualizar Context Pack IFRS 16

Executa atualização incremental do Context Pack.

## Passos

### 1. Identificar mudanças
```bash
git log --oneline -10
git diff --name-only HEAD~5
```

### 2. Mapear para docs

| Mudança | Atualizar |
|---------|-----------|
| `backend/app/*.py` | `docs/ai/30-DATA_BACKEND.md` |
| `backend/requirements.txt` | `docs/ai/10-STACK.md` |
| `*.html`, `assets/` | `docs/ai/40-FRONTEND_APP.md` |
| Arquitetura | `docs/ai/20-ARCHITECTURE.md` |
| TODOs/bugs | `docs/ai/90-OPEN_QUESTIONS.md` |

### 3. Regras de atualização

- Editar SOMENTE seções afetadas
- Manter formato existente
- AGENTS.md e CLAUDE.md < 60 linhas
- Se arquivo > 300 linhas, dividir

### 4. Finalizar

- Atualizar `docs/ai/CHANGELOG_AI.md`
- Listar arquivos alterados
- Registrar novas questões em `90-OPEN_QUESTIONS.md`

## Resultado

Informar:
1. Arquivos modificados
2. Resumo das mudanças
3. Questões em aberto (se houver)
