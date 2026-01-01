# 🔍 Relatório de Erros de Console - IFRS 16

**Data:** 2026-01-01  
**Site Analisado:** https://ifrs16-app.web.app  
**Status:** ✅ Análise Completa

---

## 📋 Resumo Executivo

Foram identificados **1 erro crítico** e **múltiplos warnings** no console do navegador. A maioria dos warnings são informativos e não afetam a funcionalidade.

---

## 🚨 Erros Identificados

### 1. **Erro de Permissions Policy - Stripe Payment API**

**Tipo:** `debug` (mas indica problema de configuração)  
**Mensagem:** 
```
Potential permissions policy violation: payment is not allowed in this document.
```

**Origem:**
- **Arquivo:** `landing.html` (ou página que carrega o Stripe Pricing Table)
- **Causa:** A política de permissões do navegador não permite o uso da API de pagamento do Stripe
- **Impacto:** Pode afetar a funcionalidade de pagamento do Stripe Pricing Table

**Localização no Código:**
- O erro ocorre quando o script do Stripe é carregado: `https://js.stripe.com/v3/pricing-table.js`
- O Stripe Pricing Table está sendo carregado via iframe na página `landing.html`

**Solução Recomendada:**

1. **Adicionar Permissions Policy no HTML:**
   ```html
   <meta http-equiv="Permissions-Policy" content="payment=(self 'https://js.stripe.com')">
   ```

2. **Ou adicionar no firebase.json (headers):**
   ```json
   {
     "source": "**/*.html",
     "headers": [
       {
         "key": "Permissions-Policy",
         "value": "payment=(self 'https://js.stripe.com')"
       }
     ]
   }
   ```

**Arquivos Afetados:**
- `landing.html` - Página principal que carrega o Stripe Pricing Table
- `firebase.json` - Configuração de headers do Firebase Hosting

---

## ⚠️ Warnings Identificados (Não Críticos)

### 1. **Console.logs de Debug em Produção**

**Localização:**
- `assets/js/auth.js` - Múltiplos `console.log`, `console.warn`, `console.error`
- `assets/js/contracts.js` - Logs de debug
- `assets/js/session-manager.js` - Logs de sessão
- `dashboard.html` - Logs de debug do dashboard
- `login.html` - Logs de debug do login

**Impacto:** Baixo - Apenas poluição do console, não afeta funcionalidade

**Solução:** Já implementada parcialmente em `config.js`:
```javascript
// Log da versão no console (apenas em desenvolvimento)
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    console.log(`🧮 Calculadora IFRS 16 v${CONFIG.VERSION} (Build ${CONFIG.BUILD})`);
    console.log(`📡 API: ${CONFIG.API_URL}`);
}
```

**Recomendação:** Aplicar a mesma lógica condicional em todos os arquivos JavaScript.

---

## 📊 Análise Detalhada por Arquivo

### `assets/js/auth.js`

**Erros/Warnings Encontrados:**
- Linha 49: `console.log('[Auth] Session token salvo:...')`
- Linha 51: `console.warn('[Auth] AVISO: session_token nao retornado pelo backend!')`
- Linha 80: `console.error('Erro no login:', error)`
- Linha 165: `console.log('✅ Acesso administrativo ativado')`
- Linha 169: `console.warn('Erro ao verificar token admin:', error)`
- Linha 198: `console.log('✅ Licença já ativada - sistema liberado')`
- Linha 202: `console.warn('⚠️ Licença inválida ou expirada')`
- Linha 207: `console.warn('⚠️ Modo offline - usando licença salva')`
- Linha 266: `console.log('🔒 Admin: Monitoramento de licença desabilitado')`
- Linha 293: `console.warn('Erro ao verificar licença (offline?):', error)`
- Linha 297: `console.log('🔒 Monitoramento de licença ativo')`
- Linha 309: `console.error('🚫 Sistema bloqueado:', mensagem)`

