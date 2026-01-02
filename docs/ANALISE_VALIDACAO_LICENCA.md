# 🔍 ANÁLISE: FLUXO DE VALIDAÇÃO DE LICENÇAS

> **Data:** 2026-01-02 21:30  
> **Status:** 🔄 **EM ANÁLISE**

---

## 📋 OBJETIVO

1. ✅ Verificar se a **validação anexa** ocorre apenas **uma vez** no primeiro acesso após compra
2. ✅ Identificar por que o usuário não conseguiu validar a licença após a compra
3. ✅ Corrigir problemas no fluxo de validação

---

## 🔄 FLUXO ATUAL DE VALIDAÇÃO

### 1. Após Compra no Stripe (Webhook)

**Arquivo:** `backend/app/services/stripe_service.py` (linhas 182-449)

**O que acontece:**
1. ✅ Webhook `checkout.session.completed` recebido
2. ✅ Cria/atualiza `Subscription` no banco
3. ✅ Cria/atualiza `License` no banco (status: `ACTIVE`)
4. ✅ Envia email com chave de licença
5. ✅ **NÃO faz validação anexa aqui** (apenas cria a licença)

**Status da Licença após webhook:**
- ✅ `status = ACTIVE`
- ✅ `user_id` vinculado
- ✅ `key` gerada (ex: `FX20251231-IFRS16-ABC123`)
- ✅ `expires_at` definido
- ⚠️ `last_validation = NULL` (ainda não validada)
- ⚠️ `machine_id = NULL` (ainda não ativada)

---

### 2. Primeiro Acesso - Dashboard

**Arquivo:** `dashboard.html` (linhas 970-1019)

**Fluxo:**
1. Usuário clica em "Acessar Calculadora"
2. Verifica se tem assinatura ativa
3. Verifica se tem licença ativa
4. **Chama `POST /api/auth/me/validate-license-token`**
5. Salva dados no `localStorage`
6. Redireciona para calculadora

**Endpoint:** `POST /api/auth/me/validate-license-token`
- **Arquivo:** `backend/app/routers/auth.py` (linhas 496-559)
- **O que faz:**
  - ✅ Busca licença ativa do usuário
  - ✅ Verifica se não expirou
  - ✅ **NÃO atualiza `last_validation`** ⚠️
  - ✅ **NÃO atualiza `machine_id`** ⚠️
  - ✅ Gera token JWT da licença
  - ✅ Retorna dados da licença

**Problema identificado:**
- ⚠️ Este endpoint **NÃO faz validação anexa** (não atualiza `last_validation`, `machine_id`)
- ⚠️ Apenas retorna dados da licença

---

### 3. Primeiro Acesso - Calculadora

**Arquivo:** `assets/js/auth.js` (linhas 139-260)

**Fluxo `verificarSessaoSalva()`:**
1. Verifica se tem licença salva no `localStorage`
2. Se tem, chama `POST /api/check-license` para verificar se ainda é válida
3. Se não tem, mostra tela de licença
4. Se usuário logado mas sem licença ativada, mostra tela de licença

**Função `validarLicenca()` (linhas 89-137):**
- Usuário digita chave de licença manualmente
- Chama `POST /api/validate-license`
- **Este endpoint FAZ validação anexa** ✅

**Endpoint:** `POST /api/validate-license`
- **Arquivo:** `backend/app/routers/licenses.py` (linhas 39-224)
- **O que faz:**
  - ✅ Busca licença por chave
  - ✅ Verifica status, expiração, revogação
  - ✅ Verifica limite de ativações
  - ✅ **Atualiza `last_validation`** ✅
  - ✅ **Atualiza `machine_id`** ✅
  - ✅ **Incrementa `current_activations`** ✅
  - ✅ **Cria log em `validation_logs`** ✅
  - ✅ Gera token JWT

**Este é o endpoint que faz a "validação anexa"!**

---

## ⚠️ PROBLEMA IDENTIFICADO

### Validação Anexa NÃO está ocorrendo no primeiro acesso após compra

