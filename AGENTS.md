# AGENTS.md

> **For:** OpenAI Codex | **Project:** IFRS 16

## Quick Start

```bash
# 1. Leia o contexto
cat docs/ai/00-INDEX.md

# 2. Antes de editar: liste arquivos

# 3. Após editar: teste
cd backend && pytest -v
```

## Context Pack → `docs/ai/`

| Arquivo | Conteúdo |
|---------|----------|
| `00-INDEX.md` | Índice e quick start |
| `10-STACK.md` | Stack, comandos, URLs |
| `20-ARCHITECTURE.md` | Diagramas e fluxos |
| `30-DATA_BACKEND.md` | Models, API, schemas |
| `40-FRONTEND_APP.md` | Páginas, deploy |
| `90-OPEN_QUESTIONS.md` | TODOs e questões |
| `CHANGELOG_AI.md` | Log de mudanças AI |

## Guardrails

1. **Nunca commitar segredos**
2. **Regra das 2 tentativas** — Se falhar 2x, pare e analise
3. **Sempre testar** — `pytest -v` antes de concluir
4. **Atualizar CHANGELOG_AI.md** após mudanças

## Comandos Essenciais

| Ação | Comando |
|------|---------|
| Testes backend | `cd backend && pytest -v` |
| Deploy frontend | `firebase deploy --only hosting --project ifrs16-app` |
| E2E tests | `.\testar_sistema_completo.ps1` |

## Stop Rules

- Após 2 falhas → análise de causa raiz
- Testes falhando → leia o arquivo de teste primeiro
- Dúvida de arquitetura → leia `docs/ai/20-ARCHITECTURE.md`

---

*Detalhes completos em `docs/ai/`*
