---
description: Scritp geral
---

# Workflow: Otimização Extensiva e Completa

> **Objetivo:** Realizar otimização abrangente de código, performance e arquitetura.

---

## Fase 1: Diagnóstico Completo

### 1.1 Mapear Estado Atual

```powershell
# Estrutura do projeto
Get-ChildItem -Recurse -Directory | Select-Object FullName

# Tamanho dos arquivos principais
Get-ChildItem backend/app/*.py | Select-Object Name, Length

# Cobertura de testes atual
cd backend
pytest -v --cov=app --cov-report=term-missing
```

### 1.2 Identificar Gargalos

- [ ] Arquivos muito grandes (> 500 linhas)
- [ ] Funções muito longas (> 50 linhas)
- [ ] Duplicação de código
- [ ] Queries N+1
- [ ] Imports não utilizados

---

## Fase 2: Otimização de Performance

### 2.1 Backend

```python
# Verificar queries lentas
# Adicionar logging de tempo em endpoints críticos

# Exemplo de otimização de query
# Antes: for item in items: db.query(Related).filter_by(item_id=item.id)
# Depois: db.query(Related).filter(Related.item_id.in_([i.id for i in items]))
```

### 2.2 Database

- [ ] Índices em colunas frequentemente filtradas
- [ ] Eager loading onde apropriado
- [ ] Connection pooling configurado

### 2.3 Frontend

- [ ] Minificação de JS/CSS
- [ ] Lazy loading de imagens
- [ ] Cache headers configurados

---

## Fase 3: Refatoração de Código

### 3.1 Princípios

- **Single Responsibility:** Uma função, uma responsabilidade
- **DRY:** Extrair código duplicado
- **KISS:** Simplificar lógica complexa

### 3.2 Checklist de Refatoração

Para cada módulo:

- [ ] Funções < 50 linhas
- [ ] Arquivos < 500 linhas
- [ ] Nomes descritivos
- [ ] Comentários úteis (não óbvios)
- [ ] Type hints completos

---

## Fase 4: Otimização de Testes

### 4.1 Cobertura

```powershell
cd backend
pytest -v --cov=app --cov-report=html
# Abrir htmlcov/index.html para ver cobertura
```

### 4.2 Velocidade

- [ ] Fixtures reutilizáveis
- [ ] Mocks para serviços externos
- [ ] Paralelização de testes

---

## Fase 5: Documentação

### 5.1 Código

- [ ] Docstrings em funções públicas
- [ ] Type hints completos
- [ ] README atualizado

### 5.2 API

- [ ] OpenAPI/Swagger atualizado
- [ ] Exemplos de request/response

---

## Fase 6: Validação

### 6.1 Testes

// turbo
```powershell
cd backend
pytest -v --cov=app
```

### 6.2 Lint

```powershell
# Se ruff estiver configurado
cd backend
ruff check .
```

### 6.3 E2E

```powershell
.\testar_sistema_completo.ps1
```

---

## Fase 7: Documentar Otimizações

Atualize `docs/ai/DECISIONS.md`:

```markdown
### DEC-XXX: Otimização de [Área] (YYYY-MM-DD)

**Contexto:** [Por que otimizar]

**Decisão:** [O que foi feito]

**Métricas:**
- Antes: [métrica]
- Depois: [métrica]

**Trade-offs:** [Se houver]
```

---

## Checklist Final

- [ ] Performance medida antes/depois
- [ ] Testes passam
- [ ] Cobertura mantida ou aumentada
- [ ] Documentação atualizada
- [ ] Changelog atualizado
- [ ] Nenhuma regressão

---

## Métricas a Acompanhar

| Métrica | Antes | Depois |
|---------|-------|--------|
| Tempo de resposta médio | | |
| Cobertura de testes | | |
| Linhas de código | | |
| Complexidade ciclomática | | |

---

*Este workflow garante otimização sistemática e mensurável.*
