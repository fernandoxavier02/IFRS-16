# 👥 Como Ver os Usuários - Passo a Passo Simples

**Data:** 17 de Janeiro de 2025

---

## ⚠️ IMPORTANTE

Os usuários **NÃO estão no Firebase**. 

Os usuários estão no **banco de dados PostgreSQL** que está no Google Cloud.

---

## 🎯 FORMA MAIS FÁCIL: Via Navegador (Swagger)

### Passo 1: Abrir a Documentação da API

1. Abra seu navegador (Chrome, Edge, etc)
2. Digite ou cole esta URL:
   ```
   https://ifrs16-backend-ox4zylcs5a-uc.a.run.app/docs
   ```
3. Pressione ENTER

Você verá uma página com vários endpoints da API listados.

---

### Passo 2: Fazer Login como Administrador

1. Na página que abriu, procure por: **`POST /api/auth/admin/login`**
2. Clique nele para expandir
3. Você verá um botão **"Try it out"** - clique nele
4. No campo que aparecer, você verá um exemplo JSON. Substitua por:
   ```json
   {
     "email": "fernandocostaxavier@gmail.com",
     "password": "Master@2025!"
   }
   ```
5. Role a página para baixo e clique no botão azul **"Execute"**
6. Você verá uma resposta. Procure por `"access_token"` e **COPIE O VALOR** (é um texto longo)

**Exemplo do que você verá:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  ...
}
```
Copie **todo o texto** do `access_token` (tudo entre as aspas).

---

### Passo 3: Autorizar o Acesso

1. No **topo da página**, procure por um **botão verde escrito "Authorize"** ou um **ícone de cadeado 🔒**
2. Clique nele
3. Uma janelinha vai abrir
4. No campo "Value", **cole o token que você copiou** no Passo 2
5. Clique no botão **"Authorize"**
6. Feche a janelinha

Agora você está autenticado!

---

### Passo 4: Ver os Usuários

1. Na página, procure por: **`GET /api/admin/users`**
2. Clique nele para expandir
3. Clique no botão **"Try it out"**
4. Você pode deixar os campos como estão, ou alterar:
   - `limit`: máximo de usuários (ex: 100)
   - `skip`: quantos pular (deixe 0 para ver do início)
   - `is_active`: deixe vazio para ver todos
5. Role para baixo e clique no botão azul **"Execute"**
6. Você verá uma resposta com a lista de usuários!

**Exemplo do que você verá:**
```json
{
  "total": 5,
  "users": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "usuario@exemplo.com",
      "name": "Nome do Usuário",
      "is_active": true,
      "created_at": "2025-01-15T10:30:00"
    },
    ...
  ]
}
```

---

## 📋 RESUMO RÁPIDO

1. ✅ Abrir: https://ifrs16-backend-ox4zylcs5a-uc.a.run.app/docs
2. ✅ Fazer login: `POST /api/auth/admin/login` (copiar o token)
3. ✅ Autorizar: Clicar no botão "Authorize" e colar o token
4. ✅ Ver usuários: `GET /api/admin/users` → "Execute"

---

## 🖼️ O QUE VOCÊ VAI VER

A página Swagger tem esta aparência:

```
┌─────────────────────────────────────────┐
│  [Authorize] 🔒                         │  ← Botão no topo
├─────────────────────────────────────────┤
│                                         │
│  POST /api/auth/admin/login             │  ← Clique aqui primeiro
│  GET  /api/admin/users                  │  ← Depois clique aqui
│  GET  /api/admin/licenses               │
│  ...                                    │
│                                         │
└─────────────────────────────────────────┘
```

---

## ❓ PROBLEMAS COMUNS

### "Não consigo ver o botão Try it out"
- Você precisa estar logado primeiro no sistema (mas não é necessário para ver a documentação)
- Se não aparecer, tente recarregar a página

### "Dá erro ao executar"
- Certifique-se de ter feito o login primeiro (Passo 2)
- Certifique-se de ter autorizado com o token (Passo 3)
- Verifique se copiou o token completo (é um texto muito longo)

### "Não aparece nenhum usuário"
- Pode ser que realmente não existam usuários cadastrados ainda
- Tente aumentar o `limit` para 1000

---

## 🔄 ALTERNATIVA: Via Console Google Cloud

Se preferir ver direto no banco de dados:

1. Acesse: https://console.cloud.google.com/sql/instances?project=ifrs16-app
2. Clique na instância `ifrs16-database`
3. Clique em "Connect using Cloud Shell"
4. Execute:
   ```sql
   SELECT email, name, created_at FROM users ORDER BY created_at DESC;
   ```

---

## 💡 DICA

Depois de fazer login uma vez, você pode usar o mesmo token para várias consultas. 
Só precisa fazer login novamente quando o token expirar (após 24 horas).
