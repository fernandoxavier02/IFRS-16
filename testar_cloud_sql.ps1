# Script de Testes Completo - Cloud SQL Migration
# Testa todos os endpoints e funcionalidades após migração

$API_URL = "https://ifrs16-backend-1051753255664.us-central1.run.app"
$FRONTEND_URL = "https://ifrs16-app.web.app"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  TESTES COMPLETOS - CLOUD SQL MIGRATION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$results = @()
$totalTests = 0
$passedTests = 0
$failedTests = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method,
        [string]$Url,
        [hashtable]$Body = $null,
        [hashtable]$Headers = @{},
        [int]$ExpectedStatus = 200
    )
    
    $totalTests++
    Write-Host "[TESTE $totalTests] $Name..." -NoNewline -ForegroundColor Yellow
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            Headers = $Headers
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json)
            $params.ContentType = "application/json"
        }
        
        $response = Invoke-RestMethod @params
        $statusCode = 200
        
        if ($statusCode -eq $ExpectedStatus) {
            Write-Host " OK" -ForegroundColor Green
            $script:passedTests++
            return @{ Success = $true; Data = $response }
        } else {
            Write-Host " FALHOU (Status: $statusCode, esperado: $ExpectedStatus)" -ForegroundColor Red
            $script:failedTests++
            return @{ Success = $false; Error = "Status code incorreto" }
        }
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq $ExpectedStatus) {
            Write-Host " OK (Status esperado: $ExpectedStatus)" -ForegroundColor Green
            $script:passedTests++
            return @{ Success = $true; StatusCode = $statusCode }
        } else {
            Write-Host " FALHOU (Status: $statusCode, esperado: $ExpectedStatus)" -ForegroundColor Red
            Write-Host "   Erro: $($_.Exception.Message)" -ForegroundColor Gray
            $script:failedTests++
            return @{ Success = $false; Error = $_.Exception.Message; StatusCode = $statusCode }
        }
    }
}

# ============================================================
# 1. TESTES DE CONECTIVIDADE BÁSICA
# ============================================================
Write-Host ""
Write-Host "1. TESTES DE CONECTIVIDADE BASICA" -ForegroundColor Cyan
Write-Host "-----------------------------------" -ForegroundColor Cyan

# 1.1 Health Check / Root
$result1 = Test-Endpoint -Name "Health Check (GET /)" -Method "GET" -Url "$API_URL/" -ExpectedStatus 200

# 1.2 Docs
$result2 = Test-Endpoint -Name "API Docs (GET /docs)" -Method "GET" -Url "$API_URL/docs" -ExpectedStatus 200

# 1.3 Frontend
try {
    Write-Host "[TESTE] Frontend acessivel..." -NoNewline -ForegroundColor Yellow
    $frontendResponse = Invoke-WebRequest -Uri $FRONTEND_URL -Method Get -TimeoutSec 10 -ErrorAction Stop
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Host " OK" -ForegroundColor Green
        $totalTests++
        $passedTests++
    } else {
        Write-Host " FALHOU" -ForegroundColor Red
        $totalTests++
        $failedTests++
    }
} catch {
    Write-Host " FALHOU" -ForegroundColor Red
    Write-Host "   Erro: $($_.Exception.Message)" -ForegroundColor Gray
    $totalTests++
    $failedTests++
}

# ============================================================
# 2. TESTES DE AUTENTICAÇÃO ADMIN
# ============================================================
Write-Host ""
Write-Host "2. TESTES DE AUTENTICACAO ADMIN" -ForegroundColor Cyan
Write-Host "-----------------------------------" -ForegroundColor Cyan

# 2.1 Login Admin
$loginBody = @{
    email = "fernandocostaxavier@gmail.com"
    password = "Master@2025!"
}
$loginResult = Test-Endpoint -Name "Login Admin" -Method "POST" -Url "$API_URL/api/auth/admin/login" -Body $loginBody -ExpectedStatus 200

$adminToken = $null
if ($loginResult.Success -and $loginResult.Data) {
    $adminToken = $loginResult.Data.access_token
    Write-Host "   Token recebido: $($adminToken.Substring(0, 30))..." -ForegroundColor Gray
}

# 2.2 Verificar Admin (se login funcionou)
if ($adminToken) {
    $headers = @{ "Authorization" = "Bearer $adminToken" }
    $meResult = Test-Endpoint -Name "Admin /me" -Method "GET" -Url "$API_URL/api/auth/admin/me" -Headers $headers -ExpectedStatus 200
} else {
    Write-Host "[TESTE] Admin /me..." -NoNewline -ForegroundColor Yellow
    Write-Host " PULADO (login falhou)" -ForegroundColor Gray
    $totalTests--
}

# ============================================================
# 3. TESTES DE LICENÇAS
# ============================================================
Write-Host ""
Write-Host "3. TESTES DE LICENCAS" -ForegroundColor Cyan
Write-Host "-----------------------------------" -ForegroundColor Cyan

if ($adminToken) {
    $headers = @{ "Authorization" = "Bearer $adminToken" }
    
    # 3.1 Listar Licenças
    $licensesResult = Test-Endpoint -Name "Listar Licencas" -Method "GET" -Url "$API_URL/api/admin/licenses" -Headers $headers -ExpectedStatus 200
    
    # 3.2 Criar Licença (se possível)
    $newLicense = @{
        customer_name = "Cliente Teste"
        email = "teste@example.com"
        license_type = "trial"
        duration_months = 1
        max_activations = 1
    }
    $createResult = Test-Endpoint -Name "Criar Licenca" -Method "POST" -Url "$API_URL/api/admin/generate-license" -Body $newLicense -Headers $headers -ExpectedStatus 200
} else {
    Write-Host "[AVISO] Testes de licencas pulados (admin nao autenticado)" -ForegroundColor Yellow
}

