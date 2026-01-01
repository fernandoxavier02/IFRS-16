# 00-core.md — Core Rules

## Session Start

1. **Read context first:**
   - `docs/ai/PROJECT_CONTEXT.md` — Full project context
   - `docs/ai/CHANGELOG_AI.md` — Recent AI changes

2. **Active retrieval:**
   - Search the repo and open the 3–10 most relevant files before proposing changes
   - Always end responses with **"Files read:"** followed by exact file paths

3. **List files you will modify** before editing

4. **Select verification command** from `PROJECT_CONTEXT.md` section 4

## Hard Rules

- **Active retrieval** — Always search and read relevant files before proposing changes
- **No guessing** — Cite file paths for all factual claims
- **No secrets** — Never expose `.env*`, keys, tokens, credentials. Treat as sensitive
- **No production edits** without reading context first
- **Stop rule** — After 2 failed fix attempts, STOP and do deeper root-cause analysis before third attempt

## Verification

After changes, run verification:

- **Backend:** `cd backend && pytest -v`
- **Frontend/E2E:** `.\testar_sistema_completo.ps1` (from project root)
- **Deploy:** `firebase deploy --only hosting --project ifrs16-app` (from project root)

## Logging

Update `docs/ai/CHANGELOG_AI.md` after completing changes with:
- Date
- Agent name
- Task description
- Files changed
- Verification evidence

## Stop Rule Details

**After 2 failed attempts:**
1. **STOP** making immediate fixes
2. **Analyze root cause** more deeply (read related files, check dependencies, trace data flow)
3. **Document hypotheses** before new attempt
4. **Only then** propose new fix

---

*Full context: `docs/ai/PROJECT_CONTEXT.md`*
