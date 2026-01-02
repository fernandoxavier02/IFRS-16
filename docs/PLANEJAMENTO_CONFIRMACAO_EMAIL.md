# 📋 PLANEJAMENTO: CONFIRMAÇÃO DE EMAIL NO CADASTRO

> **Data:** 2026-01-02 21:50  
> **Status:** 📝 **PLANEJAMENTO**

---

## 🎯 OBJETIVOS

1. ✅ Mostrar mensagem de sucesso após cadastro no frontend
2. ✅ Implementar validação de email via token de confirmação
3. ✅ Bloquear login até email ser confirmado
4. ✅ Permitir reenvio de email de confirmação

---

## 🔄 FLUXO ATUAL vs FLUXO NOVO

### Fluxo Atual:

```
1. Usuário preenche formulário de cadastro
2. Backend cria usuário (email_verified = False)
3. Backend envia email de "boas-vindas"
4. Usuário é redirecionado para login
5. ❌ Usuário pode fazer login mesmo sem confirmar email
```

### Fluxo Novo:

```
1. Usuário preenche formulário de cadastro
2. Backend cria usuário (email_verified = False)
3. Backend gera token de confirmação
4. Backend envia email com link de confirmação
5. ✅ Frontend mostra modal de sucesso: "Cadastro criado! Verifique seu email"
6. Usuário clica no link do email
7. Frontend chama endpoint de confirmação
8. Backend valida token e marca email_verified = True
9. ✅ Frontend mostra mensagem de sucesso
10. Usuário pode fazer login
11. ❌ Se tentar login sem confirmar: "Por favor, confirme seu email"
```

---

## 📦 COMPONENTES A IMPLEMENTAR

### 1. Backend

#### 1.1. Modelo de Token de Confirmação

**Tabela:** `email_verification_tokens`

```sql
CREATE TABLE email_verification_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_token (token),
    INDEX idx_user_id (user_id)
);
```

#### 1.2. Endpoints

**a) POST /api/auth/register** (MODIFICAR)
- Gerar token de confirmação
- Enviar email com link de confirmação
- Retornar sucesso

**b) POST /api/auth/verify-email** (NOVO)
- Receber token
- Validar token (existe, não expirou, não foi usado)
- Marcar email_verified = True
- Marcar token como usado
- Retornar sucesso

**c) POST /api/auth/resend-verification** (NOVO)
- Receber email
- Verificar se usuário existe e não está verificado
- Gerar novo token
- Enviar novo email
- Retornar sucesso

**d) POST /api/auth/login** (MODIFICAR)
- Verificar email_verified = True
- Se False, retornar erro 403: "Email não confirmado"

#### 1.3. Email Service

**Template de Email:**
- Assunto: "Confirme seu email - Engine IFRS 16"
- Conteúdo:
  - Boas-vindas
  - Botão "Confirmar Email"
  - Link: `https://fxstudioai.com/verify-email?token=XXX`
  - Validade: 24 horas
  - Instruções se não solicitou

---

### 2. Frontend

#### 2.1. Modal de Sucesso no Cadastro

**Arquivo:** `login.html` ou `register.html`

**Componente:**
```html
<div class="modal-overlay" id="successModal">
    <div class="modal-content">
        <div class="modal-icon success">✓</div>
        <h2>Cadastro Criado com Sucesso!</h2>
        <p>Enviamos um email de confirmação para:</p>
        <p class="email-highlight">usuario@email.com</p>
        <p>Por favor, verifique sua caixa de entrada e clique no link de confirmação.</p>
        <button class="btn-primary" onclick="closeSuccessModal()">Entendi</button>
        <p class="resend-link">
            Não recebeu? <a href="#" onclick="resendVerification()">Reenviar email</a>
        </p>
    </div>
</div>
```

**Estilo:** Seguir padrão dos modais existentes (modal de recuperação de senha)

#### 2.2. Página de Confirmação

**Arquivo:** `verify-email.html` (NOVO)

**Funcionalidade:**
- Receber token da URL (`?token=XXX`)
- Chamar endpoint `/api/auth/verify-email`
- Mostrar:
  - ✅ Sucesso: "Email confirmado! Você já pode fazer login"
  - ❌ Erro: "Link inválido ou expirado"
- Botão: "Ir para Login"

#### 2.3. Modificação no Login

**Arquivo:** `login.html`

**Funcionalidade:**
- Capturar erro 403 com detalhe "Email não confirmado"
- Mostrar mensagem específica
- Oferecer botão "Reenviar email de confirmação"

---

## 🛡️ SEGURANÇA

### 1. Token de Confirmação

- **Formato:** UUID v4 (36 caracteres)
- **Validade:** 24 horas
- **Uso único:** Marcado como usado após confirmação
- **Não reutilizável:** Cada reenvio gera novo token

### 2. Rate Limiting

- **Reenvio de email:** 3 tentativas por hora por email
- **Verificação de token:** 10 tentativas por hora por IP

### 3. Proteção contra Abuso

- Invalidar tokens antigos ao gerar novo
- Limpar tokens expirados (job diário)

---

## 📝 ARQUIVOS A MODIFICAR/CRIAR

### Backend:

1. ✅ `backend/app/models.py` - Adicionar modelo `EmailVerificationToken`
2. ✅ `backend/app/schemas.py` - Adicionar schemas:
   - `VerifyEmailRequest`
   - `ResendVerificationRequest`
3. ✅ `backend/app/routers/auth.py` - Modificar/adicionar endpoints:
   - Modificar `POST /api/auth/register`
   - Modificar `POST /api/auth/login`
   - Adicionar `POST /api/auth/verify-email`
   - Adicionar `POST /api/auth/resend-verification`
