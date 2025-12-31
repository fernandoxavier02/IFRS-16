# CLAUDE.md

> **For:** Claude Code | **Project:** IFRS 16

## Protocolo de Sessão

1. **Ler:** `docs/ai/00-INDEX.md` → contexto completo
2. **Listar arquivos** antes de editar
3. **Testar:** `cd backend && pytest -v`
4. **Logar:** atualizar `docs/ai/CHANGELOG_AI.md`

## Context Pack → `docs/ai/`

| Arquivo | Conteúdo |
|---------|----------|
| `00-INDEX.md` | Índice e quick start |
| `10-STACK.md` | Stack, comandos, URLs |
| `20-ARCHITECTURE.md` | Diagramas e fluxos |
| `30-DATA_BACKEND.md` | Models, API, schemas |
| `40-FRONTEND_APP.md` | Páginas, deploy |
| `90-OPEN_QUESTIONS.md` | TODOs e questões |

## Guardrails

1. **Nunca commitar segredos**
2. **Regra das 2 tentativas** — Se falhar 2x, pare e analise
3. **Sempre testar** antes de concluir
4. **Atualizar CHANGELOG_AI.md**

## Comandos

```bash
# Backend
cd backend && pytest -v

# Deploy
firebase deploy --only hosting --project ifrs16-app

# E2E
.\testar_sistema_completo.ps1
```

## Stop Rules

- 2 falhas → análise de causa raiz
- Testes falhando → leia o teste primeiro
- Dúvida → leia `docs/ai/`

---

*Ver também: `AGENTS.md`, `docs/ai/00-INDEX.md`*
