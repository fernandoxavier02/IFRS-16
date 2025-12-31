---
description: Atualiza Context Pack IFRS 16 (v2.0) de forma incremental
---

# /atualiza-contexto

Atualização incremental do Context Pack seguindo a norma v2.0.

## 1. Identificar Mudanças

```bash
# Ver commits recentes
git log --oneline -10

# Arquivos modificados
git diff --name-only HEAD~5

# Status atual
git status
```

## 2. Mapear Mudanças → Docs

| Mudança | Atualizar |
|---------|-----------|
| `backend/app/*.py` | `docs/ai/30-DATA_BACKEND.md` |
| `backend/requirements.txt` | `docs/ai/10-STACK.md` |
| `*.html`, `assets/**` | `docs/ai/40-FRONTEND_APP.md` |
| Arquitetura/fluxos | `docs/ai/20-ARCHITECTURE.md` |
| Novos TODOs | `docs/ai/90-OPEN_QUESTIONS.md` |
| Decisões importantes | `docs/ai/DECISIONS.md` |

## 3. Atualizar Apenas Seções Afetadas

**Regras:**
- Edite SOMENTE o necessário
- Mantenha formato existente
- Sem duplicação de conteúdo
- AGENTS.md e CLAUDE.md < 60 linhas

## 4. Verificar Tamanhos

```bash
# Verificar tamanho dos arquivos
Get-ChildItem docs/ai/*.md | Select-Object Name, Length
```

Se arquivo > 12KB (~300 linhas):
- Considere dividir em sub-arquivos
- Ex: `30-DATA_BACKEND.md` → `31-MODELS.md`, `32-API.md`

## 5. Atualizar Índice

Atualize `docs/ai/00-INDEX.md` se:
- Novos arquivos criados
- Estrutura modificada
- Novos comandos disponíveis

## 6. Registrar no CHANGELOG

Adicione em `docs/ai/CHANGELOG_AI.md`:

```markdown
### YYYY-MM-DD — Context Update

**Agent:** Windsurf Cascade
**Task:** Atualização incremental do Context Pack

**Arquivos modificados:**
- `docs/ai/XX-NOME.md` — [descrição]

**Mudanças:**
- [resumo das alterações]

**Verificação:**
- [x] Sem duplicação
- [x] Arquivos < 12KB
- [ ] Testes não afetados
```

## 7. Validar Consistência

Verificar:
- [ ] `AGENTS.md` aponta para `docs/ai/`
- [ ] `CLAUDE.md` aponta para `docs/ai/`
- [ ] `.windsurf/rules/00-always-on.md` referencia correto
- [ ] Sem informação duplicada entre arquivos

## 8. Resultado

Informar:
1. **Arquivos modificados** (lista)
2. **Resumo das mudanças** (bullet points)
3. **Novas questões** em `90-OPEN_QUESTIONS.md` (se houver)

---

## Guardrails

1. **Nunca commitar segredos**
2. **Regra das 2 tentativas** — Se falhar 2x, pare
3. **Sempre testar** — `cd backend && pytest -v` (se código mudou)
4. **Manter enxuto** — Arquivos < 12KB

---

## Exemplo de Execução

```
1. git diff --name-only HEAD~5
   → backend/app/models.py
   → backend/requirements.txt

2. Atualizar:
   → docs/ai/30-DATA_BACKEND.md (seção Models)
   → docs/ai/10-STACK.md (seção Dependências)

3. Registrar em CHANGELOG_AI.md

4. Resultado:
   ✅ 2 arquivos atualizados
   ✅ Sem duplicação
   ✅ Tamanhos OK
```
