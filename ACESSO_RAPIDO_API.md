# 🚀 Acesso Rápido à API

## 📍 Links Importantes

### Documentação Interativa (Swagger)
**https://ifrs16-backend-ox4zylcs5a-uc.a.run.app/docs**

Aqui você pode:
- ✅ Fazer login como admin
- ✅ Testar todos os endpoints
- ✅ Ver e listar usuários
- ✅ Gerenciar licenças

### Como usar:

1. **Acesse a documentação:** https://ifrs16-backend-ox4zylcs5a-uc.a.run.app/docs

2. **Faça login como admin:**
   - Procure o endpoint: `POST /api/auth/admin/login`
   - Clique em "Try it out"
   - Preencha:
     ```json
     {
       "email": "fernandocostaxavier@gmail.com",
       "password": "Master@2025!"
     }
     ```
   - Clique em "Execute"
   - Copie o `access_token` retornado

3. **Autenticar na API:**
   - Clique no botão "Authorize" no topo da página
   - Cole o token no campo "Value"
   - Clique em "Authorize"

4. **Listar usuários:**
   - Procure o endpoint: `GET /api/admin/users`
   - Clique em "Try it out"
   - Clique em "Execute"
   - Veja a lista de usuários retornada!

---

## 🔗 Outros Links Úteis

- **API Base:** https://ifrs16-backend-ox4zylcs5a-uc.a.run.app
- **ReDoc (documentação alternativa):** https://ifrs16-backend-ox4zylcs5a-uc.a.run.app/redoc
- **OpenAPI JSON:** https://ifrs16-backend-ox4zylcs5a-uc.a.run.app/openapi.json

---

## 📝 Endpoints Principais para Usuários

### Autenticação
- `POST /api/auth/admin/login` - Login como admin
- `POST /api/auth/login` - Login como usuário

### Gerenciamento de Usuários
- `GET /api/admin/users` - Listar todos os usuários
- `GET /api/admin/users/{user_id}` - Detalhes de um usuário
- `PUT /api/admin/users/{user_id}` - Atualizar usuário
- `DELETE /api/admin/users/{user_id}` - Excluir usuário

### Gerenciamento de Licenças
- `GET /api/admin/licenses` - Listar todas as licenças
- `POST /api/admin/generate-license` - Criar nova licença
