# DeceptiCloud Test with Attack Simulation
Write-Host "DeceptiCloud: Attack Simulation Test" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green

# Start background attack simulation
Write-Host "Starting background attack simulation..." -ForegroundColor Yellow

# Create attack simulation job
$attackJob = Start-Job -ScriptBlock {
    param($duration)
    
    $endTime = (Get-Date).AddSeconds($duration)
    $attackCount = 0
    
    while ((Get-Date) -lt $endTime) {
        try {
            # SSH attacks
            $env:SSH_ASKPASS = ""
            echo "test" | ssh -o ConnectTimeout=2 -o StrictHostKeyChecking=no -p 2222 root@localhost "exit" 2>$null
            
            # Web attacks
            Invoke-WebRequest -Uri "http://localhost:8080/" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue | Out-Null
            Invoke-WebRequest -Uri "http://localhost:8080/.env" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue | Out-Null
            Invoke-WebRequest -Uri "http://localhost:8080/admin" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue | Out-Null
            
            $attackCount++
            Start-Sleep -Seconds 3
        } catch {
            # Continue on errors
        }
    }
    
    return $attackCount
} -ArgumentList 60  # 60 seconds of attacks

Write-Host "Attack simulation started (60 seconds)" -ForegroundColor Green

# Wait a moment for attacks to start
Start-Sleep -Seconds 5

# Run training with attacks happening
Write-Host "Running RL training with live attacks..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"
python main_local.py --episodes 5 --timesteps 8

# Wait for attack job to complete
Write-Host "Waiting for attack simulation to complete..." -ForegroundColor Yellow
$attackResults = Receive-Job -Job $attackJob -Wait
Remove-Job -Job $attackJob

Write-Host "Attack simulation completed. Total attacks: $attackResults" -ForegroundColor Green

# Show final results
Write-Host "`nFinal Results:" -ForegroundColor Cyan
if (Test-Path "results\local_episodes.csv") {
    Write-Host "Training Results:" -ForegroundColor Yellow
    Get-Content "results\local_episodes.csv" | Select-Object -Last 6
}

# Show honeypot logs
Write-Host "`nHoneypot Activity:" -ForegroundColor Yellow
Write-Host "Cowrie SSH Logs (last 10 lines):" -ForegroundColor Cyan
docker logs --tail 10 cowrie_honeypot_local 2>$null | Select-Object -Last 5

Write-Host "`nnginx Web Logs (last 10 lines):" -ForegroundColor Cyan  
docker logs --tail 10 nginx_honeypot_local 2>$null | Select-Object -Last 5

Write-Host "`nTest completed with attack simulation!" -ForegroundColor Green