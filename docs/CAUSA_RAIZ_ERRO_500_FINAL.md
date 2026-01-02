# 🎯 CAUSA RAIZ IDENTIFICADA - ERRO 500 LOGIN

> **Data:** 2026-01-02  
> **Status:** ✅ **CAUSA ENCONTRADA**

---

## 🔴 ERRO REAL

```
asyncpg.exceptions.InvalidTextRepresentationError: 
invalid input value for enum subscriptionstatus: "ACTIVE"
```

**SQL que falhou:**
```sql
SELECT ... FROM subscriptions 
WHERE subscriptions.user_id = $1::UUID 
AND subscriptions.status = $2::subscriptionstatus 
ORDER BY subscriptions.created_at DESC

[parameters: (UUID('...'), 'ACTIVE')]  -- ❌ 'ACTIVE' em maiúsculo
```

---

## 🔍 CAUSA RAIZ

### Problema: Enum sendo passado como string errada

**O que deveria ser:**
```python
SubscriptionStatus.ACTIVE  # Enum com valor "active" (minúsculo)
```

**O que está sendo enviado ao PostgreSQL:**
```
"ACTIVE"  # String em maiúsculo
```

**Por que falha:**
- Enum no PostgreSQL: `('active', 'past_due', 'cancelled', 'incomplete', 'trialing')`
- SQLAlchemy está enviando: `'ACTIVE'` (não existe no enum)

### Localização do Problema

**`auth.py` linha 318-323:**
```python
from ..models import Subscription, SubscriptionStatus
result = await db.execute(
    select(Subscription).where(
        Subscription.user_id == user.id,
        Subscription.status == SubscriptionStatus.ACTIVE  # ❌ Problema aqui
    ).order_by(Subscription.created_at.desc())
)
```

**`models.py` linha 46-52:**
```python
class SubscriptionStatus(str, enum.Enum):
    """Status de assinatura"""
    ACTIVE = "active"  # ✅ Valor correto
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    INCOMPLETE = "incomplete"
    TRIALING = "trialing"
```

**`models.py` linha 200-204:**
```python
status = Column(
    SQLEnum(SubscriptionStatus),  # ❌ Falta values_callable
    default=SubscriptionStatus.INCOMPLETE,
    nullable=False
)
```

---

## ✅ SOLUÇÃO

### O Problema

O `SQLEnum(SubscriptionStatus)` sem `values_callable` faz o SQLAlchemy usar o **nome** do enum (`ACTIVE`) em vez do **valor** (`active`).

### A Correção

**`models.py` linha 200:**
```python
# ❌ ERRADO (atual):
status = Column(
    SQLEnum(SubscriptionStatus),
    default=SubscriptionStatus.INCOMPLETE,
    nullable=False
)

# ✅ CORRETO:
status = Column(
    SQLEnum(SubscriptionStatus, values_callable=lambda obj: [e.value for e in obj]),
    default=SubscriptionStatus.INCOMPLETE,
    nullable=False
)
```

---

## 📝 OUTROS LUGARES COM O MESMO PROBLEMA

Busquei por todos os usos de `SQLEnum` sem `values_callable`:

1. ✅ **`models.py` linha 200:** `Subscription.status` - **PRECISA CORREÇÃO**
2. ✅ **`models.py` linha 197:** `Subscription.plan_type` - **JÁ ESTÁ CORRETO**
3. ✅ **`models.py` linha 82:** `License.status` - Verificar
4. ✅ **`models.py` linha 85:** `License.license_type` - Verificar
5. ✅ **`models.py` linha 546:** `Notification.notification_type` - Verificar

---

## 🔧 PLANO DE CORREÇÃO

### Passo 1: Corrigir `Subscription.status`

**Arquivo:** `backend/app/models.py` linha 200

```python
status = Column(
    SQLEnum(SubscriptionStatus, values_callable=lambda obj: [e.value for e in obj]),
    default=SubscriptionStatus.INCOMPLETE,
    nullable=False
)
```

### Passo 2: Verificar outros SQLEnum

Verificar se outros enums também precisam de `values_callable`.

### Passo 3: Testar

1. Fazer login
2. Verificar se não há mais erro 500
3. Verificar logs do Cloud Run

---

## 🎯 IMPACTO

### Antes da Correção
- ❌ Login falha com erro 500
- ❌ Query envia `'ACTIVE'` (maiúsculo)
- ❌ PostgreSQL rejeita: enum não tem valor `'ACTIVE'`

### Depois da Correção
- ✅ Login funciona
- ✅ Query envia `'active'` (minúsculo)
- ✅ PostgreSQL aceita: enum tem valor `'active'`

---

**Relatório gerado por:** Claude Code (Opus 4.5)  
**Data:** 2026-01-02
