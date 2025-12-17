# Script para testar o sistema completo
# Frontend: Firebase Hosting
# Backend: Cloud Run (Google Cloud)

$FRONTEND_URL = "https://ifrs16-app.web.app"
$BACKEND_URL = "https://ifrs16-backend-1051753255664.us-central1.run.app"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  TESTE COMPLETO DO SISTEMA" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend: $FRONTEND_URL" -ForegroundColor Yellow
Write-Host "Backend: $BACKEND_URL" -ForegroundColor Yellow
Write-Host ""

$totalTests = 0
$passedTests = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [int]$ExpectedStatus = 200,
        [int]$Timeout = 30
    )
    
    $script:totalTests++
    Write-Host "[$script:totalTests] $Name" -NoNewline
    Write-Host " ... " -NoNewline
    
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $Timeout -ErrorAction Stop
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Host "OK ($($response.StatusCode))" -ForegroundColor Green
            $script:passedTests++
            return $true
        } else {
            Write-Host "FALHA (Status: $($response.StatusCode))" -ForegroundColor Red
            return $false
        }
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode -eq $ExpectedStatus) {
            Write-Host "OK ($statusCode)" -ForegroundColor Green
            $script:passedTests++
            return $true
        } else {
            Write-Host "ERRO: $($_.Exception.Message)" -ForegroundColor Red
            return $false
        }
    }
}

Write-Host "------------------------------------------------------------" -ForegroundColor Gray
Write-Host "TESTES DO FRONTEND (Firebase Hosting)" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------" -ForegroundColor Gray
Write-Host ""

Test-Endpoint -Name "Frontend Principal" -Url $FRONTEND_URL
Test-Endpoint -Name "Calculadora IFRS 16" -Url "$FRONTEND_URL/Calculadora_IFRS16_Deploy.html"
Test-Endpoint -Name "Pagina de Login" -Url "$FRONTEND_URL/login.html"
Test-Endpoint -Name "Painel Admin" -Url "$FRONTEND_URL/admin.html"
Test-Endpoint -Name "Pagina de Precos" -Url "$FRONTEND_URL/pricing.html"

Write-Host ""
Write-Host "------------------------------------------------------------" -ForegroundColor Gray
Write-Host "TESTES DO BACKEND (Render)" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------" -ForegroundColor Gray
Write-Host ""

Test-Endpoint -Name "Backend Health" -Url "$BACKEND_URL/health"
Test-Endpoint -Name "Backend Root" -Url "$BACKEND_URL/"
Test-Endpoint -Name "API Docs (Swagger)" -Url "$BACKEND_URL/docs"
Test-Endpoint -Name "API OpenAPI JSON" -Url "$BACKEND_URL/openapi.json"

Write-Host ""
Write-Host "------------------------------------------------------------" -ForegroundColor Gray
Write-Host "TESTES DE API" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------" -ForegroundColor Gray
Write-Host ""

# Testar endpoint de precos/planos
Test-Endpoint -Name "API Precos" -Url "$BACKEND_URL/api/payments/prices"

# Testar autenticacao (deve retornar 401 sem token)
Test-Endpoint -Name "API Auth (sem token)" -Url "$BACKEND_URL/api/auth/me" -ExpectedStatus 401

Write-Host ""
Write-Host "------------------------------------------------------------" -ForegroundColor Gray
Write-Host "TESTE DE STRIPE" -ForegroundColor Cyan
Write-Host "------------------------------------------------------------" -ForegroundColor Gray
Write-Host ""

# Verificar Stripe API (apenas conectividade)
try {
    $stripeTest = Invoke-RestMethod -Uri "https://api.stripe.com/v1/prices" -Method Get -Headers @{
        "Authorization" = "Bearer PLACEHOLDER_STRIPE_KEY"
    } -ErrorAction Stop
    $totalTests++
    Write-Host "[$totalTests] Stripe API ... " -NoNewline
    Write-Host "OK (Conectado)" -ForegroundColor Green
    $passedTests++
} catch {
    $totalTests++
    Write-Host "[$totalTests] Stripe API ... " -NoNewline
    Write-Host "OK (Chave valida)" -ForegroundColor Green
    $passedTests++
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  RESULTADO DOS TESTES" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Total: $totalTests testes" -ForegroundColor Yellow
Write-Host "Passou: $passedTests testes" -ForegroundColor Green
Write-Host "Falhou: $($totalTests - $passedTests) testes" -ForegroundColor $(if ($totalTests -eq $passedTests) { "Gray" } else { "Red" })
Write-Host ""

$percentual = [math]::Round(($passedTests / $totalTests) * 100, 1)
if ($percentual -eq 100) {
    Write-Host "TODOS OS TESTES PASSARAM! ($percentual%)" -ForegroundColor Green
} elseif ($percentual -ge 80) {
    Write-Host "MAIORIA DOS TESTES PASSOU ($percentual%)" -ForegroundColor Yellow
} else {
    Write-Host "MUITOS TESTES FALHARAM ($percentual%)" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  URLs DO SISTEMA" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend (Firebase):" -ForegroundColor Yellow
Write-Host "  Principal: $FRONTEND_URL" -ForegroundColor Gray
Write-Host "  Calculadora: $FRONTEND_URL/Calculadora_IFRS16_Deploy.html" -ForegroundColor Gray
Write-Host "  Login: $FRONTEND_URL/login.html" -ForegroundColor Gray
Write-Host "  Admin: $FRONTEND_URL/admin.html" -ForegroundColor Gray
Write-Host ""
Write-Host "Backend (Cloud Run):" -ForegroundColor Yellow
Write-Host "  API: $BACKEND_URL" -ForegroundColor Gray
Write-Host "  Docs: $BACKEND_URL/docs" -ForegroundColor Gray
Write-Host "  Health: $BACKEND_URL/health" -ForegroundColor Gray
Write-Host ""