# ============================================================
# 4. TESTES DE VALIDAÇÃO
# ============================================================
Write-Host ""
Write-Host "4. TESTES DE VALIDACAO" -ForegroundColor Cyan
Write-Host "-----------------------------------" -ForegroundColor Cyan

# 4.1 Validar Licença Inválida
$invalidLicense = @{ license_key = "INVALID-KEY-12345" }
$validateResult = Test-Endpoint -Name "Validar Licenca Invalida" -Method "POST" -Url "$API_URL/api/licenses/validate" -Body $invalidLicense -ExpectedStatus 404

# ============================================================
# 5. TESTES DE STRIPE
# ============================================================
Write-Host ""
Write-Host "5. TESTES DE STRIPE" -ForegroundColor Cyan
Write-Host "-----------------------------------" -ForegroundColor Cyan

# 5.1 Verificar Preços
$pricesResult = Test-Endpoint -Name "Listar Precos Stripe" -Method "GET" -Url "$API_URL/api/payments/prices" -ExpectedStatus 200

# ============================================================
# 6. VERIFICAR LOGS DO CLOUD RUN
# ============================================================
Write-Host ""
Write-Host "6. VERIFICAR LOGS DO CLOUD RUN" -ForegroundColor Cyan
Write-Host "-----------------------------------" -ForegroundColor Cyan

try {
    Write-Host "[TESTE] Buscar logs recentes..." -NoNewline -ForegroundColor Yellow
    $logs = & "$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd" run services logs read ifrs16-backend --region=us-central1 --project=ifrs16-app --limit=5 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
        $totalTests++
        $passedTests++
        
        # Verificar erros nos logs
        $errorLogs = $logs | Select-String -Pattern "error|Error|ERROR|exception|Exception|failed|Failed" -CaseSensitive:$false
        if ($errorLogs) {
            Write-Host "   AVISO: Erros encontrados nos logs:" -ForegroundColor Yellow
            $errorLogs | Select-Object -First 3 | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
        } else {
            Write-Host "   Nenhum erro encontrado nos logs recentes" -ForegroundColor Gray
        }
    } else {
        Write-Host " FALHOU" -ForegroundColor Red
        $totalTests++
        $failedTests++
    }
} catch {
    Write-Host " FALHOU" -ForegroundColor Red
    Write-Host "   Erro: $($_.Exception.Message)" -ForegroundColor Gray
    $totalTests++
    $failedTests++
}

# ============================================================
# 7. VERIFICAR STATUS DO CLOUD SQL
# ============================================================
Write-Host ""
Write-Host "7. VERIFICAR STATUS DO CLOUD SQL" -ForegroundColor Cyan
Write-Host "-----------------------------------" -ForegroundColor Cyan

try {
    Write-Host "[TESTE] Verificar instancia Cloud SQL..." -NoNewline -ForegroundColor Yellow
    $sqlStatus = & "$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd" sql instances describe ifrs16-database --project=ifrs16-app --format="value(state)" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " OK" -ForegroundColor Green
        Write-Host "   Status: $sqlStatus" -ForegroundColor Gray
        $totalTests++
        $passedTests++
    } else {
        Write-Host " FALHOU" -ForegroundColor Red
        $totalTests++
        $failedTests++
    }
} catch {
    Write-Host " FALHOU" -ForegroundColor Red
    $totalTests++
    $failedTests++
}

# ============================================================
# RESUMO FINAL
# ============================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  RESUMO DOS TESTES" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Total de Testes: $totalTests" -ForegroundColor White
Write-Host "Passou: " -NoNewline -ForegroundColor White
Write-Host "$passedTests" -ForegroundColor Green
Write-Host "Falhou: " -NoNewline -ForegroundColor White
Write-Host "$failedTests" -ForegroundColor Red
Write-Host ""

$successRate = if ($totalTests -gt 0) { [math]::Round(($passedTests / $totalTests) * 100, 2) } else { 0 }
Write-Host "Taxa de Sucesso: $successRate%" -ForegroundColor $(if ($successRate -ge 80) { "Green" } elseif ($successRate -ge 50) { "Yellow" } else { "Red" })
Write-Host ""

# Salvar resultados
$results = @{
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    totalTests = $totalTests
    passedTests = $passedTests
    failedTests = $failedTests
    successRate = $successRate
    adminTokenReceived = ($adminToken -ne $null)
}

$results | ConvertTo-Json | Out-File -FilePath "RELATORIO_TESTES_CLOUD_SQL.json" -Encoding UTF8
Write-Host "Resultados salvos em: RELATORIO_TESTES_CLOUD_SQL.json" -ForegroundColor Gray
Write-Host ""

if ($failedTests -eq 0) {
    Write-Host "✅ TODOS OS TESTES PASSARAM!" -ForegroundColor Green
} elseif ($successRate -ge 80) {
    Write-Host "⚠️  MAIORIA DOS TESTES PASSOU" -ForegroundColor Yellow
} else {
    Write-Host "❌ MUITOS TESTES FALHARAM - VERIFICAR SISTEMA" -ForegroundColor Red
}

Write-Host ""
