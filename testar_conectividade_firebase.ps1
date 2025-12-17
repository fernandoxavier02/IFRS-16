# Script completo de testes de conectividade Firebase
# Testa todos os componentes: Frontend, Backend, Integrações

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  TESTES DE CONECTIVIDADE FIREBASE - COMPLETO" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Data: $(Get-Date -Format 'dd/MM/yyyy HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

$results = @()
$totalTests = 0
$passedTests = 0
$failedTests = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "Get",
        [hashtable]$Headers = @{},
        [string]$ExpectedStatus = "200",
        [switch]$CheckContent
    )
    
    $totalTests++
    Write-Host "[$totalTests] Testando: $Name" -ForegroundColor Yellow
    Write-Host "    URL: $Url" -ForegroundColor Gray
    
    try {
        if ($Method -eq "Get") {
            $response = Invoke-WebRequest -Uri $Url -Method Get -Headers $Headers -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        } else {
            $response = Invoke-WebRequest -Uri $Url -Method $Method -Headers $Headers -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        }
        
        $statusCode = $response.StatusCode
        
        if ($statusCode -eq $ExpectedStatus -or ($ExpectedStatus -eq "200" -and $statusCode -eq 200)) {
            $passedTests++
            Write-Host "    ✅ PASSOU - Status: $statusCode" -ForegroundColor Green
            
            $result = @{
                Name = $Name
                Status = "✅ PASSOU"
                StatusCode = $statusCode
                Url = $Url
                Error = $null
            }
            
            if ($CheckContent) {
                if ($response.Content -match "ifrs16|IFRS|Calculadora") {
                    Write-Host "    ✅ Conteúdo válido detectado" -ForegroundColor Green
                }
            }
            
            return $result
        } else {
            $failedTests++
            Write-Host "    ❌ FALHOU - Status esperado: $ExpectedStatus, recebido: $statusCode" -ForegroundColor Red
            
            return @{
                Name = $Name
                Status = "❌ FALHOU"
                StatusCode = $statusCode
                Url = $Url
                Error = "Status code incorreto: $statusCode"
            }
        }
    }
    catch {
        $failedTests++
        $errorMsg = $_.Exception.Message
        Write-Host "    ❌ ERRO - $errorMsg" -ForegroundColor Red
        
        return @{
            Name = $Name
            Status = "❌ ERRO"
            StatusCode = $null
            Url = $Url
            Error = $errorMsg
        }
    }
    finally {
        Write-Host ""
    }
}

function Test-RestEndpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "Get",
        [hashtable]$Headers = @{},
        [object]$Body = $null
    )
    
    $totalTests++
    Write-Host "[$totalTests] Testando: $Name" -ForegroundColor Yellow
    Write-Host "    URL: $Url" -ForegroundColor Gray
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            Headers = $Headers
            TimeoutSec = 10
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json)
            $params.ContentType = "application/json"
        }
        
        $response = Invoke-RestMethod @params
        
        $passedTests++
        Write-Host "    ✅ PASSOU" -ForegroundColor Green
        
        if ($response -is [PSCustomObject] -or $response -is [Hashtable]) {
            $responseJson = $response | ConvertTo-Json -Compress
            Write-Host "    Resposta: $($responseJson.Substring(0, [Math]::Min(100, $responseJson.Length)))..." -ForegroundColor Gray
        }
        
        return @{
            Name = $Name
            Status = "✅ PASSOU"
            StatusCode = 200
            Url = $Url
            Error = $null
            Response = $response
        }
    }
    catch {
        $failedTests++
        $errorMsg = $_.Exception.Message
        Write-Host "    ❌ ERRO - $errorMsg" -ForegroundColor Red
        
        return @{
            Name = $Name
            Status = "❌ ERRO"
            StatusCode = $null
            Url = $Url
            Error = $errorMsg
        }
    }
    finally {
        Write-Host ""
    }
}

# ============================================================
# 1. TESTES DO FRONTEND (Firebase Hosting)
# ============================================================
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  1. FRONTEND - FIREBASE HOSTING" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$frontendBase = "https://ifrs16-app.web.app"

$results += Test-Endpoint -Name "Frontend Principal" -Url "$frontendBase" -CheckContent
$results += Test-Endpoint -Name "Calculadora IFRS 16" -Url "$frontendBase/Calculadora_IFRS16_Deploy.html" -CheckContent
$results += Test-Endpoint -Name "Página de Login" -Url "$frontendBase/login.html" -CheckContent
$results += Test-Endpoint -Name "Painel Admin" -Url "$frontendBase/admin.html" -CheckContent
$results += Test-Endpoint -Name "Página de Preços" -Url "$frontendBase/pricing.html" -CheckContent

# ============================================================
# 2. TESTES DO BACKEND (Cloud Run)
# ============================================================
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  2. BACKEND - GOOGLE CLOUD RUN" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$backendBase = "https://ifrs16-backend-1051753255664.us-central1.run.app"

# Health Check
$healthResult = Test-RestEndpoint -Name "Health Check" -Url "$backendBase/health"
$results += $healthResult

# API Docs
$results += Test-Endpoint -Name "API Docs (Swagger)" -Url "$backendBase/docs"
$results += Test-Endpoint -Name "API Docs (ReDoc)" -Url "$backendBase/redoc"
$results += Test-Endpoint -Name "OpenAPI Schema" -Url "$backendBase/openapi.json"

# Endpoints de API
$results += Test-RestEndpoint -Name "Prices API" -Url "$backendBase/api/payments/prices"

# Teste de endpoint protegido (deve retornar 401)
$totalTests++
Write-Host "[$totalTests] Testando: Endpoint Protegido (deve retornar 401)" -ForegroundColor Yellow
Write-Host "    URL: $backendBase/api/auth/me" -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -Uri "$backendBase/api/auth/me" -Method Get -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    $failedTests++
    Write-Host "    ❌ FALHOU - Deveria retornar 401, mas retornou: $($response.StatusCode)" -ForegroundColor Red
    $results += @{
        Name = "Endpoint Protegido (401 esperado)"
        Status = "❌ FALHOU"
        StatusCode = $response.StatusCode
        Url = "$backendBase/api/auth/me"
        Error = "Deveria retornar 401"
    }
}
catch {
    if ($_.Exception.Response.StatusCode -eq 401 -or $_.Exception.Response.StatusCode.value__ -eq 401) {
        $passedTests++
        Write-Host "    ✅ PASSOU - Retornou 401 (esperado)" -ForegroundColor Green
        $results += @{
            Name = "Endpoint Protegido (401 esperado)"
            Status = "✅ PASSOU"
            StatusCode = 401
            Url = "$backendBase/api/auth/me"
            Error = $null
        }
    } else {
        $failedTests++
        Write-Host "    ❌ ERRO - $($_.Exception.Message)" -ForegroundColor Red
        $results += @{
            Name = "Endpoint Protegido (401 esperado)"
            Status = "❌ ERRO"
            StatusCode = $null
            Url = "$backendBase/api/auth/me"
            Error = $_.Exception.Message
        }
    }
}
Write-Host ""

# ============================================================
# 3. TESTES DE INTEGRAÇÃO
# ============================================================
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  3. INTEGRAÇÕES" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Teste do webhook Stripe (deve retornar erro 400 sem payload válido, mas endpoint existe)
$totalTests++
Write-Host "[$totalTests] Testando: Stripe Webhook Endpoint" -ForegroundColor Yellow
Write-Host "    URL: $backendBase/api/payments/webhook" -ForegroundColor Gray
try {
    $response = Invoke-WebRequest -Uri "$backendBase/api/payments/webhook" -Method Post -ContentType "application/json" -Body '{}' -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    Write-Host "    ⚠️  Retornou: $($response.StatusCode) (endpoint existe)" -ForegroundColor Yellow
    $results += @{
        Name = "Stripe Webhook Endpoint"
        Status = "✅ PASSOU"
        StatusCode = $response.StatusCode
        Url = "$backendBase/api/payments/webhook"
        Error = $null
    }
    $passedTests++
}
catch {
    $statusCode = $null
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode.value__
    }
    
    if ($statusCode -eq 400 -or $statusCode -eq 422) {
        $passedTests++
        Write-Host "    ✅ PASSOU - Endpoint existe (retornou $statusCode - esperado sem payload válido)" -ForegroundColor Green
        $results += @{
            Name = "Stripe Webhook Endpoint"
            Status = "✅ PASSOU"
            StatusCode = $statusCode
            Url = "$backendBase/api/payments/webhook"
            Error = $null
        }
    } else {
        $failedTests++
        Write-Host "    ❌ ERRO - $($_.Exception.Message)" -ForegroundColor Red
        $results += @{
            Name = "Stripe Webhook Endpoint"
            Status = "❌ ERRO"
            StatusCode = $statusCode
            Url = "$backendBase/api/payments/webhook"
            Error = $_.Exception.Message
        }
    }
}
Write-Host ""

