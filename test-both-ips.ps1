# Test both possible WSL IPs
$ip1 = "192.168.65.3"
$ip2 = "192.168.68.66"

Write-Host "`n=== Testing Both WSL IPs ===" -ForegroundColor Cyan

foreach ($ip in @($ip1, $ip2)) {
    Write-Host "`nTesting IP: $ip" -ForegroundColor Yellow

    # Test port 8000
    Write-Host "  Port 8000: " -NoNewline
    try {
        $response = Invoke-WebRequest -Uri "http://${ip}:8000/health" -TimeoutSec 3 -UseBasicParsing
        Write-Host "[OK] Status $($response.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "[FAIL] $($_.Exception.Message.Split("`n")[0])" -ForegroundColor Red
    }

    # Test port 3000
    Write-Host "  Port 3000: " -NoNewline
    try {
        $response = Invoke-WebRequest -Uri "http://${ip}:3000/" -TimeoutSec 3 -UseBasicParsing
        Write-Host "[OK] Status $($response.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "[FAIL] $($_.Exception.Message.Split("`n")[0])" -ForegroundColor Red
    }
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan
