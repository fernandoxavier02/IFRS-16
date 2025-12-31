---
trigger: glob
globs: ["*.html", "assets/**"]
---

# Frontend Rules

## Antes de Editar
1. Leia docs/ai/40-FRONTEND_APP.md
2. Liste arquivos que vai modificar

## Após Editar
1. Teste no browser: https://ifrs16-app.web.app
2. Deploy: irebase deploy --only hosting --project ifrs16-app

## Padrões
- API URL: variável configurável (não hardcode)
- Tokens em localStorage
- Mobile-first CSS
