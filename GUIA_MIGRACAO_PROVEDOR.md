# 🚀 Guia de Migração - Alternativas ao Render

**Data:** 11 de Dezembro de 2025  
**Motivo:** Problemas com Render (serviços dormindo, lentidão, limitações)

---

## 📊 COMPARAÇÃO DE PROVEDORES

### Opções Recomendadas (em ordem de prioridade)

| Provedor | Preço | Vantagens | Desvantagens |
|----------|-------|-----------|--------------|
| **Railway** | $5-20/mês | ✅ Sem sleep, rápido, fácil setup | ⚠️ Pode ficar caro com uso |
| **Fly.io** | $0-15/mês | ✅ Sem sleep, global, bom para Python | ⚠️ Curva de aprendizado |
| **DigitalOcean App Platform** | $5-12/mês | ✅ Confiável, bom suporte | ⚠️ Mais caro |
| **Heroku** | $7-25/mês | ✅ Muito confiável, fácil | ❌ Caro, sem free tier |
| **Vercel (Frontend) + Railway (Backend)** | $0-20/mês | ✅ Otimizado para cada parte | ⚠️ Dois serviços |

---

## 🎯 RECOMENDAÇÃO PRINCIPAL: Railway

**Por quê Railway?**
- ✅ **Sem sleep** - Serviços sempre ativos
- ✅ **Setup simples** - Conecta direto ao GitHub
- ✅ **PostgreSQL incluído** - Banco de dados integrado
- ✅ **Deploy automático** - Igual ao Render
- ✅ **Bom para Python/FastAPI** - Suporte nativo
- ✅ **Preço razoável** - $5-20/mês para começar

---

## 📋 PLANO DE MIGRAÇÃO PARA RAILWAY

### Passo 1: Preparar o Código

#### 1.1 Criar `railway.json` (opcional, Railway detecta automaticamente)

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "cd backend && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### 1.2 Criar `railway.toml` (alternativa)

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "cd backend && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

#### 1.3 Atualizar variáveis de ambiente

Railway usa as mesmas variáveis que o Render, então não precisa mudar nada no código!

---

### Passo 2: Criar Conta e Projeto no Railway

1. Acesse: https://railway.app
2. Faça login com GitHub
3. Clique em "New Project"
4. Selecione "Deploy from GitHub repo"
5. Escolha o repositório: `fernandoxavier02/IFRS-16`

---

### Passo 3: Configurar Backend

1. **Adicionar Serviço Backend:**
   - No projeto Railway, clique em "+ New"
   - Selecione "GitHub Repo"
   - Escolha o repositório
   - Railway detectará automaticamente que é Python

2. **Configurar Root Directory:**
   - Vá em Settings → Source
   - Root Directory: `backend`

3. **Configurar Build Command:**
   - Settings → Build
   - Build Command: `pip install -r requirements.txt`

4. **Configurar Start Command:**
   - Settings → Deploy
   - Start Command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

5. **Adicionar Variáveis de Ambiente:**
   - Settings → Variables
   - Adicione todas as variáveis do Render (copie de `VARIABLES_RENDER.txt`)

---

### Passo 4: Configurar Banco de Dados PostgreSQL

1. **Adicionar PostgreSQL:**
   - No projeto Railway, clique em "+ New"
   - Selecione "Database" → "PostgreSQL"

2. **Conectar ao Backend:**
   - Railway cria automaticamente a variável `DATABASE_URL`
   - O backend já está configurado para usar essa variável!

3. **Migrar Dados (se necessário):**
   - Exportar do Render
   - Importar no Railway

---

### Passo 5: Configurar Frontend (Static Site)

**Opção A: Railway (Recomendado)**
1. Adicionar novo serviço
2. Tipo: "Static Site"
3. Root Directory: `.` (raiz do projeto)
4. Build Command: `echo "No build needed"`
5. Output Directory: `.`

**Opção B: Vercel (Melhor para Frontend)**
1. Acesse: https://vercel.com
2. Conecte o repositório GitHub
3. Framework Preset: "Other"
4. Root Directory: `.`
5. Deploy!

---

### Passo 6: Atualizar URLs no Código

Após o deploy, atualize as URLs:

1. **Backend URL:** Railway fornecerá uma URL como `https://ifrs16-backend-production.up.railway.app`
2. **Frontend URL:** Depende da opção escolhida

Atualizar em:
- `backend/app/config.py` - `FRONTEND_URL` e `API_URL`
- `backend/app/main.py` - `ALLOWED_ORIGINS`
- `Calculadora_IFRS16_Deploy.html` - Função `getApiUrl()`

---

## 🔄 ALTERNATIVA: Fly.io

