# Script para finalizar configuracao completa do Firebase
# Frontend: Firebase Hosting
# Backend: Cloud Run (via gcloud)
# Database: Cloud SQL

$PROJECT_ID = "ifrs16-app"
$REGION = "us-central1"  # ou southamerica-east1 para Sao Paulo
$SERVICE_NAME = "ifrs16-backend"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  FINALIZANDO CONFIGURACAO FIREBASE COMPLETA" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Firebase CLI
Write-Host "1. Verificando Firebase CLI..." -ForegroundColor Yellow
try {
    $firebaseVersion = firebase --version
    Write-Host "   Firebase CLI: $firebaseVersion" -ForegroundColor Green
} catch {
    Write-Host "   ERRO: Firebase CLI nao encontrado!" -ForegroundColor Red
    Write-Host "   Execute: npm install -g firebase-tools" -ForegroundColor Yellow
    exit 1
}

# 2. Selecionar projeto Firebase
Write-Host ""
Write-Host "2. Selecionando projeto Firebase..." -ForegroundColor Yellow
firebase use $PROJECT_ID
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ERRO: Nao foi possivel selecionar o projeto" -ForegroundColor Red
    exit 1
}
Write-Host "   Projeto selecionado: $PROJECT_ID" -ForegroundColor Green

# 3. Deploy do Frontend (Firebase Hosting)
Write-Host ""
Write-Host "3. Fazendo deploy do frontend (Firebase Hosting)..." -ForegroundColor Yellow
Write-Host "   Isso pode demorar alguns minutos..." -ForegroundColor Gray

firebase deploy --only hosting --project $PROJECT_ID

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "   Frontend deployado com sucesso!" -ForegroundColor Green
    Write-Host "   URL: https://$PROJECT_ID.web.app" -ForegroundColor Cyan
    Write-Host "   URL alternativa: https://$PROJECT_ID.firebaseapp.com" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "   ERRO no deploy do frontend" -ForegroundColor Red
    Write-Host "   Verifique os logs acima" -ForegroundColor Yellow
}

# 4. Verificar se gcloud está instalado
Write-Host ""
Write-Host "4. Verificando Google Cloud SDK..." -ForegroundColor Yellow
try {
    $gcloudVersion = gcloud --version | Select-Object -First 1
    Write-Host "   Google Cloud SDK instalado" -ForegroundColor Green
    $gcloudInstalled = $true
} catch {
    Write-Host "   Google Cloud SDK nao encontrado" -ForegroundColor Yellow
    Write-Host "   Para deploy do backend, instale: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    $gcloudInstalled = $false
}

# 5. Instrucoes para Backend (Cloud Run)
if (-not $gcloudInstalled) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host "  PROXIMOS PASSOS PARA BACKEND" -ForegroundColor Yellow
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Instalar Google Cloud SDK:" -ForegroundColor Cyan
    Write-Host "   https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "2. Fazer login:" -ForegroundColor Cyan
    Write-Host "   gcloud auth login" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "3. Configurar projeto:" -ForegroundColor Cyan
    Write-Host "   gcloud config set project $PROJECT_ID" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "4. Habilitar APIs necessarias:" -ForegroundColor Cyan
    Write-Host "   gcloud services enable cloudbuild.googleapis.com" -ForegroundColor Yellow
    Write-Host "   gcloud services enable run.googleapis.com" -ForegroundColor Yellow
    Write-Host "   gcloud services enable sqladmin.googleapis.com" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "5. Deploy do backend:" -ForegroundColor Cyan
    Write-Host "   .\deploy_firebase.ps1" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "5. Para fazer deploy do backend, execute:" -ForegroundColor Yellow
    Write-Host "   .\deploy_firebase.ps1" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   Ou manualmente:" -ForegroundColor Yellow
    Write-Host "   gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME backend/" -ForegroundColor Gray
    Write-Host "   gcloud run deploy $SERVICE_NAME --image gcr.io/$PROJECT_ID/$SERVICE_NAME --region $REGION --allow-unauthenticated" -ForegroundColor Gray
}

# 6. Resumo
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  CONFIGURACAO CONCLUIDA!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend (Firebase Hosting):" -ForegroundColor Cyan
Write-Host "  URL: https://$PROJECT_ID.web.app" -ForegroundColor Yellow
Write-Host "  URL alternativa: https://$PROJECT_ID.firebaseapp.com" -ForegroundColor Yellow
Write-Host ""
Write-Host "Proximos passos:" -ForegroundColor Cyan
Write-Host "  1. Configurar Cloud SQL PostgreSQL" -ForegroundColor Yellow
Write-Host "  2. Deploy do backend no Cloud Run" -ForegroundColor Yellow
Write-Host "  3. Atualizar URLs no codigo" -ForegroundColor Yellow
Write-Host "  4. Configurar variaveis de ambiente" -ForegroundColor Yellow
Write-Host ""
Write-Host "Veja o guia completo: PLANO_MIGRACAO_FIREBASE_COMPLETO.md" -ForegroundColor Cyan
Write-Host ""