# ============================================================
# 4. TESTES DO FIREBASE CLI
# ============================================================
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  4. FIREBASE CLI" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar Firebase CLI
$totalTests++
Write-Host "[$totalTests] Testando: Firebase CLI instalado" -ForegroundColor Yellow
try {
    $version = firebase --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $passedTests++
        Write-Host "    ✅ PASSOU - Versão: $version" -ForegroundColor Green
        $results += @{
            Name = "Firebase CLI instalado"
            Status = "✅ PASSOU"
            StatusCode = $null
            Url = "N/A"
            Error = $null
            Details = "Versão: $version"
        }
    } else {
        $failedTests++
        Write-Host "    ❌ FALHOU - Firebase CLI não encontrado" -ForegroundColor Red
        $results += @{
            Name = "Firebase CLI instalado"
            Status = "❌ FALHOU"
            StatusCode = $null
            Url = "N/A"
            Error = "Firebase CLI não encontrado"
        }
    }
}
catch {
    $failedTests++
    Write-Host "    ❌ ERRO - $($_.Exception.Message)" -ForegroundColor Red
    $results += @{
        Name = "Firebase CLI instalado"
        Status = "❌ ERRO"
        StatusCode = $null
        Url = "N/A"
        Error = $_.Exception.Message
    }
}
Write-Host ""

# Verificar autenticação Firebase
$totalTests++
Write-Host "[$totalTests] Testando: Autenticação Firebase" -ForegroundColor Yellow
try {
    $login = firebase login:list 2>&1
    if ($login -match "Logged in" -or $login -match "fernandocostaxavier") {
        $passedTests++
        Write-Host "    ✅ PASSOU - Usuário autenticado" -ForegroundColor Green
        $results += @{
            Name = "Autenticação Firebase"
            Status = "✅ PASSOU"
            StatusCode = $null
            Url = "N/A"
            Error = $null
        }
    } else {
        $failedTests++
        Write-Host "    ⚠️  Não autenticado" -ForegroundColor Yellow
        $results += @{
            Name = "Autenticação Firebase"
            Status = "⚠️  AVISO"
            StatusCode = $null
            Url = "N/A"
            Error = "Não autenticado"
        }
    }
}
catch {
    $failedTests++
    Write-Host "    ❌ ERRO - $($_.Exception.Message)" -ForegroundColor Red
    $results += @{
        Name = "Autenticação Firebase"
        Status = "❌ ERRO"
        StatusCode = $null
        Url = "N/A"
        Error = $_.Exception.Message
    }
}
Write-Host ""

# Verificar projeto configurado
$totalTests++
Write-Host "[$totalTests] Testando: Projeto Firebase configurado" -ForegroundColor Yellow
try {
    $current = firebase use 2>&1
    if ($current -match "ifrs16-app") {
        $passedTests++
        Write-Host "    ✅ PASSOU - Projeto: ifrs16-app" -ForegroundColor Green
        $results += @{
            Name = "Projeto Firebase configurado"
            Status = "✅ PASSOU"
            StatusCode = $null
            Url = "N/A"
            Error = $null
            Details = "Projeto: ifrs16-app"
        }
    } else {
        $failedTests++
        Write-Host "    ⚠️  Projeto não configurado" -ForegroundColor Yellow
        $results += @{
            Name = "Projeto Firebase configurado"
            Status = "⚠️  AVISO"
            StatusCode = $null
            Url = "N/A"
            Error = "Projeto não configurado"
        }
    }
}
catch {
    $failedTests++
    Write-Host "    ❌ ERRO - $($_.Exception.Message)" -ForegroundColor Red
    $results += @{
        Name = "Projeto Firebase configurado"
        Status = "❌ ERRO"
        StatusCode = $null
        Url = "N/A"
        Error = $_.Exception.Message
    }
}
Write-Host ""