4. ✅ `backend/app/services/email_service.py` - Adicionar método:
   - `send_email_verification(to_email, token, user_name)`
5. ✅ `backend/app/crud.py` - Adicionar funções:
   - `create_verification_token(db, user_id)`
   - `get_verification_token(db, token)`
   - `mark_token_as_used(db, token)`
   - `invalidate_old_tokens(db, user_id)`

### Frontend:

1. ✅ `login.html` ou `register.html` - Adicionar modal de sucesso
2. ✅ `verify-email.html` - Nova página de confirmação
3. ✅ `assets/js/auth.js` - Adicionar funções:
   - `showSuccessModal(email)`
   - `resendVerification(email)`
   - `verifyEmail(token)`

### Migrations:

1. ✅ `backend/migrations/XXXX_add_email_verification_tokens.sql`

---

## 🧪 TESTES

### 1. Teste: Cadastro com Sucesso

**Passos:**
1. Preencher formulário de cadastro
2. Submeter
3. Verificar:
   - ✅ Modal de sucesso aparece
   - ✅ Email de confirmação enviado
   - ✅ Token criado no banco
   - ✅ email_verified = False

### 2. Teste: Confirmação de Email

**Passos:**
1. Abrir link do email
2. Verificar:
   - ✅ Token validado
   - ✅ email_verified = True
   - ✅ Token marcado como usado
   - ✅ Mensagem de sucesso

### 3. Teste: Login sem Confirmar Email

**Passos:**
1. Tentar fazer login
2. Verificar:
   - ❌ Login bloqueado
   - ✅ Mensagem: "Por favor, confirme seu email"
   - ✅ Botão para reenviar email

### 4. Teste: Reenvio de Email

**Passos:**
1. Clicar em "Reenviar email"
2. Verificar:
   - ✅ Novo token gerado
   - ✅ Tokens antigos invalidados
   - ✅ Novo email enviado
   - ✅ Mensagem de sucesso

### 5. Teste: Token Expirado

**Passos:**
1. Usar token com mais de 24h
2. Verificar:
   - ❌ Erro: "Link expirado"
   - ✅ Botão para reenviar email

### 6. Teste: Token Já Usado

**Passos:**
1. Usar mesmo token duas vezes
2. Verificar:
   - ❌ Erro: "Link já foi usado"
   - ✅ Mensagem: "Seu email já está confirmado"

---

## 📊 ORDEM DE IMPLEMENTAÇÃO

### Fase 1: Backend - Modelo e Migrations

1. Criar modelo `EmailVerificationToken`
2. Criar migration SQL
3. Adicionar schemas Pydantic

### Fase 2: Backend - CRUD e Endpoints

1. Implementar funções CRUD
2. Modificar endpoint de registro
3. Adicionar endpoint de verificação
4. Adicionar endpoint de reenvio
5. Modificar endpoint de login

### Fase 3: Backend - Email Service

1. Criar template de email de confirmação
2. Adicionar método `send_email_verification`

### Fase 4: Frontend - Modal de Sucesso

1. Adicionar HTML do modal
2. Adicionar CSS
3. Adicionar JavaScript para mostrar/fechar

### Fase 5: Frontend - Página de Confirmação

1. Criar `verify-email.html`
2. Implementar lógica de verificação
3. Adicionar tratamento de erros

### Fase 6: Frontend - Modificação no Login

1. Capturar erro de email não confirmado
2. Mostrar mensagem específica
3. Adicionar botão de reenvio

### Fase 7: Testes e Deploy

1. Testar fluxo completo
2. Testar casos de erro
3. Deploy backend
4. Deploy frontend

---

## ⚠️ CONSIDERAÇÕES

### 1. Supabase Auth

**Nota:** O Supabase tem funcionalidade de autenticação integrada, mas:
- Estamos usando PostgreSQL do Supabase apenas como banco de dados
- Nossa autenticação é custom (JWT próprio)
- Não estamos usando Supabase Auth
- Portanto, implementaremos confirmação de email custom

### 2. Compatibilidade

- Usuários já cadastrados (email_verified = False):
  - Permitir login normalmente (não forçar confirmação retroativa)
  - OU: Enviar email de confirmação na próxima tentativa de login

### 3. Email de Boas-Vindas

- Substituir email atual de "boas-vindas" por email de confirmação
- Após confirmação, enviar email de boas-vindas

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

### Backend:

- [ ] Criar modelo `EmailVerificationToken`
- [ ] Criar migration SQL
- [ ] Adicionar schemas Pydantic
- [ ] Implementar funções CRUD
- [ ] Modificar `POST /api/auth/register`
- [ ] Adicionar `POST /api/auth/verify-email`
- [ ] Adicionar `POST /api/auth/resend-verification`
- [ ] Modificar `POST /api/auth/login`
- [ ] Adicionar template de email
- [ ] Adicionar método `send_email_verification`

### Frontend:

- [ ] Adicionar modal de sucesso no cadastro
- [ ] Criar página `verify-email.html`
- [ ] Modificar tratamento de erro no login
- [ ] Adicionar função de reenvio de email

### Testes:

- [ ] Testar cadastro com sucesso
- [ ] Testar confirmação de email
- [ ] Testar login sem confirmar
- [ ] Testar reenvio de email
- [ ] Testar token expirado
- [ ] Testar token já usado

### Deploy:

- [ ] Deploy backend
- [ ] Deploy frontend
- [ ] Verificar emails em produção

---

**Status:** 📝 **PLANEJAMENTO CONCLUÍDO - PRONTO PARA IMPLEMENTAÇÃO**
