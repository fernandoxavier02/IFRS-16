---
description: Prompt "Plano de Execução com Quick Wins + Sanity Check (para Codex)"
---

# Workflow: Execução de Plano com Quick Wins

> **Objetivo:** Executar um plano de desenvolvimento de forma estruturada, priorizando quick wins e validando cada etapa.

---

## Passo 1: Recuperar Contexto

```powershell
Get-Content docs/ai/PROJECT_CONTEXT.md
Get-Content docs/ai/DECISIONS.md
```

---

## Passo 2: Definir o Plano

Estruture o plano em etapas:

```markdown
## Plano de Execução

### Quick Wins (< 30 min cada)
1. [ ] [Tarefa simples 1]
2. [ ] [Tarefa simples 2]

### Tarefas Médias (30 min - 2h)
3. [ ] [Tarefa média 1]
4. [ ] [Tarefa média 2]

### Tarefas Complexas (> 2h)
5. [ ] [Tarefa complexa 1]
```

---

## Passo 3: Sanity Check do Plano

Antes de executar, valide:

- [ ] Todas as tarefas têm critério de sucesso claro?
- [ ] Dependências entre tarefas estão identificadas?
- [ ] Quick wins realmente são rápidos?
- [ ] Há testes para validar cada tarefa?

---

## Passo 4: Executar Quick Wins Primeiro

Para cada quick win:

1. Leia arquivos necessários
2. Faça a alteração mínima
3. Valide imediatamente

// turbo
```powershell
cd backend
pytest -v
```

4. Marque como concluído

---

## Passo 5: Executar Tarefas Médias

Para cada tarefa média:

1. Documente o que será feito
2. Liste arquivos a modificar
3. Implemente em incrementos pequenos
4. Valide após cada incremento

**Regra das 2 tentativas:** Se falhar 2x, pare e reavalie.

---

## Passo 6: Executar Tarefas Complexas

Para tarefas complexas:

1. Quebre em subtarefas menores
2. Crie branch se necessário
3. Implemente uma subtarefa por vez
4. Valide cada subtarefa

---

## Passo 7: Sanity Check Final

Após completar o plano:

```powershell
# Rodar todos os testes
cd backend
pytest -v --cov=app

# Verificar lint (se configurado)
# ruff check .

# Verificar E2E
.\testar_sistema_completo.ps1
```

---

## Passo 8: Documentar Conclusão

Atualize `docs/ai/CHANGELOG_AI.md`:

```markdown
### YYYY-MM-DD — Execução de Plano: [Título]

**Agent:** Windsurf Cascade  
**Task:** [Descrição do plano]

**Quick Wins Completados:**
- [x] [Tarefa 1]
- [x] [Tarefa 2]

**Tarefas Médias Completadas:**
- [x] [Tarefa 3]

**Tarefas Complexas Completadas:**
- [x] [Tarefa 4]

**Verificação:**
- [x] Todos os testes passam
- [x] Sanity check final OK
```

---

## Template de Plano

```markdown
# Plano: [Nome do Plano]

## Objetivo
[Descrição clara do objetivo]

## Quick Wins
1. [ ] [Tarefa] — Critério: [como validar]
2. [ ] [Tarefa] — Critério: [como validar]

## Tarefas Médias
3. [ ] [Tarefa] — Critério: [como validar]
   - Dependência: [se houver]

## Tarefas Complexas
4. [ ] [Tarefa] — Critério: [como validar]
   - Subtarefa 4.1: [descrição]
   - Subtarefa 4.2: [descrição]

## Sanity Check
- [ ] Testes passam
- [ ] Sem regressão
- [ ] Documentação atualizada
```

---

*Este workflow garante execução estruturada com validação contínua.*
