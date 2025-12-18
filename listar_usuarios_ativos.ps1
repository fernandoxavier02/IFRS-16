$API_URL = "https://ifrs16-backend-1051753255664.us-central1.run.app"
$EMAIL = "fernandocostaxavier@gmail.com"
$PASSWORD = "Master@2025!"

Write-Host "-------------------------------------------"
Write-Host "LISTAR USUARIOS ATIVOS (Cloud Run)"
Write-Host "-------------------------------------------"

# 1. Login Admin
Write-Host "Login Admin..." -NoNewline
$loginBody = @{
    email    = $EMAIL
    password = $PASSWORD
}

try {
    $loginResponse = Invoke-RestMethod -Uri "$API_URL/api/auth/admin/login" -Method POST -Body ($loginBody | ConvertTo-Json) -ContentType "application/json" -ErrorAction Stop
    $token = $loginResponse.access_token
    Write-Host " Success!" -ForegroundColor Green
}
catch {
    Write-Host " Failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader $_.Exception.Response.GetResponseStream()
        Write-Host "Detail: $($reader.ReadToEnd())" -ForegroundColor Yellow
    }
    exit 1
}

# 2. List Users
Write-Host "Fetching active users..."
$headers = @{
    Authorization = "Bearer $token"
}

try {
    $usersResponse = Invoke-RestMethod -Uri "$API_URL/api/admin/users?is_active=true" -Method GET -Headers $headers -ErrorAction Stop
    
    if ($usersResponse.users -and $usersResponse.users.Count -gt 0) {
        Write-Host ""
        Write-Host "Total found: $($usersResponse.total)" -ForegroundColor Cyan
        Write-Host ""
        
        $usersResponse.users | Select-Object name, email, is_active, created_at | Format-Table -AutoSize
        
        Write-Host "Done." -ForegroundColor Green
    }
    else {
        Write-Host "No active users found." -ForegroundColor Yellow
    }
}
catch {
    Write-Host "Error fetching users: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader $_.Exception.Response.GetResponseStream()
        Write-Host "Detail: $($reader.ReadToEnd())" -ForegroundColor Yellow
    }
}
