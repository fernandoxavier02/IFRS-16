# 00-core.md — Core Rules

## Session Start

1. Read `docs/ai/PROJECT_CONTEXT.md` first
2. Read `docs/ai/CHANGELOG_AI.md` for recent changes
3. List files you will modify before editing
4. Select verification command before starting

## Hard Rules

- **No guessing** — Cite file paths for all claims
- **No secrets** — Never expose `.env`, keys, tokens, credentials
- **No production edits** without reading context first
- **Stop rule** — After 2 failed fix attempts, do deeper root cause analysis

## Verification

After changes, run:

- Backend: `cd backend && pytest -v`
- Frontend: `.\testar_sistema_completo.ps1`

## Logging

Update `docs/ai/CHANGELOG_AI.md` after completing changes.
