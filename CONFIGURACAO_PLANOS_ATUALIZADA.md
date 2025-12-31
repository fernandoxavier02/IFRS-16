# Configuração de Planos - IFRS 16 (Atualizada)

**Data:** 30/12/2025
**Versão:** 2.0

---

## 📋 Mudanças Aplicadas

### 1. Trial (Demonstração)
**Duração:** 24 horas

**Características:**
- ✅ Visualização do sistema
- ❌ **SEM** criação de contratos (max_contracts: 1 apenas visualização)
- ❌ **SEM** download de Excel
- ❌ **SEM** download de CSV
- ❌ **SEM** download de PDF
- ❌ **SEM** emissão de relatórios na tela de consolidação
- ❌ **SEM** suporte
- ❌ **SEM** multi-usuário

**Limitações:**
```json
{
  "max_contracts": 1,
  "max_activations": 1,
  "duration_hours": 24,
  "export_excel": false,
  "export_csv": false,
  "export_pdf": false,
  "consolidation_reports": false,
  "support": false,
  "multi_user": false
}
```

---

### 2. Basic (Básico)
**Mudança Principal:** 3 contratos → **5 contratos**

**Características:**
- ✅ Até **5 contratos** por CNPJ
- ✅ **1 usuário** (1 ativação)
- ✅ Download Excel
- ✅ Download CSV
- ✅ Download PDF
- ✅ Emissão de relatórios na consolidação
- ✅ Suporte por email
- ❌ **SEM** multi-usuário

**Preços:**
- **Mensal:** R$ 299,00
- **Anual:** R$ 3.229,20 (economia de R$ 358,80)

**Configuração:**
```json
{
  "max_contracts": 5,  // ATUALIZADO: 3 → 5
  "max_activations": 1,  // 1 usuário = 1 assinatura
  "export_excel": true,
  "export_csv": true,
  "export_pdf": true,
  "consolidation_reports": true,
  "support": "email",
  "multi_user": false  // Cada usuário precisa de assinatura própria
}
```

---

### 3. Pro (Profissional)
**Mudança Principal:** Multi-usuário removido, agora 1 usuário por assinatura

**Características:**
- ✅ Até **20 contratos** por CNPJ
- ✅ **1 usuário** (1 ativação)
- ✅ Download Excel
- ✅ Download CSV
- ✅ Download PDF
- ✅ Emissão de relatórios na consolidação
- ✅ Suporte prioritário
- ✅ Acesso API
- ❌ **SEM** multi-usuário

**Preços:**
- **Mensal:** R$ 499,00
- **Anual:** R$ 5.389,20 (economia de R$ 599,80)

**Configuração:**
```json
{
  "max_contracts": 20,
  "max_activations": 1,  // ATUALIZADO: 5 → 1
  "export_excel": true,
  "export_csv": true,
  "export_pdf": true,
  "consolidation_reports": true,
  "support": "priority",
  "api_access": true,
  "multi_user": false  // REMOVIDO: Cada usuário precisa de assinatura própria
}
```

---

### 4. Enterprise (Corporativo)
**Mudança Principal:** Multi-usuário removido, agora 1 usuário por assinatura

**Características:**
- ✅ **Contratos ilimitados**
- ✅ **1 usuário** (1 ativação)
- ✅ Download Excel
- ✅ Download CSV
- ✅ Download PDF
- ✅ Emissão de relatórios na consolidação
- ✅ Suporte dedicado
- ✅ Acesso API
- ✅ Treinamento
- ✅ SLA garantido
- ❌ **SEM** multi-usuário

**Preços:**
- **Mensal:** R$ 999,00
- **Anual:** R$ 10.789,20 (economia de R$ 1.198,80)

**Configuração:**
```json
{
  "max_contracts": -1,  // ilimitado
  "max_activations": 1,  // ATUALIZADO: 10 → 1
  "export_excel": true,
  "export_csv": true,
  "export_pdf": true,
  "consolidation_reports": true,
  "support": "dedicated",
  "api_access": true,
  "training": true,
  "sla": true,
  "multi_user": false  // REMOVIDO: Cada usuário precisa de assinatura própria
}
```

---

## 🔄 Política de Multi-Usuário

### ❌ Modelo ANTIGO (Removido)
- Basic: 1 usuário
- Pro: até 5 usuários compartilhando mesma licença
- Enterprise: usuários ilimitados compartilhando mesma licença

### ✅ Modelo NOVO (Implementado)
**Regra Universal:** Cada usuário precisa de sua própria assinatura e licença

**Exemplo:**
- Empresa com 3 funcionários que precisam acessar o sistema
- **Antes:** 1 assinatura Pro (R$ 499/mês) para 5 usuários
- **Agora:** 3 assinaturas individuais (3 × R$ 299/mês ou 3 × R$ 499/mês ou 3 × R$ 999/mês)

