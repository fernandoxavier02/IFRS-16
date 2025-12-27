# DECISIONS.md

> **Purpose:** Log architectural and implementation decisions for AI agents and developers.  
> **Format:** Each decision includes context, options considered, and rationale.

---

## Decision Log

### DEC-001: Context Pack Structure (2025-12-27)

**Context:** Need a tool-agnostic context system for AI coding assistants (Codex, Claude Code, Windsurf).

**Decision:** Create `docs/ai/` directory with:
- `PROJECT_CONTEXT.md` — High-signal project overview
- `DECISIONS.md` — This file
- `CHANGELOG_AI.md` — AI-made changes log

Plus tool-specific wiring:
- `AGENTS.md` (root) — For OpenAI Codex
- `CLAUDE.md` (root) + `.claude/rules/` — For Claude Code

**Rationale:** 
- Centralized context reduces hallucination
- Tool-specific files follow each tool's conventions
- Version-controlled alongside code

---

### DEC-002: Backend Stack (Historical)

**Context:** Backend API for license management.

**Decision:** FastAPI + SQLAlchemy async + PostgreSQL

**Rationale:**
- FastAPI: Modern, async, auto-docs
- SQLAlchemy async: Non-blocking DB operations
- PostgreSQL: Production-grade, Render free tier

---

### DEC-003: Frontend Hosting (Historical)

**Context:** Static HTML/JS frontend needs hosting.

**Decision:** Firebase Hosting

**Rationale:**
- Free tier sufficient
- Fast CDN
- Easy deployment via CLI

---

### DEC-004: Backend Hosting (Historical)

**Context:** Python backend needs container hosting.

**Decision:** Google Cloud Run

**Rationale:**
- Scales to zero (cost-effective)
- Docker-based
- Same GCP project as Firebase

---

*Add new decisions below this line. Use format: DEC-XXX: Title (YYYY-MM-DD)*

---
