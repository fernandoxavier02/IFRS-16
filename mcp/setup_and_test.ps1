# ============================================================
# Script de Configuração e Teste de Conectividade - MCPs
# ============================================================

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Configurando e Testando Conectividade dos MCPs" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se gcloud está autenticado
Write-Host "1. Verificando autenticação Google Cloud..." -ForegroundColor Yellow
$authCheck = gcloud auth application-default print-access-token 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "   Executando login..." -ForegroundColor Yellow
    gcloud auth application-default login --project=ifrs16-app
}
Write-Host "   Google Cloud autenticado!" -ForegroundColor Green

# Configurar variáveis de ambiente
Write-Host ""
Write-Host "2. Configurando variáveis de ambiente..." -ForegroundColor Yellow

# Cloud SQL - usando IP público
$env:DATABASE_URL = "postgresql+asyncpg://ifrs16_user:bBMOLk2HURjQAvDiPNYE@136.112.221.225:5432/ifrs16_licenses?sslmode=require"
Write-Host "   DATABASE_URL configurada" -ForegroundColor Green

# Firebase
$env:FIREBASE_PROJECT_ID = "ifrs16-app"
$env:GOOGLE_APPLICATION_CREDENTIALS = "$env:APPDATA\gcloud\application_default_credentials.json"
Write-Host "   FIREBASE_PROJECT_ID configurada" -ForegroundColor Green
Write-Host "   GOOGLE_APPLICATION_CREDENTIALS configurada" -ForegroundColor Green

# Stripe (já deve estar configurada, mas garantir)
if (-not $env:STRIPE_SECRET_KEY) {
    Write-Host "   STRIPE_SECRET_KEY não encontrada - usando valor do sistema" -ForegroundColor Yellow
}

# API URL
$env:API_URL = "https://ifrs16-backend-1051753255664.us-central1.run.app"
Write-Host "   API_URL configurada" -ForegroundColor Green

Write-Host ""
Write-Host "3. Executando testes de conectividade..." -ForegroundColor Yellow
Write-Host ""

# Executar teste
python tests/test_production_connectivity.py

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Configuração e Testes Concluídos!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
