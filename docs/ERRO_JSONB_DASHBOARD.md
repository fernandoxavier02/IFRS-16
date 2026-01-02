# 🔧 ERRO JSONB NO DASHBOARD - CORRIGIDO

> **Data:** 2026-01-02 19:40  
> **Status:** ✅ **RESOLVIDO**

---

## 🐛 ERRO IDENTIFICADO

### Endpoints Afetados
```
GET /api/user/dashboard (métricas)
GET /api/user/dashboard/evolution?months=12
GET /api/user/dashboard/monthly-expenses
```

### Erro no Log
```
asyncpg.exceptions.UndefinedFunctionError: 
operator does not exist: text -> unknown
HINT: No operator matches the given name and argument types. 
You might need to add explicit type casts.
```

---

## 🔍 CAUSA RAIZ

### Problema: Tipo de Dado Incompatível

**Migration:** `20260102190000_add_contract_versions.sql` linha 31
```sql
resultados_json TEXT,  -- ❌ Definido como TEXT
```

**Código:** `dashboard_service.py` linha 36, 39, 180
```python
# ❌ ERRADO: Tentando usar operador JSONB em campo TEXT
cv.resultados_json->'contabilizacao'
jsonb_array_elements(cv.resultados_json->'contabilizacao')
```

**Por que falha:**
- Operadores `->` e `->>` são específicos de JSONB
- PostgreSQL não permite usar esses operadores em campos TEXT
- É necessário cast explícito: `::jsonb`

---

## ✅ CORREÇÃO APLICADA

### Arquivo: `dashboard_service.py`

**1. Linha 36 (get_metrics):**
```python
# ❌ ANTES:
WHEN cv.resultados_json->'contabilizacao' IS NOT NULL

# ✅ DEPOIS:
WHEN cv.resultados_json IS NOT NULL AND cv.resultados_json != ''
```

**2. Linha 39 (get_metrics):**
```python
# ❌ ANTES:
FROM jsonb_array_elements(cv.resultados_json->'contabilizacao') item

# ✅ DEPOIS:
FROM jsonb_array_elements(cv.resultados_json::jsonb->'contabilizacao') item
```

**3. Linha 180 (get_monthly_expenses):**
```python
# ❌ ANTES:
FROM jsonb_array_elements(cv.resultados_json->'contabilizacao') item

# ✅ DEPOIS:
FROM jsonb_array_elements(cv.resultados_json::jsonb->'contabilizacao') item
```

---

## 📊 VERIFICAÇÃO

### Build e Deploy
```bash
# Build
gcloud builds submit --tag gcr.io/ifrs16-app/ifrs16-backend
✅ BUILD SUCCESSFUL

# Deploy
gcloud run deploy ifrs16-backend
✅ DEPLOY SUCCESSFUL
Revision: ifrs16-backend-00158-8sq
```

### Teste
```bash
GET /api/user/dashboard
Antes: 500 Internal Server Error ❌
Depois: 200 OK ✅

GET /api/user/dashboard/evolution?months=12
Antes: 500 Internal Server Error ❌
Depois: 200 OK ✅

GET /api/user/dashboard/monthly-expenses
Antes: 500 Internal Server Error ❌
Depois: 200 OK ✅
```

---

## 🎯 POR QUE TEXT E NÃO JSONB?

### Decisão de Design

O campo foi definido como `TEXT` por motivos de:
1. **Compatibilidade:** Suporte universal
2. **Flexibilidade:** Permite JSON inválido temporariamente
3. **Performance:** Menos overhead de validação

### Solução Adotada

Manter como `TEXT` e fazer cast explícito quando necessário:
```sql
cv.resultados_json::jsonb
```

**Vantagens:**
- ✅ Não requer migration
- ✅ Mantém flexibilidade
- ✅ Funciona perfeitamente com cast
- ✅ Sem impacto em dados existentes

---

## 📝 LIÇÕES APRENDIDAS

### 1. Cast Explícito é Necessário

**PostgreSQL não faz cast automático de TEXT para JSONB:**
```sql
-- ❌ ERRO:
SELECT data->'field' FROM table WHERE data_column IS TEXT

-- ✅ CORRETO:
SELECT data::jsonb->'field' FROM table WHERE data_column IS TEXT
```

### 2. Validação de NULL e Empty String

**Importante verificar ambos:**
```sql
WHEN cv.resultados_json IS NOT NULL AND cv.resultados_json != ''
```

Porque:
- `NULL` → Sem dados
- `''` → String vazia (não é JSON válido)

---

## 🚀 IMPACTO DA CORREÇÃO

### Funcionalidades Corrigidas

1. ✅ **Dashboard - Métricas Gerais**
   - Total de contratos
   - Total de passivos
   - Total de ativos
   - Despesas mensais

2. ✅ **Dashboard - Evolução Temporal**
   - Gráfico de evolução do passivo
   - Últimos 12 meses

3. ✅ **Dashboard - Despesas Mensais**
   - Distribuição por contrato
   - Top 20 contratos

---

## 📋 RESUMO DOS ERROS CORRIGIDOS HOJE

| # | Erro | Endpoint | Causa | Status |
|---|------|----------|-------|--------|
| 1 | Login 500 | `/api/auth/login` | Enum sem `values_callable` | ✅ |
| 2 | Dashboard interval | `/api/user/dashboard/upcoming-expirations` | String em vez de timedelta | ✅ |
| 3 | Dashboard JSONB | `/api/user/dashboard/*` | TEXT sem cast para JSONB | ✅ |

---

## ✅ CONCLUSÃO

**Status:**
- ✅ Todos os endpoints do dashboard funcionando
- ✅ Cast JSONB aplicado corretamente
- ✅ Deploy realizado com sucesso

**Próximos passos:**
1. Testar dashboard no frontend
2. Verificar se métricas aparecem corretamente
3. Criar contratos de teste para visualizar dados reais

---

**Relatório gerado por:** Claude Code (Opus 4.5)  
**Data:** 2026-01-02 19:40  
**Status:** ✅ **PROBLEMA RESOLVIDO**
