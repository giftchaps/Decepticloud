# Complete Local Testing Script for DeceptiCloud (Windows PowerShell)
# This script runs all tests in sequence with validation

param(
    [switch]$SkipSetup = $false,
    [switch]$Verbose = $false
)

# Colors
$ErrorColor = "Red"
$SuccessColor = "Green"
$WarningColor = "Yellow"
$InfoColor = "Cyan"

function Print-Status {
    param([string]$Message)
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] " -ForegroundColor $InfoColor -NoNewline
    Write-Host $Message
}

function Print-Success {
    param([string]$Message)
    Write-Host "✓ " -ForegroundColor $SuccessColor -NoNewline
    Write-Host $Message
}

function Print-Error {
    param([string]$Message)
    Write-Host "✗ " -ForegroundColor $ErrorColor -NoNewline
    Write-Host $Message
}

function Print-Warning {
    param([string]$Message)
    Write-Host "⚠ " -ForegroundColor $WarningColor -NoNewline
    Write-Host $Message
}

Write-Host "==========================================" -ForegroundColor $InfoColor
Write-Host "DeceptiCloud Complete Local Test Suite" -ForegroundColor $InfoColor
Write-Host "==========================================" -ForegroundColor $InfoColor
Write-Host ""

# Step 1: Check prerequisites
Print-Status "Checking prerequisites..."

# Check Docker
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Print-Success "Docker found: $dockerVersion"
    } else {
        throw "Docker not responding"
    }
} catch {
    Print-Error "Docker not found or not running. Please install/start Docker Desktop."
    exit 1
}

# Check Python
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Print-Success "Python found: $pythonVersion"
    } else {
        throw "Python not found"
    }
} catch {
    Print-Error "Python not found. Please install Python 3.8+."
    exit 1
}

# Check if in correct directory
if (-not (Test-Path "main_local.py")) {
    Print-Error "Please run this script from the DeceptiCloud root directory"
    exit 1
}

# Step 2: Setup environment
if (-not $SkipSetup) {
    Print-Status "Setting up environment..."

    # Create directories
    $dirs = @(
        "data\cowrie\logs",
        "data\cowrie\downloads",
        "data\cowrie\etc",
        "data\nginx\logs",
        "data\nginx\content"
    )

    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }

    Print-Success "Directories created"

    # Create web content
    $indexHtml = @"
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Production API Gateway</title>
</head>
<body>
    <h1>Production API Gateway</h1>
    <p class="status">✓ All Systems Operational</p>
    <p>Build: v1.2.3-a4f8d9c</p>
</body>
</html>
"@
    $indexHtml | Out-File -FilePath "data\nginx\content\index.html" -Encoding UTF8

    $envFile = @"
# Production Environment Configuration
APP_ENV=production
DB_PASSWORD=HONEYTOKEN_DB_Pass_Prod_2024_FAKE
AWS_ACCESS_KEY_ID=AKIA3OEXAMPLEKEY123
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
STRIPE_KEY=sk_live_EXAMPLE123456789_HONEYTOKEN_FAKE
"@
    $envFile | Out-File -FilePath "data\nginx\content\.env" -Encoding UTF8

    Print-Success "Web content created"
}

# Step 3: Start honeypots
Print-Status "Starting honeypots..."
docker-compose -f docker-compose.local.yml up -d

if ($LASTEXITCODE -ne 0) {
    Print-Error "Failed to start honeypots"
    exit 1
}

Print-Status "Waiting 30 seconds for containers to initialize..."
for ($i = 30; $i -gt 0; $i--) {
    Write-Host "`r  $i seconds remaining..." -NoNewline
    Start-Sleep -Seconds 1
}
Write-Host "`r" -NoNewline
Print-Success "Containers initialized"

# Step 4: Check container status
Print-Status "Checking container health..."

$cowrieRunning = docker ps --filter "name=cowrie_honeypot_local" --format "{{.Names}}" 2>$null
$nginxRunning = docker ps --filter "name=nginx_honeypot_local" --format "{{.Names}}" 2>$null

if ($cowrieRunning -match "cowrie_honeypot_local") {
    Print-Success "Cowrie SSH honeypot: running"
} else {
    Print-Error "Cowrie SSH honeypot: not running"
}

if ($nginxRunning -match "nginx_honeypot_local") {
    Print-Success "nginx web honeypot: running"
} else {
    Print-Error "nginx web honeypot: not running"
}

