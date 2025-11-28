# Simple DeceptiCloud Test Script
param(
    [int]$Episodes = 3,
    [int]$Timesteps = 5
)

Write-Host "DeceptiCloud Simple Test" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Green

# Check containers
Write-Host "Checking containers..." -ForegroundColor Yellow
$containers = docker ps --filter "name=local" --format "{{.Names}}"
Write-Host "Running containers: $containers"

# Test connectivity
Write-Host "Testing connectivity..." -ForegroundColor Yellow
$sshTest = Test-NetConnection localhost -Port 2222 -WarningAction SilentlyContinue
$webTest = Test-NetConnection localhost -Port 8080 -WarningAction SilentlyContinue

if ($sshTest.TcpTestSucceeded) {
    Write-Host "SSH honeypot: OK" -ForegroundColor Green
} else {
    Write-Host "SSH honeypot: FAIL" -ForegroundColor Red
}

if ($webTest.TcpTestSucceeded) {
    Write-Host "Web honeypot: OK" -ForegroundColor Green
} else {
    Write-Host "Web honeypot: FAIL" -ForegroundColor Red
}

# Generate some test traffic
Write-Host "Generating test traffic..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri "http://localhost:8080/" -UseBasicParsing -ErrorAction SilentlyContinue | Out-Null
    Invoke-WebRequest -Uri "http://localhost:8080/.env" -UseBasicParsing -ErrorAction SilentlyContinue | Out-Null
    Invoke-WebRequest -Uri "http://localhost:8080/admin" -UseBasicParsing -ErrorAction SilentlyContinue | Out-Null
    Write-Host "Web traffic generated" -ForegroundColor Green
} catch {
    Write-Host "Web traffic failed" -ForegroundColor Red
}

# Run training
Write-Host "Running RL training..." -ForegroundColor Yellow
Write-Host "Command: python main_local.py --episodes $Episodes --timesteps $Timesteps"

# Activate virtual environment and run
$env:PYTHONIOENCODING = "utf-8"
& ".\.venv\Scripts\Activate.ps1"
python main_local.py --episodes $Episodes --timesteps $Timesteps

if ($LASTEXITCODE -eq 0) {
    Write-Host "Training completed successfully!" -ForegroundColor Green
} else {
    Write-Host "Training failed!" -ForegroundColor Red
}

# Show results
if (Test-Path "results\local_episodes.csv") {
    Write-Host "Results:" -ForegroundColor Yellow
    Get-Content "results\local_episodes.csv" | Select-Object -Last 5
}

Write-Host "Test completed!" -ForegroundColor Green