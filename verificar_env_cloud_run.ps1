
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  VERIFICAÇÃO DE VARIÁVEIS DE AMBIENTE (CLOUD RUN)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar gcloud
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "❌ FERRAMENTA GCLOUD NÃO ENCONTRADA!" -ForegroundColor Red
    Write-Host "Não consigo verificar as variáveis automaticamente sem o 'gcloud CLI'." -ForegroundColor Gray
    Write-Host ""
    Write-Host "POR FAVOR, EXECUTE O SEGUINTE COMANDO NO SEU TERMINAL (ONDE O GCLOUD ESTÁ INSTALADO):" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "gcloud run services describe ifrs16-backend --region us-central1 --project ifrs16-app" -ForegroundColor White
    Write-Host ""
    Write-Host "Verifique se as seguintes variáveis aparecem na seção 'env':" -ForegroundColor Cyan
    Write-Host "  - DATABASE_URL" -ForegroundColor Gray
    Write-Host "  - STRIPE_SECRET_KEY" -ForegroundColor Gray
    Write-Host "  - STRIPE_WEBHOOK_SECRET" -ForegroundColor Gray
    Write-Host "  - STRIPE_PUBLISHABLE_KEY" -ForegroundColor Gray
    Write-Host "  - ADMIN_TOKEN" -ForegroundColor Gray
    exit
}

Write-Host "🔄 Verificando configurações no Cloud Run..." -ForegroundColor Yellow

try {
    $config = gcloud run services describe ifrs16-backend --region us-central1 --project ifrs16-app --format="json" | ConvertFrom-Json
    
    if (-not $config) {
        throw "Não foi possível obter a configuração."
    }

    $envVars = $config.spec.template.spec.containers[0].env
    
    $requiredVars = @(
        "DATABASE_URL", 
        "STRIPE_SECRET_KEY", 
        "STRIPE_WEBHOOK_SECRET", 
        "STRIPE_PUBLISHABLE_KEY",
        "JWT_SECRET_KEY"
    )

    $missingVars = @()
    $foundVars = @()

    foreach ($req in $requiredVars) {
        $found = $envVars | Where-Object { $_.name -eq $req }
        if ($found) {
            $val = $found.value
            if ($req -like "*KEY*" -or $req -like "*SECRET*" -or $req -like "*TOKEN*" -or $req -like "*URL*") {
                $val = "****************" + ($val.Substring($val.Length - 4) -replace ".*(.{4})", '$1')
            }
            $foundVars += [PSCustomObject]@{ Name = $req; Value = $val; Status = "OK" }
        }
        else {
            $missingVars += $req
        }
    }

    Write-Host ""
    Write-Host "✅ VARIÁVEIS ENCONTRADAS:" -ForegroundColor Green
    $foundVars | Format-Table -AutoSize

    if ($missingVars.Count -gt 0) {
        Write-Host ""
        Write-Host "❌ VARIÁVEIS FALTANDO:" -ForegroundColor Red
        foreach ($missing in $missingVars) {
            Write-Host "  - $missing" -ForegroundColor Red
        }
        Write-Host ""
        Write-Host "⚠️  ATENÇÃO: O sistema pode não funcionar corretamente sem essas variáveis." -ForegroundColor Yellow
        Write-Host "Use o script 'deploy_firebase.ps1' ou o painel do Google Cloud para configurá-las." -ForegroundColor Gray
    }
    else {
        Write-Host ""
        Write-Host "🎉 Todas as variáveis críticas parecem estar configuradas!" -ForegroundColor Green
    }

}
catch {
    Write-Host "❌ Erro ao verificar: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Tente rodar manualmente: gcloud run services describe ifrs16-backend --region us-central1" -ForegroundColor Yellow
}
