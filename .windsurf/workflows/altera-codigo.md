---
description: Ateração segura de código
---

# Workflow: Alteração Segura de Código

> **Objetivo:** Garantir que alterações de código sigam o protocolo de recuperação ativa de contexto e regra das 2 tentativas.

---

## Passo 1: Recuperação Ativa de Contexto

Antes de qualquer alteração, leia os arquivos de contexto:

```powershell
# Ler contexto do projeto
Get-Content docs/ai/PROJECT_CONTEXT.md
Get-Content docs/ai/CHANGELOG_AI.md
```

---

## Passo 2: Identificar Arquivos Relevantes

Liste os arquivos que serão modificados:

1. Identifique o módulo/camada afetada (backend/frontend)
2. Liste todos os arquivos que precisam ser lidos
3. Liste todos os arquivos que serão modificados

**Formato obrigatório:**
```
Arquivos lidos:
- backend/app/models.py
- backend/app/routers/licenses.py

Arquivos a modificar:
- backend/app/routers/licenses.py
```

---

## Passo 3: Ler Arquivos Antes de Editar

Sempre leia o arquivo completo antes de editar:

```powershell
# Exemplo para backend
Get-Content backend/app/routers/licenses.py
```

---

## Passo 4: Fazer Alteração Mínima

- Prefira edits pequenos e focados
- Preserve estilo existente (indentação, naming)
- Imports sempre no topo do arquivo
- Não altere comentários sem necessidade

---

## Passo 5: Verificar Alteração

// turbo
```powershell
cd backend
pytest -v
```

Se os testes falharem, vá para o Passo 6.

---

## Passo 6: Regra das 2 Tentativas

**IMPORTANTE:** Se a correção falhar 2 vezes consecutivas:

1. **PARE** - Não tente uma terceira correção imediata
2. **Analise causa raiz** mais profundamente:
   - Leia arquivos relacionados
   - Verifique dependências
   - Trace o fluxo de dados
3. **Documente hipóteses** antes de nova tentativa
4. **Só então** proponha nova correção

---

## Passo 7: Atualizar Changelog

Após sucesso, atualize o changelog:

```markdown
### YYYY-MM-DD — [Título da mudança]

**Agent:** Windsurf Cascade  
**Task:** [Descrição da tarefa]

**Arquivos lidos:**
- [lista de arquivos lidos]

**Arquivos modificados:**
- `path/to/file` — [descrição da mudança]

**Verificação:**
- [x] Tests pass: `pytest -v`
```

---

## Checklist Final

- [ ] Contexto lido (PROJECT_CONTEXT.md)
- [ ] Arquivos listados antes de editar
- [ ] Alteração mínima e focada
- [ ] Testes passam
- [ ] Changelog atualizado
- [ ] Nenhum segredo exposto

---

*Este workflow implementa o protocolo de recuperação ativa de contexto e regra das 2 tentativas.*
