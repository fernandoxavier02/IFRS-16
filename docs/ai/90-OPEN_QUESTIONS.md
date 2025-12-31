# 90-OPEN_QUESTIONS.md
> **Questões em Aberto & TODOs — IFRS 16**

---

## 🔴 Prioridade Alta

### OQ-001: Migrar autenticação FIREBASE_TOKEN
**Status:** Pendente  
**Contexto:** Firebase CLI avisa que `FIREBASE_TOKEN` será descontinuado  
**Ação:** Migrar para Service Account (`GOOGLE_APPLICATION_CREDENTIALS`)  
**Responsável:** —

---

## 🟡 Prioridade Média

### OQ-002: Implementar refresh token
**Status:** Planejado  
**Contexto:** JWT atual tem expiração fixa sem refresh  
**Ação:** Adicionar endpoint `/auth/refresh` e lógica de refresh token

### OQ-003: Melhorar cobertura de testes
**Status:** Em andamento  
**Contexto:** Cobertura atual ~60%  
**Meta:** Alcançar 80% de cobertura  
**Comando:** `pytest -v --cov=app --cov-report=html`

### OQ-004: Documentar API com exemplos
**Status:** Planejado  
**Contexto:** Swagger gerado automaticamente, mas falta exemplos  
**Ação:** Adicionar `example` nos schemas Pydantic

---

## 🟢 Prioridade Baixa

### OQ-005: Dark mode no frontend
**Status:** Backlog  
**Contexto:** Usuários pediram tema escuro  
**Ação:** Implementar toggle de tema

### OQ-006: Internacionalização (i18n)
**Status:** Backlog  
**Contexto:** Sistema apenas em português  
**Ação:** Adicionar suporte a inglês

### OQ-007: PWA features
**Status:** Backlog  
**Contexto:** App funciona apenas online  
**Ação:** Adicionar service worker e manifest

---

## ✅ Resolvidos Recentemente

### OQ-000: Configurar MCP Firebase (2025-12-30)
**Status:** ✅ Resolvido  
**Solução:** Configurado em `.cursor/mcp.json`, testado e funcionando  
**Relatório:** `RELATORIO_TESTE_MCP_FIREBASE.md`

---

## 📋 Como Adicionar Questões

```markdown
### OQ-XXX: Título
**Status:** Pendente | Planejado | Em andamento | Backlog  
**Contexto:** Descrição do problema  
**Ação:** O que precisa ser feito  
**Responsável:** — (ou nome)
```

---

## 🔄 Última Revisão

**Data:** 2025-12-30  
**Por:** AI Context Pack  
**Próxima revisão:** Quando houver nova mudança significativa

---

*Atualizar este arquivo quando identificar novas questões ou resolver existentes.*