**Status:** ⚠️ Warnings informativos - Considerar condicionais para produção

---

### `assets/js/contracts.js`

**Erros/Warnings Encontrados:**
- Linha 9: `console.warn('CONFIG não está definido ainda, aguardando...')`
- Linha 17: `console.log('Nenhum token encontrado, não carregando contratos')`
- Linha 24: `console.warn('Elemento contractsList não encontrado ainda')`
- Linha 45: `console.log('Token inválido, fazendo logout...')`
- Linha 51: `console.log('Usuário não tem licença ativa para gerenciar contratos')`
- Linha 71: `console.warn('Erro ao carregar contratos:', response.status, response.statusText)`
- Linha 74: `console.error('Erro ao carregar contratos:', error)`
- Linha 187: `console.error('Elementos do modal não encontrados')`
- Linha 265: `console.error('Erro:', error)`
- Linha 296: `console.error('Erro:', error)`
- Linha 316: `console.log('Contrato selecionado:', contractId)`
- Linha 370: `console.log('Índices econômicos carregados:', economicIndexes)`
- Linha 373: `console.log('API de índices econômicos não disponível - usando modo manual')`
- Linha 377: `console.error('Erro ao carregar índices:', error)`
- Linha 477: `console.error('Erro ao arquivar versão:', error)`
- Linha 550: `console.error('Erro completo:', response.status, errorText)`
- Linha 553: `console.error('Erro ao processar contrato:', error)`
- Linha 573: `console.log('Dados recebidos:', data)`
- Linha 628: `console.error('Erro ao carregar versões:', response.status, errorMessage)`
- Linha 632: `console.error('Erro ao carregar histórico:', error)`

**Status:** ⚠️ Múltiplos logs de debug - Considerar remover ou condicionar

---

### `assets/js/session-manager.js`

**Erros/Warnings Encontrados:**
- Linha 39: `console.warn('[SessionManager] Nenhum session token encontrado...')`
- Linha 43: `console.log('[SessionManager] Iniciando heartbeat da sessão...')`
- Linha 66: `console.warn('[SessionManager] Token de autenticação ou sessão não encontrado')`
- Linha 82: `console.log('[SessionManager] Heartbeat enviado com sucesso:', data.last_activity)`
- Linha 86: `console.error('[SessionManager] Sessão inválida:', data.detail)`
- Linha 92: `console.error('[SessionManager] Erro ao enviar heartbeat:', response.status)`
- Linha 95: `console.error('[SessionManager] Erro de conexão no heartbeat:', error)`
- Linha 106: `console.log('[SessionManager] Heartbeat interrompido')`
- Linha 139: `console.warn('[SessionManager] Nenhuma sessão ativa para encerrar')`
- Linha 153: `console.log('[SessionManager] Sessão encerrada com sucesso')`
- Linha 155: `console.error('[SessionManager] Erro ao encerrar sessão:', response.status)`
- Linha 158: `console.error('[SessionManager] Erro de conexão ao encerrar sessão:', error)`
- Linha 172: `console.warn('[SessionManager] Token de autenticação não encontrado')`
- Linha 189: `console.error('[SessionManager] Erro ao listar sessões:', response.status)`
- Linha 193: `console.error('[SessionManager] Erro de conexão ao listar sessões:', error)`

**Status:** ⚠️ Logs informativos - Úteis para debug, mas podem ser condicionais

---

### `assets/js/route-protection.js`

**Erros/Warnings Encontrados:**
- Linha 48: `console.warn('🔒 Acesso negado: Usuário não autenticado')`
- Linha 70: `console.warn('🔒 Token expirado')`
- Linha 77: `console.error('🔒 Token inválido:', e)`
- Linha 114: `console.log('✅ Autenticação válida')`
- Linha 154: `console.log('🔐 Route Protection ativo')`
- Linha 155: `console.log('📄 Página:', window.location.pathname.split('/').pop())`
- Linha 156: `console.log('👤 Tipo:', getUserType() || 'Não definido')`

