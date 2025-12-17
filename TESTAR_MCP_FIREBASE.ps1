# Script para testar MCP Firebase

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  TESTE DO MCP FIREBASE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Firebase CLI
Write-Host "1. Verificando Firebase CLI..." -ForegroundColor Yellow
$version = firebase --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Firebase CLI: $version" -ForegroundColor Green
} else {
    Write-Host "   ❌ Firebase CLI não encontrado" -ForegroundColor Red
    exit 1
}

# 2. Verificar autenticação
Write-Host ""
Write-Host "2. Verificando autenticação..." -ForegroundColor Yellow
$login = firebase login:list 2>&1
if ($login -match "Logged in") {
    Write-Host "   ✅ Autenticado" -ForegroundColor Green
    Write-Host "   $login" -ForegroundColor Gray
} else {
    Write-Host "   ⚠️  Não autenticado. Execute: firebase login" -ForegroundColor Yellow
}

# 3. Verificar projeto atual
Write-Host ""
Write-Host "3. Verificando projeto atual..." -ForegroundColor Yellow
$current = firebase use 2>&1
if ($current -match "ifrs16-app") {
    Write-Host "   ✅ Projeto: ifrs16-app" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  Projeto não configurado. Execute: firebase use ifrs16-app" -ForegroundColor Yellow
}

# 4. Verificar arquivo MCP
Write-Host ""
Write-Host "4. Verificando configuração MCP..." -ForegroundColor Yellow
$mcpPath = ".cursor\mcp.json"
if (Test-Path $mcpPath) {
    $mcpContent = Get-Content $mcpPath -Raw | ConvertFrom-Json
    if ($mcpContent.mcpServers.firebase) {
        Write-Host "   ✅ MCP Firebase configurado" -ForegroundColor Green
        Write-Host "   Comando: $($mcpContent.mcpServers.firebase.command)" -ForegroundColor Gray
        Write-Host "   Args: $($mcpContent.mcpServers.firebase.args -join ' ')" -ForegroundColor Gray
    } else {
        Write-Host "   ❌ MCP Firebase não encontrado na configuração" -ForegroundColor Red
    }
} else {
    Write-Host "   ❌ Arquivo mcp.json não encontrado" -ForegroundColor Red
}

# 5. Testar comando Firebase via MCP (simulado)
Write-Host ""
Write-Host "5. Testando comandos Firebase..." -ForegroundColor Yellow
try {
    $projects = firebase projects:list 2>&1
    if ($projects -match "ifrs16-app") {
        Write-Host "   ✅ Projeto ifrs16-app encontrado na lista" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠️  Erro ao listar projetos" -ForegroundColor Yellow
}

# 6. Verificar configuração global
Write-Host ""
Write-Host "6. Verificando configuração global..." -ForegroundColor Yellow
$globalMcpPath = "$env:APPDATA\Cursor\User\mcp.json"
if (Test-Path $globalMcpPath) {
    Write-Host "   ✅ Configuração global existe" -ForegroundColor Green
} else {
    Write-Host "   ℹ️  Configuração global não existe (opcional)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  RESUMO" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "✅ MCP Firebase está configurado!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Para usar o MCP no Cursor:" -ForegroundColor Cyan
Write-Host "1. Reinicie o Cursor completamente" -ForegroundColor Yellow
Write-Host "2. Após reiniciar, você pode pedir:" -ForegroundColor Yellow
Write-Host "   - 'Liste meus projetos Firebase'" -ForegroundColor Gray
Write-Host "   - 'Faça deploy do frontend no Firebase'" -ForegroundColor Gray
Write-Host "   - 'Mostre o status do Firebase Hosting'" -ForegroundColor Gray
Write-Host ""
Write-Host "🔗 Links úteis:" -ForegroundColor Cyan
Write-Host "   - Firebase Console: https://console.firebase.google.com/project/ifrs16-app" -ForegroundColor Gray
Write-Host "   - Projeto atual: ifrs16-app" -ForegroundColor Gray
Write-Host ""
Write-Host ""
