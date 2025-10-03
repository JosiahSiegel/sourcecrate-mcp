# Comprehensive WSL2 Firewall Fix and Test Script
# Run as Administrator in Windows PowerShell

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  WSL2 Docker Desktop Firewall Fix & Test" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# Step 1: Show current state
Write-Host "STEP 1: Current State" -ForegroundColor Yellow
Write-Host "--------------------" -ForegroundColor Gray
Write-Host "WSL Distributions:" -ForegroundColor Gray
wsl -l -v
Write-Host ""

$wslIpRaw = wsl -d docker-desktop sh -c "ip addr show eth0 2>/dev/null | grep 'inet ' | head -1"
if ($wslIpRaw -match 'inet\s+(\d+\.\d+\.\d+\.\d+)') {
    $wslIp = $matches[1]
} else {
    $wslIp = "192.168.65.3"  # Default fallback
}
Write-Host "Docker Desktop WSL IP: $wslIp" -ForegroundColor Green

Write-Host "`nExisting WSL Firewall Rules:" -ForegroundColor Gray
$existingRules = Get-NetFirewallRule -DisplayName "*WSL*" -ErrorAction SilentlyContinue
if ($existingRules) {
    $existingRules | Select-Object DisplayName, Direction, Action, Enabled | Format-Table -AutoSize
} else {
    Write-Host "  (none found)" -ForegroundColor Gray
}

# Step 2: Test BEFORE fix
Write-Host "`nSTEP 2: Test Connection (BEFORE Fix)" -ForegroundColor Yellow
Write-Host "------------------------------------" -ForegroundColor Gray
Write-Host "Testing $wslIp`:8000 ... " -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://${wslIp}:8000/health" -TimeoutSec 3 -UseBasicParsing
    Write-Host "[OK] Status $($response.StatusCode)" -ForegroundColor Green
    $needsFix = $false
} catch {
    Write-Host "[FAIL] $($_.Exception.Message.Split("`n")[0])" -ForegroundColor Red
    $needsFix = $true
}

if (-not $needsFix) {
    Write-Host "`n[SUCCESS] Connection already works! No fix needed." -ForegroundColor Green
    Write-Host "Browser UI available at: http://localhost:3000" -ForegroundColor Cyan
    exit 0
}

# Step 3: Apply fixes
Write-Host "`nSTEP 3: Applying Firewall Fixes" -ForegroundColor Yellow
Write-Host "--------------------------------" -ForegroundColor Gray

# Remove old rules
Write-Host "Removing old rules ... " -NoNewline
Get-NetFirewallRule -DisplayName "*WSL*" -ErrorAction SilentlyContinue | Remove-NetFirewallRule -ErrorAction SilentlyContinue
Write-Host "[DONE]" -ForegroundColor Green

# Try Hyper-V rule first (modern Windows 11)
Write-Host "Adding Hyper-V rule ... " -NoNewline
try {
    New-NetFirewallHyperVRule -Name "WSL2Services" -DisplayName "WSL2 Web Services" `
        -Direction Inbound -VMCreatorId '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' `
        -Protocol TCP -LocalPorts 3000,8000 -ErrorAction Stop | Out-Null
    Write-Host "[OK]" -ForegroundColor Green
    $hyperVSuccess = $true
} catch {
    Write-Host "[SKIP] (not available)" -ForegroundColor Yellow
    $hyperVSuccess = $false
}

# Add subnet-based rules as fallback/supplement
Write-Host "Adding subnet rules ... " -NoNewline
New-NetFirewallRule -DisplayName "Allow WSL2 Internal Traffic" -Direction Inbound `
    -Action Allow -RemoteAddress 192.168.65.0/24,192.168.68.0/24 -Protocol TCP `
    -ErrorAction SilentlyContinue | Out-Null
New-NetFirewallRule -DisplayName "Allow WSL2 Internal Traffic" -Direction Outbound `
    -Action Allow -RemoteAddress 192.168.65.0/24,192.168.68.0/24 -Protocol TCP `
    -ErrorAction SilentlyContinue | Out-Null