# Step 5: Test SSH honeypot connectivity
Print-Status "Testing SSH honeypot connectivity..."
$sshTest = Test-NetConnection -ComputerName localhost -Port 2222 -WarningAction SilentlyContinue
if ($sshTest.TcpTestSucceeded) {
    Print-Success "SSH honeypot listening on port 2222"
} else {
    Print-Warning "SSH honeypot port 2222 not accessible"
}

# Step 6: Test web honeypot connectivity
Print-Status "Testing web honeypot connectivity..."
try {
    $webResponse = Invoke-WebRequest -Uri "http://localhost:8080/" -UseBasicParsing -ErrorAction Stop
    Print-Success "Web honeypot responding on port 8080"

    # Test honeytoken
    $envResponse = Invoke-WebRequest -Uri "http://localhost:8080/.env" -UseBasicParsing -ErrorAction SilentlyContinue
    if ($envResponse.Content -match "AWS_ACCESS_KEY_ID") {
        Print-Success "Honeytokens accessible (.env file)"
    } else {
        Print-Warning "Honeytokens not found"
    }
} catch {
    Print-Warning "Web honeypot port 8080 not accessible"
}

# Step 7: Run automated tests
Print-Status "Running automated honeypot tests..."
python scripts\test_local_honeypots.py
if ($LASTEXITCODE -eq 0) {
    Print-Success "Automated tests completed"
}

# Step 8: Generate attack traffic
Print-Status "Generating attack traffic for testing..."

# Web attacks
Print-Status "Simulating web attacks..."
$paths = @("/", "/admin", "/.env", "/robots.txt", "/.git/config")
foreach ($path in $paths) {
    try {
        Invoke-WebRequest -Uri "http://localhost:8080$path" -UseBasicParsing -ErrorAction SilentlyContinue | Out-Null
    } catch {
        # Ignore errors
    }
    Start-Sleep -Milliseconds 500
}

Start-Sleep -Seconds 3

# Step 9: Check logs
Print-Status "Checking honeypot logs..."

$cowrieLogs = docker logs --tail 20 cowrie_honeypot_local 2>&1
$nginxLogs = docker logs --tail 20 nginx_honeypot_local 2>&1

if ($cowrieLogs -match "ssh|connection|login") {
    Print-Success "Cowrie logs contain activity"
} else {
    Print-Warning "Cowrie logs appear empty"
}

if ($nginxLogs -match "GET|POST|404") {
    Print-Success "nginx logs contain activity"
} else {
    Print-Warning "nginx logs appear empty"
}

# Step 10: Test RL agent (short run)
Print-Status "Testing RL agent (2 episodes)..."
python main_local.py --episodes 2 --timesteps 5
if ($LASTEXITCODE -eq 0) {
    Print-Success "RL agent completed test run"
} else {
    Print-Error "RL agent failed"
}

# Step 11: Summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor $InfoColor
Write-Host "Test Summary" -ForegroundColor $InfoColor
Write-Host "==========================================" -ForegroundColor $InfoColor
Write-Host ""

Write-Host "Honeypot Status:"
Write-Host "  Cowrie (SSH): " -NoNewline
if ($cowrieRunning) { Write-Host "running" -ForegroundColor $SuccessColor } else { Write-Host "stopped" -ForegroundColor $ErrorColor }
Write-Host "  nginx (web):  " -NoNewline
if ($nginxRunning) { Write-Host "running" -ForegroundColor $SuccessColor } else { Write-Host "stopped" -ForegroundColor $ErrorColor }
Write-Host ""

Write-Host "Access Points:"
Write-Host "  SSH honeypot:  ssh -p 2222 root@localhost"
Write-Host "  Web honeypot:  http://localhost:8080"
Write-Host ""

Write-Host "View Logs:"
Write-Host "  docker logs -f cowrie_honeypot_local"
Write-Host "  docker logs -f nginx_honeypot_local"
Write-Host ""

Write-Host "Results:"
if (Test-Path "results\local_timesteps.csv") {
    Print-Success "Training results: results\local_timesteps.csv"
} else {
    Print-Warning "No training results found"
}

$testResults = Get-ChildItem -Path . -Filter "local_test_results_*.json" -ErrorAction SilentlyContinue | Select-Object -Last 1
if ($testResults) {
    Print-Success "Test results: $($testResults.Name)"
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor $SuccessColor
Write-Host "Testing Complete!" -ForegroundColor $SuccessColor
Write-Host "==========================================" -ForegroundColor $SuccessColor
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Run full training: python main_local.py --episodes 10"
Write-Host "  2. View results: type results\local_episodes.csv"
Write-Host "  3. Stop honeypots: docker-compose -f docker-compose.local.yml down"
Write-Host ""
