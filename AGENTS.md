# AGENTS.md

> **Purpose:** Entry point for all AI Agents (Codex, AI Assistant, etc.)  
> **For:** OpenAI Codex / IDE extensions

## Critical Protocol

1. **Read Context First:** Read `docs/ai/PROJECT_CONTEXT.md` before any action.
2. **Active Retrieval:** Search the repo and open the 3–10 most relevant files before proposing changes.
3. **Stop Rule:** After 2 failed attempts (tests/lint/build failing), STOP and produce a root-cause analysis.
4. **Cite Sources:** Always end responses with **"Files read:"** followed by exact file paths.
5. **No Guessing:** Factual claims must be grounded in files; cite paths.
6. **Privacy:** NEVER print secrets (tokens, .env). Add sensitive patterns to `.gitignore` or `.aiignore`.
7. **Verify:** Use exact verification commands from `docs/ai/PROJECT_CONTEXT.md` section 4.

## Context Pack → `docs/ai/`

- **[PROJECT_CONTEXT.md](./docs/ai/PROJECT_CONTEXT.md)** — Main project map, commands, architecture, conventions
- **[DECISIONS.md](./docs/ai/DECISIONS.md)** — Architectural decisions log
- **[CHANGELOG_AI.md](./docs/ai/CHANGELOG_AI.md)** — AI changes audit log

## Definition of Done

A task is complete only when:

1. ✅ Verification commands executed and passed:
   - Backend: `cd backend && pytest -v`
   - Frontend/E2E: `.\testar_sistema_completo.ps1` (from project root)
2. ✅ `CHANGELOG_AI.md` updated with the change and verification evidence
3. ✅ Minimal diff preference (small, focused changes)
4. ✅ All file paths cited in "Files read:" section

## Directory Notes

**Monorepo structure:**
- `backend/` — FastAPI Python backend (run commands from here)
- Root — Frontend HTML/JS files, deploy scripts

**Verification per component:**
- Backend changes: `cd backend && pytest -v`
- Frontend changes: Manual browser test or `.\testar_sistema_completo.ps1`
- Full stack: `.\testar_sistema_completo.ps1`

---

*Full details in `docs/ai/PROJECT_CONTEXT.md`*
