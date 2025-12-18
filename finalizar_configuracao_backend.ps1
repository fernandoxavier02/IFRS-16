# Script para finalizar a configuração do Backend e Frontend (Corrigido)
# Executa as etapas finais pós-login

$PROJECT_ID = "ifrs16-app"
$REGION = "us-central1"
$SERVICE_NAME = "ifrs16-backend"
$DB_INSTANCE = "ifrs16-database"
$DB_USER = "ifrs16_user"
$DB_NAME = "ifrs16_licenses"
$CONNECTION_NAME = "ifrs16-app:us-central1:ifrs16-database"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  FINALIZANDO CONFIGURACAO (Backend + Frontend)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Gerar Senhas Fortes (Recriando para garantir)
Write-Host "1. Gerando credenciais seguras..." -ForegroundColor Yellow
$dbPassword = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 20 | ForEach-Object { [char]$_ })
$jwtSecret = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object { [char]$_ })

# 2. Atualizar Senha do Banco
Write-Host "2. Atualizando senha do Cloud SQL..." -ForegroundColor Yellow
gcloud sql users set-password $DB_USER --instance=$DB_INSTANCE --password=$dbPassword --project=$PROJECT_ID
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ERRO ao atualizar senha do banco." -ForegroundColor Red
    exit 1
}
Write-Host "   Senha do banco atualizada!" -ForegroundColor Green

# 3. Criar arquivo de variáveis de ambiente (ASCII para evitar BOM)
Write-Host "3. Criando arquivo de ambiente para Cloud Run..." -ForegroundColor Yellow

$envContent = @"
DATABASE_URL: "postgresql+asyncpg://$($DB_USER):$($dbPassword)@/ifrs16_licenses?host=/cloudsql/$($CONNECTION_NAME)"
JWT_SECRET_KEY: "$jwtSecret"
JWT_ALGORITHM: "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: "1440"
ENVIRONMENT: "production"
DEBUG: "false"
FRONTEND_URL: "https://ifrs16-app.web.app"
API_URL: "https://ifrs16-backend-ox4zylcs5a-uc.a.run.app"
CORS_ORIGINS: "https://ifrs16-app.web.app,https://ifrs16-app.firebaseapp.com"
STRIPE_SECRET_KEY: "sk_live_..."
STRIPE_PUBLISHABLE_KEY: "pk_live_..."
STRIPE_WEBHOOK_SECRET: "whsec_..."
"@

$envPath = "cloud_run_env.local.yaml"
$envContent | Out-File -FilePath $envPath -Encoding ASCII
Write-Host "   Arquivo $envPath criado (ASCII)." -ForegroundColor Green

# 4. Atualizar Cloud Run (Usando deploy para garantir --env-vars-file)
# Nota: Usamos 'deploy' com a imagem existente para aplicar variaveis seguramente
Write-Host "4. Aplicando configurações no Cloud Run..." -ForegroundColor Yellow

# Primeiro pegamos a imagem atual para não precisar rebuildar
$currentImage = gcloud run services describe $SERVICE_NAME --region $REGION --project $PROJECT_ID --format="value(spec.template.spec.containers[0].image)"

Write-Host "   Usando imagem: $currentImage" -ForegroundColor Gray

gcloud run deploy $SERVICE_NAME `
    --image $currentImage `
    --env-vars-file=$envPath `
    --region=$REGION `
    --project=$PROJECT_ID `
    --set-cloudsql-instances=$CONNECTION_NAME
    
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ERRO ao atualizar Cloud Run." -ForegroundColor Red
    exit 1
}
Write-Host "   Cloud Run atualizado com sucesso!" -ForegroundColor Green

# 5. Deploy do Frontend (Firebase)
Write-Host "5. Fazendo deploy do Frontend no Firebase..." -ForegroundColor Yellow
firebase deploy --only hosting
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ERRO ao fazer deploy do Firebase. Tente rodar 'firebase login' e 'firebase init'." -ForegroundColor Yellow
}
else {
    Write-Host "   Frontend desdobrado!" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  TUDO PRONTO!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Frontend: https://ifrs16-app.web.app" -ForegroundColor Cyan
Write-Host "Backend:  https://ifrs16-backend-ox4zylcs5a-uc.a.run.app" -ForegroundColor Cyan
Write-Host ""
Write-Host "Use estas credenciais no Cloud Run se precisar:" -ForegroundColor Gray
Write-Host "DB User: $DB_USER" -ForegroundColor Gray
Write-Host "DB Pass: $dbPassword" -ForegroundColor Gray
Write-Host ""
