# AI Assistant Foundation

Always-on behavior for the IFRS 16 project:

1. **Protocol First**: Read `docs/ai/PROJECT_CONTEXT.md` and `AGENTS.md` before starting any task.
2. **Active Retrieval**: Use `search_project` and `open` to gather context from 3-10 relevant files before proposing changes.
3. **Transparency**: Always end responses with: "Files read:" followed by exact paths.
4. **Stop Rule**: After 2 failed attempts at fixing something (tests/build failing), STOP and produce a root-cause analysis + new plan.
5. **No Secrets**: Never print secrets from `.env` or other files.
6. **Minimal Diffs**: Prefer small, focused changes.
7. **Verification**: Verify changes with `cd backend && pytest -v`.
