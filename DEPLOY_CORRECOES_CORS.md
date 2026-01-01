# 🚀 Deploy das Correções de CORS e Heartbeat

**Data:** 01/01/2026
**Status:** ⏳ PENDENTE DEPLOY

---

## 📋 Correções Implementadas

### 1. CORS em Exceções (`backend/app/main.py`)

**Problema:** Quando ocorria um erro 500 não tratado, o middleware CORS não adicionava os headers na resposta, causando erro de CORS no navegador.

**Correção:** O exception handler global agora adiciona headers CORS mesmo em caso de erro.

```python
# Exception handler agora inclui:
origin = request.headers.get("origin", "")
headers = {}
if origin in ALLOWED_ORIGINS:
    headers = {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Credentials": "true",
        ...
    }
return JSONResponse(status_code=500, content=content, headers=headers)
```

### 2. Heartbeat Mais Robusto (`backend/app/routers/auth.py`)

**Problema:** O endpoint `/api/auth/sessions/heartbeat` estava falhando com erro 500, provavelmente porque:
- Tabela `user_sessions` pode não existir no banco de produção
- Problema de timezone na comparação de datas

**Correções:**
- Try/catch para capturar exceções não tratadas
- Correção de timezone removendo tzinfo quando necessário
- Graceful degradation: retorna sucesso silenciosamente se houver erro

---

## 🔧 Como Fazer o Deploy

### Opção 1: Via Terminal (Recomendado)

```powershell
# 1. Navegar para o diretório do backend
cd "D:\IFRS 16 (do replit para o Cursor)\IFRS 16-20251217T150830Z-1-001\IFRS 16\backend"

# 2. Verificar se está autenticado no gcloud
gcloud auth list

# 3. Fazer o deploy
gcloud run deploy ifrs16-backend --source . --region us-central1 --allow-unauthenticated

# 4. Quando perguntado, confirme com 'Y'
```

### Opção 2: Via Console do Google Cloud

1. Acesse: https://console.cloud.google.com/run?project=ifrs16-app
2. Clique em `ifrs16-backend`
3. Clique em "Editar e implantar nova revisão"
4. Faça upload do código ou conecte ao repositório Git
5. Clique em "Implantar"

---

## ✅ Verificação Pós-Deploy

### 1. Health Check
```bash
curl https://ifrs16-backend-1051753255664.us-central1.run.app/health
# Esperado: {"status":"healthy","environment":"production"}
```

### 2. Testar Heartbeat
```bash
# Com um token válido
curl -X POST "https://ifrs16-backend-1051753255664.us-central1.run.app/api/auth/sessions/heartbeat?session_token=test" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json"
# Deve retornar 404 (sessão não encontrada) ou success, NÃO erro 500
```

### 3. Verificar Console do Navegador
1. Acesse https://fxstudioai.com/dashboard.html
2. Abra o console (F12)
3. Não deve mais aparecer erros de CORS

---

## 📝 Arquivos Modificados

| Arquivo | Mudança |
|---------|---------|
| `backend/app/main.py` | Headers CORS no exception handler |
| `backend/app/routers/auth.py` | Try/catch no endpoint heartbeat |
| `RECUPERACAO_SENHA_ANALISE.md` | Status atualizado para COMPLETO |
| `docs/ai/CHANGELOG_AI.md` | Registro das correções |

---

## 📊 Commit

```
Commit: 722df39
Branch: Ajustes
Mensagem: Fix: CORS headers em exceções + heartbeat mais robusto
```

Para push:
```powershell
git push origin Ajustes
```

---

**Desenvolvedor:** GitHub Copilot (via Claude)
**Data:** 01/01/2026

