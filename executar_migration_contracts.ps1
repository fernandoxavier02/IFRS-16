# Script para executar migration de contratos no Cloud SQL
# Requer: gcloud CLI configurado e autenticado

param(
    [string]$ProjectId = "ifrs16-app",
    [string]$InstanceName = "ifrs16-database",
    [string]$Database = "ifrs16_licenses",
    [string]$User = "ifrs16_user"
)

Write-Host "🔄 Executando migration de contratos no Cloud SQL..." -ForegroundColor Cyan
Write-Host ""

# Verificar se gcloud está instalado
try {
    gcloud --version | Out-Null
} catch {
    Write-Host "❌ Google Cloud SDK não encontrado. Instale em: https://cloud.google.com/sdk/docs/install" -ForegroundColor Red
    exit 1
}

# Verificar se está autenticado
Write-Host "Verificando autenticação..." -ForegroundColor Yellow
$authStatus = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>&1
if (-not $authStatus) {
    Write-Host "❌ Não autenticado. Execute: gcloud auth login" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Autenticado como: $authStatus" -ForegroundColor Green
Write-Host ""

# Obter senha do banco (se necessário, pode ser passada como parâmetro)
$password = Read-Host "Digite a senha do banco de dados (ou pressione Enter para usar variável de ambiente)"

if (-not $password) {
    # Tentar obter da variável de ambiente ou arquivo
    if (Test-Path "CLOUD_SQL_PASSWORD_NEW.txt") {
        $password = Get-Content "CLOUD_SQL_PASSWORD_NEW.txt" -Raw | ForEach-Object { $_.Trim() }
        Write-Host "✅ Senha obtida do arquivo CLOUD_SQL_PASSWORD_NEW.txt" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Senha não encontrada. Usando variável de ambiente DATABASE_URL" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "📦 Executando migration via Cloud SQL Proxy..." -ForegroundColor Yellow
Write-Host ""

# Opção 1: Executar migration via Cloud SQL Proxy (recomendado)
# Primeiro, verificar se o proxy está rodando ou iniciá-lo

Write-Host "Método 1: Executar migration diretamente no Cloud Run (recomendado)" -ForegroundColor Cyan
Write-Host "A migration será executada automaticamente no próximo deploy do backend." -ForegroundColor Yellow
Write-Host ""

Write-Host "Método 2: Executar migration localmente via Cloud SQL Proxy" -ForegroundColor Cyan
Write-Host "Para executar localmente, você precisa:" -ForegroundColor Yellow
Write-Host "1. Instalar Cloud SQL Proxy: https://cloud.google.com/sql/docs/postgres/sql-proxy" -ForegroundColor Gray
Write-Host "2. Iniciar proxy: cloud_sql_proxy -instances=$ProjectId`:$Region`:$InstanceName=tcp:5432" -ForegroundColor Gray
Write-Host "3. Executar: cd backend && alembic upgrade head" -ForegroundColor Gray
Write-Host ""

Write-Host "Método 3: Executar migration via Cloud Run Job (mais seguro)" -ForegroundColor Cyan
Write-Host "Criando Cloud Run Job para executar migration..." -ForegroundColor Yellow

# Criar um job temporário para executar a migration
$jobName = "run-migration-contracts-$(Get-Date -Format 'yyyyMMddHHmmss')"

Write-Host ""
Write-Host "⚠️  IMPORTANTE: A migration será executada automaticamente no próximo deploy do backend." -ForegroundColor Yellow
Write-Host "   Se você já fez o deploy, a migration já deve ter sido executada." -ForegroundColor Yellow
Write-Host ""
Write-Host "Para verificar se a tabela 'contracts' existe:" -ForegroundColor Cyan
Write-Host "  gcloud sql connect $InstanceName --user=$User --database=$Database --project=$ProjectId" -ForegroundColor Gray
Write-Host "  \dt contracts" -ForegroundColor Gray
Write-Host ""

$proceed = Read-Host "Deseja executar a migration agora via Cloud Run Job? (s/N)"
if ($proceed -eq "s" -or $proceed -eq "S") {
    Write-Host ""
    Write-Host "Criando Cloud Run Job..." -ForegroundColor Yellow
    
    # Criar job temporário
    gcloud run jobs create $jobName `
        --image gcr.io/$ProjectId/ifrs16-backend `
        --region us-central1 `
        --project $ProjectId `
        --set-env-vars "DATABASE_URL=[SUA_DATABASE_URL]" `
        --command "alembic" `
        --args "upgrade,head" `
        --max-retries 1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Job criado. Executando..." -ForegroundColor Green
        gcloud run jobs execute $jobName --region us-central1 --project $ProjectId --wait
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Migration executada com sucesso!" -ForegroundColor Green
        } else {
            Write-Host "❌ Erro ao executar migration" -ForegroundColor Red
        }
        
        # Limpar job
        Write-Host "Limpando job temporário..." -ForegroundColor Yellow
        gcloud run jobs delete $jobName --region us-central1 --project $ProjectId --quiet
    }
} else {
    Write-Host ""
    Write-Host "✅ Migration será executada no próximo deploy do backend." -ForegroundColor Green
}

Write-Host ""
Write-Host "📋 Próximos passos:" -ForegroundColor Cyan
Write-Host "1. Fazer deploy do backend: .\deploy_firebase.ps1" -ForegroundColor Yellow
Write-Host "2. Verificar se a migration foi executada" -ForegroundColor Yellow
Write-Host "3. Testar endpoints de contratos" -ForegroundColor Yellow
