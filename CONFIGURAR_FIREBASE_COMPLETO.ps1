# Script completo para configurar Firebase
# Executa todos os passos necessarios

$PROJECT_ID = "ifrs16-app"
$REGION = "us-central1"  # ou southamerica-east1 para Sao Paulo
$SERVICE_NAME = "ifrs16-backend"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  CONFIGURACAO COMPLETA FIREBASE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Projeto: $PROJECT_ID" -ForegroundColor Yellow
Write-Host ""

# 1. Selecionar projeto Firebase
Write-Host "1. Selecionando projeto Firebase..." -ForegroundColor Yellow
firebase use $PROJECT_ID
if ($LASTEXITCODE -eq 0) {
    Write-Host "   Projeto selecionado!" -ForegroundColor Green
} else {
    Write-Host "   ERRO ao selecionar projeto" -ForegroundColor Red
    exit 1
}

# 2. Deploy Frontend
Write-Host ""
Write-Host "2. Fazendo deploy do frontend..." -ForegroundColor Yellow
firebase deploy --only hosting --project $PROJECT_ID

if ($LASTEXITCODE -eq 0) {
    $FRONTEND_URL = "https://$PROJECT_ID.web.app"
    Write-Host ""
    Write-Host "   Frontend deployado!" -ForegroundColor Green
    Write-Host "   URL: $FRONTEND_URL" -ForegroundColor Cyan
} else {
    Write-Host "   ERRO no deploy do frontend" -ForegroundColor Red
    exit 1
}

# 3. Verificar gcloud
Write-Host ""
Write-Host "3. Verificando Google Cloud SDK..." -ForegroundColor Yellow
try {
    gcloud --version | Out-Null
    $gcloudInstalled = $true
    Write-Host "   Google Cloud SDK instalado" -ForegroundColor Green
} catch {
    $gcloudInstalled = $false
    Write-Host "   Google Cloud SDK nao encontrado" -ForegroundColor Yellow
}

# 4. Instrucoes para Backend
Write-Host ""
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "  PROXIMOS PASSOS" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host ""

if (-not $gcloudInstalled) {
    Write-Host "1. Instalar Google Cloud SDK:" -ForegroundColor Cyan
    Write-Host "   https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "2. Fazer login:" -ForegroundColor Cyan
    Write-Host "   gcloud auth login" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "3. Configurar projeto:" -ForegroundColor Cyan
    Write-Host "   gcloud config set project $PROJECT_ID" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "4. Habilitar APIs:" -ForegroundColor Cyan
    Write-Host "   gcloud services enable cloudbuild.googleapis.com run.googleapis.com sqladmin.googleapis.com" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "1. Fazer login no Google Cloud:" -ForegroundColor Cyan
    Write-Host "   gcloud auth login" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "2. Configurar projeto:" -ForegroundColor Cyan
    Write-Host "   gcloud config set project $PROJECT_ID" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "3. Habilitar APIs necessarias:" -ForegroundColor Cyan
    Write-Host "   gcloud services enable cloudbuild.googleapis.com run.googleapis.com sqladmin.googleapis.com" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "4. Criar Cloud SQL PostgreSQL:" -ForegroundColor Cyan
    Write-Host "   gcloud sql instances create ifrs16-database --database-version=POSTGRES_15 --tier=db-f1-micro --region=$REGION" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "5. Deploy do backend:" -ForegroundColor Cyan
    Write-Host "   .\deploy_firebase.ps1" -ForegroundColor Yellow
    Write-Host ""
}

# 5. Resumo
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  FRONTEND CONFIGURADO!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend URL:" -ForegroundColor Cyan
Write-Host "  $FRONTEND_URL" -ForegroundColor Yellow
Write-Host ""
Write-Host "Pode acessar agora:" -ForegroundColor Cyan
Write-Host "  Calculadora: $FRONTEND_URL/Calculadora_IFRS16_Deploy.html" -ForegroundColor Yellow
Write-Host "  Login Admin: $FRONTEND_URL/login.html" -ForegroundColor Yellow
Write-Host "  Admin: $FRONTEND_URL/admin.html" -ForegroundColor Yellow
Write-Host ""
Write-Host "Para finalizar:" -ForegroundColor Cyan
Write-Host "  1. Configurar Cloud SQL (banco de dados)" -ForegroundColor Yellow
Write-Host "  2. Deploy do backend no Cloud Run" -ForegroundColor Yellow
Write-Host "  3. Atualizar URLs no codigo (ja feito parcialmente)" -ForegroundColor Yellow
Write-Host "  4. Configurar variaveis de ambiente no Cloud Run" -ForegroundColor Yellow
Write-Host ""
Write-Host "Veja: PLANO_MIGRACAO_FIREBASE_COMPLETO.md" -ForegroundColor Cyan
Write-Host ""
