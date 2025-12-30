---
description: Procolo Alteracodigo SOfia incredible
---

# Workflow: Análise de Bug

> **Objetivo:** Diagnosticar bugs de forma sistemática antes de tentar correções.

---

## Passo 1: Recuperação de Contexto

```powershell
Get-Content docs/ai/PROJECT_CONTEXT.md
Get-Content docs/ai/CHANGELOG_AI.md
```

---

## Passo 2: Reproduzir o Bug

1. Identifique os passos para reproduzir
2. Execute e observe o erro exato
3. Capture a mensagem de erro completa

```powershell
# Para erros de backend
cd backend
pytest -v tests/test_[modulo].py -k "[nome_do_teste]"
```

---

## Passo 3: Localizar Origem

1. Trace o stack trace até o arquivo de origem
2. Leia o arquivo completo
3. Identifique a função/método problemático

**Formato:**
```
Bug localizado em:
- Arquivo: backend/app/routers/licenses.py
- Função: create_license()
- Linha: ~45
- Causa provável: [descrição]
```

---

## Passo 4: Analisar Causa Raiz

Antes de corrigir, responda:

1. **O que deveria acontecer?**
2. **O que está acontecendo?**
3. **Por que está diferente?**
4. **Qual é a causa raiz (não o sintoma)?**

---

## Passo 5: Propor Correção

- Descreva a correção proposta
- Liste arquivos que serão modificados
- Explique por que esta correção resolve a causa raiz

---

## Passo 6: Implementar (com Regra das 2 Tentativas)

1. Faça a correção mínima
2. Execute testes

// turbo
```powershell
cd backend
pytest -v
```

**Se falhar 2 vezes:**
- PARE
- Volte ao Passo 4 (Analisar Causa Raiz)
- Documente novas hipóteses
- Só então tente novamente

---

## Passo 7: Verificar Regressão

Certifique-se de que a correção não quebrou outras coisas:

```powershell
cd backend
pytest -v --cov=app
```

---

## Passo 8: Documentar

Atualize `docs/ai/CHANGELOG_AI.md`:

```markdown
### YYYY-MM-DD — Bug Fix: [Título]

**Agent:** Windsurf Cascade  
**Task:** Fix bug in [módulo]

**Bug:** [Descrição do bug]
**Causa raiz:** [Explicação]
**Correção:** [O que foi feito]

**Arquivos modificados:**
- `path/to/file` — [descrição]

**Verificação:**
- [x] Bug reproduzido
- [x] Causa raiz identificada
- [x] Correção implementada
- [x] Testes passam
- [x] Sem regressão
```

---

## Checklist

- [ ] Bug reproduzido
- [ ] Stack trace analisado
- [ ] Causa raiz identificada (não sintoma)
- [ ] Correção proposta antes de implementar
- [ ] Regra das 2 tentativas respeitada
- [ ] Testes passam
- [ ] Changelog atualizado

---

*Este workflow garante análise sistemática antes de correções.*
