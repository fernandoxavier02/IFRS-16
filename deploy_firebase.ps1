# Script para deploy completo no Firebase
# Frontend: Firebase Hosting
# Backend: Cloud Run (via gcloud)

param(
    [string]$ProjectId = "ifrs16-app",
    [string]$Region = "us-central1",
    [string]$ServiceName = "ifrs16-backend",
    [switch]$SkipBuild = $false
)

Write-Host "🔥 Deploy completo para Firebase" -ForegroundColor Cyan
Write-Host "Projeto: $ProjectId" -ForegroundColor Yellow
Write-Host ""

# Verificar se Firebase CLI está instalado
try {
    $firebaseVersion = firebase --version
    Write-Host "✅ Firebase CLI: $firebaseVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Firebase CLI não encontrado. Instale com: npm install -g firebase-tools" -ForegroundColor Red
    exit 1
}

# Verificar se gcloud está instalado
try {
    $gcloudVersion = gcloud --version | Select-Object -First 1
    Write-Host "✅ Google Cloud SDK instalado" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Google Cloud SDK não encontrado. Backend não será deployado." -ForegroundColor Yellow
    Write-Host "   Instale em: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📦 Deploy do Frontend (Firebase Hosting)..." -ForegroundColor Cyan
firebase deploy --only hosting --project $ProjectId

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Frontend deployado com sucesso!" -ForegroundColor Green
} else {
    Write-Host "❌ Erro no deploy do frontend" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Deploy do Backend (Cloud Run)..." -ForegroundColor Cyan

# Verificar se gcloud está disponível
try {
    gcloud --version | Out-Null
    
    if (-not $SkipBuild) {
        Write-Host "Construindo imagem Docker..." -ForegroundColor Yellow
        Write-Host "Isso pode demorar alguns minutos..." -ForegroundColor Gray
        gcloud builds submit --tag gcr.io/$ProjectId/$ServiceName --project $ProjectId backend/
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "ERRO ao construir imagem" -ForegroundColor Red
            exit 1
        }
        Write-Host "Imagem construida!" -ForegroundColor Green
    } else {
        Write-Host "Pulando build (usando imagem existente)" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Fazendo deploy no Cloud Run..." -ForegroundColor Yellow
    Write-Host "Isso pode demorar 2-5 minutos..." -ForegroundColor Gray
    
    $deployOutput = gcloud run deploy $ServiceName `
        --image gcr.io/$ProjectId/$ServiceName `
        --platform managed `
        --region $Region `
        --allow-unauthenticated `
        --project $ProjectId `
        --set-env-vars "ENVIRONMENT=production,DEBUG=false" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "Backend deployado com sucesso!" -ForegroundColor Green
        
        # Extrair URL do output
        $urlMatch = $deployOutput | Select-String -Pattern "https://.*\.run\.app"
        if ($urlMatch) {
            $backendUrl = $urlMatch.Matches[0].Value
            Write-Host ""
            Write-Host "URL do Backend: $backendUrl" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "PROXIMOS PASSOS:" -ForegroundColor Yellow
            Write-Host "1. Configure variaveis de ambiente no Cloud Run" -ForegroundColor Yellow
            Write-Host "2. Atualize a URL no codigo: $backendUrl" -ForegroundColor Yellow
            Write-Host "3. Execute migrations: alembic upgrade head" -ForegroundColor Yellow
        }
    } else {
        Write-Host "ERRO no deploy do backend" -ForegroundColor Red
        Write-Host $deployOutput -ForegroundColor Red
    }
} catch {
    Write-Host "Pulando deploy do backend (gcloud nao disponivel)" -ForegroundColor Yellow
    Write-Host "Execute manualmente ou configure gcloud CLI" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Comandos manuais:" -ForegroundColor Cyan
    Write-Host "  gcloud builds submit --tag gcr.io/$ProjectId/$ServiceName backend/" -ForegroundColor Gray
    Write-Host "  gcloud run deploy $ServiceName --image gcr.io/$ProjectId/$ServiceName --region $Region --allow-unauthenticated" -ForegroundColor Gray
}

Write-Host ""
Write-Host "🎉 Deploy concluído!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Próximos passos:" -ForegroundColor Cyan
Write-Host "1. Verificar frontend: https://$ProjectId.web.app" -ForegroundColor Yellow
Write-Host "2. Verificar backend: gcloud run services describe $ServiceName --region $Region --project $ProjectId" -ForegroundColor Yellow
Write-Host "3. Configurar variáveis de ambiente no Cloud Run" -ForegroundColor Yellow
Write-Host "4. Atualizar URLs no código" -ForegroundColor Yellow
