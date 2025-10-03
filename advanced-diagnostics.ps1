# Advanced WSL2 Network Diagnostics and Fix
# Run as Administrator in Windows PowerShell
# This script identifies why Windows can't reach WSL2 services

param(
    [switch]$AutoFix = $false
)

$ErrorActionPreference = "Continue"

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  WSL2 Advanced Network Diagnostics" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# Get WSL IP
$wslIpRaw = wsl -d docker-desktop sh -c "ip addr show eth0 2>/dev/null | grep 'inet ' | head -1"
if ($wslIpRaw -match 'inet\s+(\d+\.\d+\.\d+\.\d+)') {
    $wslIp = $matches[1]
} else {
    $wslIp = "192.168.65.3"
}
Write-Host "Target WSL IP: $wslIp" -ForegroundColor Green
Write-Host ""

# Diagnostic Results
$diagnostics = @{}

# ============================================
# DIAGNOSTIC 1: Windows Firewall Status
# ============================================
Write-Host "DIAGNOSTIC 1: Windows Firewall Status" -ForegroundColor Yellow
Write-Host "--------------------------------------" -ForegroundColor Gray

$firewallProfiles = Get-NetFirewallProfile
foreach ($profile in $firewallProfiles) {
    $status = if ($profile.Enabled) { "ENABLED" } else { "DISABLED" }
    $color = if ($profile.Enabled) { "Red" } else { "Green" }
    Write-Host "  $($profile.Name) Profile: $status" -ForegroundColor $color
}
$diagnostics["FirewallEnabled"] = ($firewallProfiles | Where-Object { $_.Enabled }).Count -gt 0

# ============================================
# DIAGNOSTIC 2: Network Adapter Profiles
# ============================================
Write-Host "`nDIAGNOSTIC 2: Network Adapter Profiles" -ForegroundColor Yellow
Write-Host "---------------------------------------" -ForegroundColor Gray

$adapters = Get-NetConnectionProfile
$wslAdapter = $adapters | Where-Object { $_.InterfaceAlias -like "*WSL*" -or $_.InterfaceAlias -like "*vEthernet*" }

if ($wslAdapter) {
    foreach ($adapter in $wslAdapter) {
        $color = if ($adapter.NetworkCategory -eq "Public") { "Red" } else { "Green" }
        Write-Host "  $($adapter.InterfaceAlias): $($adapter.NetworkCategory)" -ForegroundColor $color
        if ($adapter.NetworkCategory -eq "Public") {
            Write-Host "    ^ PUBLIC profile blocks most traffic!" -ForegroundColor Red
        }
    }
    $diagnostics["WSLAdapterPublic"] = ($wslAdapter | Where-Object { $_.NetworkCategory -eq "Public" }).Count -gt 0
} else {
    Write-Host "  No WSL/vEthernet adapter found in connection profiles" -ForegroundColor Yellow
    $diagnostics["WSLAdapterPublic"] = $false
}

# ============================================
# DIAGNOSTIC 3: Test with Firewall Disabled
# ============================================
Write-Host "`nDIAGNOSTIC 3: Test Connection (Current State)" -ForegroundColor Yellow
Write-Host "----------------------------------------------" -ForegroundColor Gray

Write-Host "  Testing $wslIp`:8000 ... " -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://${wslIp}:8000/health" -TimeoutSec 3 -UseBasicParsing
    Write-Host "[OK]" -ForegroundColor Green
    $diagnostics["CurrentlyWorking"] = $true
} catch {
    Write-Host "[FAIL]" -ForegroundColor Red
    $diagnostics["CurrentlyWorking"] = $false
}

if (-not $diagnostics["CurrentlyWorking"] -and $diagnostics["FirewallEnabled"]) {
    Write-Host "`n  Would you like to temporarily disable Windows Firewall to test?" -ForegroundColor Yellow
    Write-Host "  (Type 'yes' to test, anything else to skip): " -NoNewline
    $response = Read-Host

    if ($response -eq "yes") {
        Write-Host "  Disabling firewall temporarily ... " -NoNewline
        Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False
        Write-Host "[DONE]" -ForegroundColor Green

        Start-Sleep -Seconds 1
        Write-Host "  Testing $wslIp`:8000 ... " -NoNewline
        try {
            $testResponse = Invoke-WebRequest -Uri "http://${wslIp}:8000/health" -TimeoutSec 3 -UseBasicParsing
            Write-Host "[OK] - FIREWALL WAS THE BLOCKER!" -ForegroundColor Green
            $diagnostics["FirewallIsBlocker"] = $true
        } catch {
            Write-Host "[FAIL] - Something else is blocking" -ForegroundColor Red
            $diagnostics["FirewallIsBlocker"] = $false
        }

        Write-Host "  Re-enabling firewall ... " -NoNewline
        Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True
        Write-Host "[DONE]" -ForegroundColor Green
    }
}