**Cenário atual:**
1. ✅ Usuário compra no Stripe
2. ✅ Webhook cria licença (status: ACTIVE, mas não validada)
3. ✅ Usuário acessa dashboard
4. ✅ Dashboard chama `/api/auth/me/validate-license-token`
5. ⚠️ **Este endpoint NÃO faz validação anexa** (não atualiza `last_validation`, `machine_id`)
6. ✅ Usuário é redirecionado para calculadora
7. ✅ Calculadora encontra licença no `localStorage`
8. ⚠️ **Calculadora NÃO faz validação anexa** (apenas verifica se token é válido)

**Resultado:**
- ❌ `last_validation` permanece `NULL`
- ❌ `machine_id` permanece `NULL`
- ❌ `current_activations` permanece `0`
- ❌ Nenhum log em `validation_logs`

**A validação anexa só ocorre se:**
- Usuário digitar a chave manualmente na calculadora
- Ou chamar `/api/validate-license` diretamente

---

## ✅ SOLUÇÃO PROPOSTA

### Opção 1: Fazer validação anexa no endpoint `/api/auth/me/validate-license-token`

**Modificar:** `backend/app/routers/auth.py` (linhas 496-559)

**Adicionar:**
```python
# Após buscar a licença e antes de retornar
from ..crud import update_license_validation, log_validation
from ..models import ValidationLog

# Obter IP e machine_id
ip_address = request.client.host if request.client else None
machine_id = request.headers.get("X-Machine-ID")  # Opcional

# Fazer validação anexa apenas se ainda não foi validada
if not license.last_validation:
    await update_license_validation(
        db,
        key=license.key,
        machine_id=machine_id,
        ip_address=ip_address
    )
    
    await log_validation(
        db,
        license_key=license.key,
        success=True,
        message="Validação inicial após compra",
        machine_id=machine_id,
        ip_address=ip_address,
        user_agent=request.headers.get("User-Agent", "")[:500]
    )
    
    await db.commit()
    print(f"[OK] Validação anexa realizada para licença {license.key}")
```

**Vantagens:**
- ✅ Validação anexa ocorre automaticamente no primeiro acesso
- ✅ Não requer digitação manual da chave
- ✅ Registra log de validação

**Desvantagens:**
- ⚠️ Requer `machine_id` (pode ser opcional)
- ⚠️ Pode ser chamado múltiplas vezes (precisa verificar `last_validation`)

---

### Opção 2: Fazer validação anexa na calculadora quando encontra licença salva

**Modificar:** `assets/js/auth.js` (linhas 178-199)

**Adicionar:**
```javascript
// Se tem licença salva, fazer validação anexa se ainda não foi feita
if (savedLicense && savedToken) {
    try {
        // Verificar se já foi validada (primeira vez)
        const response = await fetch(`${CONFIG.API_URL}/api/validate-license`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                key: savedLicense, 
                machine_id: getMachineId(),
                app_version: CONFIG.VERSION 
            })
        });
        
        // ... resto do código
    }
}
```

**Vantagens:**
- ✅ Usa endpoint existente `/api/validate-license`
- ✅ Já tem toda lógica de validação anexa

**Desvantagens:**
- ⚠️ Requer que usuário tenha chave salva (pode não ter se veio do dashboard)

---

## 🎯 RECOMENDAÇÃO

**Implementar Opção 1** (modificar `/api/auth/me/validate-license-token`)

**Por quê:**
- ✅ É o endpoint chamado automaticamente após compra
- ✅ Não requer digitação manual da chave
- ✅ Garante que validação anexa ocorre no primeiro acesso
- ✅ Pode verificar `last_validation` para evitar múltiplas validações

---

## 🔍 PRÓXIMOS PASSOS

1. ⏳ **Aguardar erros do console** do usuário
2. ✅ Implementar validação anexa no endpoint `/api/auth/me/validate-license-token`
3. ✅ Adicionar verificação para evitar múltiplas validações
4. ✅ Testar fluxo completo após compra
5. ✅ Verificar logs de validação no banco

---

**Status:** 🔄 **AGUARDANDO ERROS DO CONSOLE DO USUÁRIO**
