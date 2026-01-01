# CLAUDE.md

> **For:** Claude Code | **Project:** IFRS 16

## Session Protocol

1. **Read first:** `docs/ai/PROJECT_CONTEXT.md` + latest `docs/ai/CHANGELOG_AI.md`
2. **List files** you will modify before editing
3. **Active Retrieval:** Search repo and open 3–10 most relevant files
4. **Verify:** Run verification commands after changes
5. **Log changes:** Update `docs/ai/CHANGELOG_AI.md`

## Context Pack → `docs/ai/`

| File | Content |
|------|---------|
| `PROJECT_CONTEXT.md` | Main project map, commands, architecture, conventions |
| `DECISIONS.md` | Architectural decisions log |
| `CHANGELOG_AI.md` | AI changes audit log |

## Guardrails

1. **Never commit secrets** — Treat `.env*`, keys, tokens, credentials as sensitive
2. **Stop rule (2 attempts)** — After 2 failed fix attempts, STOP and do root-cause analysis
3. **Always verify** — Use exact commands from `PROJECT_CONTEXT.md` section 4
4. **Update CHANGELOG_AI.md** — Log all changes with verification evidence

## Verification Commands

```bash
# Backend
cd backend && pytest -v

# Frontend/E2E (from project root)
.\testar_sistema_completo.ps1

# Deploy (from project root)
firebase deploy --only hosting --project ifrs16-app
```

## Stop Rules

- **2 failed attempts** → Root-cause analysis required before third attempt
- **Tests failing** → Read test file first, understand failure
- **Uncertainty** → Read `docs/ai/PROJECT_CONTEXT.md` for context

## When New Constraints/Decisions Appear

If a new architectural constraint or decision is made:
- Update `docs/ai/DECISIONS.md` with date, decision, rationale, trade-offs, risks
- Reference the decision in code comments if relevant

---

*See also: `AGENTS.md`, `.claude/rules/`, `docs/ai/PROJECT_CONTEXT.md`*
