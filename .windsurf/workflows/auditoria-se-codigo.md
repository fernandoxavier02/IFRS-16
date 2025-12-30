---
description: Auditoria de codigos gerais
---

# Workflow: Auditoria de Código

> **Objetivo:** Revisar código existente para identificar problemas de qualidade, segurança e manutenibilidade.

---

## Passo 1: Definir Escopo

Identifique o que será auditado:

- [ ] Módulo específico (ex: `backend/app/routers/`)
- [ ] Arquivo específico
- [ ] Todo o backend
- [ ] Todo o frontend

---

## Passo 2: Ler Contexto

```powershell
Get-Content docs/ai/PROJECT_CONTEXT.md
```

---

## Passo 3: Checklist de Segurança

Para cada arquivo, verificar:

### 3.1 Secrets
- [ ] Nenhum secret hardcoded
- [ ] `.env` não commitado
- [ ] Variáveis sensíveis não logadas

### 3.2 Autenticação
- [ ] JWT validado corretamente
- [ ] Tokens expiram
- [ ] Admin endpoints protegidos

### 3.3 Input Validation
- [ ] Inputs validados com Pydantic
- [ ] SQL injection prevenido (SQLAlchemy)
- [ ] XSS prevenido (escape de HTML)

### 3.4 CORS
- [ ] Origens explícitas (sem wildcard com credentials)

---

## Passo 4: Checklist de Qualidade

### 4.1 Estrutura
- [ ] Imports no topo
- [ ] Funções com responsabilidade única
- [ ] Nomes descritivos

### 4.2 Tratamento de Erros
- [ ] Exceções tratadas adequadamente
- [ ] Mensagens de erro úteis
- [ ] Logging apropriado

### 4.3 Testes
- [ ] Cobertura adequada
- [ ] Testes para casos de borda
- [ ] Fixtures reutilizáveis

---

## Passo 5: Checklist de Performance

- [ ] Queries N+1 evitadas
- [ ] Índices de banco adequados
- [ ] Async usado corretamente
- [ ] Cache onde apropriado

---

## Passo 6: Gerar Relatório

Formato do relatório:

```markdown
# Relatório de Auditoria

**Data:** YYYY-MM-DD
**Escopo:** [descrição]
**Auditor:** Windsurf Cascade

## Resumo

- **Críticos:** X
- **Altos:** X
- **Médios:** X
- **Baixos:** X

## Achados

### [CRÍTICO] Título
- **Arquivo:** path/to/file
- **Linha:** XX
- **Descrição:** [descrição]
- **Recomendação:** [como corrigir]

### [ALTO] Título
...

## Recomendações Gerais

1. [Recomendação]
2. [Recomendação]
```

---

## Passo 7: Priorizar Correções

Ordem de prioridade:
1. **Críticos** — Corrigir imediatamente
2. **Altos** — Corrigir esta sprint
3. **Médios** — Planejar correção
4. **Baixos** — Backlog

---

## Passo 8: Documentar

Se encontrar problemas, adicionar em `docs/ai/DECISIONS.md`:

```markdown
### DEC-XXX: Auditoria de Segurança (YYYY-MM-DD)

**Contexto:** Auditoria identificou [X] problemas

**Decisão:** Priorizar correção de [lista]

**Rationale:** [explicação]
```

---

*Este workflow garante revisão sistemática de código.*
