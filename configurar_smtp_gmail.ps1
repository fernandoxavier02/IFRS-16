#############################################################
# Script para atualizar credenciais SMTP no Cloud Run
# 
# ATENÇÃO: NÃO COMMITE ESTA SENHA. EU VOU PEDIR ELA NO PROMPT.
#############################################################

# 1. Definir variáveis fixas
$SERVICE = "ifrs16-backend"
$REGION = "us-central1"
$SMTP_USER = "fernandocostaxavier@gmail.com"
$SMTP_HOST = "smtp.gmail.com"
$SMTP_PORT = "587"
$SMTP_FROM_EMAIL = "fernandocostaxavier@gmail.com"
$SMTP_FROM_NAME = "Equipe IFRS 16"

Write-Host "Configurando envio de e-mail via GMAIL ($SMTP_USER)..." -ForegroundColor Cyan
Write-Host "IMPORTANTE: Voce precisa ter uma SENHA DE APP (App Password) do Google." -ForegroundColor Yellow
Write-Host "Senha normal nao funciona se tiver 2FA ativado." -ForegroundColor Yellow
Write-Host ""
$SMTP_PASS = Read-Host -Prompt "Cole aqui sua SENHA DE APP do Google (ex: xxxx xxxx xxxx xxxx)"

if (-not $SMTP_PASS) {
    Write-Host "Senha vazia. Abortando." -ForegroundColor Red
    exit 1
}

# 2. Atualizar Cloud Run
# Precisamos manter as variáveis existentes e adicionar/atualizar estas.
# O gcloud update-env-vars faz merge, então não apaga as outras.

Write-Host ""
Write-Host "Atualizando variáveis no Cloud Run... aguarde..." -ForegroundColor Cyan

# Tentar encontrar gcloud no PATH
$gcloud_cmd = "gcloud"
try {
    # Tenta executar apenas 'gcloud' para ver se está no PATH
    Invoke-Expression "gcloud --version" | Out-Null
    Write-Host "   ✅ gcloud encontrado no PATH" -ForegroundColor Green
}
catch {
    # Fallback para caminho comum se não estiver no PATH
    $gcloud_local = "$env:LOCALAPPDATA\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
    if (Test-Path $gcloud_local) {
        $gcloud_cmd = "& `"$gcloud_local`""
        Write-Host "   ✅ gcloud encontrado em LOCALAPPDATA" -ForegroundColor Green
    }
    else {
        Write-Host "   ❌ gcloud CLI não encontrada! Instale o Google Cloud SDK." -ForegroundColor Red
        exit 1
    }
}

# Comando gcloud para atualizar
# Nota: update-env-vars reinicia o serviço (cria nova revisão)
$cmd_str = "$gcloud_cmd run services update $SERVICE --project=ifrs16-app --region=$REGION --update-env-vars `"SMTP_HOST=$SMTP_HOST,SMTP_PORT=$SMTP_PORT,SMTP_USER=$SMTP_USER,SMTP_PASSWORD=$SMTP_PASS,SMTP_FROM_EMAIL=$SMTP_FROM_EMAIL,SMTP_FROM_NAME=$SMTP_FROM_NAME`""

Invoke-Expression $cmd_str

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ SUCESSO! Cloud Run atualizado com credenciais de email." -ForegroundColor Green
    Write-Host "Agora o sistema deve conseguir enviar emails." -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "❌ ERRO ao atualizar Cloud Run." -ForegroundColor Red
}
