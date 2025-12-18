$API_URL = "https://ifrs16-backend-1051753255664.us-central1.run.app"
$EMAIL_ADMIN = "fernandocostaxavier@gmail.com"
$PASSWORD_ADMIN = "Master@2025!"
$TARGET_EMAIL = "teste@correcao.com"

Write-Host "-------------------------------------------"
Write-Host "DELETING USER: $TARGET_EMAIL"
Write-Host "-------------------------------------------"

# 1. Login Admin
Write-Host "Authenticating as Admin..." -NoNewline
$loginBody = @{
    email    = $EMAIL_ADMIN
    password = $PASSWORD_ADMIN
}

try {
    $loginResponse = Invoke-RestMethod -Uri "$API_URL/api/auth/admin/login" -Method POST -Body ($loginBody | ConvertTo-Json) -ContentType "application/json" -ErrorAction Stop
    $token = $loginResponse.access_token
    Write-Host " Success!" -ForegroundColor Green
}
catch {
    Write-Host " Failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. Get User ID
Write-Host "Searching for user..."
$headers = @{
    Authorization = "Bearer $token"
}

try {
    $usersResponse = Invoke-RestMethod -Uri "$API_URL/api/admin/users" -Method GET -Headers $headers -ErrorAction Stop
    
    $targetUser = $usersResponse.users | Where-Object { $_.email -eq $TARGET_EMAIL }
    
    if ($targetUser) {
        $userId = $targetUser.id
        Write-Host "   User found: $($targetUser.name)" -ForegroundColor Green
        Write-Host "   ID: $userId" -ForegroundColor Cyan
        
        # 3. Delete User
        Write-Host ""
        Write-Host "Deleting user..." -NoNewline
        try {
            $deleteResponse = Invoke-RestMethod -Uri "$API_URL/api/admin/users/$userId" -Method DELETE -Headers $headers -ErrorAction Stop
            Write-Host " DONE!" -ForegroundColor Green
            Write-Host "   Message: $($deleteResponse.message)" -ForegroundColor Gray
        }
        catch {
            Write-Host " FAILED!" -ForegroundColor Red
            Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
            if ($_.Exception.Response) {
                $reader = New-Object System.IO.StreamReader $_.Exception.Response.GetResponseStream()
                Write-Host "   Detail: $($reader.ReadToEnd())" -ForegroundColor Yellow
            }
        }
        
    }
    else {
        Write-Host "User with email '$TARGET_EMAIL' not found." -ForegroundColor Red
    }
    
}
catch {
    Write-Host "Error searching users: $($_.Exception.Message)" -ForegroundColor Red
}