### Por que Fly.io?
- ✅ Sem sleep
- ✅ Deploy global (múltiplas regiões)
- ✅ Bom para Python/FastAPI
- ✅ Free tier generoso

### Setup Fly.io

1. **Instalar Fly CLI:**
```powershell
# Windows
iwr https://fly.io/install.ps1 -useb | iex
```

2. **Criar `fly.toml`:**
```toml
app = "ifrs16-backend"
primary_region = "gru"  # São Paulo

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PORT = "8080"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = false
  auto_start_machines = true
  min_machines_running = 1
  processes = ["app"]

[[services]]
  http_checks = []
  internal_port = 8080
  processes = ["app"]
  protocol = "tcp"
  script_checks = []

  [services.concurrency]
    hard_limit = 25
    soft_limit = 20
    type = "connections"

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [[services.tcp_checks]]
    grace_period = "1s"
    interval = "15s"
    restart_limit = 0
    timeout = "2s"
```

3. **Deploy:**
```bash
fly launch
fly secrets set DATABASE_URL=...
fly deploy
```

---

## 🔄 ALTERNATIVA: DigitalOcean App Platform

### Setup DigitalOcean

1. Acesse: https://cloud.digitalocean.com/apps
2. Create App → GitHub
3. Configure:
   - **Backend:**
     - Type: Web Service
     - Source: `backend/`
     - Build Command: `pip install -r requirements.txt && alembic upgrade head`
     - Run Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Database:**
     - Add Database → PostgreSQL
   - **Frontend:**
     - Type: Static Site
     - Source: `.`

---

## 📝 CHECKLIST DE MIGRAÇÃO

### Antes de Migrar
- [ ] Fazer backup do banco de dados do Render
- [ ] Documentar todas as variáveis de ambiente
- [ ] Testar aplicação localmente
- [ ] Verificar se todos os arquivos estão no GitHub

### Durante a Migração
- [ ] Criar conta no novo provedor
- [ ] Criar projeto/serviço
- [ ] Configurar banco de dados
- [ ] Configurar variáveis de ambiente
- [ ] Fazer deploy do backend
- [ ] Fazer deploy do frontend
- [ ] Testar endpoints da API
- [ ] Testar frontend

### Após a Migração
- [ ] Atualizar URLs no código
- [ ] Atualizar CORS
- [ ] Migrar dados do banco (se necessário)
- [ ] Atualizar webhooks do Stripe (se necessário)
- [ ] Testar fluxo completo
- [ ] Atualizar documentação
- [ ] Desativar serviços no Render (após confirmar que tudo funciona)

---

## 🔧 SCRIPTS DE AJUDA

### Script para Exportar Variáveis do Render

Criar `exportar_variaveis_render.ps1`:

```powershell
# Exportar variáveis de ambiente do Render
$apiKey = "rnd_uVZHfR2G5aDIWaDu5yzWSpRRENFb"
$serviceId = "srv-d4r013idbo4c73c3ke10"

$headers = @{
    "Authorization" = "Bearer $apiKey"
    "Content-Type" = "application/json"
}

$url = "https://api.render.com/v1/services/$serviceId/env-vars"
$response = Invoke-RestMethod -Uri $url -Headers $headers -Method Get

$vars = @()
foreach ($var in $response.envVar) {
    $vars += [PSCustomObject]@{
        key = $var.key
        value = $var.value
    }
}

$vars | Export-Csv -Path "variaveis_render.csv" -NoTypeInformation
Write-Host "Variáveis exportadas para variaveis_render.csv"
```

---

## 💰 ESTIMATIVA DE CUSTOS

### Railway
- **Starter:** $5/mês (500 horas)
- **Developer:** $20/mês (ilimitado)
- **PostgreSQL:** Incluído ou $5/mês adicional

### Fly.io
- **Free:** $0 (3 VMs compartilhadas)
- **Paid:** ~$5-15/mês (depende do uso)

### DigitalOcean
- **Basic:** $5/mês (512MB RAM)
- **Professional:** $12/mês (1GB RAM)
- **PostgreSQL:** $15/mês adicional

---

## 🎯 RECOMENDAÇÃO FINAL

**Para seu caso, recomendo Railway porque:**
1. ✅ Mais fácil de migrar do Render
2. ✅ Sem problemas de "sleep"
3. ✅ PostgreSQL integrado
4. ✅ Preço razoável
5. ✅ Deploy automático do GitHub

**Próximos passos:**
1. Criar conta no Railway
2. Seguir o Passo 2-5 deste guia
3. Testar tudo
4. Migrar dados se necessário
5. Atualizar URLs
6. Desativar Render

---

## 📞 SUPORTE

Se precisar de ajuda na migração:
- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Fly.io Docs: https://fly.io/docs

---

**Última atualização:** 11/12/2025
