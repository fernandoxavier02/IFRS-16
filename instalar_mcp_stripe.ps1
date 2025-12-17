# Script to install and configure Stripe MCP
# Fixed JSON handling

Write-Host "Configuring Stripe MCP for Cursor..." -ForegroundColor Cyan

# 1. Verify NPM
Write-Host "1. Verifying NPM..." -ForegroundColor Yellow
try {
    npm --version | Out-Null
    Write-Host "   NPM is installed." -ForegroundColor Green
}
catch {
    Write-Host "   NPM not found. Please install Node.js." -ForegroundColor Red
    exit 1
}

# 2. Cursor directory
Write-Host "2. Configuring .cursor directory..." -ForegroundColor Yellow
$cursorDir = ".cursor"
if (-not (Test-Path $cursorDir)) {
    New-Item -ItemType Directory -Path $cursorDir | Out-Null
    Write-Host "   Directory created." -ForegroundColor Green
}
else {
    Write-Host "   Directory exists." -ForegroundColor Green
}

# Helper function to safely update mcp config
function Update-McpConfig {
    param (
        [string]$Path
    )
    
    $servers = @{}
    
    if (Test-Path $Path) {
        try {
            $json = Get-Content $Path -Raw | ConvertFrom-Json
            if ($json.mcpServers) {
                # Convert PSObject to Hashtable
                foreach ($prop in $json.mcpServers.PSObject.Properties) {
                    $servers[$prop.Name] = $prop.Value
                }
            }
        }
        catch {
            Write-Host "   Warning: Could not read existing config at $Path" -ForegroundColor Yellow
        }
    }
    
    # Add/Update Stripe
    $servers["stripe"] = @{
        command = "npx"
        args    = @("-y", "@stripe/mcp")
    }
    
    # Save
    $finalConfig = @{ mcpServers = $servers }
    $jsonContent = $finalConfig | ConvertTo-Json -Depth 10
    $jsonContent | Out-File -FilePath $Path -Encoding ASCII
    Write-Host "   Updated $Path" -ForegroundColor Green
}

# 3. Update mcp.json
Write-Host "3. Updating mcp.json for Stripe..." -ForegroundColor Yellow
$mcpPath = Join-Path $cursorDir "mcp.json"
Update-McpConfig -Path $mcpPath

# 4. Global configuration
Write-Host "4. Global configuration..." -ForegroundColor Yellow
$globalMcpPath = "$env:APPDATA\Cursor\User\mcp.json"
$globalMcpDir = Split-Path $globalMcpPath -Parent

if (-not (Test-Path $globalMcpDir)) {
    New-Item -ItemType Directory -Path $globalMcpDir -Force | Out-Null
}
Update-McpConfig -Path $globalMcpPath

# 5. Final instructions
Write-Host ""
Write-Host "Configuration complete!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Stripe MCP will ask for API Key on first run." -ForegroundColor Yellow
Write-Host "2. Restart Cursor to load the new MCP server." -ForegroundColor Yellow
