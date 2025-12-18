# Script to install and configure Google Cloud MCP
# Handles JSON config and gcloud CLI installation

Write-Host "Configuring Google Cloud MCP..." -ForegroundColor Cyan

# 1. Update MCP Config (Both Local and Global)
function Update-McpConfig {
    param (
        [string]$Path,
        [string]$ServerName,
        [string]$Package
    )
    
    $config = @{ mcpServers = @{} }
    
    if (Test-Path $Path) {
        try {
            $json = Get-Content $Path -Raw | ConvertFrom-Json
            if ($json.mcpServers) {
                foreach ($prop in $json.mcpServers.PSObject.Properties) {
                    $config.mcpServers[$prop.Name] = $prop.Value
                }
            }
        }
        catch {
            Write-Host "   Warning: Could not read $Path" -ForegroundColor Yellow
        }
    }
    
    # Configure GCP MCP
    $config.mcpServers[$ServerName] = @{
        command = "npx"
        args    = @("-y", $Package)
    }
    
    # Save
    $jsonContent = $config | ConvertTo-Json -Depth 10
    $jsonContent | Out-File -FilePath $Path -Encoding ASCII
    Write-Host "   Updated $Path" -ForegroundColor Green
}

# Update Local .cursor/mcp.json
$localDir = ".cursor"
if (-not (Test-Path $localDir)) { New-Item -ItemType Directory -Path $localDir | Out-Null }
Update-McpConfig -Path "$localDir\mcp.json" -ServerName "gcloud" -Package "@google-cloud/gcloud-mcp"

# Update Global Config
$globalPath = "$env:APPDATA\Cursor\User\mcp.json"
$globalDir = Split-Path $globalPath -Parent
if (-not (Test-Path $globalDir)) { New-Item -ItemType Directory -Path $globalDir -Force | Out-Null }
Update-McpConfig -Path $globalPath -ServerName "gcloud" -Package "@google-cloud/gcloud-mcp"

# 2. Check and Install gcloud CLI
Write-Host "Checking for gcloud CLI..." -ForegroundColor Yellow
$gcloudInstalled = $false
try {
    $null = Get-Command "gcloud" -ErrorAction Stop
    $gcloudInstalled = $true
    Write-Host "   gcloud is already installed." -ForegroundColor Green
}
catch {
    Write-Host "   gcloud not found in PATH." -ForegroundColor Yellow
}

if (-not $gcloudInstalled) {
    Write-Host "Attempting to install Google Cloud SDK via Winget..." -ForegroundColor Cyan
    try {
        # Using winget to install
        Start-Process winget -ArgumentList "install Google.CloudSDK --accept-source-agreements --accept-package-agreements --silent" -Wait -NoNewWindow
        Write-Host "   Installation command finished." -ForegroundColor Green
        Write-Host "   NOTE: You may need to restart your terminal/Cursor to use gcloud." -ForegroundColor Yellow
    }
    catch {
        Write-Host "   Failed to run winget: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Config Complete!" -ForegroundColor Green
Write-Host "1. Restart Cursor to load the new MCP server." -ForegroundColor Yellow
Write-Host "2. Ensure you run 'gcloud auth login' if you haven't already." -ForegroundColor Yellow
