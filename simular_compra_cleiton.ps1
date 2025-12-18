$API_URL = "https://ifrs16-backend-1051753255664.us-central1.run.app"
$EMAIL_ADMIN = "fernandocostaxavier@gmail.com"
$PASSWORD_ADMIN = "Master@2025!"
$NEW_USER_EMAIL = "cleiton.fernandesjesus@gmail.com"
$NEW_USER_NAME = "Cleiton Fernandes Jesus"
$CC_EMAIL = "fernandocostaxavier@gmail.com"
$TEMP_PASSWORD = "TempPassword123!"

Write-Host "-------------------------------------------"
Write-Host "SIMULACAO DE COMPRA - RETRY"
Write-Host "-------------------------------------------"

# 1. Obter Token Admin
Write-Host "1. Admin Authentication..." -NoNewline
try {
    $loginBody = @{ email = $EMAIL_ADMIN; password = $PASSWORD_ADMIN }
    $loginRes = Invoke-RestMethod -Uri "$API_URL/api/auth/admin/login" -Method POST -Body ($loginBody | ConvertTo-Json) -ContentType "application/json"
    $token = $loginRes.access_token
    Write-Host " Success!" -ForegroundColor Green
}
catch {
    Write-Host " Failed!" -ForegroundColor Red
    exit 1
}

# 2. Verificar/Criar Usuário
Write-Host "2. Getting User ID..." -NoNewline
try {
    # Buscar lista de usuários e filtrar
    $usersRes = Invoke-RestMethod -Uri "$API_URL/api/admin/users" -Method GET -Headers @{Authorization = "Bearer $token" }
    $existing = $usersRes.users | Where-Object { $_.email -eq $NEW_USER_EMAIL }
    
    if ($existing) {
        $userId = $existing.id
        Write-Host " Found existing: $userId" -ForegroundColor Yellow
    }
    else {
        # Criar via endpoint público
        Write-Host " Creating new..." -NoNewline
        $registerBody = @{
            name     = $NEW_USER_NAME
            email    = $NEW_USER_EMAIL
            password = $TEMP_PASSWORD
        }
        $regRes = Invoke-RestMethod -Uri "$API_URL/api/auth/register" -Method POST -Body ($registerBody | ConvertTo-Json) -ContentType "application/json"
        $userId = $regRes.id
        Write-Host " Created: $userId" -ForegroundColor Green
    }
}
catch {
    Write-Host " Failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 3. Conceder Licença (Tentando APENAS com duration_months, sem license_type se o enum estiver falhando na conversão via query param)
# Validando schemas.py: 
# grant_license_to_user(..., license_type: LicenseStatusEnum = Query(LicenseStatusEnum.ACTIVE), duration_months: Optional[int] = Query(None, ge=1, le=120))
# WAIT! The parameter is called 'license_type' but the TYPE hint is `LicenseStatusEnum` (default ACTIVE).
# In models.py `License` model has `license_type` as `LicenseType` enum (trial, basic, pro, enterprise).
# In `admin.py`: 
# 490:    license_type: LicenseStatusEnum = Query(LicenseStatusEnum.ACTIVE),
# 534:        license_type=LicenseType.PRO,  # Licenças manuais são PRO por padrão
#
# BUG CRÍTICO DETECTADO NO BACKEND:
# O endpoint `grant_license_to_user` recebe `license_type` como argumento, mas a tipagem (e default) é `LicenseStatusEnum` (active, suspended...),
# E no corpo da função ele IGNORA esse argumento e hardcoda `LicenseType.PRO` na linha 534!
#
# Isso significa que:
# 1. Eu NÃO consigo criar licença "Enterprise" via este endpoint manual. Ele sempre cria PRO.
# 2. O erro 422 Unknown provavelmente acontece porque eu estou passando "enterprise" (string), mas o FastAPI espera um valor do enum `LicenseStatusEnum` (active, suspended...), pois a assinatura da função está ERRADA.

Write-Host "3. Granting License (WORKAROUND)..." 
Write-Host "   ⚠ Backend bug detected: Admin endpoint forces 'PRO' and expects 'Status' enum in 'Type' param." -ForegroundColor Yellow
Write-Host "   Sending default valid request to get a PRO license first..." -NoNewline

try {
    # Não passamos license_type pois ele espera status enum (bizarro) e ignora anyway.
    # Passamos apenas duration.
    $grantUrl = "$API_URL/api/admin/users/$userId/grant-license?duration_months=12"
    $grantRes = Invoke-RestMethod -Uri $grantUrl -Method POST -Headers @{Authorization = "Bearer $token" } -ErrorAction Stop
    $licenseKey = $grantRes.license_key
    Write-Host " Success! (Created PRO license)" -ForegroundColor Green
    
    # AGORA precisamos hackear/update para Enterprise? 
    # Não tem endpoint de update de licença exposto no admin.py :(
    # Apenas revoke, reactivate, delete.
    
    Write-Host "   ⚠ License created is PRO (Backend limitation)." -ForegroundColor Yellow
}
catch {
    Write-Host " Failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader $_.Exception.Response.GetResponseStream()
        Write-Host "Detail: $($reader.ReadToEnd())" -ForegroundColor Yellow
    }
    exit 1
}

Write-Host ""
Write-Host "========================== EMAIL INFO ==========================" -ForegroundColor Cyan
Write-Host "To: $NEW_USER_EMAIL"
Write-Host "CC: $CC_EMAIL"
Write-Host "Subject: Acesso Liberado"
Write-Host ""
Write-Host "Link: https://ifrs16-app.web.app/login.html"
Write-Host "Email: $NEW_USER_EMAIL"
Write-Host "Password: $TEMP_PASSWORD"
Write-Host "License: $licenseKey"
Write-Host "Plan: PRO (Manual Grant Limitation)"
Write-Host "================================================================" -ForegroundColor Cyan
