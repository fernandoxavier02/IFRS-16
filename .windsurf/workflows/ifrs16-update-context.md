---
description: Atualiza o Context Pack do IFRS 16 de forma incremental
---

# Workflow: Atualizar Context Pack IFRS 16

## 1. Identificar mudanças recentes

```bash
# Ver commits recentes
git log --oneline -10

# Ver arquivos modificados
git diff --name-only HEAD~5
```

## 2. Analisar impacto das mudanças

Para cada arquivo modificado, identificar qual doc precisa atualizar:

| Tipo de mudança | Doc a atualizar |
|-----------------|-----------------|
| `backend/app/*.py` | `docs/ai/30-DATA_BACKEND.md` |
| `backend/requirements.txt` | `docs/ai/10-STACK.md` |
| `*.html`, `assets/` | `docs/ai/40-FRONTEND_APP.md` |
| Arquitetura/fluxos | `docs/ai/20-ARCHITECTURE.md` |
| Novos TODOs/bugs | `docs/ai/90-OPEN_QUESTIONS.md` |

## 3. Atualizar apenas seções afetadas

- Edite SOMENTE as seções relevantes
- Mantenha formato existente
- Não duplique informação

## 4. Verificar tamanho dos arquivos

Se algum arquivo ultrapassar 300 linhas:
- Considere dividir em sub-arquivos
- Exemplo: `30-DATA_BACKEND.md` -> `31-MODELS.md`, `32-API.md`

## 5. Manter AGENTS.md e CLAUDE.md curtos

- Esses arquivos devem ter < 60 linhas
- Apenas ponteiros para `docs/ai/`
- Sem duplicação de conteúdo

## 6. Atualizar CHANGELOG_AI.md

Adicione entrada com:
- Data
- Arquivos modificados
- Resumo das mudanças

## 7. Resultado esperado

Ao final, liste:
- Arquivos alterados em `docs/ai/`
- Resumo das atualizações
- Novas questões em `90-OPEN_QUESTIONS.md` (se houver)