**Status:** ⚠️ Logs de segurança - Úteis para debug, mas podem ser condicionais

---

### `dashboard.html`

**Erros/Warnings Encontrados:**
- Linha 467: `console.log('📊 Dados da assinatura recebidos:', subscription)`
- Linha 469: `console.warn('⚠️ Erro ao buscar assinatura:', subscriptionResponse.status)`
- Linha 485: `console.log('📋 Dashboard data final:', dashboardData)`
- Linha 488: `console.error('Erro:', error)`
- Linha 520: `console.log('🔍 Verificando assinatura:', {...})`
- Linha 528: `console.log('✅ Assinatura ativa detectada, renderizando dados...')`
- Linha 714: `console.error('Erro ao validar licença:', error)`
- Linha 727: `console.log('✅ Licença validada e salva. Acesso liberado à calculadora.')`
- Linha 733: `console.error('Erro ao acessar calculadora:', error)`

**Status:** ⚠️ Logs de debug - Adicionados recentemente para correções (ver `CORRECOES_31-12-2025.md`)

---

### `login.html`

**Erros/Warnings Encontrados:**
- Linha 376: `console.log('🔍 DEBUG LOGIN:', {...})`
- Linha 392: `console.log('📥 RESPOSTA:', {...})`
- Linha 407: `console.log('[Auth] Session token salvo:...')`
- Linha 409: `console.warn('[Auth] AVISO: session_token nao retornado pelo backend!')`

**Status:** ⚠️ Logs de debug - Úteis para troubleshooting

---

## 🎯 Recomendações de Correção

### Prioridade Alta 🔴

1. **Corrigir Permissions Policy do Stripe**
   - Adicionar meta tag ou header HTTP para permitir payment API
   - Arquivos: `landing.html` e `firebase.json`

### Prioridade Média 🟡

2. **Condicionar Console.logs em Produção**
   - Criar função helper para logs condicionais
   - Aplicar em todos os arquivos JavaScript
   - Exemplo:
   ```javascript
   const DEBUG = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
   const log = DEBUG ? console.log.bind(console) : () => {};
   const warn = DEBUG ? console.warn.bind(console) : () => {};
   const error = console.error.bind(console); // Sempre mostrar erros
   ```

3. **Manter Logs de Erro Críticos**
   - `console.error` deve sempre ser exibido (não condicionar)
   - Erros de autenticação, sessão e API são críticos

### Prioridade Baixa 🟢

4. **Documentar Logs de Debug**
   - Manter logs informativos durante desenvolvimento
   - Considerar criar sistema de logging mais robusto no futuro

---

## 📝 Checklist de Implementação

- [ ] Adicionar Permissions Policy para Stripe em `landing.html`
- [ ] Adicionar header Permissions Policy em `firebase.json`
- [ ] Criar função helper para logs condicionais em `config.js`
- [ ] Aplicar logs condicionais em `auth.js`
- [ ] Aplicar logs condicionais em `contracts.js`
- [ ] Aplicar logs condicionais em `session-manager.js`
- [ ] Aplicar logs condicionais em `route-protection.js`
- [ ] Aplicar logs condicionais em `dashboard.html` (inline scripts)
- [ ] Aplicar logs condicionais em `login.html` (inline scripts)
- [ ] Testar em produção após correções
- [ ] Verificar console após deploy

---

## 🔗 Referências

- **Documentação Stripe Permissions Policy:** https://stripe.com/docs/stripe-js/elements/payment-request-button#permissions-policy
- **MDN Permissions Policy:** https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Permissions-Policy
- **Correções Anteriores:** `CORRECOES_31-12-2025.md`

---

**Gerado em:** 2026-01-01  
**Analisado por:** AI Assistant  
**Próxima Revisão:** Após implementação das correções
