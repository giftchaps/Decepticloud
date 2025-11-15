# PowerShell script to apply Terraform configuration
param(
    [string]$Region = "us-east-1",
    [string]$KeyName = "",
    [string]$InstanceType = "t2.micro",
    [string]$S3BucketName = "",
    [switch]$CreateS3Bucket,
    [switch]$AutoApprove,
    [switch]$Plan
)

$here = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $here\..\infra

Write-Host "=== DeceptiCloud Terraform Apply ===" -ForegroundColor Green

# Validate required parameters
if (-not $KeyName) {
    Write-Host "ERROR: -KeyName is required (your EC2 key pair name)" -ForegroundColor Red
    exit 1
}

if ($CreateS3Bucket -and -not $S3BucketName) {
    Write-Host "ERROR: -S3BucketName is required when -CreateS3Bucket is specified" -ForegroundColor Red
    exit 1
}

# Build terraform command
$tfVars = @(
    "-var", "region=$Region"
    "-var", "key_name=$KeyName"
    "-var", "instance_type=$InstanceType"
)

if ($CreateS3Bucket) {
    $tfVars += "-var", "create_s3_bucket=true"
    $tfVars += "-var", "s3_bucket_name=$S3BucketName"
}

if ($Plan) {
    Write-Host "Running terraform plan..." -ForegroundColor Yellow
    & terraform plan @tfVars
} else {
    Write-Host "Applying Terraform configuration..." -ForegroundColor Yellow
    if ($AutoApprove) {
        & terraform apply -auto-approve @tfVars
    } else {
        & terraform apply @tfVars
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n=== Deployment Complete ===" -ForegroundColor Green
        Write-Host "Getting outputs..." -ForegroundColor Yellow
        & terraform output
        
        Write-Host "`nNext steps:" -ForegroundColor Cyan
        Write-Host "1. Note the public_ip and instance_id from above"
        Write-Host "2. Update your main.py with the EC2 details"
        Write-Host "3. Run: .\scripts\run_experiment.ps1 -Host <public_ip> -KeyFile <path_to_key>"
    }
}