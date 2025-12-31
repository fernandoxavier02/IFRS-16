# 🔐 Análise: Sistema de Recuperação de Senha

**Data:** 31/12/2025
**Status:** ⚠️ PARCIALMENTE IMPLEMENTADO

---

## 📋 Estado Atual

### ✅ O que JÁ está implementado:

1. **Frontend (login.html)**
   - Botão "Esqueceu a senha?" (linha 115)
   - Função `forgotPassword()` (linhas 242-256)
   - Chama endpoint `/api/auth/forgot-password`
   - Exibe mensagem genérica de sucesso

2. **Backend - Endpoint Forgot Password**
   - **Arquivo:** `backend/app/routers/auth.py` (linhas 459-491)
   - **Endpoint:** `POST /api/auth/forgot-password`
   - **Schema:** `ForgotPasswordRequest` (email)
   - **Comportamento atual:**
     - Recebe email do usuário
     - Busca usuário no banco
     - ❌ NÃO gera token
     - ❌ NÃO envia email
     - Retorna sucesso genérico (por segurança)

3. **Backend - Template de Email**
   - **Arquivo:** `backend/app/services/email_service.py` (linhas 636-716)
   - **Método:** `send_password_reset_email()`
   - **Template:** Email HTML profissional com botão
   - **Link:** Aponta para `/reset-password.html?token={token}`
   - ✅ Template completo e pronto para uso

4. **Backend - Schema de Reset**
   - **Arquivo:** `backend/app/schemas.py`
   - **Schema:** `ResetPasswordRequest`
   - **Campos:**
     - `token`: Token de reset
     - `new_password`: Nova senha (min 8 chars)

---

## ❌ O que FALTA implementar:

### 1. Geração de Token de Reset

**Localização:** `backend/app/auth.py`

**Falta criar:**
```python
def create_reset_token(user_id: int) -> str:
    """
    Cria um token JWT para reset de senha.
    Expira em 1 hora.
    """
    expires = datetime.utcnow() + timedelta(hours=1)
    payload = {
        "user_id": user_id,
        "type": "password_reset",
        "exp": expires
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

**Validação:**
```python
def verify_reset_token(token: str) -> Optional[int]:
    """
    Valida token de reset e retorna user_id.
    Retorna None se inválido ou expirado.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "password_reset":
            return None
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None  # Token expirado
    except jwt.InvalidTokenError:
        return None  # Token inválido
```

---

### 2. Completar Endpoint Forgot Password

**Arquivo:** `backend/app/routers/auth.py` (linha 481-485)

**Código atual:**
```python
if user:
    # TODO: Implementar envio de email com token de reset
    # token = create_reset_token(user.id)
    # send_reset_email(user.email, token)
    pass
```

**Deve ser substituído por:**
```python
if user:
    # Gerar token de reset
    reset_token = create_reset_token(user.id)

    # Enviar email
    from ..services.email_service import EmailService
    try:
        await EmailService.send_password_reset_email(
            to_email=user.email,
            user_name=user.name,
            reset_token=reset_token
        )
        print(f"[OK] Email de reset enviado para: {user.email}")
    except Exception as e:
        print(f"[WARN] Erro ao enviar email de reset: {e}")
```

---

### 3. Criar Endpoint Reset Password

**Arquivo:** `backend/app/routers/auth.py`

**Adicionar APÓS linha 491:**

```python
@router.post(
    "/reset-password",
    summary="Resetar Senha",
    description="Reseta a senha usando o token recebido por email"
)
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reseta a senha do usuário.

    - **token**: Token recebido por email
    - **new_password**: Nova senha

    Retorna erro se token for inválido ou expirado.
    """
    # Validar token
    user_id = verify_reset_token(body.token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado"
        )

    # Buscar usuário
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )

    # Atualizar senha
    user.password_hash = hash_password(body.new_password)
    user.password_changed_at = datetime.utcnow()
    user.password_must_change = False  # Já trocou a senha

    await db.commit()

    return {
        "success": True,
        "message": "Senha redefinida com sucesso. Você já pode fazer login com a nova senha."
    }
```

---

### 4. Criar Página reset-password.html

**Arquivo:** Frontend na raiz do projeto

**Estrutura:**
- Header com logo
- Formulário com:
  - Campo: Nova senha (password, min 8 chars)
  - Campo: Confirmar nova senha
  - Indicador de força da senha
  - Botão: Redefinir Senha
- Links: Voltar para login
- Validações:
  - Senhas devem coincidir
  - Senha forte (maiúscula, minúscula, número)
- Lógica:
  - Pegar token da URL (`?token=xxx`)
  - Enviar para `POST /api/auth/reset-password`
  - Redirecionar para login em caso de sucesso
  - Exibir erro se token inválido/expirado

**Template base:** Copiar estrutura de `login.html` ou `register.html`

---

## 🔄 Fluxo Completo Esperado

### Cenário 1: Usuário Esqueceu a Senha

```
1. Usuário em login.html
2. Clica "Esqueceu a senha?"
3. Função forgotPassword() executa
4. Pede email (já digitado no campo)
5. POST /api/auth/forgot-password
6. Backend:
   - Busca usuário por email
   - Gera token JWT (exp: 1h)
   - Envia email com link
