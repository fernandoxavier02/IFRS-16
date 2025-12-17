# Script para criar e configurar Cloud SQL PostgreSQL

$PROJECT_ID = "ifrs16-app"
$INSTANCE_NAME = "ifrs16-database"
$REGION = "us-central1"  # ou southamerica-east1 para Sao Paulo
$DATABASE_NAME = "ifrs16_licenses"
$DB_USER = "ifrs16_user"
$DB_PASSWORD = ""  # Será solicitado ou gerado

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  CONFIGURAR CLOUD SQL POSTGRESQL" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se gcloud está instalado
try {
    gcloud --version | Out-Null
} catch {
    Write-Host "ERRO: Google Cloud SDK nao encontrado!" -ForegroundColor Red
    Write-Host "Instale em: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# Verificar se está logado
Write-Host "Verificando autenticacao..." -ForegroundColor Yellow
$auth = gcloud auth list --filter=status:ACTIVE --format="value(account)"
if (-not $auth) {
    Write-Host "ERRO: Nao esta logado no gcloud!" -ForegroundColor Red
    Write-Host "Execute: gcloud auth login" -ForegroundColor Yellow
    exit 1
}
Write-Host "Autenticado como: $auth" -ForegroundColor Green

# Configurar projeto
Write-Host ""
Write-Host "Configurando projeto..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID

# Habilitar APIs
Write-Host ""
Write-Host "Habilitando APIs necessarias..." -ForegroundColor Yellow
gcloud services enable sqladmin.googleapis.com --project $PROJECT_ID

# Verificar se instância já existe
Write-Host ""
Write-Host "Verificando se instancia ja existe..." -ForegroundColor Yellow
$existing = gcloud sql instances describe $INSTANCE_NAME --project $PROJECT_ID 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "Instancia ja existe!" -ForegroundColor Yellow
    Write-Host "Deseja recriar? (s/N): " -NoNewline
    $recreate = Read-Host
    if ($recreate -ne 's') {
        Write-Host "Usando instancia existente" -ForegroundColor Green
        exit 0
    }
    Write-Host "Deletando instancia existente..." -ForegroundColor Yellow
    gcloud sql instances delete $INSTANCE_NAME --project $PROJECT_ID --quiet
}

# Gerar senha se não fornecida
if (-not $DB_PASSWORD) {
    Write-Host ""
    Write-Host "Gerando senha forte..." -ForegroundColor Yellow
    $DB_PASSWORD = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 16 | ForEach-Object {[char]$_})
    Write-Host "Senha gerada (SALVE ESTA SENHA!): $DB_PASSWORD" -ForegroundColor Cyan
    Write-Host ""
}

# Criar instância
Write-Host "Criando instancia Cloud SQL..." -ForegroundColor Yellow
Write-Host "Isso pode demorar 5-10 minutos..." -ForegroundColor Gray

gcloud sql instances create $INSTANCE_NAME `
    --database-version=POSTGRES_15 `
    --tier=db-f1-micro `
    --region=$REGION `
    --root-password=$DB_PASSWORD `
    --project=$PROJECT_ID

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Instancia criada com sucesso!" -ForegroundColor Green
    
    # Criar database
    Write-Host ""
    Write-Host "Criando database..." -ForegroundColor Yellow
    gcloud sql databases create $DATABASE_NAME --instance=$INSTANCE_NAME --project=$PROJECT_ID
    
    # Criar usuário
    Write-Host ""
    Write-Host "Criando usuario do banco..." -ForegroundColor Yellow
    gcloud sql users create $DB_USER --instance=$INSTANCE_NAME --password=$DB_PASSWORD --project=$PROJECT_ID
    
    # Obter IP público
    Write-Host ""
    Write-Host "Obtendo informacoes de conexao..." -ForegroundColor Yellow
    $connectionName = gcloud sql instances describe $INSTANCE_NAME --format="value(connectionName)" --project=$PROJECT_ID
    $ipAddress = gcloud sql instances describe $INSTANCE_NAME --format="value(ipAddresses[0].ipAddress)" --project=$PROJECT_ID
    
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  CLOUD SQL CONFIGURADO!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Connection Name: $connectionName" -ForegroundColor Cyan
    Write-Host "IP Publico: $ipAddress" -ForegroundColor Cyan
    Write-Host "Database: $DATABASE_NAME" -ForegroundColor Cyan
    Write-Host "User: $DB_USER" -ForegroundColor Cyan
    Write-Host "Password: $DB_PASSWORD" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "DATABASE_URL (para Cloud Run):" -ForegroundColor Yellow
    Write-Host "postgresql://$DB_USER`:$DB_PASSWORD@/$DATABASE_NAME?host=/cloudsql/$connectionName" -ForegroundColor Gray
    Write-Host ""
    Write-Host "DATABASE_URL (para conexao direta):" -ForegroundColor Yellow
    Write-Host "postgresql://$DB_USER`:$DB_PASSWORD@$ipAddress:5432/$DATABASE_NAME" -ForegroundColor Gray
    Write-Host ""
    Write-Host "SALVE ESTAS INFORMACOES!" -ForegroundColor Red
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "ERRO ao criar instancia" -ForegroundColor Red
    exit 1
}
