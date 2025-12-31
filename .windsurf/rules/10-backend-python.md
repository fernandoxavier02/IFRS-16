---
trigger: glob
globs: ["backend/**/*.py"]
---

# Backend Python Rules

## Antes de Editar
1. Leia docs/ai/30-DATA_BACKEND.md
2. Liste arquivos que vai modificar

## Após Editar
1. Execute: cd backend && pytest -v
2. Atualize docs/ai/CHANGELOG_AI.md

## Padrões
- Use async/await para operações de DB
- Imports no topo do arquivo
- Siga o estilo existente