# ============================================
# DIAGNOSTIC 4: Hyper-V Virtual Switches
# ============================================
Write-Host "`nDIAGNOSTIC 4: Hyper-V Virtual Switches" -ForegroundColor Yellow
Write-Host "---------------------------------------" -ForegroundColor Gray

try {
    $switches = Get-VMSwitch -ErrorAction Stop
    if ($switches) {
        foreach ($switch in $switches) {
            Write-Host "  $($switch.Name): $($switch.SwitchType)" -ForegroundColor Gray
        }
        $wslSwitch = $switches | Where-Object { $_.Name -like "*WSL*" }
        $diagnostics["WSLSwitchExists"] = $wslSwitch -ne $null
    } else {
        Write-Host "  No Hyper-V switches found" -ForegroundColor Yellow
        $diagnostics["WSLSwitchExists"] = $false
    }
} catch {
    Write-Host "  Hyper-V not available or not running" -ForegroundColor Yellow
    $diagnostics["WSLSwitchExists"] = $false
}

# ============================================
# DIAGNOSTIC 5: Check Existing Firewall Rules
# ============================================
Write-Host "`nDIAGNOSTIC 5: Existing WSL Firewall Rules" -ForegroundColor Yellow
Write-Host "------------------------------------------" -ForegroundColor Gray

$wslRules = Get-NetFirewallRule -DisplayName "*WSL*" -ErrorAction SilentlyContinue
if ($wslRules) {
    $enabledRules = $wslRules | Where-Object { $_.Enabled -eq $true }
    Write-Host "  Total WSL rules: $($wslRules.Count)" -ForegroundColor Gray
    Write-Host "  Enabled rules: $($enabledRules.Count)" -ForegroundColor $(if ($enabledRules.Count -gt 0) { "Green" } else { "Red" })
    $diagnostics["HasWSLRules"] = $enabledRules.Count -gt 0
} else {
    Write-Host "  No WSL-specific rules found" -ForegroundColor Red
    $diagnostics["HasWSLRules"] = $false
}

# ============================================
# DIAGNOSTIC 6: Check if ports are reachable via netsh
# ============================================
Write-Host "`nDIAGNOSTIC 6: Port Forwarding Status" -ForegroundColor Yellow
Write-Host "-------------------------------------" -ForegroundColor Gray

$portProxies = netsh interface portproxy show all
if ($portProxies -match "8000" -or $portProxies -match "3000") {
    Write-Host "  Existing port proxies found:" -ForegroundColor Green
    Write-Host $portProxies -ForegroundColor Gray
    $diagnostics["HasPortProxy"] = $true
} else {
    Write-Host "  No port proxies configured" -ForegroundColor Yellow
    $diagnostics["HasPortProxy"] = $false
}

# ============================================
# ANALYSIS & RECOMMENDATIONS
# ============================================
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  ANALYSIS & RECOMMENDATIONS" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

$rootCause = $null
$fixCommands = @()

if ($diagnostics["CurrentlyWorking"]) {
    Write-Host "[SUCCESS] Connection is working! No fix needed." -ForegroundColor Green
    exit 0
}

