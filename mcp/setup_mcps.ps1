# ============================================================
# Script de Configuração dos MCPs - Stripe, Firebase, Cloud SQL
# ============================================================

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Configurando MCPs para IFRS 16" -ForegroundColor Cyan
Write-Host "  Stripe | Firebase | Google Cloud SQL" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar Node.js/NPM
Write-Host "1. Verificando Node.js e NPM..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    $npmVersion = npm --version
    Write-Host "   Node.js: $nodeVersion" -ForegroundColor Green
    Write-Host "   NPM: $npmVersion" -ForegroundColor Green
}
catch {
    Write-Host "   ERRO: Node.js não encontrado. Instale em https://nodejs.org" -ForegroundColor Red
    exit 1
}

# Verificar Python
Write-Host ""
Write-Host "2. Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "   $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "   ERRO: Python não encontrado." -ForegroundColor Red
    exit 1
}

# Criar diretório .cursor se não existir
Write-Host ""
Write-Host "3. Configurando diretório .cursor..." -ForegroundColor Yellow
$cursorDir = ".cursor"
if (-not (Test-Path $cursorDir)) {
    New-Item -ItemType Directory -Path $cursorDir | Out-Null
    Write-Host "   Diretório criado: $cursorDir" -ForegroundColor Green
}
else {
    Write-Host "   Diretório já existe: $cursorDir" -ForegroundColor Green
}

# Instalar dependências Python para MCPs
Write-Host ""
Write-Host "4. Instalando dependências Python..." -ForegroundColor Yellow
$mcpDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$requirementsPath = Join-Path $mcpDir "requirements.txt"

if (Test-Path $requirementsPath) {
    pip install -r $requirementsPath --quiet
    Write-Host "   Dependências instaladas com sucesso!" -ForegroundColor Green
}
else {
    Write-Host "   Instalando dependências manualmente..." -ForegroundColor Yellow
    pip install stripe firebase-admin asyncpg python-dotenv --quiet
    Write-Host "   Dependências instaladas!" -ForegroundColor Green
}

# Função para criar/atualizar mcp.json
function Update-McpConfig {
    param (
        [string]$Path,
        [hashtable]$NewServers
    )
    
    $servers = @{}
    
    # Ler config existente
    if (Test-Path $Path) {
        try {
            $json = Get-Content $Path -Raw | ConvertFrom-Json
            if ($json.mcpServers) {
                foreach ($prop in $json.mcpServers.PSObject.Properties) {
                    $servers[$prop.Name] = $prop.Value
                }
            }
        }
        catch {
            Write-Host "   Aviso: Não foi possível ler config existente" -ForegroundColor Yellow
        }
    }
    
    # Adicionar novos servers
    foreach ($key in $NewServers.Keys) {
        $servers[$key] = $NewServers[$key]
    }
    
    # Salvar
    $finalConfig = @{ mcpServers = $servers }
    $jsonContent = $finalConfig | ConvertTo-Json -Depth 10
    $jsonContent | Out-File -FilePath $Path -Encoding UTF8
}

# Configurar MCPs
Write-Host ""
Write-Host "5. Configurando MCP servers..." -ForegroundColor Yellow

$mcpServers = @{
    # Stripe MCP (oficial)
    "stripe" = @{
        command = "npx"
        args    = @("-y", "@stripe/mcp", "--tools=all")
        env     = @{
            STRIPE_SECRET_KEY = "sk_live_YOUR_KEY_HERE"
        }
    }
    
    # Firebase MCP
    "firebase" = @{
        command = "npx"
        args    = @("-y", "firebase-mcp")
        env     = @{
            FIREBASE_PROJECT_ID = "ifrs16-app"
        }
    }
    
    # PostgreSQL MCP (para Cloud SQL)
    "postgres" = @{
        command = "npx"
        args    = @(
            "-y",
            "@modelcontextprotocol/server-postgres",
            "postgresql://USER:PASSWORD@HOST:5432/ifrs16_licenses?sslmode=require"
        )
    }
}

