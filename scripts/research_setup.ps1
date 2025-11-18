# Complete research environment setup script
param(
    [string]$KeyName = "decepticloud-key",
    [string]$Region = "us-east-1",
    [int]$Episodes = 20,
    [switch]$SkipInfrastructure
)

Write-Host "=== DeceptiCloud Research Setup ===" -ForegroundColor Green

# Step 1: Check prerequisites
Write-Host "`n1. Checking prerequisites..." -ForegroundColor Cyan
$missing = @()

if (-not (Get-Command aws -ErrorAction SilentlyContinue)) { $missing += "AWS CLI" }
if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) { $missing += "Terraform" }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { $missing += "Python" }

if ($missing.Count -gt 0) {
    Write-Host "ERROR: Missing required tools: $($missing -join ', ')" -ForegroundColor Red
    Write-Host "Please install missing tools and run again." -ForegroundColor Yellow
    exit 1
}

# Step 2: Create key pair if not exists
Write-Host "`n2. Setting up EC2 key pair..." -ForegroundColor Cyan
if (-not (Test-Path "$KeyName.pem")) {
    Write-Host "Creating new key pair: $KeyName"
    aws ec2 create-key-pair --key-name $KeyName --query 'KeyMaterial' --output text | Out-File -FilePath "$KeyName.pem" -Encoding ASCII
    if ($LASTEXITCODE -eq 0) {
        # Set proper permissions
        icacls "$KeyName.pem" /inheritance:r /grant:r "${env:USERNAME}:R" | Out-Null
        Write-Host "Key pair created successfully" -ForegroundColor Green
    } else {
        Write-Host "Failed to create key pair" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Key pair already exists: $KeyName.pem" -ForegroundColor Green
}

# Step 3: Deploy infrastructure
if (-not $SkipInfrastructure) {
    Write-Host "`n3. Deploying cloud infrastructure..." -ForegroundColor Cyan
    & .\scripts\terraform_init.ps1 -Region $Region
    if ($LASTEXITCODE -ne 0) { exit 1 }
    
    & .\scripts\terraform_apply.ps1 -KeyName $KeyName -Region $Region -AutoApprove
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

# Step 4: Get EC2 details
Write-Host "`n4. Getting EC2 instance details..." -ForegroundColor Cyan
$publicIP = terraform -chdir=infra output -raw public_ip
$instanceId = terraform -chdir=infra output -raw instance_id

if (-not $publicIP) {
    Write-Host "ERROR: Could not get EC2 public IP" -ForegroundColor Red
    exit 1
}

Write-Host "EC2 Public IP: $publicIP" -ForegroundColor Green
Write-Host "Instance ID: $instanceId" -ForegroundColor Green

# Step 5: Wait for instance to be ready
Write-Host "`n5. Waiting for EC2 instance to be ready..." -ForegroundColor Cyan
$maxAttempts = 30
$attempt = 0

do {
    $attempt++
    Write-Host "Attempt $attempt/$maxAttempts - Testing SSH connection..."
    
    $testResult = ssh -i "$KeyName.pem" -o ConnectTimeout=10 -o StrictHostKeyChecking=no ubuntu@$publicIP "echo 'ready'" 2>$null
    
    if ($testResult -eq "ready") {
        Write-Host "EC2 instance is ready!" -ForegroundColor Green
        break
    }
    
    if ($attempt -ge $maxAttempts) {
        Write-Host "ERROR: EC2 instance not responding after $maxAttempts attempts" -ForegroundColor Red
        exit 1
    }
    
    Start-Sleep 10
} while ($true)

# Step 6: Setup Docker on EC2
Write-Host "`n6. Setting up Docker containers on EC2..." -ForegroundColor Cyan
scp -i "$KeyName.pem" -r docker ubuntu@${publicIP}:~/
ssh -i "$KeyName.pem" ubuntu@$publicIP "cd docker && sudo docker-compose build"

# Step 7: Setup local Python environment
Write-Host "`n7. Setting up Python environment..." -ForegroundColor Cyan
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Step 8: Configure experiment
Write-Host "`n8. Configuring research experiment..." -ForegroundColor Cyan
$env:EC2_HOST = $publicIP
$env:EC2_USER = "ubuntu"
$env:EC2_KEY_FILE = "$KeyName.pem"
$env:AWS_REGION = $Region

# Update episodes in main.py for research
$mainContent = Get-Content main.py -Raw
$mainContent = $mainContent -replace 'EPISODES = \d+', "EPISODES = $Episodes"
$mainContent | Set-Content main.py

Write-Host "`n=== Research Environment Ready! ===" -ForegroundColor Green
Write-Host "EC2 Instance: $publicIP" -ForegroundColor Cyan
Write-Host "Episodes configured: $Episodes" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Run experiment: python main.py"
Write-Host "2. Generate attacks: python -c `"from src.attacker import run_attacker_thread; run_attacker_thread('$publicIP', 'ubuntu', '$KeyName.pem')`""
Write-Host "3. Analyze results: jupyter notebook notebooks/01_data_analysis.ipynb"
Write-Host "4. Cleanup when done: .\scripts\terraform_destroy.ps1 -AutoApprove"