if ($diagnostics.ContainsKey("FirewallIsBlocker") -and $diagnostics["FirewallIsBlocker"]) {
    Write-Host "[ROOT CAUSE] Windows Firewall is blocking the connection" -ForegroundColor Red
    $rootCause = "firewall"

    if ($diagnostics["WSLAdapterPublic"]) {
        Write-Host "`nRECOMMENDED FIX: Change WSL network to Private profile" -ForegroundColor Yellow
        Write-Host "----------------------------------------" -ForegroundColor Gray
        Write-Host "The WSL network adapter is on Public profile, which blocks all inbound traffic." -ForegroundColor Gray
        Write-Host ""
        Write-Host "Run this command to change it to Private:" -ForegroundColor Cyan

        $setProfileCmd = 'Get-NetConnectionProfile | Where-Object { $_.InterfaceAlias -like "*WSL*" -or $_.InterfaceAlias -like "*vEthernet*" } | Set-NetConnectionProfile -NetworkCategory Private'
        Write-Host $setProfileCmd -ForegroundColor White
        $fixCommands += $setProfileCmd
    } else {
        Write-Host "`nRECOMMENDED FIX: Add Hyper-V Firewall Rule" -ForegroundColor Yellow
        Write-Host "-------------------------------------------" -ForegroundColor Gray
        Write-Host "Add a Hyper-V firewall rule for WSL2 VM:" -ForegroundColor Gray
        Write-Host ""

        $hyperVCmd = "New-NetFirewallHyperVRule -Name 'WSL2Services' -DisplayName 'WSL2 Web Services' -Direction Inbound -VMCreatorId '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -Protocol TCP -LocalPorts 3000,8000"
        Write-Host $hyperVCmd -ForegroundColor White
        $fixCommands += $hyperVCmd
    }
} elseif (-not $diagnostics["HasWSLRules"]) {
    Write-Host "[LIKELY CAUSE] No firewall rules exist for WSL" -ForegroundColor Red
    $rootCause = "no_rules"

    Write-Host "`nRECOMMENDED FIX: Add multiple firewall rules" -ForegroundColor Yellow
    Write-Host "---------------------------------------------" -ForegroundColor Gray

    $fixCommands += "New-NetFirewallRule -DisplayName 'WSL2 Port 8000' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000"
    $fixCommands += "New-NetFirewallRule -DisplayName 'WSL2 Port 3000' -Direction Inbound -Action Allow -Protocol TCP -LocalPort 3000"

    foreach ($cmd in $fixCommands) {
        Write-Host $cmd -ForegroundColor White
        Write-Host ""
    }
} else {
    Write-Host "[UNKNOWN CAUSE] Firewall rules exist but connection still fails" -ForegroundColor Yellow
    $rootCause = "unknown"

    Write-Host "`nWORKAROUND: Use netsh port proxy" -ForegroundColor Yellow
    Write-Host "---------------------------------" -ForegroundColor Gray
    Write-Host "Forward localhost ports to WSL IP:" -ForegroundColor Gray
    Write-Host ""

    $fixCommands += "netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$wslIp"
    $fixCommands += "netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=$wslIp"

    foreach ($cmd in $fixCommands) {
        Write-Host $cmd -ForegroundColor White
        Write-Host ""
    }

    Write-Host "Note: Port proxies must be recreated after WSL IP changes" -ForegroundColor Yellow
}

# Auto-fix option
if ($AutoFix -and $fixCommands.Count -gt 0) {
    Write-Host "`n[AUTO-FIX] Applying recommended fixes..." -ForegroundColor Cyan
    foreach ($cmd in $fixCommands) {
        Write-Host "Executing: $cmd" -ForegroundColor Gray
        Invoke-Expression $cmd
    }

    Write-Host "`nTesting connection after fix..." -ForegroundColor Yellow
    Start-Sleep -Seconds 1

    try {
        $response = Invoke-WebRequest -Uri "http://${wslIp}:8000/health" -TimeoutSec 5 -UseBasicParsing
        Write-Host "[SUCCESS] Connection now works!" -ForegroundColor Green
    } catch {
        Write-Host "[FAIL] Fix didn't work. Manual intervention needed." -ForegroundColor Red
    }
} elseif ($fixCommands.Count -gt 0) {
    Write-Host "`nWould you like to apply these fixes now? (yes/no): " -NoNewline -ForegroundColor Yellow
    $response = Read-Host

    if ($response -eq "yes") {
        foreach ($cmd in $fixCommands) {
            Write-Host "Executing: $cmd" -ForegroundColor Gray
            try {
                Invoke-Expression $cmd
                Write-Host "  [OK]" -ForegroundColor Green
            } catch {
                Write-Host "  [FAIL] $($_.Exception.Message)" -ForegroundColor Red
            }
        }

        Write-Host "`nTesting connection after fix..." -ForegroundColor Yellow
        Start-Sleep -Seconds 1

        try {
            $response = Invoke-WebRequest -Uri "http://${wslIp}:8000/health" -TimeoutSec 5 -UseBasicParsing
            Write-Host "[SUCCESS] Connection now works!" -ForegroundColor Green
            Write-Host "`nBrowser UI available at: http://localhost:3000" -ForegroundColor Cyan
        } catch {
            Write-Host "[FAIL] Connection still not working" -ForegroundColor Red
            Write-Host "`nAdditional troubleshooting:" -ForegroundColor Yellow
            Write-Host "  1. Restart WSL: wsl --shutdown" -ForegroundColor Gray
            Write-Host "  2. Restart Docker Desktop" -ForegroundColor Gray
            Write-Host "  3. Check Docker Desktop settings > Resources > Network" -ForegroundColor Gray
        }
    }
}

Write-Host "`n============================================`n" -ForegroundColor Cyan