**Benefícios:**
- ✅ Controle individual de acesso
- ✅ Licenças independentes
- ✅ Melhor rastreabilidade
- ✅ Maior segurança
- ✅ Facilita cancelamentos individuais

---

## 📊 Tabela Comparativa Atualizada

| Feature | Trial | Basic | Pro | Enterprise |
|---------|-------|-------|-----|------------|
| **Contratos** | 1 (visualização) | **5** | 20 | Ilimitado |
| **Usuários** | 1 | 1 | 1 | 1 |
| **Ativações** | 1 | 1 | 1 | 1 |
| **Duração** | 24h | Ilimitado | Ilimitado | Ilimitado |
| **Excel** | ❌ | ✅ | ✅ | ✅ |
| **CSV** | ❌ | ✅ | ✅ | ✅ |
| **PDF** | ❌ | ✅ | ✅ | ✅ |
| **Relatórios Consolidação** | ❌ | ✅ | ✅ | ✅ |
| **Suporte** | ❌ | Email | Prioritário | Dedicado |
| **API** | ❌ | ❌ | ✅ | ✅ |
| **Treinamento** | ❌ | ❌ | ❌ | ✅ |
| **SLA** | ❌ | ❌ | ❌ | ✅ |
| **Multi-user** | ❌ | ❌ | ❌ | ❌ |
| **Preço Mensal** | Grátis | R$ 299 | R$ 499 | R$ 999 |
| **Preço Anual** | - | R$ 3.229 | R$ 5.389 | R$ 10.789 |

---

## 🔧 Arquivos Modificados

### 1. backend/app/config.py
**Seções atualizadas:**
- `LICENSE_LIMITS` (linhas 95-137)
- `PLAN_CONFIG` (linhas 152-269)
- Comentários dos price IDs (linhas 34-45)

**Mudanças:**
```python
# Trial
"duration_hours": 24,  # NOVO
"consolidation_reports": False,  # NOVO
"export_pdf": False,  # NOVO

# Basic
"max_contracts": 5,  # MUDOU: 3 → 5
"max_activations": 1,  # MUDOU: 2 → 1
"multi_user": False,  # MUDOU: True → False

# Pro
"max_activations": 1,  # MUDOU: 5 → 1
"multi_user": False,  # MUDOU: True → False

# Enterprise
"max_activations": 1,  # MUDOU: 10 → 1
"multi_user": False,  # MUDOU: True → False
```

---

## 🚀 Próximos Passos

### 1. Frontend
Atualizar [pricing.html](frontend/pricing.html) para refletir:
- Basic: **5 contratos** (não 3)
- Trial: **24 horas**, sem downloads, sem relatórios
- Todos os planos: **1 usuário por assinatura**
- Remover menções a "multi-usuário"

### 2. Stripe Dashboard
Verificar se os preços correspondem:
- Basic Monthly: R$ 299,00
- Basic Yearly: R$ 3.229,20
- Pro Monthly: R$ 499,00
- Pro Yearly: R$ 5.389,20
- Enterprise Monthly: R$ 999,00
- Enterprise Yearly: R$ 10.789,20

### 3. Documentação
Atualizar:
- README.md com novos limites
- Documentação da API (/docs)
- Material de marketing

---

## ⚠️ Impactos em Produção

### Usuários Existentes
- **Trial:** Sem impacto (já são 24h por padrão)
- **Basic:** Ganham 2 contratos extras (3→5) ✅
- **Pro:** Perdem multi-usuário (precisarão de múltiplas assinaturas) ⚠️
- **Enterprise:** Perdem multi-usuário (precisarão de múltiplas assinaturas) ⚠️

### Recomendação
1. Notificar clientes Pro/Enterprise sobre mudança
2. Oferecer período de transição (30-60 dias)
3. Criar plano de migração assistida

---

## ✅ Validação

### Testes Necessários
- [ ] Criar licença Trial → verificar 24h de validade
- [ ] Criar licença Basic → verificar limite de 5 contratos
- [ ] Tentar download em Trial → deve bloquear
- [ ] Tentar emitir relatório consolidação em Trial → deve bloquear
- [ ] Verificar que max_activations = 1 em todos os planos
- [ ] Testar múltiplas assinaturas para mesmo usuário

### Endpoints para Testar
```bash
# Obter configuração de planos
curl http://localhost:8000/api/payments/prices

# Validar licença Trial
curl -X POST http://localhost:8000/api/validate-license \
  -H "Content-Type: application/json" \
  -d '{"key": "FX-TRIAL-ABC123", "machine_id": "test-001"}'

# Verificar limites de contratos
curl http://localhost:8000/api/user/subscription \
  -H "Authorization: Bearer <token>"
```

---

**Configurações atualizadas e prontas para uso! ✅**
