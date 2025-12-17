# 👥 Como Ver os Usuários do Sistema

**Data:** 17 de Janeiro de 2025

---

## 📌 IMPORTANTE

Os usuários **NÃO estão no Firebase**. Eles estão armazenados no **banco de dados PostgreSQL (Cloud SQL)**.

O Firebase é usado apenas para **hosting** do frontend, não para autenticação.

---

## 🔍 OPÇÕES PARA VER OS USUÁRIOS

### 1. Via API do Backend (Recomendado)

Use o endpoint administrativo para listar usuários:

**Endpoint:**
```
GET https://ifrs16-backend-ox4zylcs5a-uc.a.run.app/api/admin/users
```

**Autenticação:**
Você precisa estar logado como administrador. Use o token JWT no header:

```
Authorization: Bearer <seu_token_admin>
```

**Parâmetros opcionais:**
- `skip`: Número de registros a pular (paginação)
- `limit`: Máximo de registros (padrão: 100, máximo: 1000)
- `is_active`: Filtrar por status (true/false)

**Exemplo completo:**
```bash
# 1. Fazer login como admin
curl -X POST https://ifrs16-backend-ox4zylcs5a-uc.a.run.app/api/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "fernandocostaxavier@gmail.com",
    "password": "Master@2025!"
  }'

# 2. Usar o token retornado para listar usuários
curl -X GET "https://ifrs16-backend-ox4zylcs5a-uc.a.run.app/api/admin/users?limit=100" \
  -H "Authorization: Bearer <token_aqui>"
```

---

### 2. Via Console do Google Cloud SQL

Acesse diretamente o banco de dados:

**Passo a passo:**

1. Acesse o Console do Google Cloud:
   ```
   https://console.cloud.google.com/sql/instances?project=ifrs16-app
   ```

2. Clique na instância: `ifrs16-database`

3. Vá na aba **"Databases"** e selecione `ifrs16_licenses`

4. Clique em **"Connect using Cloud Shell"** ou use o cliente PostgreSQL

5. Execute a query:
   ```sql
   -- Ver todos os usuários clientes
   SELECT 
       id, 
       email, 
       name, 
       is_active, 
       email_verified, 
       created_at, 
       last_login 
   FROM users 
   ORDER BY created_at DESC;
   
   -- Ver administradores
   SELECT 
       id, 
       username, 
       email, 
       role, 
       is_active, 
       created_at, 
       last_login 
   FROM admin_users 
   ORDER BY created_at DESC;
   ```

---

### 3. Via Painel Admin do Sistema (Frontend)

Se houver uma página admin no frontend:

1. Acesse: https://ifrs16-app.web.app/admin.html
2. Faça login como administrador
3. Procure pela seção de gerenciamento de usuários

---

### 4. Via gcloud CLI (Terminal)

```powershell
# Conectar ao banco via Cloud SQL Proxy ou direto
$gcloudPath = "$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"

# Conectar ao banco
& $gcloudPath sql connect ifrs16-database \
  --user=ifrs16_user \
  --database=ifrs16_licenses \
  --project=ifrs16-app

# Depois de conectado, execute as queries SQL acima
```

---

## 📊 ESTRUTURA DAS TABELAS

### Tabela `users` (Clientes)
- `id`: UUID único
- `email`: Email do usuário (único)
- `name`: Nome completo
- `password_hash`: Hash da senha (bcrypt)
- `stripe_customer_id`: ID do cliente no Stripe
- `is_active`: Se o usuário está ativo
- `email_verified`: Se o email foi verificado
- `created_at`: Data de criação
- `last_login`: Último login

### Tabela `admin_users` (Administradores)
- `id`: UUID único
- `username`: Nome de usuário (único)
- `email`: Email (único)
- `password_hash`: Hash da senha (bcrypt)
- `role`: Role (SUPERADMIN, ADMIN)
- `is_active`: Se está ativo
- `created_at`: Data de criação
- `last_login`: Último login

---

## 🔐 CREDENCIAIS DE ACESSO

### Admin Master
- **Email:** `fernandocostaxavier@gmail.com`
- **Senha:** `Master@2025!`
- **Role:** `SUPERADMIN`

---

## ✅ RECOMENDAÇÃO

Para visualização rápida, use a **API do backend** (opção 1). É a forma mais fácil e não requer acesso direto ao banco.

Para análise mais detalhada ou grandes volumes, use o **Console do Google Cloud SQL** (opção 2).