7. Usuário recebe email
8. Clica no botão "Redefinir Senha"
9. Abre reset-password.html?token=xxx
10. Digita nova senha
11. POST /api/auth/reset-password
12. Backend:
    - Valida token
    - Busca usuário
    - Atualiza senha
13. Redireciona para login.html
14. Usuário faz login com nova senha
```

---

## 📝 Tarefas de Implementação

### Prioridade ALTA

- [ ] **Tarefa 1:** Implementar funções de token em `backend/app/auth.py`
  - `create_reset_token(user_id)`
  - `verify_reset_token(token)`

- [ ] **Tarefa 2:** Completar endpoint forgot-password
  - Descomentar e implementar linhas 482-484
  - Adicionar chamada para `EmailService.send_password_reset_email()`

- [ ] **Tarefa 3:** Criar endpoint reset-password
  - Adicionar em `backend/app/routers/auth.py`
  - Usar schema `ResetPasswordRequest`
  - Validar token antes de resetar

- [ ] **Tarefa 4:** Criar página reset-password.html
  - Copiar estrutura de login.html
  - Campos: nova senha + confirmar
  - Indicador de força da senha
  - Validação de senhas iguais
  - Pegar token da URL
  - POST para /api/auth/reset-password

### Prioridade MÉDIA

- [ ] **Tarefa 5:** Adicionar logging
  - Log quando token é gerado
  - Log quando email é enviado
  - Log quando senha é resetada

- [ ] **Tarefa 6:** Tratamento de erros
  - Token expirado → mensagem clara
  - Token inválido → mensagem clara
  - Email não existe → não revelar (segurança)

### Prioridade BAIXA

- [ ] **Tarefa 7:** Melhorias UX
  - Contador de tempo do token (mostra quanto tempo resta)
  - Opção de reenviar email se expirou
  - Validação em tempo real da força da senha

---

## 🔒 Considerações de Segurança

### ✅ Implementado

1. **Não revelar se email existe**
   - Sempre retorna mensagem genérica
   - Evita enumeração de usuários

2. **Email template profissional**
   - Link clicável
   - Aviso de expiração

### ⚠️ A implementar

1. **Token com expiração curta**
   - Usar 1 hora (já definido no template)
   - Validar expiração no backend

2. **Token de uso único**
   - OPCIONAL: Marcar token como usado no banco
   - Impedir reutilização após reset

3. **Rate limiting**
   - OPCIONAL: Limitar pedidos de reset por IP
   - Ex: Máximo 3 pedidos por hora

---

## 🧪 Testes Recomendados

### Teste 1: Fluxo Feliz
1. Login → Esqueceu senha
2. Digita email válido
3. Recebe email
4. Clica no link
5. Define nova senha
6. Faz login com nova senha
7. ✅ Deve funcionar

### Teste 2: Token Expirado
1. Gerar token manualmente
2. Esperar 1 hora (ou modificar tempo de exp)
3. Tentar usar token
4. ✅ Deve dar erro "Token expirado"

### Teste 3: Token Inválido
1. Modificar token no URL
2. Tentar resetar senha
3. ✅ Deve dar erro "Token inválido"

### Teste 4: Email Não Existe
1. Pedir reset para email inexistente
2. ✅ Deve retornar sucesso (sem revelar)
3. ✅ NÃO deve enviar email

### Teste 5: Senhas Não Coincidem
1. Digitar senhas diferentes
2. ✅ Deve bloquear submit
3. ✅ Deve mostrar erro visual

---

## 📦 Dependências

**Já instaladas:**
- ✅ PyJWT (para tokens)
- ✅ SendGrid (para emails)
- ✅ Pydantic (para schemas)
- ✅ FastAPI (rotas)

**Não precisa instalar nada novo!**

---

## 🚀 Estimativa de Implementação

**Tempo total:** ~2-3 horas

- Funções de token: 30 min
- Endpoints backend: 45 min
- Página HTML: 1 hora
- Testes: 45 min

---

## 📚 Referências

**Arquivos existentes:**
- `backend/app/routers/auth.py` (linhas 459-491)
- `backend/app/services/email_service.py` (linhas 636-716)
- `backend/app/schemas.py` (ResetPasswordRequest)
- `login.html` (exemplo de estrutura)
- `register.html` (exemplo de validação de senha)

**Padrão de implementação:**
- Seguir estilo dos outros endpoints
- Usar mesmos padrões de validação
- Manter consistência visual com outras páginas

---

## 💡 Observações

1. **Por que o TODO ainda está lá?**
   - Implementação foi iniciada mas não concluída
   - Template de email já foi criado
   - Schemas já foram definidos
   - Só falta "ligar os fios"

2. **Por que usar JWT para reset?**
   - Stateless (não precisa armazenar no banco)
   - Expira automaticamente
   - Seguro se SECRET_KEY for forte

3. **Alternativa ao JWT:**
   - Gerar token aleatório (UUID)
   - Salvar no banco com expiração
   - Marcar como usado após reset
   - Mais controle, mas mais complexo

4. **Decisão:** Usar JWT é mais simples e suficiente para este caso

---

## ✅ Próximos Passos

1. Revisar esta análise com o usuário
2. Confirmar prioridades
3. Começar implementação pela Tarefa 1
4. Testar cada componente isoladamente
5. Testar fluxo completo
6. Deploy

---

**Desenvolvedor:** Claude Sonnet 4.5 + Fernando Costa Xavier
**Data:** 31/12/2025
**Versão:** 1.0
