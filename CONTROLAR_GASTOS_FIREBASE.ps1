param(
    [string]$ProjectId = "ifrs16-app",
    [string]$Region = "us-central1",
    [string]$CloudRunServiceName = "ifrs16-backend",

    # Orçamento mensal (na moeda do billing account)
    [decimal]$BudgetAmount = 50,
    [string]$BudgetDisplayName = "IFRS16 - Orçamento Mensal",

    # Limite de custo por pico (Cloud Run)
    [int]$MaxInstances = 2
)

$ErrorActionPreference = "Stop"

$GCLOUD = "C:\Users\Mazars\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"

function Assert-CommandExists {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        throw "gcloud não encontrado em: $Path. Abra o Google Cloud SDK Shell ou ajuste o caminho no script."
    }
}

function Get-BillingAccountId {
    param([string]$ProjectId)

    $billingName = & $GCLOUD billing projects describe $ProjectId --format="value(billingAccountName)" 2>$null
    if (-not $billingName) {
        throw "O projeto '$ProjectId' não está vinculado a um Billing Account. Vincule em: https://console.cloud.google.com/billing?project=$ProjectId"
    }

    # Ex: billingAccounts/01A1B2-3C4D5E-6F7G8H
    return ($billingName -replace "^billingAccounts/", "")
}

function Ensure-BudgetsApiEnabled {
    param([string]$ProjectId)
    & $GCLOUD services enable billingbudgets.googleapis.com --project $ProjectId | Out-Null
}

function Ensure-Budget {
    param(
        [string]$BillingAccountId,
        [string]$ProjectId,
        [string]$BudgetDisplayName,
        [decimal]$BudgetAmount
    )

    # Se já existir budget com o mesmo nome, não cria outro.
    $existing = & $GCLOUD billing budgets list --billing-account $BillingAccountId --format="value(displayName)" 2>$null
    if ($existing -and ($existing -contains $BudgetDisplayName)) {
        Write-Host "✅ Budget já existe: '$BudgetDisplayName'" -ForegroundColor Green
        return
    }

    Write-Host "Criando budget '$BudgetDisplayName' (mensal) no valor de $BudgetAmount..." -ForegroundColor Yellow

    # Regras de alerta: 50%, 80%, 100% do gasto atual + 90% previsto
    & $GCLOUD billing budgets create `
        --billing-account $BillingAccountId `
        --display-name "$BudgetDisplayName" `
        --budget-amount "$BudgetAmount" `
        --calendar-period month `
        --filter-projects "projects/$ProjectId" `
        --threshold-rule percent=0.50 `
        --threshold-rule percent=0.80 `
        --threshold-rule percent=1.00 `
        --threshold-rule percent=0.90,basis=forecasted-spend `
        --disable-default-iam-recipients=false | Out-Null

    Write-Host "✅ Budget criado!" -ForegroundColor Green
    Write-Host "Dica: para adicionar emails específicos, crie 'Notification Channels' no Cloud Monitoring e associe no budget." -ForegroundColor Gray
}

function Apply-CloudRunLimits {
    param(
        [string]$ProjectId,
        [string]$Region,
        [string]$ServiceName,
        [int]$MaxInstances
    )

    Write-Host "Aplicando limite de escala no Cloud Run: max-instances=$MaxInstances" -ForegroundColor Yellow

    & $GCLOUD run services update $ServiceName `
        --project $ProjectId `
        --region $Region `
        --max-instances $MaxInstances | Out-Null

    Write-Host "✅ Cloud Run atualizado (max-instances=$MaxInstances)." -ForegroundColor Green
}

# ==========================
# Execução
# ==========================

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  CONTROLE DE GASTOS (Firebase/GCP)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Assert-CommandExists -Path $GCLOUD

Write-Host "Projeto: $ProjectId" -ForegroundColor White

# 1) Descobrir Billing Account
$billingAccountId = Get-BillingAccountId -ProjectId $ProjectId
Write-Host "Billing Account: $billingAccountId" -ForegroundColor White

# 2) Garantir API e criar budget
Ensure-BudgetsApiEnabled -ProjectId $ProjectId
Ensure-Budget -BillingAccountId $billingAccountId -ProjectId $ProjectId -BudgetDisplayName $BudgetDisplayName -BudgetAmount $BudgetAmount

# 3) Limitar escala no Cloud Run
Apply-CloudRunLimits -ProjectId $ProjectId -Region $Region -ServiceName $CloudRunServiceName -MaxInstances $MaxInstances

Write-Host "" 
Write-Host "Links úteis:" -ForegroundColor Cyan
Write-Host "- Budget: https://console.cloud.google.com/billing/$billingAccountId/budgets?project=$ProjectId" -ForegroundColor Gray
Write-Host "- Billing: https://console.cloud.google.com/billing?project=$ProjectId" -ForegroundColor Gray
Write-Host "- Cloud Run: https://console.cloud.google.com/run/detail/$Region/$CloudRunServiceName/metrics?project=$ProjectId" -ForegroundColor Gray
Write-Host "" 
Write-Host "✅ Controle de gastos aplicado." -ForegroundColor Green
