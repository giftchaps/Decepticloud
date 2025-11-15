# Complete infrastructure setup script for DeceptiCloud
param(
    [Parameter(Mandatory=$true)]
    [string]$KeyName,
    
    [string]$Region = "us-east-1",
    [string]$InstanceType = "t2.micro",
    [string]$S3BucketName = "",
    [switch]$CreateS3Bucket,
    [switch]$SkipInit
)

$here = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootDir = Split-Path -Parent $here

Write-Host "=== DeceptiCloud Infrastructure Setup ===" -ForegroundColor Green

# Step 1: Initialize Terraform (unless skipped)
if (-not $SkipInit) {
    Write-Host "`nStep 1: Initializing Terraform..." -ForegroundColor Cyan
    & $here\terraform_init.ps1 -Region $Region
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Terraform initialization failed!" -ForegroundColor Red
        exit 1
    }
}

# Step 2: Plan the deployment
Write-Host "`nStep 2: Planning deployment..." -ForegroundColor Cyan
$planArgs = @{
    KeyName = $KeyName
    Region = $Region
    InstanceType = $InstanceType
    Plan = $true
}
if ($CreateS3Bucket) {
    $planArgs.CreateS3Bucket = $true
    $planArgs.S3BucketName = $S3BucketName
}

& $here\terraform_apply.ps1 @planArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "Terraform plan failed!" -ForegroundColor Red
    exit 1
}

# Step 3: Confirm and apply
Write-Host "`nStep 3: Ready to deploy infrastructure" -ForegroundColor Yellow
Write-Host "This will create AWS resources that may incur charges." -ForegroundColor Yellow
$confirm = Read-Host "Continue with deployment? (yes/no)"

if ($confirm -eq "yes") {
    $planArgs.Remove('Plan')
    $planArgs.AutoApprove = $true
    & $here\terraform_apply.ps1 @planArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n=== Setup Complete! ===" -ForegroundColor Green
        Write-Host "Infrastructure deployed successfully." -ForegroundColor Green
        Write-Host "`nNext steps:" -ForegroundColor Cyan
        Write-Host "1. Copy the public_ip from the output above"
        Write-Host "2. Update main.py with your EC2 details"
        Write-Host "3. Run experiment: .\scripts\run_experiment.ps1 -EC2Host <public_ip> -KeyFile <path_to_key>"
        Write-Host "`nTo destroy resources later: .\scripts\terraform_destroy.ps1 -AutoApprove"
    }
} else {
    Write-Host "Deployment cancelled." -ForegroundColor Yellow
}