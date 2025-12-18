# Script para criar usuario master no Cloud SQL
# Usa o arquivo SQL gerado e o gcloud sql connect

$PROJECT_ID = "ifrs16-app"
$DB_INSTANCE = "ifrs16-database"
$DB_NAME = "ifrs16_licenses"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  CRIANDO USUARIO MASTER (via Cloud SQL Direct)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Conectando ao Cloud SQL ($DB_NAME)..." -ForegroundColor Yellow
Write-Host "   Isso pode demorar um pouco para estabelecer o tunnel..." -ForegroundColor Yellow
Write-Host ""

# Lê o SQL gerado (precisa ler como texto para passar pro gcloud, ou via pipe)
# O problema do pipe no Windows com gcloud as vezes eh encoding.
# Vamos tentar passar o arquivo diretamente para o cliente psql dentro do gcloud se possivel,
# mas 'gcloud sql connect' abre uma sessao interativa.

# Alternativa: Usar 'gcloud sql import sql' (mas precisa estar no bucket)
# Alternativa Melhor: Usar o pipe standard input

$sqlFile = "backend/insert_master_final.sql"

if (-not (Test-Path $sqlFile)) {
    Write-Host "ERRO: Arquivo $sqlFile nao encontrado." -ForegroundColor Red
    exit 1
}

Write-Host "   Executando SQL..." -ForegroundColor Cyan
Get-Content $sqlFile | Write-Host -ForegroundColor Gray

# No Windows PowerShell, o pipe pro gcloud sql connect as vezes falha em ser non-interactive.
# Mas vamos tentar:
Get-Content $sqlFile | gcloud sql connect $DB_INSTANCE --user=postgres --quiet --database=$DB_NAME

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "   Comando enviado com sucesso!" -ForegroundColor Green
    Write-Host "   (Verifique acima se houve erro de SQL)" -ForegroundColor Yellow
}
else {
    Write-Host ""
    Write-Host "   ERRO ao conectar/executar." -ForegroundColor Red
    Write-Host "   Tente rodar manualmente: gcloud sql connect $DB_INSTANCE --user=postgres" -ForegroundColor Yellow
}