# Atualizar config local (.cursor/mcp.json)
$localMcpPath = Join-Path $cursorDir "mcp.json"
Update-McpConfig -Path $localMcpPath -NewServers $mcpServers
Write-Host "   Configurado: $localMcpPath" -ForegroundColor Green

# Atualizar config global (AppData)
$globalMcpPath = "$env:APPDATA\Cursor\User\mcp.json"
$globalMcpDir = Split-Path $globalMcpPath -Parent
if (-not (Test-Path $globalMcpDir)) {
    New-Item -ItemType Directory -Path $globalMcpDir -Force | Out-Null
}
Update-McpConfig -Path $globalMcpPath -NewServers $mcpServers
Write-Host "   Configurado: $globalMcpPath" -ForegroundColor Green

# Criar arquivo de ambiente de exemplo
Write-Host ""
Write-Host "6. Criando arquivo de ambiente..." -ForegroundColor Yellow
$envExamplePath = Join-Path $mcpDir ".env.example"
$envContent = @"
# ============================================================
# Configurações dos MCPs - IFRS 16
# ============================================================
# Copie este arquivo para .env e preencha com suas credenciais

# STRIPE
# Obtenha em: https://dashboard.stripe.com/apikeys
STRIPE_SECRET_KEY=sk_live_YOUR_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET_HERE

# FIREBASE
# Baixe o arquivo de credenciais em:
# https://console.firebase.google.com/project/ifrs16-app/settings/serviceaccounts/adminsdk
FIREBASE_PROJECT_ID=ifrs16-app
GOOGLE_APPLICATION_CREDENTIALS=./firebase-service-account.json

# GOOGLE CLOUD SQL (PostgreSQL)
# Obtenha no Cloud Console: https://console.cloud.google.com/sql
POSTGRES_HOST=YOUR_CLOUD_SQL_IP
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=YOUR_PASSWORD
POSTGRES_DATABASE=ifrs16_licenses

# Ou use a connection string completa:
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/ifrs16_licenses?sslmode=require
"@
$envContent | Out-File -FilePath $envExamplePath -Encoding UTF8
Write-Host "   Criado: $envExamplePath" -ForegroundColor Green

# Instruções finais
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  CONFIGURAÇÃO CONCLUÍDA!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "PRÓXIMOS PASSOS:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. STRIPE:" -ForegroundColor Yellow
Write-Host "   - Obtenha sua API Key em: https://dashboard.stripe.com/apikeys"
Write-Host "   - Edite .cursor/mcp.json e substitua 'sk_live_YOUR_KEY_HERE'"
Write-Host ""
Write-Host "2. FIREBASE:" -ForegroundColor Yellow
Write-Host "   - Baixe o arquivo de credenciais (Service Account JSON)"
Write-Host "   - Salve como 'firebase-service-account.json' na raiz do projeto"
Write-Host "   - Ou configure GOOGLE_APPLICATION_CREDENTIALS"
Write-Host ""
Write-Host "3. CLOUD SQL:" -ForegroundColor Yellow
Write-Host "   - Obtenha o IP/Host do seu Cloud SQL"
Write-Host "   - Edite a connection string em .cursor/mcp.json"
Write-Host ""
Write-Host "4. REINICIE O CURSOR para carregar os MCPs" -ForegroundColor Magenta
Write-Host ""
Write-Host "ARQUIVOS CRIADOS:" -ForegroundColor Cyan
Write-Host "   - mcp/stripe_mcp_server.py    (Servidor MCP Stripe)"
Write-Host "   - mcp/firebase_mcp_server.py  (Servidor MCP Firebase)"
Write-Host "   - mcp/cloudsql_mcp_server.py  (Servidor MCP Cloud SQL)"
Write-Host "   - mcp/mcp_config_template.json (Template de configuração)"
Write-Host "   - .cursor/mcp.json            (Configuração local)"
Write-Host ""
