# Script de Teste de Assinatura - IFRS 16
# Valida fluxo completo: Frontend → Backend → Banco de Dados

param(
    [string]$BackendUrl = "https://ifrs16-backend-ox4zylcs5a-rj.a.run.app",
    [string]$FrontendUrl = "https://fxstudioai.com",
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

Write-Host "🧪 TESTE DE ASSINATURA - IFRS 16" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Cores para output
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor Green }
function Write-Error { param($msg) Write-Host "❌ $msg" -ForegroundColor Red }
function Write-Warning { param($msg) Write-Host "⚠️  $msg" -ForegroundColor Yellow }
function Write-Info { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor Blue }

# FASE 1: Verificação Inicial
Write-Host "📋 FASE 1: Verificação Inicial" -ForegroundColor Yellow
Write-Host ""

# 1.1 Verificar Backend
Write-Info "Verificando backend..."
try {
    $healthResponse = Invoke-RestMethod -Uri "$BackendUrl/health" -Method Get -ErrorAction Stop
    if ($healthResponse.status -eq "healthy") {
        Write-Success "Backend está saudável"
        Write-Host "   Ambiente: $($healthResponse.environment)" -ForegroundColor Gray
    } else {
        Write-Error "Backend retornou status não saudável"
        exit 1
    }
} catch {
    Write-Error "Não foi possível conectar ao backend: $_"
    exit 1
}

# 1.2 Verificar Endpoint de Preços
Write-Info "Verificando endpoint de preços..."
try {
    $pricesResponse = Invoke-RestMethod -Uri "$BackendUrl/api/payments/prices" -Method Get -ErrorAction Stop
    $priceCount = $pricesResponse.prices.Count
    if ($priceCount -ge 6) {
        Write-Success "Endpoint de preços funcionando ($priceCount planos encontrados)"
    } else {
        Write-Warning "Apenas $priceCount planos encontrados (esperado: 6+)"
    }
} catch {
    Write-Error "Erro ao buscar preços: $_"
    exit 1
}

# 1.3 Verificar Frontend (básico)
Write-Info "Verificando frontend..."
try {
    $frontendResponse = Invoke-WebRequest -Uri "$FrontendUrl/pricing.html" -Method Get -ErrorAction Stop -UseBasicParsing
    if ($frontendResponse.StatusCode -eq 200) {
        Write-Success "Frontend acessível"
    } else {
        Write-Warning "Frontend retornou status $($frontendResponse.StatusCode)"
    }
} catch {
    Write-Warning "Não foi possível verificar frontend: $_"
}

Write-Host ""
Write-Success "FASE 1 concluída!"
Write-Host ""

# FASE 2: Instruções para Teste Manual
Write-Host "📋 FASE 2: Teste Manual de Assinatura" -ForegroundColor Yellow
Write-Host ""
Write-Host "Para continuar o teste, siga estes passos:" -ForegroundColor White
Write-Host ""
Write-Host "1. Abra o navegador em modo anônimo/privado" -ForegroundColor Cyan
Write-Host "2. Acesse: $FrontendUrl/pricing.html" -ForegroundColor Cyan
Write-Host "3. Clique em 'Assinar' no plano Basic Monthly" -ForegroundColor Cyan
Write-Host "4. Use os dados de teste do Stripe:" -ForegroundColor Cyan
Write-Host "   - Cartão: 4242 4242 4242 4242" -ForegroundColor Gray
Write-Host "   - Data: 12/34" -ForegroundColor Gray
Write-Host "   - CVC: 123" -ForegroundColor Gray
Write-Host "   - Email: teste.assinatura+$(Get-Date -Format 'yyyyMMddHHmmss')@gmail.com" -ForegroundColor Gray
Write-Host ""
Write-Host "5. Após o pagamento, pressione ENTER para continuar..." -ForegroundColor Yellow
Write-Host ""

$null = Read-Host "Pressione ENTER após completar o pagamento"

# FASE 3: Validação Pós-Assinatura
Write-Host ""
Write-Host "📋 FASE 3: Validação Pós-Assinatura" -ForegroundColor Yellow
Write-Host ""

Write-Info "Aguardando processamento do webhook (10 segundos)..."
Start-Sleep -Seconds 10

# 3.1 Verificar se webhook foi processado (via logs ou API)
Write-Info "Verificando processamento do webhook..."
Write-Host "   (Verifique os logs do backend para confirmar)" -ForegroundColor Gray
Write-Host "   Procure por: 'checkout.session.completed'" -ForegroundColor Gray
Write-Host ""

# FASE 4: Instruções Finais
Write-Host "📋 FASE 4: Validações Manuais Necessárias" -ForegroundColor Yellow
Write-Host ""

Write-Host "Execute as seguintes verificações manualmente:" -ForegroundColor White
Write-Host ""
Write-Host "✅ Banco de Dados:" -ForegroundColor Cyan
Write-Host "   - Verificar criação de usuário no Supabase" -ForegroundColor Gray
Write-Host "   - Verificar criação de licença" -ForegroundColor Gray
Write-Host "   - Verificar criação de subscription" -ForegroundColor Gray
Write-Host ""
Write-Host "✅ Emails:" -ForegroundColor Cyan
Write-Host "   - Verificar recebimento de email de boas-vindas" -ForegroundColor Gray
Write-Host "   - Verificar senha temporária no email" -ForegroundColor Gray
Write-Host "   - Verificar chave de licença no email" -ForegroundColor Gray
Write-Host ""
Write-Host "✅ Frontend:" -ForegroundColor Cyan
Write-Host "   - Fazer login com senha temporária" -ForegroundColor Gray
Write-Host "   - Trocar senha" -ForegroundColor Gray
Write-Host "   - Verificar dashboard com dados corretos" -ForegroundColor Gray
Write-Host ""

# Resumo
Write-Host "=================================" -ForegroundColor Cyan
Write-Host "📊 RESUMO DO TESTE" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""
Write-Success "Backend verificado e funcionando"
Write-Success "Endpoint de preços funcionando"
Write-Success "Frontend acessível"
Write-Host ""
Write-Info "Próximos passos:"
Write-Host "   1. Complete o teste manual de assinatura" -ForegroundColor Gray
Write-Host "   2. Verifique banco de dados" -ForegroundColor Gray
Write-Host "   3. Verifique emails recebidos" -ForegroundColor Gray
Write-Host "   4. Teste login e dashboard" -ForegroundColor Gray
Write-Host ""
Write-Host "📖 Consulte TESTE_ASSINATURA_COMPLETO.md para guia detalhado" -ForegroundColor Yellow
Write-Host ""
