$API_URL = "https://ifrs16-backend-1051753255664.us-central1.run.app"
$EMAIL_ADMIN = "fernandocostaxavier@gmail.com"
$PASSWORD_ADMIN = "Master@2025!"
$NEW_USER_EMAIL = "cleiton.fernandesjesus@gmail.com"
$TEMP_PASSWORD = "TempPassword123!"

# Dados que já temos da execução anterior (hardcoded para teste, ou podemos buscar)
# Licença: FX20251217-IFRS16-YX77D4IZ

Write-Host "-------------------------------------------"
Write-Host "TENTANDO ENVIAR EMAIL DE TESTE PELO BACKEND"
Write-Host "-------------------------------------------"

# Vamos usar o endpoint /api/payments/test-email encontrado no código!
# Ele envia um email com dados FIXOS (user_name="Teste", license="FX-TEST..."), 
# mas valida se o SMTP está funcionando.
# Se funcionar, significa que o sistema de email está "vivo".
# Infelizmente ele não permite customizar o corpo do email via parametros da query string (apenas o email).
# Código: async def test_email(email: str): ... send_welcome_email(to_email=email, user_name="Teste"...)

Write-Host "Sending test email to $NEW_USER_EMAIL..." -NoNewline
try {
    # Endpoint: POST /api/payments/test-email?email=XYZ
    $response = Invoke-RestMethod -Uri "$API_URL/api/payments/test-email?email=$NEW_USER_EMAIL" -Method POST -ErrorAction Stop
    
    if ($response.success) {
        Write-Host " Success!" -ForegroundColor Green
        Write-Host "   Backend sent a GENERIC test email to user." -ForegroundColor Green
        Write-Host "   Note: It contains fake data (fake password/license) as per code definition." -ForegroundColor Yellow
        Write-Host "   Wait for user to receive 'Bem-vindo ao IFRS 16' email." -ForegroundColor Gray
    }
    else {
        Write-Host " Failed!" -ForegroundColor Red
        Write-Host "   Message: $($response.message)" -ForegroundColor Red
        Write-Host "   Possible cause: SMTP credentials not valid in Cloud Run secrets." -ForegroundColor Yellow
    }
}
catch {
    Write-Host " Failed!" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader $_.Exception.Response.GetResponseStream()
        Write-Host "Detail: $($reader.ReadToEnd())" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "⚠️  IMPORTANT:"
Write-Host "The system email (if sent) contains GENERIC TEST DATA."
Write-Host "You MUST send the REAL credentials manually as requested before."
