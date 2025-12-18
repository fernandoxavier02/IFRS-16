# Script para completar login do Google Cloud e configurar tudo
# Execute este script APÓS fazer login no navegador

param(
    [string]$AuthCode = ""
)


# gcloud está no PATH


$PROJECT_ID = "ifrs16-app"
$REGION = "us-central1"
$SERVICE_NAME = "ifrs16-backend"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  CONFIGURACAO COMPLETA GOOGLE CLOUD" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Se código de autenticação fornecido
if ($AuthCode) {
    Write-Host "Autenticando com codigo fornecido..." -ForegroundColor Yellow
    # O gcloud auth login precisa ser feito interativamente
}

# Verificar se já está logado
Write-Host "1. Verificando autenticacao..." -ForegroundColor Yellow
$accounts = gcloud auth list --format="value(account)" 2>$null
if ($accounts) {
    Write-Host "   Logado como: $accounts" -ForegroundColor Green
}
else {
    Write-Host "   Nao logado. Execute: gcloud auth login" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Abrindo navegador para login..." -ForegroundColor Yellow
    gcloud auth login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   ERRO no login" -ForegroundColor Red
        exit 1
    }
}

# Configurar projeto
Write-Host ""
Write-Host "2. Configurando projeto..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID
if ($LASTEXITCODE -eq 0) {
    Write-Host "   Projeto configurado: $PROJECT_ID" -ForegroundColor Green
}
else {
    Write-Host "   ERRO ao configurar projeto" -ForegroundColor Red
    exit 1
}

# Habilitar APIs
Write-Host ""
Write-Host "3. Habilitando APIs necessarias..." -ForegroundColor Yellow
Write-Host "   Cloud Build..." -ForegroundColor Gray
gcloud services enable cloudbuild.googleapis.com --project $PROJECT_ID 2>$null
Write-Host "   Cloud Run..." -ForegroundColor Gray
gcloud services enable run.googleapis.com --project $PROJECT_ID 2>$null
Write-Host "   Cloud SQL..." -ForegroundColor Gray
gcloud services enable sqladmin.googleapis.com --project $PROJECT_ID 2>$null
Write-Host "   Container Registry..." -ForegroundColor Gray
gcloud services enable containerregistry.googleapis.com --project $PROJECT_ID 2>$null
Write-Host "   APIs habilitadas!" -ForegroundColor Green

# Verificar Cloud SQL
Write-Host ""
Write-Host "4. Verificando Cloud SQL..." -ForegroundColor Yellow
$sqlInstances = gcloud sql instances list --project $PROJECT_ID --format="value(name)" 2>$null
if ($sqlInstances) {
    Write-Host "   Instancia existente: $sqlInstances" -ForegroundColor Green
}
else {
    Write-Host "   Nenhuma instancia encontrada" -ForegroundColor Yellow
    Write-Host "   Deseja criar uma nova instancia Cloud SQL? (s/N): s"
    $criar = 's'
    if ($criar -eq 's') {
        Write-Host ""
        Write-Host "   Criando Cloud SQL PostgreSQL..." -ForegroundColor Yellow
        Write-Host "   Isso pode demorar 5-10 minutos..." -ForegroundColor Gray
        
        $dbPassword = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 16 | ForEach-Object { [char]$_ })
        
        gcloud sql instances create ifrs16-database `
            --database-version=POSTGRES_15 `
            --tier=db-f1-micro `
            --region=$REGION `
            --root-password=$dbPassword `
            --project=$PROJECT_ID
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   Cloud SQL criado!" -ForegroundColor Green
            Write-Host "   Senha root: $dbPassword" -ForegroundColor Cyan
            Write-Host "   SALVE ESTA SENHA!" -ForegroundColor Red
            
            # Criar database
            gcloud sql databases create ifrs16_licenses --instance=ifrs16-database --project=$PROJECT_ID
            
            # Criar usuário
            gcloud sql users create ifrs16_user --instance=ifrs16-database --password=$dbPassword --project=$PROJECT_ID
        }
    }
}

# Deploy Backend
Write-Host ""
Write-Host "5. Deploy do Backend no Cloud Run..." -ForegroundColor Yellow
Write-Host "   Deseja fazer deploy do backend? (s/N): s"
$deploy = 's'

if ($deploy -eq 's') {
    Write-Host ""
    Write-Host "   Construindo imagem Docker..." -ForegroundColor Yellow
    Write-Host "   Isso pode demorar alguns minutos..." -ForegroundColor Gray
    
    Set-Location "c:\Projetos\IFRS 16"
    gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME --project $PROJECT_ID backend/
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   Imagem construida!" -ForegroundColor Green
        
        Write-Host ""
        Write-Host "   Fazendo deploy no Cloud Run..." -ForegroundColor Yellow
        gcloud run deploy $SERVICE_NAME `
            --image gcr.io/$PROJECT_ID/$SERVICE_NAME `
            --platform managed `
            --region $REGION `
            --allow-unauthenticated `
            --project $PROJECT_ID
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "   Backend deployado!" -ForegroundColor Green
            
            # Obter URL
            $serviceUrl = gcloud run services describe $SERVICE_NAME --region $REGION --project $PROJECT_ID --format="value(status.url)"
            Write-Host "   URL: $serviceUrl" -ForegroundColor Cyan
        }
    }
}

# Resumo
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  CONFIGURACAO CONCLUIDA!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Frontend: https://ifrs16-app.web.app" -ForegroundColor Cyan
Write-Host ""
Write-Host "Proximos passos:" -ForegroundColor Yellow
Write-Host "  1. Configurar variaveis de ambiente no Cloud Run" -ForegroundColor Yellow
Write-Host "  2. Atualizar URLs no codigo" -ForegroundColor Yellow
Write-Host "  3. Testar tudo" -ForegroundColor Yellow
Write-Host ""
