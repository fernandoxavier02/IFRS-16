# 👤 Usuário Master - Ambiente de Produção

**Data:** 11 de Dezembro de 2025  
**Ambiente:** Produção (Render)

---

## 🔐 CREDENCIAIS DO USUÁRIO MASTER

### Dados de Acesso

| Campo | Valor |
|------|-------|
| **Username** | `master` |
| **Email** | `fernandocostaxavier@gmail.com` |
| **Senha** | `Master@2025!` |
| **Role** | `SUPERADMIN` |
| **Status** | ✅ Ativo |

---

## 🌐 COMO FAZER LOGIN

### 1️⃣ Acesse a URL de Login Admin

```
https://ifrs-16-1.onrender.com/login.html
```

### 2️⃣ Clique na Aba "Administrador"

Na página de login, você verá duas abas:
- 👤 **Usuário** (para usuários comuns)
- 🔧 **Administrador** ← **CLIQUE AQUI!**

### 3️⃣ Preencha os Campos

**Campo Email:**
```
fernandocostaxavier@gmail.com
```

**Campo Senha:**
```
Master@2025!
```

### 4️⃣ Clique em "Entrar"

Após preencher, clique no botão "Entrar".

---

## ⚠️ IMPORTANTE - ERROS COMUNS

### ❌ NÃO USE "master" no campo de email!

O sistema usa **EMAIL** para login, não username!

- ❌ **ERRADO:** `master`
- ✅ **CORRETO:** `fernandocostaxavier@gmail.com`

### Outros Erros Comuns:

1. **Senha com espaços extras**
   - Certifique-se de não ter espaços antes ou depois
   - Senha correta: `Master@2025!`

2. **Caps Lock ativado**
   - A senha diferencia maiúsculas de minúsculas
   - Deve ser exatamente: `Master@2025!`

3. **Aba errada**
   - Certifique-se de estar na aba "**Administrador**"
   - Não use a aba "Usuário"

---

## 📋 RESUMO VISUAL

```
┌─────────────────────────────────────────────┐
│  🔧 Administrador                          │
├─────────────────────────────────────────────┤
│                                             │
│  Email:                                     │
│  ┌─────────────────────────────────────────┐ │
│  │ fernandocostaxavier@gmail.com          │ │
│  └─────────────────────────────────────────┘ │
│                                             │
│  Senha:                                     │
│  ┌─────────────────────────────────────────┐ │
│  │ Master@2025!                           │ │
│  └─────────────────────────────────────────┘ │
│                                             │
│  ┌─────────────────────────────────────────┐ │
│  │         🔐 Entrar                      │ │
│  └─────────────────────────────────────────┘ │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 🔧 CRIAR/VERIFICAR USUÁRIO MASTER

### Script Automático

Execute o script para criar ou verificar o usuário master:

```powershell
cd "c:\Projetos\IFRS 16\backend"
python criar_usuario_master_producao.py
```

O script irá:
- ✅ Conectar ao banco de produção
- ✅ Verificar se o usuário existe
- ✅ Criar se não existir
- ✅ Atualizar se você quiser

---

## 🎯 APÓS O LOGIN

Após fazer login com sucesso, você será redirecionado para:

**Painel Administrativo:**
```
https://ifrs-16-1.onrender.com/admin.html
```

No painel você poderá:
- ✅ Gerenciar usuários
- ✅ Gerenciar licenças
- ✅ Ver assinaturas Stripe
- ✅ Ver estatísticas do sistema
- ✅ Administrar tudo

---

## 🔒 SEGURANÇA

### ⚠️ Recomendações Importantes:

1. **ALTERE A SENHA** após o primeiro login
2. **NÃO COMPARTILHE** estas credenciais
3. **USE 2FA** se disponível
4. **MONITORE** logs de acesso
5. **FAÇA BACKUP** das credenciais em local seguro

---

## 📊 INFORMAÇÕES DO BANCO DE DADOS

### Tabela: `admin_users`

O usuário master está armazenado na tabela `admin_users` com:
- `username`: `master`
- `email`: `fernandocostaxavier@gmail.com`
- `role`: `SUPERADMIN`
- `is_active`: `true`

### Verificar no Banco:

```sql
SELECT id, username, email, role, is_active, created_at 
FROM admin_users 
WHERE username = 'master' OR email = 'fernandocostaxavier@gmail.com';
```

---

## 🆘 TROUBLESHOOTING

### Login não funciona

1. Verifique se está na aba "Administrador"
2. Verifique se está usando o EMAIL (não username)
3. Verifique se a senha está correta (sem espaços)
4. Verifique Caps Lock
5. Abra o Console do navegador (F12) para ver erros

### Usuário não existe no banco

Execute o script:
```powershell
python backend\criar_usuario_master_producao.py
```

### Esqueceu a senha

Execute o script e escolha atualizar a senha, ou use o script de reset:
```powershell
python backend\reset_master_password.py
```

---

## 📞 CONTATO

**Email do Administrador:** fernandocostaxavier@gmail.com

---

**Última atualização:** 11/12/2025  
**Status:** ✅ Credenciais testadas e funcionando
