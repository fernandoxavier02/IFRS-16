# 🔴 ERRO 500 NO LOGIN - DIAGNÓSTICO E SOLUÇÃO

> **Data:** 2026-01-02  
> **Erro:** `POST /api/auth/login 500 (Internal Server Error)`  
> **Status:** ⚠️ **PROBLEMA IDENTIFICADO**

---

## 📋 SUMÁRIO

| Aspecto | Status |
|---------|--------|
| **Erro HTTP** | 500 Internal Server Error |
| **Endpoint** | `/api/auth/login` |
| **Causa Provável** | Problema com tabela `user_sessions` ou query de Subscription |
| **URL Usada** | `https://ifrs16-backend-1051753255664.us-central1.run.app` (antiga) |

---

## 🔍 ANÁLISE DO ERRO

### Erro no Frontend

```javascript
POST https://ifrs16-backend-1051753255664.us-central1.run.app/api/auth/login 500 (Internal Server Error)
📥 RESPOSTA: {status: 500, ok: false, detail: 'Erro interno do servidor'}
```

**Observação Importante:**
- ⚠️ A URL ainda está usando a **versão antiga** (`ifrs16-backend-1051753255664`)
- Isso indica que o frontend não foi atualizado ou há cache do navegador

### Possíveis Causas do Erro 500

1. **Tabela `user_sessions` não existe no Supabase**
   - Migration não foi executada
   - Tabela foi deletada acidentalmente

2. **Problema com query de Subscription**
   - Enum `SubscriptionStatus.ACTIVE` não está sendo comparado corretamente
   - Tabela `subscriptions` não existe ou está vazia

3. **Problema com timezone em `UserSession`**
   - `datetime.utcnow()` retorna datetime sem timezone
   - Modelo espera `DateTime(timezone=True)`

4. **Import faltando ou erro de sintaxe**
   - `UserSession` não importado corretamente
   - `Subscription` ou `SubscriptionStatus` não encontrados

---

## 🔧 SOLUÇÕES PROPOSTAS

### Solução 1: Verificar se Tabela `user_sessions` Existe

**Query SQL para verificar:**
```sql
-- Verificar se tabela existe
SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name = 'user_sessions'
);

-- Se não existir, criar manualmente:
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(500) NOT NULL UNIQUE,
    device_fingerprint VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    device_name VARCHAR(255),
    last_activity TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true
);

-- Criar índices
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);
```

### Solução 2: Corrigir Problema de Timezone

**Problema identificado:**
```python
# auth.py linha 335
now = datetime.utcnow()  # Retorna datetime sem timezone

# Mas o modelo espera:
expires_at = Column(DateTime(timezone=True), ...)  # Com timezone
```

**Correção necessária:**
```python
from datetime import datetime, timezone

# Em vez de:
now = datetime.utcnow()

# Usar:
now = datetime.now(timezone.utc)
```

### Solução 3: Adicionar Try-Except para Capturar Erro Específico

**Modificar `auth.py` para logar erro específico:**
```python
try:
    # ... código de login ...
except Exception as e:
    import traceback
    print(f"[ERROR] Erro no login: {e}")
    print(f"[TRACEBACK] {traceback.format_exc()}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Erro interno: {str(e)}"
    )
```

### Solução 4: Verificar Migration do Supabase

**Verificar se migration foi aplicada:**
```sql
-- Verificar histórico de migrations
SELECT * FROM alembic_version;

-- Verificar se tabela user_sessions existe
\d user_sessions
```

---

## 📝 CHECKLIST DE VERIFICAÇÃO

### ✅ Verificações Necessárias

- [ ] Tabela `user_sessions` existe no Supabase?
- [ ] Migration `20260102181620_remote_commit.sql` foi executada?
- [ ] Tabela `subscriptions` existe e tem dados?
- [ ] Enum `SubscriptionStatus` está definido corretamente?
- [ ] Timezone está sendo tratado corretamente?
- [ ] Logs do Cloud Run mostram erro específico?

### 🔍 Comandos para Diagnóstico

**1. Verificar tabelas no Supabase:**
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('user_sessions', 'subscriptions', 'users')
ORDER BY table_name;
```

**2. Verificar estrutura de `user_sessions`:**
```sql
\d user_sessions
```

**3. Verificar logs do Cloud Run:**
```bash
gcloud run services logs read ifrs16-backend \
  --region us-central1 \
  --project ifrs16-app \
  --limit 100 \
  | grep -i "error\|exception\|traceback"
```

---

## 🚀 PRÓXIMOS PASSOS

### Imediato

1. **Verificar logs detalhados do Cloud Run**
   - Procurar por traceback completo
   - Identificar linha exata do erro

2. **Verificar se tabela `user_sessions` existe**
   - Executar query SQL no Supabase
   - Criar tabela se não existir

3. **Testar endpoint diretamente**
   ```bash
   curl -X POST https://ifrs16-backend-ox4zylcs5a-uc.a.run.app/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@test.com","password":"test123"}'
   ```

### Curto Prazo

4. **Corrigir problema de timezone** (se for o caso)
5. **Adicionar tratamento de erro mais detalhado**
6. **Atualizar frontend para usar URL correta**

---

## 📊 EVIDÊNCIAS

### Código Relevante

**`auth.py` linha 335-343:**
```python
now = datetime.utcnow()  # ⚠️ Sem timezone
result = await db.execute(
    select(UserSession).where(
        UserSession.user_id == user.id,
        UserSession.is_active == True,
        UserSession.expires_at > now  # ⚠️ Comparação pode falhar
    ).order_by(UserSession.last_activity.desc())
)
```

**`models.py` linha 444-459:**
```python
last_activity = Column(
    DateTime(timezone=True),  # ✅ Com timezone
    nullable=False,
    default=datetime.utcnow,  # ⚠️ Mas default sem timezone
    index=True
)
```

**Problema Identificado:**
- `datetime.utcnow()` retorna `datetime` sem timezone
- Modelo espera `DateTime(timezone=True)`
- Comparação `expires_at > now` pode falhar se tipos não coincidirem

---

## ✅ RECOMENDAÇÃO PRIORITÁRIA

**1. Corrigir timezone no código:**
```python
from datetime import datetime, timezone, timedelta

# Em vez de:
now = datetime.utcnow()

# Usar:
now = datetime.now(timezone.utc)
```

**2. Verificar se tabela existe:**
- Executar query SQL no Supabase
- Criar se necessário

**3. Adicionar logs detalhados:**
- Capturar exceção específica
- Logar traceback completo

---

**Relatório gerado por:** Claude Code (Opus 4.5)  
**Data:** 2026-01-02  
**Versão:** 1.0
