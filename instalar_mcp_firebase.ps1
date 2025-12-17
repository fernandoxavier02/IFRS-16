# Script para instalar e configurar MCP Firebase no Cursor

Write-Host "🔥 Configurando MCP Firebase para Cursor" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar/Instalar Firebase CLI
Write-Host "1️⃣ Verificando Firebase CLI..." -ForegroundColor Yellow
$firebaseInstalled = npm list -g firebase-tools 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "   Instalando Firebase CLI..." -ForegroundColor Yellow
    npm install -g firebase-tools
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Firebase CLI instalado!" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Erro ao instalar Firebase CLI" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "   ✅ Firebase CLI já está instalado" -ForegroundColor Green
}

# 2. Criar diretório .cursor se não existir
Write-Host ""
Write-Host "2️⃣ Configurando diretório .cursor..." -ForegroundColor Yellow
$cursorDir = ".cursor"
if (-not (Test-Path $cursorDir)) {
    New-Item -ItemType Directory -Path $cursorDir | Out-Null
    Write-Host "   ✅ Diretório .cursor criado" -ForegroundColor Green
} else {
    Write-Host "   ✅ Diretório .cursor já existe" -ForegroundColor Green
}

# 3. Criar arquivo mcp.json
Write-Host ""
Write-Host "3️⃣ Criando arquivo mcp.json..." -ForegroundColor Yellow
$mcpConfig = @{
    mcpServers = @{
        firebase = @{
            command = "npx"
            args = @("-y", "firebase-tools@latest", "mcp")
        }
    }
} | ConvertTo-Json -Depth 10

$mcpPath = Join-Path $cursorDir "mcp.json"
$mcpConfig | Out-File -FilePath $mcpPath -Encoding UTF8
Write-Host "   ✅ Arquivo mcp.json criado em: $mcpPath" -ForegroundColor Green

# 4. Criar tambem configuracao global (opcional)
Write-Host ""
Write-Host "4. Configuracao global (opcional)..." -ForegroundColor Yellow
$globalMcpPath = "$env:APPDATA\Cursor\User\mcp.json"
$globalMcpDir = Split-Path $globalMcpPath -Parent

if (-not (Test-Path $globalMcpDir)) {
    New-Item -ItemType Directory -Path $globalMcpDir -Force | Out-Null
}

# Ler configuração existente se houver
$globalConfig = @{}
if (Test-Path $globalMcpPath) {
    try {
        $existing = Get-Content $globalMcpPath | ConvertFrom-Json
        if ($existing.mcpServers) {
            $globalConfig = $existing.mcpServers | ConvertTo-Hashtable
        }
    } catch {
        Write-Host "   ⚠️  Arquivo global existe mas não pôde ser lido" -ForegroundColor Yellow
    }
}

# Adicionar Firebase se não estiver
if (-not $globalConfig.ContainsKey("firebase")) {
    $globalConfig["firebase"] = @{
        command = "npx"
        args = @("-y", "firebase-tools@latest", "mcp")
    }
    
    $globalMcpConfig = @{
        mcpServers = $globalConfig
    } | ConvertTo-Json -Depth 10
    
    $globalMcpConfig | Out-File -FilePath $globalMcpPath -Encoding UTF8
    Write-Host "   ✅ Configuração global criada em: $globalMcpPath" -ForegroundColor Green
} else {
    Write-Host "   ✅ Firebase já está configurado globalmente" -ForegroundColor Green
}

# 5. Instruções finais
Write-Host ""
Write-Host "✅ Configuração concluída!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Próximos passos:" -ForegroundColor Cyan
Write-Host "1. Execute: firebase login" -ForegroundColor Yellow
Write-Host "2. Execute: firebase init (se ainda não fez)" -ForegroundColor Yellow
Write-Host "3. Reinicie o Cursor para carregar o MCP" -ForegroundColor Yellow
Write-Host ""
Write-Host "📄 Arquivos criados:" -ForegroundColor Cyan
Write-Host "   - Local: $((Get-Location).Path)\$mcpPath" -ForegroundColor Yellow
Write-Host "   - Global: $globalMcpPath" -ForegroundColor Yellow
Write-Host ""
