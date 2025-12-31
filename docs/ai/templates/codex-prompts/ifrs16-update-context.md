# Template Codex: Atualizar Context Pack IFRS 16

**Versão:** 1.0.0  
**Uso:** `/prompts:ifrs16-update-context`

---

## Prompt para Codex

```
Você é um assistente de manutenção do Context Pack do projeto IFRS 16.

TAREFA: Atualizar o Context Pack de forma incremental.

PASSOS:

1. IDENTIFICAR MUDANÇAS
   - Execute: git log --oneline -10
   - Execute: git diff --name-only HEAD~5
   - Liste os arquivos modificados recentemente

2. MAPEAR PARA DOCUMENTAÇÃO
   - backend/app/*.py → docs/ai/30-DATA_BACKEND.md
   - backend/requirements.txt → docs/ai/10-STACK.md
   - *.html, assets/ → docs/ai/40-FRONTEND_APP.md
   - Mudanças de arquitetura → docs/ai/20-ARCHITECTURE.md
   - Novos TODOs/bugs → docs/ai/90-OPEN_QUESTIONS.md

3. ATUALIZAR SOMENTE O NECESSÁRIO
   - Edite apenas as seções afetadas
   - Mantenha o formato existente
   - Não duplique informação

4. VERIFICAR TAMANHOS
   - AGENTS.md e CLAUDE.md devem ter < 60 linhas
   - Se arquivo > 300 linhas, considere dividir

5. REGISTRAR MUDANÇAS
   - Atualize docs/ai/CHANGELOG_AI.md com:
     - Data
     - Arquivos modificados
     - Resumo das mudanças

RESULTADO ESPERADO:
- Lista de arquivos alterados
- Resumo das atualizações
- Novas questões em aberto (se houver)

GUARDRAILS:
- Nunca commitar segredos
- Regra das 2 tentativas: se falhar 2x, pare e analise
- Sempre testar: cd backend && pytest -v
```

---

## Como Instalar no Codex

1. Copie o conteúdo do bloco de prompt acima
2. No Codex, crie um novo prompt com nome `ifrs16-update-context`
3. Cole o conteúdo
4. Use com: `/prompts:ifrs16-update-context`

---

## Variações

### Versão Curta (para atualizações rápidas)

```
Atualize o Context Pack do IFRS 16:
1. git diff --name-only HEAD~5
2. Atualize docs/ai/ conforme mudanças
3. Mantenha AGENTS.md e CLAUDE.md < 60 linhas
4. Atualize CHANGELOG_AI.md
```

### Versão Focada em Backend

```
Atualize docs/ai/30-DATA_BACKEND.md com mudanças recentes em backend/app/.
Verifique models.py, schemas.py, routers/ e atualize seções relevantes.
```

### Versão Focada em Frontend

```
Atualize docs/ai/40-FRONTEND_APP.md com mudanças recentes em *.html e assets/.
Verifique novas páginas, componentes ou mudanças de deploy.
```

---

*Registrado em AGENTS.md como referência para instalação.*