Write-Host "[OK]" -ForegroundColor Green

# Add port-specific rules for good measure
Write-Host "Adding port rules ... " -NoNewline
New-NetFirewallRule -DisplayName "WSL2 Port 3000" -Direction Inbound `
    -Action Allow -Protocol TCP -LocalPort 3000 -ErrorAction SilentlyContinue | Out-Null
New-NetFirewallRule -DisplayName "WSL2 Port 8000" -Direction Inbound `
    -Action Allow -Protocol TCP -LocalPort 8000 -ErrorAction SilentlyContinue | Out-Null
Write-Host "[OK]" -ForegroundColor Green

# Step 4: Test AFTER fix
Write-Host "`nSTEP 4: Test Connection (AFTER Fix)" -ForegroundColor Yellow
Write-Host "-----------------------------------" -ForegroundColor Gray
Start-Sleep -Seconds 1

$testResults = @{
    "Port 8000" = $false
    "Port 3000" = $false
    "Streaming" = $false
}

Write-Host "Testing port 8000 ... " -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://${wslIp}:8000/health" -TimeoutSec 5 -UseBasicParsing
    Write-Host "[OK] Status $($response.StatusCode)" -ForegroundColor Green
    $testResults["Port 8000"] = $true
} catch {
    Write-Host "[FAIL] $($_.Exception.Message.Split("`n")[0])" -ForegroundColor Red
}

Write-Host "Testing port 3000 ... " -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://${wslIp}:3000/" -TimeoutSec 5 -UseBasicParsing
    Write-Host "[OK] Status $($response.StatusCode)" -ForegroundColor Green
    $testResults["Port 3000"] = $true
} catch {
    Write-Host "[FAIL] $($_.Exception.Message.Split("`n")[0])" -ForegroundColor Red
}

Write-Host "Testing streaming ... " -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://${wslIp}:8000/api/v1/search/stream?query=test&limit=2" -TimeoutSec 8 -UseBasicParsing
    Write-Host "[OK] Status $($response.StatusCode)" -ForegroundColor Green
    $testResults["Streaming"] = $true
} catch {
    Write-Host "[FAIL] $($_.Exception.Message.Split("`n")[0])" -ForegroundColor Red
}

# Step 5: Summary
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  RESULTS" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

$allPassed = ($testResults.Values -notcontains $false)

if ($allPassed) {
    Write-Host "`n[SUCCESS] All tests passed!" -ForegroundColor Green
    Write-Host "`nBrowser UI is now available at:" -ForegroundColor Cyan
    Write-Host "  http://localhost:3000" -ForegroundColor White
    Write-Host "`nAPI server accessible at:" -ForegroundColor Cyan
    Write-Host "  http://${wslIp}:8000" -ForegroundColor White
} else {
    Write-Host "`n[PARTIAL] Some tests failed" -ForegroundColor Yellow
    Write-Host "`nTest Results:" -ForegroundColor Gray
    foreach ($test in $testResults.GetEnumerator()) {
        $status = if ($test.Value) { "[PASS]" } else { "[FAIL]" }
        $color = if ($test.Value) { "Green" } else { "Red" }
        Write-Host "  $status $($test.Key)" -ForegroundColor $color
    }

    Write-Host "`nTroubleshooting:" -ForegroundColor Yellow
    Write-Host "  1. Temporarily disable Windows Firewall and test" -ForegroundColor Gray
    Write-Host "  2. Restart WSL: wsl --shutdown" -ForegroundColor Gray
    Write-Host "  3. Check if servers are running in WSL: wsl -d docker-desktop ss -tlnp | grep ':8000'" -ForegroundColor Gray
    Write-Host "  4. Try accessing directly: http://${wslIp}:3000" -ForegroundColor Gray
}

Write-Host "`n============================================`n" -ForegroundColor Cyan
