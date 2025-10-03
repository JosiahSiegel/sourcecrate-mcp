# Test WSL2 Firewall Configuration
# Run this in Windows PowerShell as Administrator

Write-Host "`n=== Testing WSL2 Firewall Rules ===" -ForegroundColor Cyan

# 1. Check if firewall rules exist
Write-Host "`n1. Checking firewall rules..." -ForegroundColor Yellow
$rules = Get-NetFirewallRule -DisplayName "*WSL*" -ErrorAction SilentlyContinue
if ($rules) {
    $rules | Select-Object DisplayName, Direction, Action, Enabled | Format-Table -AutoSize
} else {
    Write-Host "   No WSL firewall rules found!" -ForegroundColor Red
}

# 2. Get WSL2 IP address from Docker Desktop WSL
Write-Host "`n2. Getting WSL2 IP address..." -ForegroundColor Yellow
Write-Host "   Available WSL distros:" -ForegroundColor Gray
wsl -l -v
Write-Host ""
# Docker Desktop uses BusyBox, query via ip command instead
$wslIpRaw = wsl -d docker-desktop sh -c "ip addr show eth0 2>/dev/null | grep 'inet ' | head -1"
if ($wslIpRaw -match 'inet\s+(\d+\.\d+\.\d+\.\d+)') {
    $wslIp = $matches[1]
    Write-Host "   Docker Desktop WSL IP (eth0): $wslIp" -ForegroundColor Green
} else {
    Write-Host "   Could not get Docker Desktop IP, using Ubuntu default" -ForegroundColor Yellow
    $wslIp = wsl hostname -I | ForEach-Object { $_.Trim().Split()[0] }
    Write-Host "   Ubuntu WSL IP: $wslIp" -ForegroundColor Green
}

# 3. Test connection to port 8000
Write-Host "`n3. Testing connection to port 8000..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://${wslIp}:8000/health" -TimeoutSec 5 -UseBasicParsing
    Write-Host "   [OK] Port 8000: SUCCESS (Status: $($response.StatusCode))" -ForegroundColor Green
    Write-Host "   Response: $($response.Content)" -ForegroundColor Gray
} catch {
    Write-Host "   [FAIL] Port 8000: FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

# 4. Test connection to port 3000
Write-Host "`n4. Testing connection to port 3000..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://${wslIp}:3000/" -TimeoutSec 5 -UseBasicParsing
    Write-Host "   [OK] Port 3000: SUCCESS (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "   [FAIL] Port 3000: FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

# 5. Test streaming endpoint
Write-Host "`n5. Testing streaming endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://${wslIp}:8000/api/v1/search/stream?query=test&limit=2" -TimeoutSec 10 -UseBasicParsing
    Write-Host "   [OK] Streaming: SUCCESS (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "   [FAIL] Streaming: FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan
Write-Host "`nIf tests failed, run these commands to add firewall rules:" -ForegroundColor Yellow
Write-Host "Remove-NetFirewallRule -DisplayName 'WSL' -ErrorAction SilentlyContinue" -ForegroundColor Gray
Write-Host "New-NetFirewallRule -DisplayName 'WSL2 Port 3000' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 3000" -ForegroundColor Gray
Write-Host "New-NetFirewallRule -DisplayName 'WSL2 Port 8000' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000" -ForegroundColor Gray