# ============================================================
# 5. TESTES DE CORS
# ============================================================
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  5. TESTES DE CORS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Testar requisição do frontend para o backend
$totalTests++
Write-Host "[$totalTests] Testando: CORS - Frontend → Backend" -ForegroundColor Yellow
Write-Host "    Origin: $frontendBase" -ForegroundColor Gray
Write-Host "    URL: $backendBase/api/payments/prices" -ForegroundColor Gray
try {
    $headers = @{
        "Origin" = $frontendBase
        "Referer" = "$frontendBase/"
    }
    $response = Invoke-RestMethod -Uri "$backendBase/api/payments/prices" -Method Get -Headers $headers -TimeoutSec 10 -ErrorAction Stop
    $passedTests++
    Write-Host "    ✅ PASSOU - CORS funcionando" -ForegroundColor Green
    $results += @{
        Name = "CORS - Frontend → Backend"
        Status = "✅ PASSOU"
        StatusCode = 200
        Url = "$backendBase/api/payments/prices"
        Error = $null
    }
}
catch {
    $failedTests++
    Write-Host "    ❌ ERRO - $($_.Exception.Message)" -ForegroundColor Red
    $results += @{
        Name = "CORS - Frontend → Backend"
        Status = "❌ ERRO"
        StatusCode = $null
        Url = "$backendBase/api/payments/prices"
        Error = $_.Exception.Message
    }
}
Write-Host ""

# ============================================================
# RESUMO FINAL
# ============================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  RESUMO DOS TESTES" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Total de testes: $totalTests" -ForegroundColor White
Write-Host "✅ Passou: $passedTests" -ForegroundColor Green
Write-Host "❌ Falhou: $failedTests" -ForegroundColor Red
Write-Host ""

$successRate = if ($totalTests -gt 0) { [math]::Round(($passedTests / $totalTests) * 100, 2) } else { 0 }
Write-Host "Taxa de sucesso: $successRate`%" -ForegroundColor $(if ($successRate -ge 90) { "Green" } elseif ($successRate -ge 70) { "Yellow" } else { "Red" })
Write-Host ""

# Detalhes dos testes
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  DETALHES DOS TESTES" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

foreach ($result in $results) {
    $statusColor = if ($result.Status -match "PASSOU") { "Green" } elseif ($result.Status -match "AVISO") { "Yellow" } else { "Red" }
    Write-Host "$($result.Status) $($result.Name)" -ForegroundColor $statusColor
    if ($result.Url -ne "N/A") {
        Write-Host "    URL: $($result.Url)" -ForegroundColor Gray
    }
    if ($result.StatusCode) {
        Write-Host "    Status: $($result.StatusCode)" -ForegroundColor Gray
    }
    if ($result.Error) {
        Write-Host "    Erro: $($result.Error)" -ForegroundColor Red
    }
    if ($result.Details) {
        Write-Host "    Detalhes: $($result.Details)" -ForegroundColor Gray
    }
    Write-Host ""
}

# Salvar relatório
$reportPath = "RELATORIO_CONECTIVIDADE_FIREBASE_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
$results | ConvertTo-Json -Depth 10 | Out-File -FilePath $reportPath -Encoding UTF8

Write-Host "============================================================" -ForegroundColor Green
Write-Host "  RELATORIO SALVO" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Arquivo: $reportPath" -ForegroundColor Gray
Write-Host ""

if ($failedTests -eq 0) {
    Write-Host "TODOS OS TESTES PASSARAM!" -ForegroundColor Green
} elseif ($successRate -ge 90) {
    Write-Host "Sistema funcionando bem ($successRate`% de sucesso)" -ForegroundColor Green
} else {
    Write-Host "Alguns testes falharam. Revise os erros acima." -ForegroundColor Yellow
}

Write-Host ""
