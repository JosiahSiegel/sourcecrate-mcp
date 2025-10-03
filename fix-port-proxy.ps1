# Fix WSL2 Port Proxies with Correct IP
# Run as Administrator in Windows PowerShell

$ErrorActionPreference = "Stop"

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  WSL2 Port Proxy Fix" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# Get the correct WSL IP from docker-desktop instance
Write-Host "Getting WSL IP from docker-desktop..." -NoNewline
$wslIpRaw = wsl -d docker-desktop sh -c "ip addr show eth0 | grep 'inet ' | head -1"
if ($wslIpRaw -match 'inet\s+(\d+\.\d+\.\d+\.\d+)') {
    $wslIp = $matches[1]
    Write-Host " [OK]" -ForegroundColor Green
    Write-Host "WSL IP: $wslIp" -ForegroundColor Green
} else {
    Write-Host " [FAIL]" -ForegroundColor Red
    Write-Host "Could not detect WSL IP, using default: 192.168.65.3" -ForegroundColor Yellow
    $wslIp = "192.168.65.3"
}

Write-Host "`nStep 1: Remove existing port proxies" -ForegroundColor Yellow
Write-Host "-------------------------------------" -ForegroundColor Gray

$existingProxies = netsh interface portproxy show all
if ($existingProxies -match "8000" -or $existingProxies -match "3000") {
    Write-Host "Removing port 8000..." -NoNewline
    try {
        netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0 2>$null
        Write-Host " [OK]" -ForegroundColor Green
    } catch {
        Write-Host " [SKIP]" -ForegroundColor Yellow
    }

    Write-Host "Removing port 3000..." -NoNewline
    try {
        netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0 2>$null
        Write-Host " [OK]" -ForegroundColor Green
    } catch {
        Write-Host " [SKIP]" -ForegroundColor Yellow
    }
} else {
    Write-Host "No existing port proxies found" -ForegroundColor Gray
}

Write-Host "`nStep 2: Create new port proxies with correct IP" -ForegroundColor Yellow
Write-Host "------------------------------------------------" -ForegroundColor Gray

Write-Host "Creating port proxy: 8000 -> ${wslIp}:8000..." -NoNewline
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$wslIp
Write-Host " [OK]" -ForegroundColor Green

Write-Host "Creating port proxy: 3000 -> ${wslIp}:3000..." -NoNewline
netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=$wslIp
Write-Host " [OK]" -ForegroundColor Green

Write-Host "`nStep 3: Verify port proxies" -ForegroundColor Yellow
Write-Host "----------------------------" -ForegroundColor Gray

$proxies = netsh interface portproxy show all
Write-Host $proxies -ForegroundColor Gray

Write-Host "`nStep 4: Test connection from Windows" -ForegroundColor Yellow
Write-Host "-------------------------------------" -ForegroundColor Gray

Write-Host "Testing localhost:8000/health..." -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host " [OK]" -ForegroundColor Green
        Write-Host "Response: $($response.Content)" -ForegroundColor Gray
    } else {
        Write-Host " [FAIL] Status: $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host " [FAIL]" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  Results" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

Write-Host "Port proxies configured for WSL IP: $wslIp" -ForegroundColor Green
Write-Host "Browser UI: http://localhost:3000" -ForegroundColor Cyan
Write-Host "API Server: http://localhost:8000" -ForegroundColor Cyan
Write-Host "`nNote: Port proxies persist until you run 'netsh interface portproxy reset'" -ForegroundColor Yellow
Write-Host "      or until WSL IP changes (after restart)" -ForegroundColor Yellow

Write-Host "`n============================================`n" -ForegroundColor Cyan
