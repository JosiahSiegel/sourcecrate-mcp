# Fix Windows Firewall for WSL2 Docker Desktop
# Run as Administrator

Write-Host "`n=== Fixing WSL2 Firewall Rules ===" -ForegroundColor Cyan

# Remove old incorrect rules
Write-Host "`n1. Removing old port-based rules..." -ForegroundColor Yellow
Get-NetFirewallRule -DisplayName "*WSL2 Port*" -ErrorAction SilentlyContinue | Remove-NetFirewallRule
Write-Host "   Old rules removed" -ForegroundColor Green

# Add Hyper-V firewall rule (Windows 11 with Hyper-V)
Write-Host "`n2. Adding Hyper-V firewall rule..." -ForegroundColor Yellow
try {
    New-NetFirewallHyperVRule -Name "WSL2Ports" -DisplayName "WSL2 Web Services" -Direction Inbound -VMCreatorId '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -Protocol TCP -LocalPorts 3000,8000 -ErrorAction Stop
    Write-Host "   [OK] Hyper-V rule added successfully" -ForegroundColor Green
} catch {
    Write-Host "   [INFO] Hyper-V rule failed (expected on older Windows): $($_.Exception.Message.Split("`n")[0])" -ForegroundColor Yellow
    Write-Host "   Falling back to subnet-based rule..." -ForegroundColor Yellow

    # Fallback: Allow all traffic to WSL subnet
    New-NetFirewallRule -DisplayName "WSL2 Network Access" -Direction Outbound -Action Allow -RemoteAddress 192.168.65.0/24,192.168.68.0/24 -Protocol TCP -ErrorAction SilentlyContinue
    Write-Host "   [OK] Subnet-based outbound rule added" -ForegroundColor Green
}

# Also add a rule to allow inbound from WSL subnet
Write-Host "`n3. Adding inbound rule from WSL subnet..." -ForegroundColor Yellow
New-NetFirewallRule -DisplayName "WSL2 Inbound" -Direction Inbound -Action Allow -RemoteAddress 192.168.65.0/24,192.168.68.0/24 -Protocol TCP -ErrorAction SilentlyContinue
Write-Host "   [OK] Inbound rule added" -ForegroundColor Green

Write-Host "`n=== Firewall Configuration Complete ===" -ForegroundColor Cyan
Write-Host "`nTesting connection..." -ForegroundColor Yellow

# Test connection
Start-Sleep -Seconds 1
$wslIp = "192.168.65.3"
try {
    $response = Invoke-WebRequest -Uri "http://${wslIp}:8000/health" -TimeoutSec 5 -UseBasicParsing
    Write-Host "   [OK] Connection successful! Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "`nYou can now access the browser UI at: http://localhost:3000" -ForegroundColor Cyan
} catch {
    Write-Host "   [FAIL] Connection still failing: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nIf this persists, you may need to:" -ForegroundColor Yellow
    Write-Host "   1. Disable Windows Firewall temporarily to test" -ForegroundColor Gray
    Write-Host "   2. Check Docker Desktop network settings" -ForegroundColor Gray
    Write-Host "   3. Restart WSL: wsl --shutdown" -ForegroundColor Gray
}
