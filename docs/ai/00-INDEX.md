# 00-INDEX.md
> **IFRS 16 License Management System — Context Pack**  
> **Versão:** 2.0.0 | **Atualizado:** 2025-12-30

---

## 📁 Estrutura do Context Pack

| Arquivo | Conteúdo |
|---------|----------|
| `00-INDEX.md` | Este índice |
| `10-STACK.md` | Stack tecnológica e dependências |
| `20-ARCHITECTURE.md` | Arquitetura, diagramas, fluxos |
| `30-DATA_BACKEND.md` | Models, schemas, API, database |
| `40-FRONTEND_APP.md` | Páginas, assets, deploy |
| `90-OPEN_QUESTIONS.md` | Questões em aberto, TODOs |
| `CHANGELOG_AI.md` | Log de mudanças feitas por AI |
| `DECISIONS.md` | Log de decisões arquiteturais |
| `PROJECT_CONTEXT.md` | Contexto completo (legacy, será modularizado) |

---

## 🚀 Quick Start para AI Agents

```bash
# 1. Leia o contexto
docs/ai/00-INDEX.md      # Este arquivo
docs/ai/10-STACK.md      # Stack e comandos
docs/ai/20-ARCHITECTURE.md # Arquitetura

# 2. Antes de editar
- Liste arquivos que vai modificar
- Leia os arquivos antes de editar

# 3. Após editar
cd backend && pytest -v   # Teste backend
# OU
.\testar_sistema_completo.ps1  # Teste E2E

# 4. Documente
docs/ai/CHANGELOG_AI.md  # Registre mudanças
```

---

## 🔗 Arquivos de Wiring (Raiz)

| Arquivo | Ferramenta | Propósito |
|---------|------------|-----------|
| `AGENTS.md` | OpenAI Codex | Instruções + ponteiro para docs/ai |
| `CLAUDE.md` | Claude Code | Instruções + ponteiro para docs/ai |
| `.windsurf/rules/` | Windsurf | Regras always-on |
| `.windsurf/workflows/` | Windsurf | Comandos slash |
| `.claude/commands/` | Claude Code | Comandos slash |

---

## ⚠️ Guardrails

1. **Nunca commitar segredos** — `.env` está no `.gitignore`
2. **Regra das 2 tentativas** — Se falhar 2x, pare e analise causa raiz
3. **Sempre testar** — `pytest -v` antes de considerar tarefa concluída
4. **Atualizações incrementais** — Edite só o necessário
5. **Sem duplicação** — Use ponteiros, não copie conteúdo

---

*Mantenedor: AI Context Pack | Última revisão: 2025-12-30*
